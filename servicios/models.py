from django.db import models
from usuarios.models import PerfilUsuario

# Create your models here.

#ajustar modelos sin ID
class Servicio (models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    descripcion = models.TextField()
    duracion = models.DurationField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo')

    class Meta:
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'

    def __str__(self):
        return self.nombre


class multimediaServicio(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='multimedia')
    url = models.URLField(max_length=200, blank=True, null=False)
    tipo = models.CharField(max_length=10, choices=[('imagen', 'Imagen'), ('video', 'Video')])

    class Meta:
        verbose_name = 'servicioMultimedia'
        verbose_name_plural = 'servicioMultimedias'

    def __str__(self):
        return f'{self.tipo} - {self.servicio.nombre}'

class servicioInsumo(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='insumos')
    nombre = models.CharField(max_length=100)
    idinsumo = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'servicioInsumo'
        verbose_name_plural = 'servicioInsumos'

    def __str__(self):
        return f'{self.nombre} - {self.servicio.nombre}' 