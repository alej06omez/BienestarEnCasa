from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, ServicioViewSet, ContenidoMultimediaServicioViewSet, ElementoServicioViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'servicios', ServicioViewSet, basename='servicio')
router.register(r'multimedia', ContenidoMultimediaServicioViewSet, basename='multimedia')
router.register(r'elementos', ElementoServicioViewSet, basename='elemento')

urlpatterns = [
    path('', include(router.urls)),
]
