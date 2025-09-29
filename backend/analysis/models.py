from django.db import models

# Create your models here.
from django.db import models

class AnalyzeRequest(models.Model):
    COIN_CHOICES = []  # optional enum list or just free text

    coin = models.CharField(max_length=50)
    message = models.TextField(max_length=500, blank=True, null=True)
    timeframe = models.CharField(max_length=20, default='24h')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    input_payload = models.JSONField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"{id} = {self.coin} => {self.message},"
