import os
import pandas as pd
import numpy as np
import arff
from sklearn.model_selection import train_test_split


# ─────────────────────────────────────────────
# VALIDACIÓN DE ARCHIVOS
# ─────────────────────────────────────────────
def validate_file_extension(filename: str) -> bool:
    """Valida que el archivo tenga extensión .arff"""
    return filename.lower().endswith('.arff')


# ─────────────────────────────────────────────
# LECTURA DEL DATASET ARFF
# ─────────────────────────────────────────────
def read_arff_dataset(file):
    """
    Lee un archivo ARFF y lo convierte a DataFrame de pandas.
    Acepta archivos subidos desde un formulario de Django (InMemoryUploadedFile).
    """
    try:
        # Asegurar que el puntero del archivo está al inicio
        file.seek(0)
        content = file.read().decode('utf-8', errors='ignore')

        dataset = arff.loads(content)
        attributes = [attr[0] for attr in dataset['attributes']]
        data = dataset['data']

        df = pd.DataFrame(data, columns=attributes)
        return df

    except Exception as e:
        raise ValueError(f"Error al leer el archivo ARFF: {str(e)}")


# ─────────────────────────────────────────────
# DIVISIÓN DEL DATASET
# ─────────────────────────────────────────────
def train_val_test_split(df, rstate=42, shuffle=True, stratify=None):
    """
    Divide el dataset en train (60%), validation (20%) y test (20%).
    Si 'stratify' es una columna, se realiza muestreo estratificado.
    """
    try:
        strat = df[stratify] if stratify else None

        train_set, temp_set = train_test_split(
            df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat
        )

        strat_temp = temp_set[stratify] if stratify else None
        val_set, test_set = train_test_split(
            temp_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat_temp
        )

        return train_set, val_set, test_set

    except Exception as e:
        raise ValueError(f"Error al dividir el dataset: {str(e)}")


# ─────────────────────────────────────────────
# CONVERSIÓN A ARFF
# ─────────────────────────────────────────────
def convert_to_arff(df, relation_name="dataset"):
    """Convierte un DataFrame a formato ARFF válido."""
    attributes = []

    for col_name, dtype in df.dtypes.items():
        if np.issubdtype(dtype, np.number):
            attributes.append((col_name, 'NUMERIC'))
        else:
            unique_vals = df[col_name].dropna().unique()
            # Si tiene muchos valores distintos, se trata como cadena
            if len(unique_vals) > 20:
                attributes.append((col_name, 'STRING'))
            else:
                attributes.append((col_name, [str(v) for v in unique_vals]))

    # Limpieza y conversión segura de datos
    data = []
    for _, row in df.iterrows():
        clean_row = []
        for val in row:
            if pd.isna(val):
                clean_row.append(None)
            elif isinstance(val, (int, float, np.integer, np.floating)):
                clean_row.append(float(val))
            else:
                clean_row.append(str(val))
        data.append(clean_row)

    arff_data = {
        'description': f'{relation_name} dataset dividido por Dataset Divider',
        'relation': relation_name,
        'attributes': attributes,
        'data': data
    }

    return arff.dumps(arff_data)


# ─────────────────────────────────────────────
# INFORMACIÓN DEL DATASET
# ─────────────────────────────────────────────
def get_dataset_info(df):
    """Devuelve estadísticas básicas del dataset."""
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'data_types': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'memory_usage_kb': int(df.memory_usage(deep=True).sum() / 1024),
    }


# ─────────────────────────────────────────────
# TIPOS DE COLUMNAS
# ─────────────────────────────────────────────
def get_column_types(df):
    """Identifica columnas numéricas y categóricas."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    return {
        'numeric': numeric_cols,
        'categorical': categorical_cols,
        'all_columns': list(df.columns)
    }


# ─────────────────────────────────────────────
# DETECCIÓN AUTOMÁTICA DE COLUMNA PARA ESTRATIFICAR
# ─────────────────────────────────────────────
def find_stratify_column(df):
    """
    Intenta encontrar una columna adecuada para estratificación.
    Busca primero entre las categóricas y luego entre las numéricas discretas.
    """
    categorical_cols = df.select_dtypes(include=['object']).columns

    for col in categorical_cols:
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 10:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['class', 'target', 'label', 'type', 'category']):
                return col
            return col

    # Si no encuentra categórica, intenta con numéricas discretas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 10:
            return col

    return None
