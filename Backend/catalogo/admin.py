from django.contrib import admin
from .models import Categoria, ContenidoMultimediaServicio, ElementoServicio, Servicio


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria', 'proveedor', 'precio', 'duracion_minutos', 'estado')
    list_filter = ('estado', 'categoria')
    search_fields = ('nombre', 'descripcion', 'proveedor__perfil_usuario__usuario__email')


@admin.register(ContenidoMultimediaServicio)
class ContenidoMultimediaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'servicio', 'tipo', 'descripcion')
    list_filter = ('tipo',)


@admin.register(ElementoServicio)
class ElementoServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'servicio', 'tipo', 'nombre')
    list_filter = ('tipo',)
    search_fields = ('nombre',)
