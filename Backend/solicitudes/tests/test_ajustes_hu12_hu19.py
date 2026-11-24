"""Ajustes de HU-12, HU-13, HU-14 y HU-19: hora de fin, estado legible,
correo del cliente en el detalle y agenda del proveedor."""
import datetime as dt
from datetime import time

from django.utils import timezone

from solicitudes.tests.test_sprint3_negociacion_cierre import Estado, Sprint3BaseTestCase


class DatosNuevosDeLaSolicitudTests(Sprint3BaseTestCase):

    def test_detalle_incluye_correo_del_cliente_hora_fin_y_estado_legible(self):
        sol = self.crear_solicitud_bd(hora=time(10, 30))
        for usuario in (self.user_cliente, self.user_proveedor):
            self.client.force_authenticate(usuario)
            d = self.client.get(f'/api/solicitudes/{sol.id}/').data
            self.assertEqual(d['cliente_email'], 'cli.s3@test.com')
            self.assertEqual(d['cliente_nombre'], 'Camila Lopez')
            self.assertEqual(d['hora_fin'], '11:30:00')  # 10:30 + 60 min conservados
            self.assertEqual(d['estado_display'], 'Pendiente')

    def test_hora_fin_usa_la_duracion_conservada_aunque_cambie_el_catalogo(self):
        sol = self.crear_solicitud_bd(hora=time(9, 0))
        self.servicio.__class__.objects.filter(pk=self.servicio.pk).update(duracion_minutos=120)
        self.client.force_authenticate(self.user_proveedor)
        self.assertEqual(self.client.get(f'/api/solicitudes/{sol.id}/').data['hora_fin'], '10:00:00')

    def test_el_correo_es_de_solo_lectura(self):
        sol = self.crear_solicitud_bd()
        self.client.force_authenticate(self.user_cliente)
        self.client.patch(f'/api/solicitudes/{sol.id}/', {'cliente_email': 'x@x.com'}, format='json')
        self.assertEqual(self.client.get(f'/api/solicitudes/{sol.id}/').data['cliente_email'], 'cli.s3@test.com')


class HU19AgendaTests(Sprint3BaseTestCase):
    url = '/api/solicitudes/agenda/'

    def test_solo_aceptadas_de_hoy_en_adelante_en_orden_cronologico(self):
        tarde = self.crear_solicitud_bd(hora=time(15, 0), estado=Estado.ACEPTADA)
        temprano = self.crear_solicitud_bd(hora=time(9, 0), cliente=self.user_otro_cliente, estado=Estado.ACEPTADA)
        otro_dia = self.crear_solicitud_bd(fecha=self.fecha2, hora=time(8, 0), estado=Estado.ACEPTADA)
        self.crear_solicitud_bd(hora=time(11, 0), estado=Estado.PENDIENTE)
        self.crear_solicitud_bd(hora=time(12, 0), estado=Estado.CANCELADA)
        self.crear_solicitud_bd(hora=time(13, 0), estado=Estado.COMPLETADA)
        pasada = self.crear_solicitud_bd(hora=time(10, 0), estado=Estado.ACEPTADA)
        pasada.__class__.objects.filter(pk=pasada.pk).update(
            fecha_solicitada=timezone.localdate() - dt.timedelta(days=3))

        self.client.force_authenticate(self.user_proveedor)
        d = self.client.get(self.url).data
        self.assertEqual([r['id'] for r in d['reservas']], [temprano.id, tarde.id, otro_dia.id])
        self.assertEqual(d['desde'], timezone.localdate().isoformat())

    def test_periodo_servicio_y_direccion(self):
        self.crear_solicitud_bd(hora=time(9, 0), estado=Estado.ACEPTADA)
        self.client.force_authenticate(self.user_proveedor)
        r = self.client.get(self.url).data['reservas'][0]
        self.assertEqual((r['hora_solicitada'], r['hora_fin']), ('09:00:00', '10:00:00'))
        self.assertEqual((r['nombre_servicio_copia'], r['direccion_atencion']),
                         ('Masaje descontracturante', 'Calle 10 # 20-30'))

    def test_sin_reservas_aceptadas_lo_informa(self):
        self.crear_solicitud_bd(estado=Estado.PENDIENTE)
        self.client.force_authenticate(self.user_proveedor)
        d = self.client.get(self.url).data
        self.assertEqual(d['reservas'], [])
        self.assertEqual(d['mensaje'], 'No tienes reservas aceptadas para mostrar.')

    def test_no_ve_la_agenda_de_otro_proveedor_y_el_cliente_no_tiene_agenda(self):
        self.crear_solicitud_bd(estado=Estado.ACEPTADA)
        self.client.force_authenticate(self.user_otro_proveedor)
        self.assertEqual(self.client.get(self.url).data['reservas'], [])
        self.client.force_authenticate(self.user_cliente)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_sin_autenticacion_se_deniega(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))

    def test_rango_de_fechas_invalido(self):
        self.client.force_authenticate(self.user_proveedor)
        self.assertEqual(self.client.get(self.url + '?desde=2026-12-10&hasta=2026-12-01').status_code, 400)
        self.assertEqual(self.client.get(self.url + '?desde=10-12-2026').status_code, 400)
