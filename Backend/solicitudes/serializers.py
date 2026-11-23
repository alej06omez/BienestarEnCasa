from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import SolicitudReserva
from catalogo.models import Servicio
from usuarios.validators import validar_horario_reserva
from .limites import validar_limites_cliente

class SolicitudReservaSerializer(serializers.ModelSerializer):
    nombre_proveedor = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    cliente_telefono = serializers.SerializerMethodField()
    categoria_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudReserva
        fields = [
            'id', 'cliente', 'cliente_nombre', 'cliente_telefono', 'proveedor', 'nombre_proveedor', 'servicio',
            'categoria_nombre',
            'nombre_servicio_copia', 'precio_copia', 'duracion_minutos_copia',
            'fecha_solicitada', 'hora_solicitada', 'direccion_atencion',
            'barrio_sector', 'informacion_complementaria', 'observaciones',
            'estado', 'motivo_rechazo_cancelacion',
            'fecha_sugerida', 'hora_sugerida', 'comentario_contrapropuesta',
            'cancelado_por', 'cancelado_en',
            'completado_en', 'observaciones_finalizacion',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = [
            'cliente', 'categoria_nombre', 'nombre_servicio_copia', 'precio_copia',
            'duracion_minutos_copia',
            'fecha_sugerida', 'hora_sugerida', 'comentario_contrapropuesta',
            'cancelado_por', 'cancelado_en',
            'completado_en', 'observaciones_finalizacion',
            'creado_en', 'actualizado_en'
        ]
        extra_kwargs = {
            'proveedor': {'required': False},
        }

    def get_categoria_nombre(self, obj):
        if obj.servicio and obj.servicio.categoria:
            return obj.servicio.categoria.nombre
        return ''

    def get_cliente_telefono(self, obj):
        if not obj.cliente:
            return ''
        perfil = getattr(obj.cliente, 'perfil', None)
        return getattr(perfil, 'telefono', '') if perfil else ''

    def get_cliente_nombre(self, obj):
        if not obj.cliente:
            return "Usuario"

        # 1. Nombre completo desde el modelo User de Django
        first_name = getattr(obj.cliente, 'first_name', '')
        last_name = getattr(obj.cliente, 'last_name', '')
        nombre_completo = f"{first_name} {last_name}".strip()
        if nombre_completo:
            return nombre_completo

        # 2. Nombre completo desde PerfilUsuario si existe
        perfil = getattr(obj.cliente, 'perfil', None)
        if perfil:
            nom_p = getattr(perfil, 'nombres', '')
            ape_p = getattr(perfil, 'apellidos', '')
            completo_perfil = f"{nom_p} {ape_p}".strip()
            if completo_perfil:
                return completo_perfil

        # 3. Nombre basado en email
        email = getattr(obj.cliente, 'email', '')
        if email:
            return email.split('@')[0].capitalize()

        return getattr(obj.cliente, 'username', 'Usuario')

    def get_nombre_proveedor(self, obj):
        if not obj.proveedor or not hasattr(obj.proveedor, 'perfil_usuario'):
            return "Proveedor no asignado"
        u = obj.proveedor.perfil_usuario.usuario
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def validate(self, attrs):
        if self.instance is not None and self.instance.estado in (
            SolicitudReserva.Estado.CANCELADA,
            SolicitudReserva.Estado.COMPLETADA,
        ):
            raise serializers.ValidationError({
                'estado': 'No se puede modificar una solicitud que ya fue cancelada o completada.'
            })

        if self.instance is not None and 'estado' in attrs and attrs['estado'] != self.instance.estado:
            nuevo_estado = attrs['estado']
            estado_actual = self.instance.estado
            transiciones_validas = {
                SolicitudReserva.Estado.PENDIENTE: {
                    SolicitudReserva.Estado.SUGERIDA,
                    SolicitudReserva.Estado.ACEPTADA,
                    SolicitudReserva.Estado.CANCELADA,
                },
                SolicitudReserva.Estado.SUGERIDA: {
                    SolicitudReserva.Estado.ACEPTADA,
                    SolicitudReserva.Estado.CANCELADA,
                },
                SolicitudReserva.Estado.ACEPTADA: {
                    SolicitudReserva.Estado.COMPLETADA,
                    SolicitudReserva.Estado.CANCELADA,
                },
            }
            if nuevo_estado not in transiciones_validas.get(estado_actual, set()):
                raise serializers.ValidationError({
                    'estado': f'Transición de estado no permitida de {estado_actual} a {nuevo_estado}.'
                })

        campos_horario = {'fecha_solicitada', 'hora_solicitada', 'servicio'}
        if self.instance is None or campos_horario.intersection(attrs):
            fecha = attrs.get('fecha_solicitada', getattr(self.instance, 'fecha_solicitada', None))
            hora = attrs.get('hora_solicitada', getattr(self.instance, 'hora_solicitada', None))
            servicio = attrs.get('servicio', getattr(self.instance, 'servicio', None))
            if self.instance is None and not servicio:
                raise serializers.ValidationError({
                    'servicio': 'Debes seleccionar un servicio válido para crear la solicitud.'
                })
            if (
                self.instance is None
                and servicio
                and str(servicio.estado).upper() != Servicio.Estado.ACTIVO
            ):
                raise serializers.ValidationError({
                    'servicio': 'Este servicio está inactivo y no acepta nuevas solicitudes.'
                })
            proveedor = (
                servicio.proveedor if servicio
                else getattr(self.instance, 'proveedor', None)
            )
            if self.instance and 'servicio' not in attrs:
                duracion = self.instance.duracion_minutos_copia
            else:
                duracion = servicio.duracion_minutos if servicio else 0
            validar_horario_reserva(proveedor, fecha, hora, duracion)

            # Límites por cliente: sin cruces de horario y máximo 3 solicitudes por día (solo al crear)
            if self.instance is None:
                request = self.context.get('request')
                cliente = getattr(request, 'user', None)
                if cliente is not None and cliente.is_authenticated:
                    validar_limites_cliente(cliente, fecha, hora, duracion)

        return super().validate(attrs)

    def create(self, validated_data):
        servicio = validated_data.get('servicio')

        # Si el campo servicio vino como un entero/ID, obtenemos el objeto de la BD
        if isinstance(servicio, int):
            servicio = Servicio.objects.filter(id=servicio).first()

        # Si el objeto servicio existe, copiamos sus atributos; de lo contrario asignamos valores por defecto no nulos
        if servicio:
            validated_data['nombre_servicio_copia'] = getattr(servicio, 'nombre', 'Servicio General')
            validated_data['precio_copia'] = getattr(servicio, 'precio', 0.00)
            validated_data['duracion_minutos_copia'] = getattr(servicio, 'duracion_minutos', 60)
        else:
            validated_data['nombre_servicio_copia'] = 'Servicio General'
            validated_data['precio_copia'] = 0.00
            validated_data['duracion_minutos_copia'] = 60

        # Evita la condición de carrera: dos peticiones simultáneas del mismo cliente se
        # serializan bloqueando la fila del usuario; la segunda re-valida con la primera ya guardada.
        request = self.context.get('request')
        cliente = getattr(request, 'user', None)
        if cliente is None or not cliente.is_authenticated:
            return super().create(validated_data)

        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=cliente.pk)
            try:
                validar_limites_cliente(
                    cliente,
                    validated_data.get('fecha_solicitada'),
                    validated_data.get('hora_solicitada'),
                    validated_data['duracion_minutos_copia'],
                )
            except ValidationError as exc:
                # Misma forma de respuesta que cuando el error sale de validate(): {campo: [mensaje]}
                raise ValidationError(serializers.as_serializer_error(exc))
            return super().create(validated_data)


