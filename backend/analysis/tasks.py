from celery import shared_task
import time
from .models import AnalyzeRequest
from django.conf import settings
from pycoingecko import CoinGeckoAPI
import pandas as pd
import pandas_ta as ta
import resend
from decouple import config
import datetime
import os
import requests
import numpy as np

cg = CoinGeckoAPI()
resend.api_key = config('RESEND_API_KEY')


def fetch_price_history_coin_gecko(coin_id, days=7, vs_currency='usd'):
    # returns a pandas DataFrame with timestamp & price
    data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
    prices = data['prices']  # list of [timestamp, price]
    df = pd.DataFrame(prices, columns=['ts','price'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df = df.set_index('ts')
    # ensure numeric
    return df

def compute_indicators(df):
    out = {}
    # make a copy with a price column for ta
    s = df['price'].astype(float)
    # Simple moving averages
    out['SMA_10'] = s.rolling(window=10).mean().iloc[-1].item() if len(s)>=10 else None
    out['SMA_50'] = s.rolling(window=50).mean().iloc[-1].item() if len(s)>=50 else None
    # RSI
    try:
        rsi = ta.rsi(s, length=14)
        out['RSI_14'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
    except Exception:
        out['RSI_14'] = None
    # MACD
    try:
        macd = ta.macd(s)
        out['MACD'] = float(macd['MACD_12_26_9'].iloc[-1])
        out['MACD_signal'] = float(macd['MACDs_12_26_9'].iloc[-1])
    except Exception:
        out['MACD'] = out['MACD_signal'] = None
    # Bollinger
    try:
        bb = ta.bbands(s)
        out['BB_upper'] = float(bb['BBU_20_2.0'].iloc[-1])
        out['BB_lower'] = float(bb['BBL_20_2.0'].iloc[-1])
    except Exception:
        out['BB_upper'] = out['BB_lower'] = None
    # last price
    out['last_price'] = float(s.iloc[-1])
    return out

def mock_ai_analysis(indicators, fundamentals):
    # Use basic rules to simulate AI output
    last_price = indicators.get('last_price', 0)
    rsi = indicators.get('RSI_14', 50)
    macd = indicators.get('MACD', 0)
    
    prediction = "up" if rsi < 30 or macd > 0 else "down" if rsi > 70 or macd < 0 else "sideways"
    confidence = min(max(abs(macd)*50, 30), 90)  # just a mock confidence
    bullets = [
        f"Last price: ${last_price:.2f}",
        f"RSI: {rsi}, MACD: {macd:.2f}",
        f"Predicted short-term trend: {prediction}",
        f"Confidence: {confidence:.1f}%",
        "Risk: standard crypto volatility",
        "Suggested action: observe or small trade depending on risk appetite"
    ]
    return "\n".join(bullets)

def send_resend_email(to_email, subject, html_body):
    try:
        response = resend.Emails.send({
            "from": "Acme <onboarding@resend.dev>",
            "to": [to_email],  # list of recipients
            "subject": subject,
            "html": html_body
        })
        # print("Resend response:", response)  # debug
        return {"success":True, "response":response}
    except Exception as e:
        # print("Error sending email with Resend:", e)
        return {"success":False, "error":str(e)}


@shared_task(bind=True)
def run_analysis_task(self, analyze_request_id):
    try:
        # ✅ Fetch AnalyzeRequest from DB
        ar = AnalyzeRequest.objects.get(pk=analyze_request_id)
        ar.status = 'running'
        ar.save()

        # Extract email directly from request payload for reuse
        to_email = None
        if ar.input_payload and "email" in ar.input_payload:
            to_email = ar.input_payload["email"]

        # ---------------- STEP 1 ----------------
        # Added email, coin, timeframe for better frontend context
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Submitting request...",
                "email": to_email,
                "coin": ar.coin,
                "timeframe": ar.timeframe,
            }
        )
        time.sleep(1)

        # ---------------- STEP 2 ----------------
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Fetching price history...",
                "coin": ar.coin,
                "timeframe": ar.timeframe,
                "email": to_email,
            }
        )
        tf = ar.timeframe
        if tf.endswith('h'):
            hours = int(tf[:-1])
            days = max(1, hours // 24)
        elif tf.endswith('d'):
            days = int(tf[:-1])
        else:
            days = 1
        df = fetch_price_history_coin_gecko(ar.coin, days=max(1, days))

        # ---------------- STEP 3 ----------------
        self.update_state(
            state="PROGRESS",
            meta={"step": "Analyzing technical indicators...", "coin": ar.coin}
        )
        indicators = compute_indicators(df)

        # ---------------- STEP 4 ----------------
        self.update_state(
            state="PROGRESS",
            meta={"step": "Checking fundamentals...", "coin": ar.coin}
        )
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

        # ---------------- STEP 5 ----------------
        self.update_state(
            state="PROGRESS",
            meta={"step": "Generating analysis...", "coin": ar.coin}
        )
        ai_text = mock_ai_analysis(indicators, fundamentals)

        # ---------------- STEP 6 ----------------
        self.update_state(
            state="PROGRESS",
            meta={"step": "Rounding up results...", "coin": ar.coin}
        )
        result_payload = {
            'indicators': indicators,
            'fundamentals': fundamentals,
            'ai_analysis': ai_text,
            'timestamp': datetime.datetime.now().isoformat()
        }

        ar.result = result_payload
        ar.status = 'done'
        ar.save()

        # ---------------- STEP 7 (Optional Email) ----------------
        email_status = None 

        if to_email:
            self.update_state(
                state="PROGRESS",
                meta={"step": f"Sending report to {to_email}...", "coin": ar.coin}
            )
            subject = f"{ar.coin.upper()} Market Outlook ({ar.timeframe})"
            html_body = f"<h2>{ar.coin.upper()} Market Outlook</h2><pre>{ai_text}</pre>"

            result = send_resend_email(to_email, subject, html_body)
            
            if result.get("success"):
                email_status = {"success": True, "message": "Email sent successfully"}
            else:
                # ✅ Modified: Capture the error to send back to frontend
                email_status = {"success": False, "error": result.get("error")}

        return {
            "status": "done",
            "coin": ar.coin,
            "timeframe": ar.timeframe,
            "email": to_email,
            "result": result_payload,
            "email_status": email_status  # ✅ Added: frontend can now read this
        }


    except Exception as e:
        # Ensure failures are tracked
        ar = AnalyzeRequest.objects.get(pk=analyze_request_id)
        ar.status = 'failed'
        ar.result = {'error': str(e)}
        ar.save()

        # Celery will serialize the error too
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
