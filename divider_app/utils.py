import os
import pandas as pd
from sklearn.model_selection import train_test_split
from django.conf import settings


def divide_dataset(file_path, test_size=0.2, random_state=42):
    """
    Divide el dataset en entrenamiento y prueba, guarda los archivos y devuelve rutas.
    Compatible con .arff y .csv.
    """
    filename, extension = os.path.splitext(os.path.basename(file_path))
    base_dir = os.path.join(settings.MEDIA_ROOT, filename)
    os.makedirs(base_dir, exist_ok=True)

    # Leer dataset
    if extension.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif extension.lower() == '.arff':
        import arff
        data = arff.load(open(file_path, 'r'))
        df = pd.DataFrame(data['data'], columns=[a[0] for a in data['attributes']])
    else:
        raise ValueError("Formato de archivo no compatible. Usa .csv o .arff")

    # División del dataset
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)

    # Guardar conjuntos
    train_path = os.path.join(base_dir, 'train.csv')
    test_path = os.path.join(base_dir, 'test.csv')

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    return {
        'train_path': base_dir,
        'test_path': base_dir,
        'train_preview': train_df.head(),
        'test_preview': test_df.head()
    }
