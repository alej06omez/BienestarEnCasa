from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .limites import validar_conflicto_proveedor, validar_limites_cliente
from .models import SolicitudReserva
from .serializers import (
    CancelarSolicitudSerializer,
    ContraproponerSolicitudSerializer,
    FinalizarServicioSerializer,
    RechazarContrapropuestaSerializer,
    RechazarSolicitudSerializer,
    SolicitudReservaSerializer,
)
from usuarios.authentication import CookieJWTAuthentication
import datetime

from django.utils.dateparse import parse_date
from usuarios.models import PerfilProveedor, PeriodoNoDisponible
from usuarios.validators import validar_horario_reserva


class ClienteSolicitudesViewSet(viewsets.ModelViewSet):
    """
    Vista para la gestión y consulta de solicitudes/reservas (Clientes y Proveedores).
    Incluye el ciclo completo de Sprint 3: HU-15, HU-16, HU-17 y HU-18.
    """
    serializer_class = SolicitudReservaSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def _es_proveedor_de_solicitud(self, usuario, solicitud):
        if usuario.is_staff or usuario.is_superuser:
            return True
        perfil = getattr(usuario, 'perfil', None)
        rol = str(getattr(perfil, 'rol', '')).upper()
        if rol not in ['PROVEEDOR', 'PRO']:
            return False
        if solicitud.proveedor and solicitud.proveedor.perfil_usuario.usuario_id == usuario.id:
            return True
        if (
            solicitud.servicio
            and solicitud.servicio.proveedor
            and solicitud.servicio.proveedor.perfil_usuario.usuario_id == usuario.id
        ):
            return True
        return False

    def _es_cliente_de_solicitud(self, usuario, solicitud):
        return solicitud.cliente_id == usuario.id

    def get_queryset(self):
        usuario = self.request.user
        if not usuario or not usuario.is_authenticated:
            return SolicitudReserva.objects.none()

        perfil = getattr(usuario, 'perfil', None)
        rol = str(getattr(perfil, 'rol', '')).upper()

        # Si el usuario es PROVEEDOR, obtiene las solicitudes dirigidas a sus servicios o a su perfil
        if rol in ['PROVEEDOR', 'PRO'] or usuario.is_staff:
            perfil_profesional = getattr(perfil, 'perfil_profesional', None)

            # Construir filtro flexible para proveedores
            filtro_proveedor = (
                Q(servicio__proveedor__perfil_usuario__usuario=usuario)
                | Q(proveedor__perfil_usuario__usuario=usuario)
            )
            if perfil_profesional:
                filtro_proveedor |= Q(proveedor=perfil_profesional)

            qs = SolicitudReserva.objects.filter(filtro_proveedor).distinct().order_by('-creado_en')
        else:
            # Si es CLIENTE, retorna únicamente sus solicitudes creadas
            qs = SolicitudReserva.objects.filter(cliente=usuario).order_by('-creado_en')

        if self.action == 'list':
            estado_param = self.request.query_params.get('estado', '').strip().upper()
            if estado_param:
                qs = qs.filter(estado=estado_param)

        return qs

    def perform_create(self, serializer):
        usuario = self.request.user
        perfil = getattr(usuario, 'perfil', None)
        rol = str(getattr(perfil, 'rol', '')).upper()

        # E1: Validar estrictamente que un proveedor no pueda crear solicitudes
        if rol in ['PROVEEDOR', 'PRO'] and not usuario.is_staff:
            raise PermissionDenied("Los usuarios con rol de Proveedor no tienen permitida la creación de solicitudes.")

        servicio = serializer.validated_data.get('servicio')
        proveedor_obj = None

        # 1. Obtener el proveedor desde el servicio de forma segura
        if servicio:
            if hasattr(servicio, 'proveedor') and servicio.proveedor:
                proveedor_obj = servicio.proveedor

        # 2. Asignar el User autenticado como cliente y el proveedor identificado
        serializer.save(
            cliente=usuario,
            proveedor=proveedor_obj
        )

    def perform_update(self, serializer):
        """
        Guarda actualizaciones parciales validando reglas de rol y conflicto
        en caso de que se intente modificar el estado vía PATCH.
        """
        solicitud = self.get_object()
        nuevo_estado = serializer.validated_data.get('estado')
        if nuevo_estado and nuevo_estado != solicitud.estado:
            es_proveedor = self._es_proveedor_de_solicitud(self.request.user, solicitud)
            es_cliente = self._es_cliente_de_solicitud(self.request.user, solicitud)

            if nuevo_estado in (
                SolicitudReserva.Estado.SUGERIDA,
                SolicitudReserva.Estado.COMPLETADA,
            ) and not es_proveedor:
                raise PermissionDenied("Solo el proveedor puede realizar esta transición de estado.")

            if nuevo_estado == SolicitudReserva.Estado.ACEPTADA:
                if solicitud.estado == SolicitudReserva.Estado.PENDIENTE and not es_proveedor:
                    raise PermissionDenied("Solo el proveedor puede aceptar una solicitud pendiente.")
                if solicitud.estado == SolicitudReserva.Estado.SUGERIDA and not es_cliente:
                    raise PermissionDenied("Solo el cliente puede aceptar una contrapropuesta.")
                validar_conflicto_proveedor(
                    solicitud.proveedor,
                    serializer.validated_data.get('fecha_solicitada', solicitud.fecha_solicitada),
                    serializer.validated_data.get('hora_solicitada', solicitud.hora_solicitada),
                    solicitud.duracion_minutos_copia,
                    excluir_solicitud_id=solicitud.pk,
                )

        serializer.save()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"mensaje": "No tienes solicitudes o reservas registradas.", "resultados": []},
                status=status.HTTP_200_OK
            )
        return super().list(request, *args, **kwargs)

    # -------------------------------------------------------------------------
    # HU-15: Gestión de la respuesta del proveedor a una solicitud
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='aceptar')
    def aceptar(self, request, pk=None):
        """HU-15: El proveedor acepta una solicitud en estado PENDIENTE."""
        solicitud = self.get_object()
        if not self._es_proveedor_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el proveedor asignado puede aceptar esta solicitud.")

        with transaction.atomic():
            if solicitud.proveedor_id:
                PerfilProveedor.objects.select_for_update().get(pk=solicitud.proveedor_id)
            solicitud = SolicitudReserva.objects.select_for_update().get(pk=solicitud.pk)

            if solicitud.estado != SolicitudReserva.Estado.PENDIENTE:
                raise ValidationError({
                    'estado': 'Solo se pueden aceptar solicitudes en estado PENDIENTE.'
                })

            validar_horario_reserva(
                solicitud.proveedor,
                solicitud.fecha_solicitada,
                solicitud.hora_solicitada,
                solicitud.duracion_minutos_copia,
            )
            validar_conflicto_proveedor(
                solicitud.proveedor,
                solicitud.fecha_solicitada,
                solicitud.hora_solicitada,
                solicitud.duracion_minutos_copia,
                excluir_solicitud_id=solicitud.pk,
            )

            solicitud.estado = SolicitudReserva.Estado.ACEPTADA
            solicitud.save(update_fields=['estado', 'actualizado_en'])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='rechazar')
    def rechazar(self, request, pk=None):
        """HU-15: El proveedor rechaza una solicitud PENDIENTE indicando un motivo."""
        solicitud = self.get_object()
        if not self._es_proveedor_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el proveedor asignado puede rechazar esta solicitud.")

        if solicitud.estado != SolicitudReserva.Estado.PENDIENTE:
            raise ValidationError({
                'estado': 'Solo se pueden rechazar solicitudes en estado PENDIENTE.'
            })

        input_serializer = RechazarSolicitudSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        solicitud.estado = SolicitudReserva.Estado.CANCELADA
        solicitud.motivo_rechazo_cancelacion = input_serializer.validated_data['motivo']
        solicitud.cancelado_por = SolicitudReserva.CanceladoPor.PROVEEDOR
        solicitud.cancelado_en = timezone.now()
        solicitud.save(update_fields=[
            'estado', 'motivo_rechazo_cancelacion', 'cancelado_por', 'cancelado_en', 'actualizado_en'
        ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='contraproponer')
    def contraproponer(self, request, pk=None):
        """HU-15: El proveedor sugiere una nueva fecha y/u hora para una solicitud PENDIENTE."""
        solicitud = self.get_object()
        if not self._es_proveedor_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el proveedor asignado puede proponer un nuevo horario.")

        if solicitud.estado != SolicitudReserva.Estado.PENDIENTE:
            raise ValidationError({
                'estado': 'Solo se puede enviar una contrapropuesta a solicitudes en estado PENDIENTE.'
            })

        input_serializer = ContraproponerSolicitudSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        fecha_sug = input_serializer.validated_data.get('fecha_sugerida') or solicitud.fecha_solicitada
        hora_sug = input_serializer.validated_data['hora_sugerida']
        comentario = input_serializer.validated_data.get('comentario_contrapropuesta', '').strip()

        if fecha_sug == solicitud.fecha_solicitada and hora_sug == solicitud.hora_solicitada:
            raise ValidationError({
                'hora_sugerida': 'La contrapropuesta debe proponer una fecha u hora diferente a la solicitada.'
            })

        validar_horario_reserva(
            solicitud.proveedor,
            fecha_sug,
            hora_sug,
            solicitud.duracion_minutos_copia,
        )
        validar_conflicto_proveedor(
            solicitud.proveedor,
            fecha_sug,
            hora_sug,
            solicitud.duracion_minutos_copia,
            excluir_solicitud_id=solicitud.pk,
        )

        solicitud.fecha_sugerida = fecha_sug
        solicitud.hora_sugerida = hora_sug
        solicitud.comentario_contrapropuesta = comentario
        solicitud.estado = SolicitudReserva.Estado.SUGERIDA
        solicitud.save(update_fields=[
            'fecha_sugerida', 'hora_sugerida', 'comentario_contrapropuesta', 'estado', 'actualizado_en'
        ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # HU-16: Gestión de la respuesta del cliente a una contrapropuesta
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='aceptar-contrapropuesta')
    def aceptar_contrapropuesta(self, request, pk=None):
        """HU-16: El cliente acepta la contrapropuesta sugerida por el proveedor."""
        solicitud = self.get_object()
        if not self._es_cliente_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el cliente propietario puede responder a esta contrapropuesta.")

        with transaction.atomic():
            if solicitud.proveedor_id:
                PerfilProveedor.objects.select_for_update().get(pk=solicitud.proveedor_id)
            get_user_model().objects.select_for_update().get(pk=solicitud.cliente_id)
            solicitud = SolicitudReserva.objects.select_for_update().get(pk=solicitud.pk)

            if solicitud.estado != SolicitudReserva.Estado.SUGERIDA:
                raise ValidationError({
                    'estado': 'Solo puedes aceptar una contrapropuesta cuando la solicitud está en estado SUGERIDA.'
                })

            if not solicitud.fecha_sugerida or not solicitud.hora_sugerida:
                raise ValidationError({
                    'hora_sugerida': 'La solicitud no cuenta con una fecha u hora sugerida válida.'
                })

            validar_horario_reserva(
                solicitud.proveedor,
                solicitud.fecha_sugerida,
                solicitud.hora_sugerida,
                solicitud.duracion_minutos_copia,
            )
            validar_conflicto_proveedor(
                solicitud.proveedor,
                solicitud.fecha_sugerida,
                solicitud.hora_sugerida,
                solicitud.duracion_minutos_copia,
                excluir_solicitud_id=solicitud.pk,
            )
            validar_limites_cliente(
                solicitud.cliente,
                solicitud.fecha_sugerida,
                solicitud.hora_sugerida,
                solicitud.duracion_minutos_copia,
                excluir_solicitud_id=solicitud.pk,
            )

            solicitud.fecha_solicitada = solicitud.fecha_sugerida
            solicitud.hora_solicitada = solicitud.hora_sugerida
            solicitud.estado = SolicitudReserva.Estado.ACEPTADA
            solicitud.save(update_fields=[
                'fecha_solicitada', 'hora_solicitada', 'estado', 'actualizado_en'
            ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='rechazar-contrapropuesta')
    def rechazar_contrapropuesta(self, request, pk=None):
        """HU-16: El cliente rechaza la contrapropuesta del proveedor y la solicitud queda CANCELADA."""
        solicitud = self.get_object()
        if not self._es_cliente_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el cliente propietario puede responder a esta contrapropuesta.")

        if solicitud.estado != SolicitudReserva.Estado.SUGERIDA:
            raise ValidationError({
                'estado': 'Solo puedes rechazar una contrapropuesta cuando la solicitud está en estado SUGERIDA.'
            })

        input_serializer = RechazarContrapropuestaSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        motivo = input_serializer.validated_data.get('motivo', '').strip()
        if not motivo:
            motivo = 'Contrapropuesta rechazada por el cliente.'

        solicitud.estado = SolicitudReserva.Estado.CANCELADA
        solicitud.motivo_rechazo_cancelacion = motivo
        solicitud.cancelado_por = SolicitudReserva.CanceladoPor.CLIENTE
        solicitud.cancelado_en = timezone.now()
        solicitud.save(update_fields=[
            'estado', 'motivo_rechazo_cancelacion', 'cancelado_por', 'cancelado_en', 'actualizado_en'
        ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # HU-17: Cancelación de una solicitud o reserva
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """HU-17: Cliente o Proveedor cancela una solicitud/reserva activa (PENDIENTE, SUGERIDA o ACEPTADA)."""
        solicitud = self.get_object()
        es_cliente = self._es_cliente_de_solicitud(request.user, solicitud)
        es_proveedor = self._es_proveedor_de_solicitud(request.user, solicitud)

        if not es_cliente and not es_proveedor:
            raise PermissionDenied("No tienes permiso para cancelar esta solicitud o reserva.")

        if solicitud.estado == SolicitudReserva.Estado.CANCELADA:
            raise ValidationError({'estado': 'Esta solicitud o reserva ya se encuentra cancelada.'})

        if solicitud.estado == SolicitudReserva.Estado.COMPLETADA:
            raise ValidationError({'estado': 'No se puede cancelar un servicio que ya fue completado.'})

        input_serializer = CancelarSolicitudSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        solicitud.estado = SolicitudReserva.Estado.CANCELADA
        solicitud.motivo_rechazo_cancelacion = input_serializer.validated_data['motivo']
        solicitud.cancelado_por = (
            SolicitudReserva.CanceladoPor.CLIENTE
            if es_cliente
            else SolicitudReserva.CanceladoPor.PROVEEDOR
        )
        solicitud.cancelado_en = timezone.now()
        solicitud.save(update_fields=[
            'estado', 'motivo_rechazo_cancelacion', 'cancelado_por', 'cancelado_en', 'actualizado_en'
        ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # HU-18: Finalización del servicio
    # -------------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """HU-18: El proveedor marca una reserva ACEPTADA como COMPLETADA."""
        solicitud = self.get_object()
        if not self._es_proveedor_de_solicitud(request.user, solicitud):
            raise PermissionDenied("Solo el proveedor asignado puede finalizar el servicio.")

        if solicitud.estado == SolicitudReserva.Estado.COMPLETADA:
            raise ValidationError({'estado': 'Este servicio ya fue marcado como completado.'})

        if solicitud.estado != SolicitudReserva.Estado.ACEPTADA:
            raise ValidationError({
                'estado': 'Solo se pueden finalizar reservas que estén en estado ACEPTADA.'
            })

        input_serializer = FinalizarServicioSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        solicitud.estado = SolicitudReserva.Estado.COMPLETADA
        solicitud.completado_en = timezone.now()
        solicitud.observaciones_finalizacion = input_serializer.validated_data.get(
            'observaciones_finalizacion', ''
        ).strip()
        solicitud.save(update_fields=[
            'estado', 'completado_en', 'observaciones_finalizacion', 'actualizado_en'
        ])

        return Response(self.get_serializer(solicitud).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # HU-19: Agenda del proveedor (reservas ACEPTADAS en orden cronológico)
    # GET /api/solicitudes/agenda/?desde=AAAA-MM-DD&hasta=AAAA-MM-DD
    # Sin parámetros: de hoy en adelante (hasta 92 días).
    # -------------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='agenda')
    def agenda(self, request):
        perfil = getattr(request.user, 'perfil', None)
        if str(getattr(perfil, 'rol', '')).upper() not in ('PROVEEDOR', 'PRO'):
            raise PermissionDenied('Solo los proveedores tienen agenda.')

        def fecha_param(nombre):
            valor = request.query_params.get(nombre)
            if not valor:
                return None
            fecha = parse_date(valor)
            if fecha is None:
                raise ValidationError({nombre: 'Usa el formato AAAA-MM-DD.'})
            return fecha

        desde = fecha_param('desde') or timezone.localdate()
        hasta = fecha_param('hasta') or (desde + datetime.timedelta(days=92))
        if hasta < desde:
            raise ValidationError({'hasta': 'La fecha final no puede ser anterior a la inicial.'})
        if (hasta - desde).days > 92:
            raise ValidationError({'hasta': 'El rango máximo es de 92 días.'})

        # Siempre las del proveedor autenticado: no hay forma de pedir la agenda de otro
        reservas = SolicitudReserva.objects.filter(
            proveedor__perfil_usuario__usuario=request.user,
            estado=SolicitudReserva.Estado.ACEPTADA,
            fecha_solicitada__gte=desde,
            fecha_solicitada__lte=hasta,
        ).select_related(
            'cliente__perfil', 'proveedor__perfil_usuario__usuario', 'servicio__categoria'
        ).order_by('fecha_solicitada', 'hora_solicitada')

        perfil_proveedor = getattr(perfil, 'perfil_profesional', None)
        periodos = []
        if perfil_proveedor:
            periodos = [
                {'id': p.id, 'fecha_inicio': p.fecha_inicio.isoformat(),
                 'fecha_fin': p.fecha_fin.isoformat(), 'motivo': p.motivo}
                for p in PeriodoNoDisponible.objects.filter(
                    proveedor=perfil_proveedor, fecha_inicio__lte=hasta, fecha_fin__gte=desde
                ).order_by('fecha_inicio')
            ]

        datos = self.get_serializer(reservas, many=True).data
        return Response({
            'desde': desde.isoformat(),
            'hasta': hasta.isoformat(),
            'reservas': datos,
            'mensaje': '' if datos else 'No tienes reservas aceptadas para mostrar.',
            'periodos_no_disponibles': periodos,
        })
