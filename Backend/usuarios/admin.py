from django.contrib import admin

from .models import (
    Direccion,
    DisponibilidadProveedor,
    PerfilProveedor,
    PerfilUsuario,
    PeriodoNoDisponible,
    ZonaAtencion,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'creado_en')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__email', 'telefono')


@admin.register(PerfilProveedor)
class PerfilProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'perfil_usuario', 'creado_en')
    search_fields = ('perfil_usuario__usuario__email', 'perfil_usuario__usuario__first_name')


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'direccion', 'barrio', 'ciudad', 'es_principal')
    list_filter = ('ciudad', 'es_principal')
    search_fields = ('usuario__email', 'direccion', 'barrio')


@admin.register(ZonaAtencion)
class ZonaAtencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'perfil_proveedor', 'ciudad', 'barrio_sector')
    list_filter = ('ciudad',)
    search_fields = ('barrio_sector', 'ciudad')


@admin.register(DisponibilidadProveedor)
class DisponibilidadProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'dia_semana', 'hora_inicio', 'hora_fin')
    list_filter = ('dia_semana',)
    search_fields = ('proveedor__perfil_usuario__usuario__email', 'proveedor__perfil_usuario__usuario__first_name')


@admin.register(PeriodoNoDisponible)
class PeriodoNoDisponibleProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'fecha_inicio', 'fecha_fin', 'motivo')
    list_filter = ('fecha_inicio', 'fecha_fin')
    search_fields = ('proveedor__perfil_usuario__usuario__email', 'motivo')
