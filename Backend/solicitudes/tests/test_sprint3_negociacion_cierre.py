from datetime import time

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from catalogo.models import Categoria, Servicio
from solicitudes.models import SolicitudReserva
from solicitudes.tests.test_creacion_y_limites import dia_habil
from usuarios.models import DisponibilidadProveedor, PerfilProveedor, PerfilUsuario, PeriodoNoDisponible

User = get_user_model()
Estado = SolicitudReserva.Estado


# =============================================================================
# SPRINT 3: Negociación, reservas y agenda (HU-15, HU-16, HU-17, HU-18)
# =============================================================================

class Sprint3BaseTestCase(APITestCase):
    """Base con actores, servicio y disponibilidad para pruebas del Sprint 3."""

    @classmethod
    def setUpTestData(cls):
        cls.user_cliente = cls._crear_usuario('cli.s3@test.com', 'Camila', 'Lopez', PerfilUsuario.Rol.CLIENTE)
        cls.user_otro_cliente = cls._crear_usuario('otrocli.s3@test.com', 'Mateo', 'Ruiz', PerfilUsuario.Rol.CLIENTE)
        cls.user_proveedor = cls._crear_usuario('prov.s3@test.com', 'Sofia', 'Martinez', PerfilUsuario.Rol.PROVEEDOR)
        cls.user_otro_proveedor = cls._crear_usuario('otroprov.s3@test.com', 'Diego', 'Silva', PerfilUsuario.Rol.PROVEEDOR)

        cls.proveedor = PerfilProveedor.objects.create(
            perfil_usuario=cls.user_proveedor.perfil,
            descripcion_profesional='Terapeuta certificada a domicilio',
        )
        cls.otro_proveedor = PerfilProveedor.objects.create(
            perfil_usuario=cls.user_otro_proveedor.perfil,
            descripcion_profesional='Estilista a domicilio',
        )
        cls.categoria = Categoria.objects.create(nombre='Terapias Sprint 3')
        cls.servicio = Servicio.objects.create(
            proveedor=cls.proveedor,
            categoria=cls.categoria,
            nombre='Masaje descontracturante',
            duracion_minutos=60,
            precio='95000.00',
        )
        cls.servicio_otro = Servicio.objects.create(
            proveedor=cls.otro_proveedor,
            categoria=cls.categoria,
            nombre='Corte clásico',
            duracion_minutos=60,
            precio='35000.00',
        )
        # Horario lunes a viernes 08:00 a 17:00
        for dia in range(5):
            DisponibilidadProveedor.objects.create(
                proveedor=cls.proveedor,
                dia_semana=dia,
                hora_inicio=time(8, 0),
                hora_fin=time(17, 0),
            )
        cls.fecha1 = dia_habil(1)
        cls.fecha2 = dia_habil(2)

    @staticmethod
    def _crear_usuario(email, nombres, apellidos, rol):
        u = User.objects.create_user(
            username=email,
            email=email,
            first_name=nombres,
            last_name=apellidos,
            password='ClaveSegura123!',
        )
        PerfilUsuario.objects.create(usuario=u, rol=rol, telefono='3001112233')
        return u

    def crear_solicitud_bd(
        self,
        cliente=None,
        servicio=None,
        fecha=None,
        hora=time(10, 0),
        estado=Estado.PENDIENTE,
        fecha_sugerida=None,
        hora_sugerida=None,
        comentario_contrapropuesta='',
    ):
        servicio = servicio or self.servicio
        return SolicitudReserva.objects.create(
            cliente=cliente or self.user_cliente,
            proveedor=servicio.proveedor,
            servicio=servicio,
            nombre_servicio_copia=servicio.nombre,
            precio_copia=servicio.precio,
            duracion_minutos_copia=servicio.duracion_minutos,
            fecha_solicitada=fecha or self.fecha1,
            hora_solicitada=hora,
            direccion_atencion='Calle 10 # 20-30',
            barrio_sector='San Fernando',
            estado=estado,
            fecha_sugerida=fecha_sugerida,
            hora_sugerida=hora_sugerida,
            comentario_contrapropuesta=comentario_contrapropuesta,
        )


