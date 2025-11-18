from django.db import models
import os
import uuid
from django.core.files.storage import default_storage

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

def plot_upload_path(instance, filename):
    """Generar path único para gráficas"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('plots', filename)

class DatasetFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=dataset_upload_path, storage=default_storage)
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
    
    def delete(self, *args, **kwargs):
        # Eliminar archivo físico al eliminar el objeto
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

class DatasetSplit(models.Model):
    name = models.CharField(max_length=255)
    dataset_file = models.ForeignKey(DatasetFile, on_delete=models.CASCADE)
    stratify_column = models.CharField(max_length=100, blank=True, null=True)
    random_state = models.IntegerField(default=42)
    shuffle = models.BooleanField(default=True)
    
    # Archivos de splits
    train_file = models.FileField(upload_to=split_upload_path, storage=default_storage, blank=True, null=True)
    validation_file = models.FileField(upload_to=split_upload_path, storage=default_storage, blank=True, null=True)
    test_file = models.FileField(upload_to=split_upload_path, storage=default_storage, blank=True, null=True)
    
    # Tamaños
    train_size = models.IntegerField()
    validation_size = models.IntegerField()
    test_size = models.IntegerField()
    
    # Gráficas
    distribution_plot = models.ImageField(upload_to=plot_upload_path, storage=default_storage, blank=True, null=True)
    comparison_plot = models.ImageField(upload_to=plot_upload_path, storage=default_storage, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at}"
    
    def delete(self, *args, **kwargs):
        # Eliminar archivos físicos al eliminar el objeto
        files_to_delete = [
            self.train_file,
            self.validation_file,
            self.test_file,
            self.distribution_plot,
            self.comparison_plot
        ]
        
        for file_field in files_to_delete:
            if file_field:
                file_field.delete(save=False)
        
        super().delete(*args, **kwargs)