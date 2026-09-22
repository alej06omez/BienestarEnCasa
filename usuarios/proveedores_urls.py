from django.urls import path

from .views import MiPerfilProveedorView, MisZonasAtencionView


urlpatterns = [
    path(
        'mi-perfil/',
        MiPerfilProveedorView.as_view(),
        name='mi-perfil-proveedor',
    ),
    path(
        'mis-zonas/',
        MisZonasAtencionView.as_view(),
        name='mis-zonas-atencion',
    ),
]