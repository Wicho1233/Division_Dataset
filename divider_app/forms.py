from django import forms

class DatasetUploadForm(forms.Form):
    dataset_file = forms.FileField(
        label='Selecciona tu archivo ARFF',
        help_text='Solo se aceptan archivos .arff',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.arff'
        })
    )