

from django import forms
from .models import Servicio


class CrearNewServicio(forms.Form):
    nombre = forms.CharField(label="Nombre del Servicio", max_length=200, required=True)
    categoria = forms.ChoiceField(choices=[('Masajes no medicos', 'masajes no medicos'), ('Estetico', 'estetico'), ('Bienestar', 'bienestar')] ,label="Categoría", required=True)
    descripcion = forms.CharField(label="Descripción", widget=forms.Textarea, required=True)
    duracion = forms.CharField(label="Duración", max_length=100, required=True)
    precio = forms.DecimalField(label="Precio", max_digits=10, decimal_places=2, required=True)
    estado = forms.ChoiceField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], initial='activo', required=True, label="Estado")

class addServicioInsumoForm(forms.Form):
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.all(),
        label='Servicio'
    )
    tipo = forms.ChoiceField(choices=[('Producto', 'producto'), ('Equipos', 'equipo'), ('Insumo', 'insumo')], initial='activo', required=True, label="Tipo de complemento")
    nombre = forms.CharField(label='Nombre del Insumo', max_length=100)

class addServicioMultimediaForm(forms.Form):
    servicio = forms.ModelChoiceField(queryset=Servicio.objects.all(), label='Servicio')
    tipo = forms.ChoiceField(label="Tipo de Archivo", choices=[('Imagen', 'Imagen'), ('Video', 'Video')])
    url = forms.FileField(label="Archivo Multimedia")