class HU15RespuestaProveedorTests(Sprint3BaseTestCase):
    """HU-15: Aceptar, rechazar y contraproponer solicitudes pendientes por el proveedor."""

    def test_proveedor_acepta_solicitud_pendiente(self):
        sol = self.crear_solicitud_bd(hora=time(10, 0))
        self.client.force_authenticate(self.user_proveedor)
        res = self.client.post(f'/api/solicitudes/{sol.id}/aceptar/', {}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['estado'], Estado.ACEPTADA)
        sol.refresh_from_db()
        self.assertEqual(sol.estado, Estado.ACEPTADA)

    def test_proveedor_no_puede_aceptar_con_conflicto_de_horario_pero_si_consecutiva(self):
        self.crear_solicitud_bd(cliente=self.user_otro_cliente, hora=time(10, 0), estado=Estado.ACEPTADA)
        sol_solapada = self.crear_solicitud_bd(hora=time(10, 30), estado=Estado.PENDIENTE)
        sol_consecutiva = self.crear_solicitud_bd(hora=time(11, 0), estado=Estado.PENDIENTE)

        self.client.force_authenticate(self.user_proveedor)
        res_conflicto = self.client.post(f'/api/solicitudes/{sol_solapada.id}/aceptar/', {}, format='json')
        self.assertEqual(res_conflicto.status_code, 400)
        self.assertIn('hora_solicitada', res_conflicto.data)
        sol_solapada.refresh_from_db()
        self.assertEqual(sol_solapada.estado, Estado.PENDIENTE)

        res_ok = self.client.post(f'/api/solicitudes/{sol_consecutiva.id}/aceptar/', {}, format='json')
        self.assertEqual(res_ok.status_code, 200, res_ok.data)
        self.assertEqual(res_ok.data['estado'], Estado.ACEPTADA)

    def test_no_se_puede_aceptar_solicitud_que_no_esta_pendiente(self):
        self.client.force_authenticate(self.user_proveedor)
        for estado in (Estado.SUGERIDA, Estado.ACEPTADA, Estado.COMPLETADA, Estado.CANCELADA):
            with self.subTest(estado=estado):
                sol = self.crear_solicitud_bd(estado=estado)
                res = self.client.post(f'/api/solicitudes/{sol.id}/aceptar/', {}, format='json')
                self.assertEqual(res.status_code, 400)
                self.assertIn('estado', res.data)

    def test_permisos_acciones_hu15_cliente_403_ajeno_404_anonimo_401(self):
        sol = self.crear_solicitud_bd(hora=time(9, 0))
        acciones = [
            ('aceptar', {}),
            ('rechazar', {'motivo': 'Sin cupo'}),
            ('contraproponer', {'hora_sugerida': '11:00:00'}),
        ]
        for accion, body in acciones:
            with self.subTest(accion=accion):
                # Anónimo -> 401
                self.client.force_authenticate(None)
                self.assertEqual(
                    self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', body, format='json').status_code,
                    401,
                )
                # Cliente propietario -> 403
                self.client.force_authenticate(self.user_cliente)
                self.assertEqual(
                    self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', body, format='json').status_code,
                    403,
                )
                # Otro proveedor -> 404 (no está en su queryset)
                self.client.force_authenticate(self.user_otro_proveedor)
                self.assertEqual(
                    self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', body, format='json').status_code,
                    404,
                )

    def test_proveedor_rechaza_solicitud_con_motivo_obligatorio(self):
        sol = self.crear_solicitud_bd(hora=time(10, 0))
        self.client.force_authenticate(self.user_proveedor)

        # Sin motivo o solo espacios -> 400
        for payload in ({}, {'motivo': ''}, {'motivo': '   '}):
            res_err = self.client.post(f'/api/solicitudes/{sol.id}/rechazar/', payload, format='json')
            self.assertEqual(res_err.status_code, 400)
            self.assertIn('motivo', res_err.data)

        # Motivo válido -> 200 y CANCELADA por PROVEEDOR
        res_ok = self.client.post(
            f'/api/solicitudes/{sol.id}/rechazar/',
            {'motivo': 'Zona fuera de cobertura en ese horario.'},
            format='json',
        )
        self.assertEqual(res_ok.status_code, 200, res_ok.data)
        self.assertEqual(res_ok.data['estado'], Estado.CANCELADA)
        self.assertEqual(res_ok.data['cancelado_por'], SolicitudReserva.CanceladoPor.PROVEEDOR)
        self.assertIsNotNone(res_ok.data['cancelado_en'])
        self.assertEqual(res_ok.data['motivo_rechazo_cancelacion'], 'Zona fuera de cobertura en ese horario.')

    def test_proveedor_envia_contrapropuesta_valida_y_conserva_original(self):
        sol = self.crear_solicitud_bd(fecha=self.fecha1, hora=time(10, 0))
        self.client.force_authenticate(self.user_proveedor)

        res = self.client.post(
            f'/api/solicitudes/{sol.id}/contraproponer/',
            {
                'fecha_sugerida': self.fecha2.isoformat(),
                'hora_sugerida': '14:00:00',
                'comentario_contrapropuesta': 'Puedo atenderte mejor al día siguiente en la tarde.',
            },
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['estado'], Estado.SUGERIDA)
        self.assertEqual(res.data['fecha_solicitada'], self.fecha1.isoformat())
        self.assertEqual(res.data['hora_solicitada'], '10:00:00')
        self.assertEqual(res.data['fecha_sugerida'], self.fecha2.isoformat())
        self.assertEqual(res.data['hora_sugerida'], '14:00:00')
        self.assertEqual(
            res.data['comentario_contrapropuesta'],
            'Puedo atenderte mejor al día siguiente en la tarde.',
        )

    def test_contrapropuesta_rechaza_misma_fecha_hora_y_horarios_invalidos(self):
        sol = self.crear_solicitud_bd(fecha=self.fecha1, hora=time(10, 0))
        # Reserva aceptada a las 15:00 para probar conflicto
        self.crear_solicitud_bd(
            cliente=self.user_otro_cliente,
            fecha=self.fecha1,
            hora=time(15, 0),
            estado=Estado.ACEPTADA,
        )
        PeriodoNoDisponible.objects.create(
            proveedor=self.proveedor,
            fecha_inicio=self.fecha2,
            fecha_fin=self.fecha2,
            motivo='Capacitación',
        )
        self.client.force_authenticate(self.user_proveedor)

        # Misma fecha y hora -> 400
        misma = self.client.post(
            f'/api/solicitudes/{sol.id}/contraproponer/',
            {'fecha_sugerida': self.fecha1.isoformat(), 'hora_sugerida': '10:00:00'},
            format='json',
        )
        self.assertEqual(misma.status_code, 400)
        self.assertIn('hora_sugerida', misma.data)

        # Fuera de horario del proveedor (16:30 + 60m = 17:30 > 17:00) -> 400
        fuera = self.client.post(
            f'/api/solicitudes/{sol.id}/contraproponer/',
            {'fecha_sugerida': self.fecha1.isoformat(), 'hora_sugerida': '16:30:00'},
            format='json',
        )
        self.assertEqual(fuera.status_code, 400)
        self.assertIn('hora_solicitada', fuera.data)

        # Periodo no disponible -> 400
        bloqueado = self.client.post(
            f'/api/solicitudes/{sol.id}/contraproponer/',
            {'fecha_sugerida': self.fecha2.isoformat(), 'hora_sugerida': '11:00:00'},
            format='json',
        )
        self.assertEqual(bloqueado.status_code, 400)
        self.assertIn('fecha_solicitada', bloqueado.data)

        # Conflicto con reserva aceptada a las 15:00 -> 400
        conflicto = self.client.post(
            f'/api/solicitudes/{sol.id}/contraproponer/',
            {'fecha_sugerida': self.fecha1.isoformat(), 'hora_sugerida': '15:00:00'},
            format='json',
        )
        self.assertEqual(conflicto.status_code, 400)
        self.assertIn('hora_solicitada', conflicto.data)


