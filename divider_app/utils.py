import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from django.core.files.base import ContentFile
import arff

def validate_file_extension(filename):
    """Valida que el archivo sea .arff"""
    return filename.lower().endswith('.arff')

def read_arff_dataset(file):
    """Lee un archivo ARFF y lo convierte a DataFrame de pandas"""
    try:
        content = file.read().decode('utf-8')
        dataset = arff.loads(content)
        attributes = [attr[0] for attr in dataset['attributes']]
        df = pd.DataFrame(dataset['data'], columns=attributes)
        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo ARFF: {str(e)}")

def train_val_test_split(df, rstate=42, shuffle=True, stratify=None):
    """
    Divide el dataset en train (60%), validation (20%) y test (20%)
    """
    strat = df[stratify] if stratify else None 
    
    train_set, test_set = train_test_split(
        df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat)
    
    strat = test_set[stratify] if stratify else None 
    val_set, test_set = train_test_split(
        test_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat)
    
    return (train_set, val_set, test_set)

def convert_to_arff(df, relation_name="dataset"):
    """Convierte un DataFrame de pandas a formato ARFF"""
    
    attributes = []
    for col_name, dtype in df.dtypes.items():
        if np.issubdtype(dtype, np.number):
            attributes.append((col_name, 'NUMERIC'))
        else:
            unique_vals = df[col_name].dropna().unique()
            if len(unique_vals) > 20:
                attributes.append((col_name, 'STRING'))
            else:
                attributes.append((col_name, [str(x) for x in unique_vals]))
    
    data = []
    for _, row in df.iterrows():
        data_row = []
        for val in row:
            if pd.isna(val):
                data_row.append(None)
            elif isinstance(val, (int, float)):
                data_row.append(float(val))
            else:
                data_row.append(str(val))
        data.append(data_row)
    
    arff_data = {
        'description': f'{relation_name} dataset divided by Dataset Divider',
        'relation': relation_name,
        'attributes': attributes,
        'data': data
    }
    
    return arff.dumps(arff_data)

def get_dataset_info(df):
    """Obtiene información básica del dataset"""
    info = {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'data_types': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum() // 1024
    }
    return info

def get_column_types(df):
    """Obtiene información sobre los tipos de columnas"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    return {
        'numeric': numeric_cols,
        'categorical': categorical_cols,
        'all_columns': list(df.columns)
    }

def find_stratify_column(df):
    """Encuentra automáticamente una columna buena para stratified sampling"""
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 10:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['class', 'target', 'label', 'type', 'category']):
                return col
            return col
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 10:
            return col
    
    return None