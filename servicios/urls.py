from django.urls import include, path
from . import views

urlpatterns = [
    path('servicios/', views.servicios_view, name='servicios'),

    path('servicios/<int:servicio_id>/', views.servicio_datalle_view, name='servicio_detalle'),

    path('servicios/crear_servicio', views.crear_servicio_view, name='crear_servicio'),

    ]