class HU16RespuestaClienteContrapropuestaTests(Sprint3BaseTestCase):
    """HU-16: Aceptar o rechazar una contrapropuesta por parte del cliente."""

    def test_cliente_acepta_contrapropuesta_actualiza_fecha_hora_y_pasa_a_aceptada(self):
        sol = self.crear_solicitud_bd(
            fecha=self.fecha1,
            hora=time(10, 0),
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha2,
            hora_sugerida=time(14, 0),
            comentario_contrapropuesta='Te propongo a las 2 PM.',
        )
        self.client.force_authenticate(self.user_cliente)
        res = self.client.post(f'/api/solicitudes/{sol.id}/aceptar-contrapropuesta/', {}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['estado'], Estado.ACEPTADA)
        self.assertEqual(res.data['fecha_solicitada'], self.fecha2.isoformat())
        self.assertEqual(res.data['hora_solicitada'], '14:00:00')

        sol.refresh_from_db()
        self.assertEqual(sol.estado, Estado.ACEPTADA)
        self.assertEqual(sol.fecha_solicitada, self.fecha2)
        self.assertEqual(sol.hora_solicitada, time(14, 0))

    def test_solo_cliente_propietario_puede_responder_contrapropuesta(self):
        sol = self.crear_solicitud_bd(
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha1,
            hora_sugerida=time(14, 0),
        )
        for accion in ('aceptar-contrapropuesta', 'rechazar-contrapropuesta'):
            with self.subTest(accion=accion):
                # Proveedor -> 403
                self.client.force_authenticate(self.user_proveedor)
                self.assertEqual(
                    self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', {}, format='json').status_code,
                    403,
                )
                # Otro cliente -> 404
                self.client.force_authenticate(self.user_otro_cliente)
                self.assertEqual(
                    self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', {}, format='json').status_code,
                    404,
                )

    def test_no_se_puede_responder_contrapropuesta_si_no_esta_sugerida(self):
        sol = self.crear_solicitud_bd(estado=Estado.PENDIENTE)
        self.client.force_authenticate(self.user_cliente)
        for accion in ('aceptar-contrapropuesta', 'rechazar-contrapropuesta'):
            res = self.client.post(f'/api/solicitudes/{sol.id}/{accion}/', {}, format='json')
            self.assertEqual(res.status_code, 400)
            self.assertIn('estado', res.data)

    def test_aceptar_contrapropuesta_revalida_conflicto_proveedor_y_limites_cliente(self):
        # 1) Conflicto con otra reserva aceptada del proveedor
        sol = self.crear_solicitud_bd(
            fecha=self.fecha1,
            hora=time(9, 0),
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha1,
            hora_sugerida=time(14, 0),
        )
        self.crear_solicitud_bd(
            cliente=self.user_otro_cliente,
            fecha=self.fecha1,
            hora=time(14, 0),
            estado=Estado.ACEPTADA,
        )
        self.client.force_authenticate(self.user_cliente)
        res_prov = self.client.post(f'/api/solicitudes/{sol.id}/aceptar-contrapropuesta/', {}, format='json')
        self.assertEqual(res_prov.status_code, 400)
        self.assertIn('hora_solicitada', res_prov.data)

        # 2) Cruce con otra solicitud activa del mismo cliente
        sol2 = self.crear_solicitud_bd(
            fecha=self.fecha1,
            hora=time(11, 0),
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha2,
            hora_sugerida=time(10, 0),
        )
        self.crear_solicitud_bd(
            cliente=self.user_cliente,
            servicio=self.servicio_otro,
            fecha=self.fecha2,
            hora=time(10, 0),
            estado=Estado.PENDIENTE,
        )
        res_cli = self.client.post(f'/api/solicitudes/{sol2.id}/aceptar-contrapropuesta/', {}, format='json')
        self.assertEqual(res_cli.status_code, 400)
        self.assertIn('hora_solicitada', res_cli.data)

    def test_cliente_rechaza_contrapropuesta_con_y_sin_motivo(self):
        sol_con_motivo = self.crear_solicitud_bd(
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha1,
            hora_sugerida=time(14, 0),
        )
        sol_sin_motivo = self.crear_solicitud_bd(
            hora=time(11, 0),
            estado=Estado.SUGERIDA,
            fecha_sugerida=self.fecha1,
            hora_sugerida=time(15, 0),
        )
        self.client.force_authenticate(self.user_cliente)

        r1 = self.client.post(
            f'/api/solicitudes/{sol_con_motivo.id}/rechazar-contrapropuesta/',
            {'motivo': 'A esa hora estoy en reunión.'},
            format='json',
        )
        self.assertEqual(r1.status_code, 200, r1.data)
        self.assertEqual(r1.data['estado'], Estado.CANCELADA)
        self.assertEqual(r1.data['cancelado_por'], SolicitudReserva.CanceladoPor.CLIENTE)
        self.assertEqual(r1.data['motivo_rechazo_cancelacion'], 'A esa hora estoy en reunión.')

        r2 = self.client.post(
            f'/api/solicitudes/{sol_sin_motivo.id}/rechazar-contrapropuesta/',
            {},
            format='json',
        )
        self.assertEqual(r2.status_code, 200, r2.data)
        self.assertEqual(r2.data['estado'], Estado.CANCELADA)
        self.assertEqual(r2.data['cancelado_por'], SolicitudReserva.CanceladoPor.CLIENTE)
        self.assertEqual(r2.data['motivo_rechazo_cancelacion'], 'Contrapropuesta rechazada por el cliente.')


