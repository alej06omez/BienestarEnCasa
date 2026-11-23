from django.contrib import admin
from .models import SolicitudReserva


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nombre_servicio_copia', 'cliente', 'proveedor',
        'fecha_solicitada', 'hora_solicitada', 'estado', 'creado_en',
    )
    list_filter = ('estado', 'fecha_solicitada', 'cancelado_por')
    search_fields = ('nombre_servicio_copia', 'cliente__email', 'direccion_atencion', 'barrio_sector')
