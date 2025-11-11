from django.shortcuts import render, redirect
from django.http import HttpResponse
import os
from django.contrib import messages
from django.core.files.base import ContentFile
from .forms import DatasetUploadForm
from .models import DatasetDivision
from .utils import (
    read_arff_dataset,
    train_val_test_split,
    validate_file_extension,
    get_dataset_info,
    get_column_types,
    convert_to_arff,
    find_stratify_column
)


def home(request):
    """Página principal para subir el dataset."""
    form = DatasetUploadForm()
    return render(request, 'upload.html', {'form': form})


def upload_dataset(request):
    """Procesa la carga y división del dataset ARFF."""
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, 'Por favor selecciona un archivo ARFF válido.')
            return render(request, 'upload.html', {'form': form})

        try:
            dataset_file = request.FILES['dataset_file']

            # --- Validaciones ---
            if dataset_file.size > 50 * 1024 * 1024:
                messages.error(request, 'El archivo es demasiado grande (máx. 50MB).')
                return render(request, 'upload.html', {'form': form})

            if not validate_file_extension(dataset_file.name):
                messages.error(request, 'Solo se aceptan archivos con extensión .arff.')
                return render(request, 'upload.html', {'form': form})

            # --- Lectura del archivo ---
            df = read_arff_dataset(dataset_file)
            if df.empty:
                messages.error(request, 'El archivo ARFF no contiene datos válidos.')
                return render(request, 'upload.html', {'form': form})

            # --- Determinar columna de estratificación ---
            stratify_column = find_stratify_column(df)

            # --- División del dataset ---
            try:
                train_set, val_set, test_set = train_val_test_split(
                    df, rstate=42, shuffle=True, stratify=stratify_column
                )
            except ValueError as ve:
                # Error común: clase con un solo ejemplo
                if "least populated class" in str(ve):
                    messages.warning(
                        request,
                        "Advertencia: algunas clases tienen un solo ejemplo. "
                        "La división se realizó sin estratificación."
                    )
                    train_set, val_set, test_set = train_val_test_split(
                        df, rstate=42, shuffle=True, stratify=None
                    )
                else:
                    raise ve

            # --- Guardar registro en BD ---
            division = DatasetDivision(train_size=0.6, val_size=0.2, test_size=0.2)
            division.original_file.save(dataset_file.name, dataset_file)

            base_name = os.path.splitext(dataset_file.name)[0]
            train_filename = f"train_{base_name}.arff"
            val_filename = f"val_{base_name}.arff"
            test_filename = f"test_{base_name}.arff"

            # --- Convertir y guardar archivos ---
            train_arff = convert_to_arff(train_set, f"train_{base_name}")
            val_arff = convert_to_arff(val_set, f"val_{base_name}")
            test_arff = convert_to_arff(test_set, f"test_{base_name}")

            division.train_set.save(train_filename, ContentFile(train_arff.encode('utf-8')))
            division.val_set.save(val_filename, ContentFile(val_arff.encode('utf-8')))
            division.test_set.save(test_filename, ContentFile(test_arff.encode('utf-8')))
            division.save()

            # --- Preparar datos para resultados ---
            column_info = get_column_types(df)
            context = {
                'division': division,
                'train_rows': len(train_set),
                'val_rows': len(val_set),
                'test_rows': len(test_set),
                'total_rows': len(df),
                'dataset_info': get_dataset_info(df),
                'column_info': column_info,
                'train_percentage': (len(train_set) / len(df)) * 100,
                'val_percentage': (len(val_set) / len(df)) * 100,
                'test_percentage': (len(test_set) / len(df)) * 100,
                'used_stratify': stratify_column if stratify_column else 'Ninguna (muestreo aleatorio)',
                'split_ratio': '60% Train - 20% Validation - 20% Test'
            }

            messages.success(request, '¡Dataset ARFF dividido exitosamente!')
            return render(request, 'results.html', context)

        except Exception as e:
            messages.error(request, f'Error al procesar el dataset: {str(e)}')
            return render(request, 'upload.html', {'form': form})

    # Si no es POST, mostrar el formulario vacío
    form = DatasetUploadForm()
    return render(request, 'upload.html', {'form': form})


def download_set(request, division_id, set_type):
    """Permite descargar uno de los conjuntos (train, val, test)."""
    from django.shortcuts import get_object_or_404
    division = get_object_or_404(DatasetDivision, id=division_id)

    file_map = {
        'train': (division.train_set, 'train'),
        'val': (division.val_set, 'val'),
        'test': (division.test_set, 'test'),
    }

    if set_type not in file_map:
        messages.error(request, 'Tipo de conjunto inválido.')
        return redirect('home')

    file, label = file_map[set_type]
    response = HttpResponse(file.read(), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{label}_set_{division_id}.arff"'
    return response
