from django.db import models

class DatasetDivision(models.Model):
    original_file = models.FileField(upload_to='datasets/')
    train_set = models.FileField(upload_to='results/', blank=True, null=True)
    val_set = models.FileField(upload_to='results/', blank=True, null=True)
    test_set = models.FileField(upload_to='results/', blank=True, null=True)
    train_size = models.FloatField(default=0.6)
    val_size = models.FloatField(default=0.2)
    test_size = models.FloatField(default=0.2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Division {self.id} - {self.created_at}"