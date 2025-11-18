from rest_framework import serializers
from .models import DatasetFile, DatasetSplit
import os

class DatasetFileSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    
    class Meta:
        model = DatasetFile
        fields = '__all__'
        read_only_fields = ['uploaded_at', 'file_size', 'rows', 'columns']
    
    def get_file_name(self, obj):
        return os.path.basename(obj.file.name)
    
    def get_file_type(self, obj):
        return obj.file.name.split('.')[-1].upper()
    
    def validate_file(self, value):
        # Validar que sea archivo ARFF
        if not value.name.lower().endswith('.arff'):
            raise serializers.ValidationError("Solo se permiten archivos ARFF")
        return value

class DatasetSplitSerializer(serializers.ModelSerializer):
    dataset_file_name = serializers.SerializerMethodField()
    train_file_url = serializers.SerializerMethodField()
    validation_file_url = serializers.SerializerMethodField()
    test_file_url = serializers.SerializerMethodField()
    distribution_plot_url = serializers.SerializerMethodField()
    comparison_plot_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DatasetSplit
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_dataset_file_name(self, obj):
        return obj.dataset_file.name
    
    def get_train_file_url(self, obj):
        if obj.train_file:
            return obj.train_file.url
        return None
    
    def get_validation_file_url(self, obj):
        if obj.validation_file:
            return obj.validation_file.url
        return None
    
    def get_test_file_url(self, obj):
        if obj.test_file:
            return obj.test_file.url
        return None
    
    def get_distribution_plot_url(self, obj):
        if obj.distribution_plot:
            return obj.distribution_plot.url
        return None
    
    def get_comparison_plot_url(self, obj):
        if obj.comparison_plot:
            return obj.comparison_plot.url
        return None

class SplitDatasetSerializer(serializers.Serializer):
    dataset_file_id = serializers.IntegerField()
    stratify_column = serializers.CharField(max_length=100, required=False)
    random_state = serializers.IntegerField(required=False, default=42)
    shuffle = serializers.BooleanField(required=False, default=True)
    generate_plots = serializers.BooleanField(required=False, default=True)

class VisualizationSerializer(serializers.Serializer):
    dataset_file_id = serializers.IntegerField(required=False)
    split_id = serializers.IntegerField(required=False)
    column_name = serializers.CharField(max_length=100, required=False)
    plot_type = serializers.ChoiceField(
        choices=['distribution', 'comparison', 'all'],
        default='all'
    )
