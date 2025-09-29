from django.contrib import admin
from .models import AnalyzeRequest
# Register your models here.


@admin.register(AnalyzeRequest)
class AnalyzeRequestAdmin(admin.ModelAdmin):
    list_display = ['coin', 'message']
    prepopulated_fields = {'coin': ('message',)}