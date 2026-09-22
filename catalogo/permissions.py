from rest_framework import permissions
from usuarios.models import PerfilUsuario

class IsProveedor(permissions.BasePermission):
    """
    Verifica que el usuario autenticado sea un Proveedor con perfil activo.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return hasattr(request.user, 'perfil') and request.user.perfil.rol == PerfilUsuario.Rol.PROVEEDOR


class IsProveedorOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a cualquier usuario autenticado, pero solo permite
    modificaciones al proveedor dueño del servicio.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Comprueba si el usuario autenticado posee el perfil de proveedor que registró el servicio
        if hasattr(request.user, 'perfil') and hasattr(request.user.perfil, 'perfil_profesional'):
            return obj.proveedor == request.user.perfil.perfil_profesional
        return False