class HU17CancelacionSolicitudReservaTests(Sprint3BaseTestCase):
    """HU-17: Cancelación por cliente o proveedor con motivo y liberación de agenda."""

    def test_cliente_cancela_en_estados_activos(self):
        self.client.force_authenticate(self.user_cliente)
        for idx, estado in enumerate((Estado.PENDIENTE, Estado.SUGERIDA, Estado.ACEPTADA)):
            with self.subTest(estado=estado):
                sol = self.crear_solicitud_bd(hora=time(9 + idx, 0), estado=estado)
                res = self.client.post(
                    f'/api/solicitudes/{sol.id}/cancelar/',
                    {'motivo': 'Cambio de planes personales.'},
                    format='json',
                )
                self.assertEqual(res.status_code, 200, res.data)
                self.assertEqual(res.data['estado'], Estado.CANCELADA)
                self.assertEqual(res.data['cancelado_por'], SolicitudReserva.CanceladoPor.CLIENTE)
                self.assertIsNotNone(res.data['cancelado_en'])
                self.assertEqual(res.data['motivo_rechazo_cancelacion'], 'Cambio de planes personales.')

    def test_proveedor_cancela_en_estados_activos(self):
        self.client.force_authenticate(self.user_proveedor)
        for idx, estado in enumerate((Estado.PENDIENTE, Estado.SUGERIDA, Estado.ACEPTADA)):
            with self.subTest(estado=estado):
                sol = self.crear_solicitud_bd(hora=time(9 + idx, 0), estado=estado)
                res = self.client.post(
                    f'/api/solicitudes/{sol.id}/cancelar/',
                    {'motivo': 'Imprevisto de fuerza mayor.'},
                    format='json',
                )
                self.assertEqual(res.status_code, 200, res.data)
                self.assertEqual(res.data['estado'], Estado.CANCELADA)
                self.assertEqual(res.data['cancelado_por'], SolicitudReserva.CanceladoPor.PROVEEDOR)
                self.assertIsNotNone(res.data['cancelado_en'])

    def test_cancelacion_exige_motivo_y_bloquea_canceladas_o_completadas(self):
        sol_activa = self.crear_solicitud_bd(estado=Estado.ACEPTADA)
        sol_cancelada = self.crear_solicitud_bd(hora=time(11, 0), estado=Estado.CANCELADA)
        sol_completada = self.crear_solicitud_bd(hora=time(12, 0), estado=Estado.COMPLETADA)

        self.client.force_authenticate(self.user_cliente)
        # Sin motivo -> 400
        sin_motivo = self.client.post(f'/api/solicitudes/{sol_activa.id}/cancelar/', {'motivo': '  '}, format='json')
        self.assertEqual(sin_motivo.status_code, 400)
        self.assertIn('motivo', sin_motivo.data)

        # Ya cancelada -> 400
        ya_canc = self.client.post(
            f'/api/solicitudes/{sol_cancelada.id}/cancelar/', {'motivo': 'Otro'}, format='json'
        )
        self.assertEqual(ya_canc.status_code, 400)
        self.assertIn('estado', ya_canc.data)

        # Ya completada -> 400
        ya_comp = self.client.post(
            f'/api/solicitudes/{sol_completada.id}/cancelar/', {'motivo': 'Otro'}, format='json'
        )
        self.assertEqual(ya_comp.status_code, 400)
        self.assertIn('estado', ya_comp.data)

    def test_cancelar_reserva_aceptada_libera_horario_para_proveedor_y_cliente(self):
        reserva = self.crear_solicitud_bd(fecha=self.fecha1, hora=time(10, 0), estado=Estado.ACEPTADA)
        otra_pendiente = self.crear_solicitud_bd(
            cliente=self.user_otro_cliente,
            fecha=self.fecha1,
            hora=time(10, 0),
            estado=Estado.PENDIENTE,
        )

        # Proveedor cancela la reserva original -> el espacio de las 10:00 queda libre
        self.client.force_authenticate(self.user_proveedor)
        res_canc = self.client.post(
            f'/api/solicitudes/{reserva.id}/cancelar/',
            {'motivo': 'Reorganización de agenda'},
            format='json',
        )
        self.assertEqual(res_canc.status_code, 200)

        # Ahora el proveedor sí puede aceptar la otra solicitud a las 10:00
        res_acept = self.client.post(f'/api/solicitudes/{otra_pendiente.id}/aceptar/', {}, format='json')
        self.assertEqual(res_acept.status_code, 200, res_acept.data)

        # Y el cliente original también puede agendar otro servicio a las 10:00
        self.client.force_authenticate(self.user_cliente)
        res_nueva = self.client.post('/api/solicitudes/', {
            'servicio': self.servicio_otro.id,
            'proveedor': self.otro_proveedor.id,
            'fecha_solicitada': self.fecha1.isoformat(),
            'hora_solicitada': '10:00:00',
            'direccion_atencion': 'Calle 10 # 20-30',
            'barrio_sector': 'San Fernando',
        }, format='json')
        self.assertEqual(res_nueva.status_code, 201, res_nueva.data)

    def test_usuario_ajeno_no_puede_cancelar_y_anonimo_recibe_401(self):
        sol = self.crear_solicitud_bd(estado=Estado.PENDIENTE)
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post(f'/api/solicitudes/{sol.id}/cancelar/', {'motivo': 'X'}, format='json').status_code,
            401,
        )
        self.client.force_authenticate(self.user_otro_cliente)
        self.assertEqual(
            self.client.post(f'/api/solicitudes/{sol.id}/cancelar/', {'motivo': 'X'}, format='json').status_code,
            404,
        )


