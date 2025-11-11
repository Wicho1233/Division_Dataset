import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import arff


# =============================
# 🔍 Validación del archivo
# =============================
def validate_file_extension(filename):
    """Valida que el archivo tenga extensión .arff"""
    return filename.lower().endswith('.arff')


# =============================
# 📖 Lectura del dataset ARFF
# =============================
def read_arff_dataset(file):
    """Lee un archivo ARFF y lo convierte en un DataFrame de pandas"""
    try:
        content = file.read().decode('utf-8')
        dataset = arff.loads(content)
        attributes = [attr[0] for attr in dataset['attributes']]
        df = pd.DataFrame(dataset['data'], columns=attributes)
        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo ARFF: {str(e)}")


# =============================
# ✂️ División del dataset
# =============================
def train_val_test_split(df, rstate=42, shuffle=True, stratify=None):
    """
    Divide el dataset en train (60%), validation (20%) y test (20%).
    Si la columna de estratificación no es válida, se hace división aleatoria.
    """
    strat = None
    if stratify and stratify in df.columns:
        try:
            # Evita error si la columna tiene un solo valor o valores nulos
            if df[stratify].nunique() > 1:
                strat = df[stratify]
        except Exception:
            strat = None

    train_set, test_set = train_test_split(
        df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat
    )

    strat = None
    if stratify and stratify in test_set.columns:
        try:
            if test_set[stratify].nunique() > 1:
                strat = test_set[stratify]
        except Exception:
            strat = None

    val_set, test_set = train_test_split(
        test_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat
    )

    return (train_set, val_set, test_set)


# =============================
# 🧮 Conversión a ARFF
# =============================
def convert_to_arff(df, relation_name="dataset"):
    """
    Convierte un DataFrame de pandas en texto ARFF válido.
    Maneja valores nulos, cadenas con comillas y columnas mixtas.
    """
    import pandas as pd
    import numpy as np

    arff_str = f"@RELATION {relation_name}\n\n"

    # --- Atributos ---
    for col in df.columns:
        dtype = df[col].dtype

        if pd.api.types.is_numeric_dtype(dtype):
            attr_type = "NUMERIC"
        elif pd.api.types.is_bool_dtype(dtype):
            attr_type = "{True, False}"
        else:
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) > 0 and len(unique_vals) <= 20:
                clean_vals = [
                    str(v).replace(',', '').replace(' ', '_').replace('"', "'")
                    for v in unique_vals
                ]
                attr_type = "{" + ",".join(clean_vals) + "}"
            else:
                attr_type = "STRING"

        arff_str += f"@ATTRIBUTE {col} {attr_type}\n"

    arff_str += "\n@DATA\n"

    # --- Datos ---
    for _, row in df.iterrows():
        values = []
        for val in row:
            if pd.isna(val) or (isinstance(val, (float, int)) and not np.isfinite(val)):
                values.append("?")  # valor faltante
            elif isinstance(val, str):
                safe_val = val.replace('"', "'").replace(',', '').strip()
                values.append(f'"{safe_val}"')
            else:
                values.append(str(val))
        arff_str += ",".join(values) + "\n"

    return arff_str


# =============================
# ℹ️ Información del dataset
# =============================
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


# =============================
# 🧩 Tipos de columnas
# =============================
def get_column_types(df):
    """Obtiene información sobre los tipos de columnas"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    return {
        'numeric': numeric_cols,
        'categorical': categorical_cols,
        'all_columns': list(df.columns)
    }


# =============================
# 🎯 Columna para estratificar
# =============================
def find_stratify_column(df):
    """
    Encuentra automáticamente una columna adecuada para estratificación.
    Prefiere columnas llamadas 'class', 'label', 'target', etc.
    """
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

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
