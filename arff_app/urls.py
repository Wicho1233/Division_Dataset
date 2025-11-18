from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Gestión de datasets
    path('datasets/upload/', views.upload_dataset, name='upload-dataset'),
    path('datasets/', views.list_datasets, name='list-datasets'),
    path('datasets/<int:dataset_id>/info/', views.dataset_info, name='dataset-info'),
    
    # Divisiones de datasets
    path('splits/create/', views.split_dataset, name='split-dataset'),
    path('splits/', views.list_splits, name='list-splits'),
    path('splits/<int:split_id>/', views.get_split_detail, name='get-split-detail'),
    path('splits/<int:split_id>/delete/', views.delete_split, name='delete-split'),
    
    # Descargas
    path('splits/<int:split_id>/download/<str:file_type>/', views.download_split_file, name='download-split-file'),
    
    # Visualizaciones
    path('visualizations/generate/', views.generate_visualizations, name='generate-visualizations'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)