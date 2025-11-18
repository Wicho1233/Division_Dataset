import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile

def save_file_to_storage(file_content, filename):
    """
    Guarda un archivo en el sistema de almacenamiento configurado
    (S3 en producción, sistema de archivos local en desarrollo)
    """
    try:
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            
            # Guardar usando el storage de Django
            with open(temp_file.name, 'rb') as file:
                saved_path = default_storage.save(filename, ContentFile(file.read()))
            
            # Limpiar archivo temporal
            os.unlink(temp_file.name)
            
            return saved_path
            
    except Exception as e:
        print(f"Error saving file to storage: {e}")
        raise

def get_file_from_storage(file_path):
    """
    Obtiene un archivo del sistema de almacenamiento
    """
    try:
        if default_storage.exists(file_path):
            return default_storage.open(file_path)
        return None
    except Exception as e:
        print(f"Error getting file from storage: {e}")
        return None

def delete_file_from_storage(file_path):
    """
    Elimina un archivo del sistema de almacenamiento
    """
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file from storage: {e}")
        return False