class HU18FinalizacionServicioTests(Sprint3BaseTestCase):
    """HU-18: Finalización del servicio por el proveedor e inmutabilidad posterior."""

    def test_proveedor_finaliza_reserva_aceptada(self):
        sol = self.crear_solicitud_bd(estado=Estado.ACEPTADA)
        self.client.force_authenticate(self.user_proveedor)

        res = self.client.post(
            f'/api/solicitudes/{sol.id}/finalizar/',
            {'observaciones_finalizacion': 'Sesión completada sin novedades.'},
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['estado'], Estado.COMPLETADA)
        self.assertIsNotNone(res.data['completado_en'])
        self.assertEqual(res.data['observaciones_finalizacion'], 'Sesión completada sin novedades.')

        # También funciona sin observaciones (opcional)
        sol2 = self.crear_solicitud_bd(hora=time(12, 0), estado=Estado.ACEPTADA)
        res2 = self.client.post(f'/api/solicitudes/{sol2.id}/finalizar/', {}, format='json')
        self.assertEqual(res2.status_code, 200, res2.data)
        self.assertEqual(res2.data['estado'], Estado.COMPLETADA)
        self.assertEqual(res2.data['observaciones_finalizacion'], '')

    def test_permisos_finalizacion_cliente_403_ajeno_404_anonimo_401(self):
        sol = self.crear_solicitud_bd(estado=Estado.ACEPTADA)

        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(f'/api/solicitudes/{sol.id}/finalizar/', {}, format='json').status_code, 401)

        self.client.force_authenticate(self.user_cliente)
        self.assertEqual(self.client.post(f'/api/solicitudes/{sol.id}/finalizar/', {}, format='json').status_code, 403)

        self.client.force_authenticate(self.user_otro_proveedor)
        self.assertEqual(self.client.post(f'/api/solicitudes/{sol.id}/finalizar/', {}, format='json').status_code, 404)

    def test_no_se_puede_finalizar_si_no_esta_aceptada_ni_modificar_completada(self):
        self.client.force_authenticate(self.user_proveedor)
        for estado in (Estado.PENDIENTE, Estado.SUGERIDA, Estado.CANCELADA, Estado.COMPLETADA):
            with self.subTest(estado=estado):
                sol = self.crear_solicitud_bd(estado=estado)
                res = self.client.post(f'/api/solicitudes/{sol.id}/finalizar/', {}, format='json')
                self.assertEqual(res.status_code, 400)
                self.assertIn('estado', res.data)

        # Una completada no se puede editar vía PATCH
        completada = self.crear_solicitud_bd(estado=Estado.COMPLETADA)
        res_patch = self.client.patch(
            f'/api/solicitudes/{completada.id}/',
            {'observaciones': 'Intento tardío'},
            format='json',
        )
        self.assertEqual(res_patch.status_code, 400)
        self.assertIn('estado', res_patch.data)


