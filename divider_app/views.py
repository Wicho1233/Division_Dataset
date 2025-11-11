import io
import zipfile
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages

from .utils import (
    validate_file_extension,
    read_arff_dataset,
    get_dataset_info,
    get_column_types,
    find_stratify_column,
    train_val_test_split,
    convert_to_arff
)

def index(request):
    """Página principal."""
    return render(request, 'divider_app/index.html')


def upload_dataset(request):
    """Sube un archivo ARFF, lo divide y permite descargar los subconjuntos."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('dataset')

        # Validación de extensión
        if not uploaded_file or not validate_file_extension(uploaded_file.name):
            messages.error(request, "Por favor, sube un archivo con extensión .arff válida.")
            return render(request, 'divider_app/index.html')

        try:
            # Leer dataset
            df = read_arff_dataset(uploaded_file)
            base_name = uploaded_file.name.replace('.arff', '')

            # Obtener información básica del dataset
            dataset_info = get_dataset_info(df)
            col_types = get_column_types(df)
            stratify_col = find_stratify_column(df)

            # Dividir dataset
            train_set, val_set, test_set = train_val_test_split(
                df, stratify=stratify_col
            )

            # Convertir a formato ARFF
            train_arff = convert_to_arff(train_set, f"train_{base_name}")
            val_arff = convert_to_arff(val_set, f"val_{base_name}")
            test_arff = convert_to_arff(test_set, f"test_{base_name}")

            # Crear archivo ZIP en memoria
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"{base_name}_train.arff", train_arff)
                zip_file.writestr(f"{base_name}_val.arff", val_arff)
                zip_file.writestr(f"{base_name}_test.arff", test_arff)

            zip_buffer.seek(0)

            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={base_name}_split_datasets.zip'

            # Mostrar información del dataset en la vista
            context = {
                'dataset_info': dataset_info,
                'col_types': col_types,
                'stratify_column': stratify_col or 'Ninguna',
                'file_name': uploaded_file.name,
                'success': True
            }

            return response

        except Exception as e:
            messages.error(request, f"Ocurrió un error procesando el archivo: {str(e)}")
            return render(request, 'divider_app/index.html')

    # Si no es POST, muestra formulario vacío
    return render(request, 'divider_app/index.html')
