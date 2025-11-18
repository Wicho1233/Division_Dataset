import matplotlib
matplotlib.use('Agg')  # Para evitar problemas con GUI
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
from django.core.files.base import ContentFile
import os

def create_distribution_plot(df, stratify_column):
    """Crear gráfica de distribución de la columna de estratificación"""
    plt.figure(figsize=(10, 6))
    
    # Gráfica de barras para la distribución
    value_counts = df[stratify_column].value_counts()
    bars = plt.bar(value_counts.index, value_counts.values)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.title(f'Distribución de {stratify_column} - Dataset Completo')
    plt.xlabel(stratify_column)
    plt.ylabel('Frecuencia')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convertir a imagen
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_comparison_plot(original_df, train_df, val_df, test_df, stratify_column):
    """Crear gráfica comparativa de distribuciones entre splits"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'Comparación de Distribuciones - {stratify_column}', fontsize=16)
    
    # Dataset original
    original_counts = original_df[stratify_column].value_counts()
    axes[0, 0].bar(original_counts.index, original_counts.values, color='blue', alpha=0.7)
    axes[0, 0].set_title('Dataset Original')
    axes[0, 0].set_ylabel('Frecuencia')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Training set
    train_counts = train_df[stratify_column].value_counts()
    axes[0, 1].bar(train_counts.index, train_counts.values, color='green', alpha=0.7)
    axes[0, 1].set_title('Training Set')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Validation set
    val_counts = val_df[stratify_column].value_counts()
    axes[1, 0].bar(val_counts.index, val_counts.values, color='orange', alpha=0.7)
    axes[1, 0].set_title('Validation Set')
    axes[1, 0].set_ylabel('Frecuencia')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Test set
    test_counts = test_df[stratify_column].value_counts()
    axes[1, 1].bar(test_counts.index, test_counts.values, color='red', alpha=0.7)
    axes[1, 1].set_title('Test Set')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Convertir a imagen
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_column_distribution_plot(df, column_name):
    """Crear gráfica de distribución para una columna específica"""
    plt.figure(figsize=(12, 6))
    
    if df[column_name].dtype == 'object':
        # Columna categórica
        value_counts = df[column_name].value_counts().head(10)  # Top 10
        bars = plt.bar(value_counts.index, value_counts.values)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.title(f'Distribución de {column_name} (Top 10)')
        plt.xticks(rotation=45)
    else:
        # Columna numérica
        plt.hist(df[column_name].dropna(), bins=30, alpha=0.7, edgecolor='black')
        plt.title(f'Distribución de {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frecuencia')
    
    plt.tight_layout()
    
    # Convertir a imagen
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer