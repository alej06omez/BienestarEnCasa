from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.servicios_view, name='servicios'),

    path('servicios/<int:servicio_id>/', views.servicio_datalle_view, name='servicio_detalle'),

    path('servicios/crear_servicio', views.crear_servicio_view, name='crear_servicio'),

    path('servicios/anadir_insumo/<int:servicio_id>/', views.addServicioInsumo, 
    name='add_insumo'),

    path('servicios/anadir_multimedia/<int:servicio_id>/', views.addServicioMultimedia, name='add_multimedia'),
    

    ] 


