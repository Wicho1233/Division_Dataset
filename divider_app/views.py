from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .forms import DatasetUploadForm
from .utils import (
    read_arff_dataset,
    train_val_test_split,
    validate_file_extension,
    get_dataset_info,
    get_column_types,
    convert_to_arff,
    find_stratify_column
)
from .models import DatasetDivision
from django.core.files.base import ContentFile


def home(request):
    form = DatasetUploadForm()
    return render(request, 'upload.html', {'form': form})


def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                dataset_file = request.FILES['dataset_file']

                # Validar tamaño máximo
                if dataset_file.size > 50 * 1024 * 1024:
                    messages.error(request, 'El archivo es demasiado grande. Máximo 50MB.')
                    return render(request, 'upload.html', {'form': form})

                # Validar extensión
                if not validate_file_extension(dataset_file.name):
                    messages.error(request, 'Solo se aceptan archivos con extensión .arff')
                    return render(request, 'upload.html', {'form': form})

                # Leer dataset ARFF
                df = read_arff_dataset(dataset_file)
                if len(df) == 0:
                    messages.error(request, 'El archivo ARFF no contiene datos.')
                    return render(request, 'upload.html', {'form': form})

                # Determinar columna para estratificación
                stratify_column = find_stratify_column(df)

                # --- División del dataset con manejo de error de estratificación ---
                try:
                    train_set, val_set, test_set = train_val_test_split(
                        df, rstate=42, shuffle=True, stratify=stratify_column
                    )
                except ValueError as ve:
                    if "least populated class" in str(ve):
                        messages.warning(
                            request,
                            "Advertencia: Algunas clases tienen solo un ejemplo. "
                            "La división se realizó sin estratificación."
                        )
                        # Repetir división sin estratificar
                        train_set, val_set, test_set = train_val_test_split(
                            df, rstate=42, shuffle=True, stratify=None
                        )
                    else:
                        raise ve

                # Guardar registro de división en la BD
                division = DatasetDivision(
                    train_size=0.6,
                    val_size=0.2,
                    test_size=0.2
                )
                division.original_file.save(dataset_file.name, dataset_file)

                # Nombres base
                base_name = dataset_file.name.split('.')[0]
                train_filename = f"train_{base_name}.arff"
                val_filename = f"val_{base_name}.arff"
                test_filename = f"test_{base_name}.arff"

                # Convertir divisiones a ARFF
                train_arff = convert_to_arff(train_set, f"train_{base_name}")
                val_arff = convert_to_arff(val_set, f"val_{base_name}")
                test_arff = convert_to_arff(test_set, f"test_{base_name}")

                # Guardar archivos en modelo
                division.train_set.save(train_filename, ContentFile(train_arff.encode('utf-8')))
                division.val_set.save(val_filename, ContentFile(val_arff.encode('utf-8')))
                division.test_set.save(test_filename, ContentFile(test_arff.encode('utf-8')))
                division.save()

                # Información para el template
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
                messages.error(request, f'Error al procesar el dataset ARFF: {str(e)}')
                return render(request, 'upload.html', {'form': form})

        else:
            messages.error(request, 'Por favor selecciona un archivo ARFF válido.')
            return render(request, 'upload.html', {'form': form})

    else:
        form = DatasetUploadForm()

    return render(request, 'upload.html', {'form': form})


def download_set(request, division_id, set_type):
    try:
        division = DatasetDivision.objects.get(id=division_id)

        if set_type == 'train':
            file = division.train_set
            filename = f"train_set_{division_id}.arff"
        elif set_type == 'val':
            file = division.val_set
            filename = f"val_set_{division_id}.arff"
        elif set_type == 'test':
            file = division.test_set
            filename = f"test_set_{division_id}.arff"
        else:
            messages.error(request, 'Tipo de conjunto inválido.')
            return redirect('home')

        response = HttpResponse(file.read(), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except DatasetDivision.DoesNotExist:
        messages.error(request, 'División no encontrada.')
        return redirect('home')
