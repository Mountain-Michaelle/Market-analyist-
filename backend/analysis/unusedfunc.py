def call_openai_analysis(system_prompt, user_prompt, max_tokens=400):
    resp = client.chat.completions.create(
        model= "gpt-4o-mini", # substitute with available model
        messages=[
            {"role":"system","content": system_prompt},
            {"role":"user","content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    text = resp.choices[0].message.content
    return text


def call_hf_inference(prompt, max_length=200):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_length}}

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    # Hugging Face returns a list of generated texts
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]
    return str(data)


class TaskStatusView(APIView):
    def get(self, request, task_id):
        # task_request = request.query_params.get("task_id")
        try:
            ar = AnalyzeRequest.objects.get(task_id=task_id)
        except AnalyzeRequest.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        # Celery task result object
        task_result = AsyncResult(ar.task_id)
        response_data = {
            "task_request": task_id,
            "id": ar.id,
            "status": ar.status,
            "celery_state": task_result.state,
            "progress": task_result.info if isinstance(task_result.info, dict) else None,
            "result": ar.result if ar.status == "done" else None,
        }
        return Response(response_data)
    


    @shared_task(bind=True)
def run_analysis_task(self, analyze_request_id):
    try:
        ar = AnalyzeRequest.objects.get(pk=analyze_request_id)
        ar.status = 'running'
        ar.save()

        # Step 1: Submitting...
        self.update_state(state="PROGRESS", meta={"step": "Submitting request..."})
        time.sleep(1)

        # Step 2: Fetching price history
        self.update_state(state="PROGRESS", meta={"step": "Fetching price history..."})
        tf = ar.timeframe
        if tf.endswith('h'):
            hours = int(tf[:-1])
            days = max(1, hours // 24)
        elif tf.endswith('d'):
            days = int(tf[:-1])
        else:
            days = 1

        df = fetch_price_history_coin_gecko(ar.coin, days=max(1, days))

        # Step 3: Computing indicators
        self.update_state(state="PROGRESS", meta={"step": "Analyzing technical indicators..."})
        indicators = compute_indicators(df)

        # Step 4: Checking fundamentals
        self.update_state(state="PROGRESS", meta={"step": "Checking fundamentals..."})
        try:
            coin_info = cg.get_coin_by_id(ar.coin, localization=False, tickers=False, market_data=True)
            market_data = coin_info.get('market_data', {})
            fundamentals = {
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'circulating_supply': market_data.get('circulating_supply'),
                'market_cap_rank': coin_info.get('market_cap_rank'),
            }
        except Exception:
            fundamentals = {}

        # Step 5: Calling AI
        self.update_state(state="PROGRESS", meta={"step": "Generating AI analysis..."})
        system_prompt = (
            "You are a helpful, conservative crypto market analyst. "
            "Use the indicators and fundamentals provided to give a short (3-6 bullet) analysis: "
            "1) summary of current technical indicators (RSI/MACD/SMA/Bollinger) 2) short-term directional prediction (next 24h) "
            "3) confidence (0-100) and reason. Keep friendly, concise, and add actionable note."
        )

        user_prompt = f"""
                    Coin: {ar.coin}
                    Timeframe: {ar.timeframe}
                    Indicators: {indicators}
                    Fundamentals: {fundamentals}
                    Recent prices (last 10): {df['price'].tail(10).round(6).to_list()}
                    Give an analysis: 1) quick TL;DR, 2) prediction (up/down/sideways) with percent-like confidence, 3) key reasons, 4) risk notes, 5) suggested action.
                    """
        # prompt = f"{system_prompt}\n{user_prompt}"
        ai_text = ai_text = mock_ai_analysis(indicators, fundamentals)

        # Step 6: Rounding up
        self.update_state(state="PROGRESS", meta={"step": "Rounding up results..."})
        result_payload = {
            'indicators': indicators,
            'fundamentals': fundamentals,
            'ai_analysis': ai_text,
            'timestamp': datetime.datetime.now().isoformat()
        }

        ar.result = result_payload
        ar.status = 'done'
        ar.save()

        # Step 7: Sending email (if provided)
        ar = AnalyzeRequest.objects.get(pk=analyze_request_id)
        to_email = ar.input_payload.get("input_payload", {}).get('email') if ar.input_payload else None
        if to_email:
            self.update_state(state="PROGRESS", meta={"step": f"Sending report to {to_email}..."})
            subject = f"{ar.coin.upper()} Market Outlook ({ar.timeframe})"
            html_body = f"<h2>{ar.coin.upper()} Market Outlook</h2><pre>{ai_text}</pre>"
            send_resend_email(to_email, subject, html_body)
            print(f"{to_email}, email heh ooooooh after send resend function.........")


        return result_payload

    except Exception as e:
        ar = AnalyzeRequest.objects.get(pk=analyze_request_id)
        ar.status = 'failed'
        ar.result = {'error': str(e)}
        ar.save()
        raise
