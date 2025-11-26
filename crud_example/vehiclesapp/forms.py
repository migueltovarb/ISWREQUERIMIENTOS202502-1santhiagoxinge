from django import forms
from .models import vehicle

# Creación del formulario
class VehicleForm(forms.ModelForm):
    class Meta:
        # Especificar el modelo a usar
        model = vehicle

        # Campos del formulario
        fields = [
            "placa",
            "marca",
            "modelo",
            "color_vehiculo"
        ]

        # Etiquetas visibles en el formulario
        labels = {
            'placa': 'Número de placa',
            'marca': 'Marca del vehículo',
            'modelo': 'Modelo del vehículo',
            'color_vehiculo': 'Color del vehículo'
        }

        # Estilo visual de los campos
        widgets = {
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'color_vehiculo': forms.Select(attrs={'class': 'form-control'}),
        }
