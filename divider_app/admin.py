from django.contrib import admin
from .models import DatasetDivision

@admin.register(DatasetDivision)
class DatasetDivisionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'train_size', 'val_size', 'test_size']
    list_filter = ['created_at']
    readonly_fields = ['created_at']