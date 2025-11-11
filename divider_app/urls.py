from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('divide/<int:division_id>/', views.divide_dataset, name='divide_dataset'),
    path('download/<int:division_id>/<str:set_type>/', views.download_set, name='download_set'),
]
