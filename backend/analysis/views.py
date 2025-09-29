from django.shortcuts import render
from celery.result import AsyncResult
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AnalyzeRequestSerializer
from .models import AnalyzeRequest
from .tasks import run_analysis_task  # Celery task (or fallback function)

class AnalyzeView(APIView):
    def post(self, request):
        data = request.data
        serializer = AnalyzeRequestSerializer(data={
            'coin': data.get('coin'),
            'message': data.get('message'),
            'timeframe': data.get('timeframe', '24h'),
            'input_payload': data
        })
        if serializer.is_valid():
            ar = serializer.save()
            # Enqueue background task
            task = run_analysis_task.delay(ar.id)
            ar.task_id = task.id
            ar.save()
            return Response({'id': ar.id, 'task_id': str(task.id), 'message': 'Analysis queued'}, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult


class TaskStatusView(APIView):
    def get(self, request, task_id):
        # Directly fetch the task result from Celery
        task_result = AsyncResult(str(task_id))

        # Build response payload
        response_data = {
            "task_id": task_id,
            "celery_state": task_result.state,
            "progress": task_result.info if isinstance(task_result.info, dict) else None,
            "result": task_result.result if task_result.state == "SUCCESS" else None,
        }

        # Handle "not found" tasks
        if task_result.state == "PENDING":
            return Response({"error": "Task not found or still pending"}, status=status.HTTP_404_NOT_FOUND)

        return Response(response_data)
