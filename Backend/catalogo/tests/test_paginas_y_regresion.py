from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase


class CatalogoPaginasFrontendTests(TestCase):
    def test_paginas_de_gestion_catalogo_y_perfil_renderizan(self):
        rutas = (
            '/mis-servicios/',
            '/mis-servicios/nuevo/',
            '/mis-servicios/1/editar/',
            '/catalogo/',
            '/catalogo/1/',
            '/proveedor/1/',
        )
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_base_template_no_incrusta_codigo_javascript(self):
        plantilla_base = settings.BASE_DIR.parent / 'frontend' / 'templates' / 'base.html'
        contenido = plantilla_base.read_text(encoding='utf-8')
        self.assertNotIn('<script', contenido.lower())



class RegresionCategoriasYProveedorNuevoTests(APITestCase):
    """Verifica que las categorías iniciales existan tras migrar y un proveedor nuevo pueda crear servicios."""

    def test_categorias_iniciales_existen_y_proveedor_nuevo_puede_crear_editar_eliminar_servicio(self):
        # 1. Las categorías iniciales vienen precargadas por la migración de datos
        res_cats = self.client.get('/api/catalogo/categorias/')
        self.assertEqual(res_cats.status_code, 200)
        nombres = {c['nombre'] for c in res_cats.data}
        self.assertIn('Peluquería', nombres)
        self.assertIn('Masajes no Médicos', nombres)
        cat_id = res_cats.data[0]['id']

        # 2. Un proveedor recién registrado (sin PerfilProveedor previo) inicia sesión
        reg = self.client.post('/api/auth/registro/', {
            'nombres': 'Tomas',
            'apellidos': 'Prueba',
            'email': 'tomas.nuevo@test.com',
            'rol': 'PROVEEDOR',
            'password': 'ClaveSegura123!',
            'password_confirmacion': 'ClaveSegura123!',
            'telefono': '3001234567',
        }, format='json')
        self.assertEqual(reg.status_code, 201, reg.data)
        login = self.client.post('/api/auth/iniciar-sesion/', {
            'email': 'tomas.nuevo@test.com',
            'password': 'ClaveSegura123!',
        }, format='json')
        self.assertEqual(login.status_code, 200, login.data)
        self.client.cookies['access'] = login.cookies['access'].value

        # 3. Crea un servicio inmediatamente sin haber llenado /perfil-profesional/
        creado = self.client.post('/api/catalogo/servicios/', {
            'nombre': 'Corte clásico a domicilio',
            'categoria': cat_id,
            'precio': 35000,
            'duracion_minutos': 45,
            'descripcion': 'Incluye lavado',
            'estado': 'ACTIVO',
        }, format='json')
        self.assertEqual(creado.status_code, 201, creado.data)
        self.assertEqual(creado.data['categoria_detalle']['id'], cat_id)

        # 4. Aparece en /api/catalogo/servicios/mios/ con categoria_detalle poblado
        mios = self.client.get('/api/catalogo/servicios/mios/')
        self.assertEqual(mios.status_code, 200)
        self.assertEqual(len(mios.data), 1)
        self.assertEqual(mios.data[0]['categoria_detalle']['nombre'], res_cats.data[0]['nombre'])

        # 5. Puede eliminarlo sin error
        eliminado = self.client.delete(f"/api/catalogo/servicios/{creado.data['id']}/")
        self.assertEqual(eliminado.status_code, 204)

    def test_disponibilidad_html_conserva_horas_seleccionadas_y_direccion_str(self):
        from usuarios.models import Direccion

        reg = self.client.post('/api/auth/registro/', {
            'nombres': 'Laura',
            'apellidos': 'Disp',
            'email': 'laura.disp@test.com',
            'rol': 'PROVEEDOR',
            'password': 'ClaveSegura123!',
            'password_confirmacion': 'ClaveSegura123!',
        }, format='json')
        self.assertEqual(reg.status_code, 201)
        login = self.client.post('/api/auth/iniciar-sesion/', {
            'email': 'laura.disp@test.com',
            'password': 'ClaveSegura123!',
        }, format='json')
        self.assertEqual(login.status_code, 200)
        self.client.cookies['access'] = login.cookies['access'].value

        # Guardar disponibilidad para Lunes 09:00 a 16:00
        guardar = self.client.post('/disponibilidad/', {
            'accion': 'guardar_disponibilidad',
            'dias': ['0'],
            'hora_inicio_0': '09:00',
            'hora_fin_0': '16:00',
        })
        self.assertEqual(guardar.status_code, 302)

        # Al volver a cargar /disponibilidad/, 09:00 y 16:00 deben venir seleccionados
        pagina = self.client.get('/disponibilidad/')
        self.assertEqual(pagina.status_code, 200)
        html = pagina.content.decode('utf-8')
        self.assertIn('<option value="09:00" selected>09:00 AM</option>', html)
        self.assertIn('<option value="16:00" selected>04:00 PM</option>', html)

        # Direccion.__str__ no debe lanzar AttributeError
        usuario = get_user_model().objects.get(email='laura.disp@test.com')
        dir_obj = Direccion.objects.create(
            usuario=usuario, direccion='Calle 1 # 2-3', ciudad='Cali', barrio='San Fernando'
        )
        self.assertEqual(str(dir_obj), 'Calle 1 # 2-3, San Fernando - Cali')
