from rest_framework import serializers
from .models import AnalyzeRequest

class AnalyzeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyzeRequest
        fields = '__all__'
        read_only_fields = ('created_at','status','message', 'result')
