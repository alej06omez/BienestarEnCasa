

from django import forms
from .models import Servicio

class CrearNewServicio(forms.Form):
    nombre = forms.CharField(label="Nombre del Servicio", max_length=200)
    categoria = forms.CharField(label="Categoría", max_length=100)
    descripcion = forms.CharField(label="Descripción", widget=forms.Textarea)
    duracion = forms.CharField(label="Duración", max_length=100)
    precio = forms.DecimalField(label="Precio", max_digits=10, decimal_places=2)
    creado_en = forms.DateTimeField(auto_now_add=True)
    estado = forms.CharField(max_length=20, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo')

class addServicioInsumo(forms.Form):
    nombre = forms.CharField(label='Nombre del Servicio', max_length=100)

class addMultimediaServicio(forms.Form):
    archivo = forms.FileField(label="Archivo Multimedia")
    tipo = forms.ChoiceField(label="Tipo de Archivo", choices=[('imagen', 'Imagen'), ('video', 'Video')])