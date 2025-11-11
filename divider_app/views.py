import os
import pandas as pd
import zipfile
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .models import Division
from .utils import divide_dataset


def upload_file(request):
    """
    Vista principal: permite subir un archivo ARFF o CSV.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        upload = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(upload.name, upload)
        file_path = fs.path(filename)

        # Guardar archivo en base de datos
        division = Division.objects.create(name=filename, file_path=file_path)
        return redirect('divide_dataset', division_id=division.id)

    return render(request, 'upload.html')


def divide_dataset(request, division_id):
    """
    Divide el dataset en conjuntos de entrenamiento y prueba.
    """
    division = get_object_or_404(Division, id=division_id)

    # Divide el dataset y genera rutas
    result = divide_dataset(division.file_path)

    division.train_path = result['train_path']
    division.test_path = result['test_path']
    division.save()

    context = {
        'division': division,
        'train_preview': result['train_preview'].to_html(classes='table table-striped', index=False),
        'test_preview': result['test_preview'].to_html(classes='table table-striped', index=False),
    }
    return render(request, 'result.html', context)


def download_set(request, division_id, set_type):
    """
    Permite descargar el conjunto de entrenamiento o prueba como archivo ZIP.
    """
    division = get_object_or_404(Division, id=division_id)

    if set_type == 'train':
        folder_path = division.train_path
        zip_filename = f"{division.name}_train.zip"
    elif set_type == 'test':
        folder_path = division.test_path
        zip_filename = f"{division.name}_test.zip"
    else:
        raise Http404("Tipo de conjunto inválido")

    # Crear el ZIP en memoria
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)

    buffer.seek(0)

    # Devolver el archivo ZIP
    response = HttpResponse(buffer, content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'
    return response
