from django.db import models
import os
import uuid

def dataset_upload_path(instance, filename):
    """Generar path único para archivos de dataset"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('datasets', filename)

def split_upload_path(instance, filename):
    """Generar path único para archivos de splits"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('splits', filename)

class DatasetFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=dataset_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    columns = models.IntegerField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

class DatasetSplit(models.Model):
    name = models.CharField(max_length=255)
    dataset_file = models.ForeignKey(DatasetFile, on_delete=models.CASCADE)
    stratify_column = models.CharField(max_length=100, blank=True, null=True)
    random_state = models.IntegerField(default=42)
    shuffle = models.BooleanField(default=True)
    
    # Archivos de splits
    train_file = models.FileField(upload_to=split_upload_path, blank=True, null=True)
    validation_file = models.FileField(upload_to=split_upload_path, blank=True, null=True)
    test_file = models.FileField(upload_to=split_upload_path, blank=True, null=True)
    
    # Tamaños
    train_size = models.IntegerField()
    validation_size = models.IntegerField()
    test_size = models.IntegerField()
    
    # Gráficas
    distribution_plot = models.ImageField(upload_to='plots/', blank=True, null=True)
    comparison_plot = models.ImageField(upload_to='plots/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at}"