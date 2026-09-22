from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, ServicioViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'servicios', ServicioViewSet, basename='servicio')

urlpatterns = [
    path('', include(router.urls)),
]