class RechazarSolicitudSerializer(serializers.Serializer):
    """HU-15: Rechazo de una solicitud pendiente por parte del proveedor."""
    motivo = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
        error_messages={
            'required': 'Debes indicar un motivo para rechazar la solicitud.',
            'blank': 'Debes indicar un motivo para rechazar la solicitud.',
        },
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'motivo' not in data and 'motivo_rechazo_cancelacion' in data:
            data = {**data, 'motivo': data.get('motivo_rechazo_cancelacion')}
        return super().to_internal_value(data)

    def validate_motivo(self, value):
        limpio = value.strip()
        if not limpio:
            raise serializers.ValidationError('Debes indicar un motivo para rechazar la solicitud.')
        return limpio


class ContraproponerSolicitudSerializer(serializers.Serializer):
    """HU-15: Contrapropuesta de fecha/hora por parte del proveedor."""
    fecha_sugerida = serializers.DateField(required=False)
    hora_sugerida = serializers.TimeField(
        required=True,
        error_messages={
            'required': 'Debes seleccionar una hora sugerida para la contrapropuesta.',
        },
    )
    comentario_contrapropuesta = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=1000,
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            copia = dict(data)
            if 'fecha_sugerida' not in copia and 'fecha_solicitada' in copia:
                copia['fecha_sugerida'] = copia.get('fecha_solicitada')
            if 'hora_sugerida' not in copia and 'hora_solicitada' in copia:
                copia['hora_sugerida'] = copia.get('hora_solicitada')
            if 'comentario_contrapropuesta' not in copia:
                if 'comentario' in copia:
                    copia['comentario_contrapropuesta'] = copia.get('comentario')
                elif 'observaciones' in copia:
                    copia['comentario_contrapropuesta'] = copia.get('observaciones')
            data = copia
        return super().to_internal_value(data)


class RechazarContrapropuestaSerializer(serializers.Serializer):
    """HU-16: Rechazo de la contrapropuesta por parte del cliente."""
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=1000,
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'motivo' not in data and 'motivo_rechazo_cancelacion' in data:
            data = {**data, 'motivo': data.get('motivo_rechazo_cancelacion')}
        return super().to_internal_value(data)


class CancelarSolicitudSerializer(serializers.Serializer):
    """HU-17: Cancelación de una solicitud o reserva por cliente o proveedor."""
    motivo = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
        error_messages={
            'required': 'Debes indicar el motivo de la cancelación.',
            'blank': 'Debes indicar el motivo de la cancelación.',
        },
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'motivo' not in data and 'motivo_rechazo_cancelacion' in data:
            data = {**data, 'motivo': data.get('motivo_rechazo_cancelacion')}
        return super().to_internal_value(data)

    def validate_motivo(self, value):
        limpio = value.strip()
        if not limpio:
            raise serializers.ValidationError('Debes indicar el motivo de la cancelación.')
        return limpio


class FinalizarServicioSerializer(serializers.Serializer):
    """HU-18: Finalización del servicio por parte del proveedor."""
    observaciones_finalizacion = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=1000,
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'observaciones_finalizacion' not in data and 'observaciones' in data:
            data = {**data, 'observaciones_finalizacion': data.get('observaciones')}
        return super().to_internal_value(data)