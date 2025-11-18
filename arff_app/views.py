from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
import os

from .models import DatasetFile, DatasetSplit
from .serializers import (
    DatasetFileSerializer, 
    DatasetSplitSerializer, 
    SplitDatasetSerializer,
    VisualizationSerializer
)
from .utils.dataset_utils import (
    load_kdd_dataset_from_file,
    train_val_test_split,
    get_dataset_info,
    get_available_stratification_columns,
    save_dataframe_to_arff
)
from .utils.visualization import (
    create_distribution_plot,
    create_comparison_plot,
    create_column_distribution_plot
)

@api_view(['POST'])
def upload_dataset(request):
    """Endpoint para subir archivos ARFF"""
    if 'file' not in request.FILES:
        return Response({
            'status': 'error',
            'message': 'No se proporcionó ningún archivo'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    name = request.POST.get('name', file.name)
    
    # Validar extensión
    if not file.name.lower().endswith('.arff'):
        return Response({
            'status': 'error',
            'message': 'Solo se permiten archivos ARFF'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Cargar dataset para validar
        df = load_kdd_dataset_from_file(file)
        
        # Crear objeto DatasetFile
        dataset_file = DatasetFile.objects.create(
            name=name,
            file=file,
            rows=len(df),
            columns=len(df.columns)
        )
        
        serializer = DatasetFileSerializer(dataset_file)
        
        return Response({
            'status': 'success',
            'message': 'Archivo ARFF subido exitosamente',
            'dataset': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error al procesar el archivo ARFF: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_datasets(request):
    """Endpoint para listar todos los datasets subidos"""
    datasets = DatasetFile.objects.all()
    serializer = DatasetFileSerializer(datasets, many=True)
    
    return Response({
        'status': 'success',
        'datasets': serializer.data,
        'count': len(serializer.data)
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def split_dataset(request):
    """Endpoint para dividir el dataset"""
    serializer = SplitDatasetSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            dataset_file_id = serializer.validated_data['dataset_file_id']
            stratify_column = serializer.validated_data.get('stratify_column')
            random_state = serializer.validated_data.get('random_state', 42)
            shuffle = serializer.validated_data.get('shuffle', True)
            generate_plots = serializer.validated_data.get('generate_plots', True)
            
            # Obtener dataset file
            dataset_file = get_object_or_404(DatasetFile, id=dataset_file_id)
            
            # Cargar dataset
            df = load_kdd_dataset_from_file(dataset_file.file)
            
            # Dividir dataset
            train_set, val_set, test_set = train_val_test_split(
                df, rstate=random_state, shuffle=shuffle, stratify=stratify_column)
            
            # Crear objeto DatasetSplit
            split_name = f"{dataset_file.name}_split_{DatasetSplit.objects.count() + 1}"
            dataset_split = DatasetSplit.objects.create(
                name=split_name,
                dataset_file=dataset_file,
                stratify_column=stratify_column,
                random_state=random_state,
                shuffle=shuffle,
                train_size=len(train_set),
                validation_size=len(val_set),
                test_size=len(test_set)
            )
            
            # Guardar splits como archivos ARFF
            dataset_split.train_file = save_dataframe_to_arff(train_set, f"{split_name}_train")
            dataset_split.validation_file = save_dataframe_to_arff(val_set, f"{split_name}_validation")
            dataset_split.test_file = save_dataframe_to_arff(test_set, f"{split_name}_test")
            
            # Generar gráficas si se solicita
            if generate_plots and stratify_column:
                # Gráfica de distribución
                dist_plot_buffer = create_distribution_plot(df, stratify_column)
                dataset_split.distribution_plot.save(
                    f"{split_name}_distribution.png", 
                    dist_plot_buffer
                )
                
                # Gráfica comparativa
                comp_plot_buffer = create_comparison_plot(df, train_set, val_set, test_set, stratify_column)
                dataset_split.comparison_plot.save(
                    f"{split_name}_comparison.png", 
                    comp_plot_buffer
                )
            
            dataset_split.save()
            
            response_serializer = DatasetSplitSerializer(dataset_split)
            
            return Response({
                'status': 'success',
                'message': 'Dataset dividido exitosamente',
                'split': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error', 
                'message': f'Error al dividir el dataset: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Añadir esta importación al inicio del archivo
from django.conf import settings

# Y actualizar la función download_split_file para producción
@api_view(['GET'])
def download_split_file(request, split_id, file_type):
    """Endpoint para descargar archivos de splits"""
    dataset_split = get_object_or_404(DatasetSplit, id=split_id)
    
    file_mapping = {
        'train': dataset_split.train_file,
        'validation': dataset_split.validation_file,
        'test': dataset_split.test_file
    }
    
    if file_type not in file_mapping:
        return Response({
            'status': 'error',
            'message': 'Tipo de archivo no válido. Opciones: train, validation, test'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = file_mapping[file_type]
    
    if not file:
        return Response({
            'status': 'error',
            'message': f'Archivo {file_type} no disponible'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # En producción, redirigir a la URL de S3
    if not settings.DEBUG and hasattr(file, 'url'):
        return Response({
            'status': 'success',
            'download_url': file.url,
            'filename': file.name
        }, status=status.HTTP_200_OK)
    
    # En desarrollo, servir el archivo directamente
    response = FileResponse(file.open(), as_attachment=True, filename=file.name)
    return response

@api_view(['POST'])
def generate_visualizations(request):
    """Endpoint para generar visualizaciones"""
    serializer = VisualizationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            dataset_file_id = serializer.validated_data.get('dataset_file_id')
            split_id = serializer.validated_data.get('split_id')
            column_name = serializer.validated_data.get('column_name')
            plot_type = serializer.validated_data.get('plot_type', 'all')
            
            if dataset_file_id:
                dataset_file = get_object_or_404(DatasetFile, id=dataset_file_id)
                df = load_kdd_dataset_from_file(dataset_file.file)
                
                if column_name and column_name in df.columns:
                    # Gráfica de distribución de columna específica
                    plot_buffer = create_column_distribution_plot(df, column_name)
                    response = HttpResponse(plot_buffer.getvalue(), content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="{column_name}_distribution.png"'
                    return response
                
            elif split_id:
                dataset_split = get_object_or_404(DatasetSplit, id=split_id)
                
                if plot_type == 'distribution' and dataset_split.distribution_plot:
                    return FileResponse(dataset_split.distribution_plot.open(), content_type='image/png')
                elif plot_type == 'comparison' and dataset_split.comparison_plot:
                    return FileResponse(dataset_split.comparison_plot.open(), content_type='image/png')
            
            return Response({
                'status': 'error',
                'message': 'No se pudo generar la visualización solicitada'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al generar visualización: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_splits(request):
    """Endpoint para listar todas las divisiones"""
    splits = DatasetSplit.objects.all()
    serializer = DatasetSplitSerializer(splits, many=True)
    
    return Response({
        'status': 'success',
        'splits': serializer.data,
        'count': len(serializer.data)
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_split_detail(request, split_id):
    """Endpoint para obtener detalles de una división específica"""
    dataset_split = get_object_or_404(DatasetSplit, id=split_id)
    serializer = DatasetSplitSerializer(dataset_split)
    
    return Response({
        'status': 'success',
        'split': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_split(request, split_id):
    """Endpoint para eliminar una división"""
    dataset_split = get_object_or_404(DatasetSplit, id=split_id)
    dataset_split.delete()
    
    return Response({
        'status': 'success',
        'message': 'División eliminada exitosamente'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def dataset_info(request, dataset_id):
    """Endpoint para obtener información de un dataset específico"""
    dataset_file = get_object_or_404(DatasetFile, id=dataset_id)
    
    try:
        df = load_kdd_dataset_from_file(dataset_file.file)
        info = get_dataset_info(df)
        stratification_columns = get_available_stratification_columns(df)
        
        return Response({
            'status': 'success',
            'dataset_id': dataset_id,
            'dataset_name': dataset_file.name,
            'info': info,
            'stratification_columns': stratification_columns
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error al obtener información del dataset: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
