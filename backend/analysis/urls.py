from django.urls import path
from .views import AnalyzeView, TaskStatusView

urlpatterns = [
    path('analyze/', AnalyzeView.as_view(), name='analyze'),
    path('status/<uuid:task_id>/', TaskStatusView.as_view(), name='task-status'),

]