class Sprint3FlujoCompletoYFrontendTests(APITestCase):
    """Flujo E2E completo de Sprint 3 con login JWT en cookies + renderizado de vistas HTML."""

    def _login(self, email, nombres, rol):
        self.client.cookies.clear()
        reg = self.client.post('/api/auth/registro/', {
            'nombres': nombres,
            'apellidos': 'Sprint3',
            'email': email,
            'rol': rol,
            'password': 'ClaveSegura123!',
            'password_confirmacion': 'ClaveSegura123!',
            'telefono': '3001234567',
        }, format='json')
        self.assertEqual(reg.status_code, 201, reg.data)
        login = self.client.post('/api/auth/iniciar-sesion/', {
            'email': email,
            'password': 'ClaveSegura123!',
        }, format='json')
        self.assertEqual(login.status_code, 200, login.data)
        return login.cookies['access'].value

    def _con_token(self, token):
        self.client.cookies.clear()
        self.client.cookies['access'] = token

    def test_flujo_completo_negociacion_reserva_y_finalizacion_con_jwt(self):
        token_prov = self._login('prov.e2e@test.com', 'Elena', 'PROVEEDOR')
        token_cli = self._login('cli.e2e@test.com', 'Tomas', 'CLIENTE')

        # Proveedor configura perfil y servicio
        self._con_token(token_prov)
        perfil = self.client.post('/api/proveedores/mi-perfil/', {
            'descripcion_profesional': 'Especialista en bienestar',
        }, format='json')
        self.assertEqual(perfil.status_code, 201, perfil.data)
        cat = self.client.post('/api/catalogo/categorias/', {'nombre': 'Spa E2E'}, format='json')
        self.assertEqual(cat.status_code, 201, cat.data)
        srv = self.client.post('/api/catalogo/servicios/', {
            'nombre': 'Aromaterapia',
            'categoria': cat.data['id'],
            'descripcion': 'Relajación total',
            'duracion_minutos': 60,
            'precio': '70000.00',
        }, format='json')
        self.assertEqual(srv.status_code, 201, srv.data)

        fecha1 = dia_habil(1)
        fecha2 = dia_habil(2)

        # 1. Cliente crea solicitud (PENDIENTE)
        self._con_token(token_cli)
        creada = self.client.post('/api/solicitudes/', {
            'servicio': srv.data['id'],
            'proveedor': perfil.data['id'],
            'fecha_solicitada': fecha1.isoformat(),
            'hora_solicitada': '10:00:00',
            'direccion_atencion': 'Carrera 5 # 12-34',
            'barrio_sector': 'Granada',
        }, format='json')
        self.assertEqual(creada.status_code, 201, creada.data)
        sol_id = creada.data['id']
        self.assertEqual(creada.data['estado'], Estado.PENDIENTE)

        # 2. HU-15: Proveedor envía contrapropuesta (PENDIENTE -> SUGERIDA)
        self._con_token(token_prov)
        contra = self.client.post(f'/api/solicitudes/{sol_id}/contraproponer/', {
            'fecha_sugerida': fecha2.isoformat(),
            'hora_sugerida': '14:00:00',
            'comentario_contrapropuesta': '¿Te sirve mañana a las 2 PM?',
        }, format='json')
        self.assertEqual(contra.status_code, 200, contra.data)
        self.assertEqual(contra.data['estado'], Estado.SUGERIDA)

        # 3. Filtro ?estado=SUGERIDA para el cliente
        self._con_token(token_cli)
        filtradas = self.client.get('/api/solicitudes/?estado=SUGERIDA')
        self.assertEqual(filtradas.status_code, 200)
        self.assertEqual(len(filtradas.data), 1)
        self.assertEqual(filtradas.data[0]['id'], sol_id)

        # 4. HU-16: Cliente acepta contrapropuesta (SUGERIDA -> ACEPTADA)
        aceptada = self.client.post(f'/api/solicitudes/{sol_id}/aceptar-contrapropuesta/', {}, format='json')
        self.assertEqual(aceptada.status_code, 200, aceptada.data)
        self.assertEqual(aceptada.data['estado'], Estado.ACEPTADA)
        self.assertEqual(aceptada.data['fecha_solicitada'], fecha2.isoformat())
        self.assertEqual(aceptada.data['hora_solicitada'], '14:00:00')

        # 5. HU-18: Proveedor finaliza el servicio (ACEPTADA -> COMPLETADA)
        self._con_token(token_prov)
        finalizada = self.client.post(f'/api/solicitudes/{sol_id}/finalizar/', {
            'observaciones_finalizacion': 'Cliente satisfecho.',
        }, format='json')
        self.assertEqual(finalizada.status_code, 200, finalizada.data)
        self.assertEqual(finalizada.data['estado'], Estado.COMPLETADA)
        self.assertIsNotNone(finalizada.data['completado_en'])

    def test_paginas_frontend_sprint3_renderizan_y_contienen_controles(self):
        panel = self.client.get('/panel-proveedor/')
        self.assertEqual(panel.status_code, 200)
        html_panel = panel.content.decode('utf-8')
        self.assertIn('modalContraproponer', html_panel)
        self.assertIn('modalMotivoProveedor', html_panel)
        self.assertIn('modalFinalizarServicio', html_panel)

        mis_sol = self.client.get('/mis-solicitudes/')
        self.assertEqual(mis_sol.status_code, 200)
        html_mis_sol = mis_sol.content.decode('utf-8')
        self.assertIn('aceptarContrapropuestaCliente', html_mis_sol)
        self.assertIn('abrirModalCancelarCliente', html_mis_sol)
        self.assertIn('selectEstado', html_mis_sol)

        detalle = self.client.get('/mis-solicitudes/1/')
        self.assertEqual(detalle.status_code, 200)
        html_detalle = detalle.content.decode('utf-8')
        self.assertIn('btn-aceptar-contrapropuesta', html_detalle)
        self.assertIn('btn-rechazar-contrapropuesta', html_detalle)
        self.assertIn('btn-cancelar-detalle', html_detalle)
        self.assertIn('btn-finalizar-detalle', html_detalle)

    def test_solicitud_incluye_categoria_nombre_y_valida_servicio_requerido(self):
        token_prov = self._login('prov.cat@test.com', 'Ana', 'PROVEEDOR')
        token_cli = self._login('cli.cat@test.com', 'Luis', 'CLIENTE')

        self._con_token(token_prov)
        cat_id = self.client.get('/api/catalogo/categorias/').data[0]['id']
        cat_nombre = self.client.get('/api/catalogo/categorias/').data[0]['nombre']
        srv = self.client.post('/api/catalogo/servicios/', {
            'nombre': 'Servicio con categoría',
            'categoria': cat_id,
            'duracion_minutos': 60,
            'precio': '45000.00',
        }, format='json')
        self.assertEqual(srv.status_code, 201, srv.data)

        self._con_token(token_cli)
        # Sin servicio -> 400 (no 500)
        sin_srv = self.client.post('/api/solicitudes/', {
            'fecha_solicitada': dia_habil(1).isoformat(),
            'hora_solicitada': '10:00:00',
            'direccion_atencion': 'Calle 10 # 5-5',
            'barrio_sector': 'San Antonio',
        }, format='json')
        self.assertEqual(sin_srv.status_code, 400)
        self.assertIn('servicio', sin_srv.data)

        # Con servicio (incluso omitiendo proveedor explícito) -> 201 y expone categoria_nombre
        ok = self.client.post('/api/solicitudes/', {
            'servicio': srv.data['id'],
            'fecha_solicitada': dia_habil(1).isoformat(),
            'hora_solicitada': '10:00:00',
            'direccion_atencion': 'Calle 10 # 5-5',
            'barrio_sector': 'San Antonio',
        }, format='json')
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(ok.data['categoria_nombre'], cat_nombre)
