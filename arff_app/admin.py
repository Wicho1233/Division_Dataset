from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DatasetFile, DatasetSplit

@admin.register(DatasetFile)
class DatasetFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file', 'file_size', 'rows', 'columns', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['name']
    readonly_fields = ['file_size', 'rows', 'columns', 'uploaded_at']

@admin.register(DatasetSplit)
class DatasetSplitAdmin(admin.ModelAdmin):
    list_display = ['name', 'dataset_file', 'stratify_column', 'train_size', 'validation_size', 'test_size', 'created_at']
    list_filter = ['created_at', 'stratify_column']
    search_fields = ['name', 'dataset_file__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'dataset_file', 'created_at')
        }),
        ('Configuración de División', {
            'fields': ('stratify_column', 'random_state', 'shuffle')
        }),
        ('Archivos de Splits', {
            'fields': ('train_file', 'validation_file', 'test_file')
        }),
        ('Gráficas', {
            'fields': ('distribution_plot', 'comparison_plot')
        }),
        ('Tamaños de Conjuntos', {
            'fields': ('train_size', 'validation_size', 'test_size')
        }),
    )