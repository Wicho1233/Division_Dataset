from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_dataset, name='home'),
    path('download/<int:division_id>/<str:set_type>/', views.download_set, name='download_set'),
]