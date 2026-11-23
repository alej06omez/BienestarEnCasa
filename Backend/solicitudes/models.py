from django.db import models
from django.conf import settings
from catalogo.models import Servicio
from usuarios.models import PerfilProveedor

class SolicitudReserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        SUGERIDA = 'SUGERIDA', 'Sugerida'
        ACEPTADA = 'ACEPTADA', 'Aceptada'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    class CanceladoPor(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        PROVEEDOR = 'PROVEEDOR', 'Proveedor'

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes_cliente'
    )
    proveedor = models.ForeignKey(
        PerfilProveedor,
        on_delete=models.CASCADE,
        related_name='solicitudes_recibidas'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        null=True,
        related_name='solicitudes'
    )

    # Copia de condiciones del servicio en la creación (RF-23 / RN-13)
    nombre_servicio_copia = models.CharField(max_length=150)
    precio_copia = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos_copia = models.PositiveIntegerField()

    # Datos del agendamiento y ubicación
    fecha_solicitada = models.DateField()
    hora_solicitada = models.TimeField()
    direccion_atencion = models.CharField(max_length=255)
    barrio_sector = models.CharField(max_length=100)
    informacion_complementaria = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    # Estado y motivo de cancelación/rechazo (HU-13, HU-15, HU-16, HU-17, HU-18)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo_rechazo_cancelacion = models.TextField(blank=True, null=True)

    # Negociación / Contrapropuesta del proveedor (HU-15, HU-16)
    fecha_sugerida = models.DateField(blank=True, null=True)
    hora_sugerida = models.TimeField(blank=True, null=True)
    comentario_contrapropuesta = models.TextField(blank=True, default='')

    # Trazabilidad de cancelación (HU-15, HU-16, HU-17)
    cancelado_por = models.CharField(
        max_length=12,
        choices=CanceladoPor.choices,
        blank=True,
        default='',
    )
    cancelado_en = models.DateTimeField(blank=True, null=True)

    # Finalización del servicio (HU-18)
    completado_en = models.DateTimeField(blank=True, null=True)
    observaciones_finalizacion = models.TextField(blank=True, default='')

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'solicitud o reserva'
        verbose_name_plural = 'solicitudes y reservas'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Solicitud #{self.id} - {self.nombre_servicio_copia} ({self.estado})"