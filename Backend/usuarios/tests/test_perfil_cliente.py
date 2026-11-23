from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from usuarios.models import Direccion, PerfilProveedor, PerfilUsuario, ZonaAtencion

Usuario = get_user_model()


#HU-04
#E1
class ConsultaPerfilClienteTests(APITestCase):
    def setUp(self):
        """
        Crea un usuario con rol CLIENTE, su PerfilUsuario y dos
        direcciones (una principal y una secundaria), para confirmar
        que el serializer selecciona la correcta.
        """
        self.url_mi_perfil = "/api/auth/mi-perfil/"
 
        self.usuario_cliente = Usuario.objects.create_user(
            username="cliente@test.com",
            email="cliente@test.com",
            password="ClaveSegura123!",
            first_name="Ana",
            last_name="Martínez",
        )
 
        self.perfil_cliente = PerfilUsuario.objects.create(
            usuario=self.usuario_cliente,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3001234567",
        )
 
        self.direccion_secundaria = Direccion.objects.create(
            usuario=self.usuario_cliente,
            direccion="Calle 10 # 20-30",
            ciudad="Cali",
            barrio="San Fernando",
            es_principal=False,
        )
 
        self.direccion_principal = Direccion.objects.create(
            usuario=self.usuario_cliente,
            direccion="Avenida Siempreviva # 7-42",
            ciudad="Cali",
            barrio="El Ingenio",
            complemento="Apto 301",
            es_principal=True,
        )
 
        # Se autentica directamente al cliente de pruebas para aislar este
        # escenario del flujo de login (ya cubierto en otro módulo).
        self.client.force_authenticate(user=self.usuario_cliente)
 
    def test_consulta_perfil_cliente_satisfactoria(self):
        """
        Un cliente autenticado debe recibir sus datos personales
        junto con el objeto completo de su dirección principal.
        """
        response = self.client.get(self.url_mi_perfil)
 
        data = response.json()
        direccion = data.get("direccion_principal")
 
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            data.get("email"),
            "cliente@test.com",
        )
        self.assertEqual(
            data.get("nombres"),
            "Ana",
        )
        self.assertEqual(
            data.get("apellidos"),
            "Martínez",
        )
        self.assertEqual(
            data.get("rol"),
            PerfilUsuario.Rol.CLIENTE,
        )
        self.assertIsNotNone(
            direccion,
            msg="Se esperaba el objeto direccion_principal en el JSON",
        )
        self.assertEqual(
            direccion.get("direccion"),
            "Avenida Siempreviva # 7-42",
        )
        self.assertEqual(
            direccion.get("barrio"),
            "El Ingenio",
        )
        self.assertTrue(
            direccion.get("es_principal"),
        )
 
        print(
            "\n[test_consulta_perfil_cliente_satisfactoria]",
            "\nStatus:", response.status_code,
            "\nDatos personales:", {
                "email": data.get("email"),
                "nombres": data.get("nombres"),
                "apellidos": data.get("apellidos"),
                "rol": data.get("rol"),
            },
            "\ndireccion_principal:", direccion,
        )

#E2
class actualizarPerfilClienteTest(APITestCase):
    def setUp(self):
            """
            Crea un usuario con rol CLIENTE, su PerfilUsuario y dos
            direcciones (una principal y una secundaria), para confirmar
            que el serializer selecciona la correcta.
            """
            self.url_mi_perfil = "/api/auth/mi-perfil/"
     
            self.usuario_cliente = Usuario.objects.create_user(
                username="cliente@test.com",
                email="cliente@test.com",
                password="ClaveSegura123!",
                first_name="Ana",
                last_name="Martínez",
            )
     
            self.perfil_cliente = PerfilUsuario.objects.create(
                usuario=self.usuario_cliente,
                rol=PerfilUsuario.Rol.CLIENTE,
                telefono="3001234567",
            )
     
            self.direccion_secundaria = Direccion.objects.create(
                usuario=self.usuario_cliente,
                direccion="Calle 10 # 20-30",
                ciudad="Cali",
                barrio="San Fernando",
                es_principal=False,
            )
     
            self.direccion_principal = Direccion.objects.create(
                usuario=self.usuario_cliente,
                direccion="Avenida Siempreviva # 7-42",
                ciudad="Cali",
                barrio="El Ingenio",
                complemento="Apto 301",
                es_principal=True,
            )
     
            # Se autentica directamente al cliente de pruebas para aislar este
            # escenario del flujo de login (ya cubierto en otro módulo).
            self.client.force_authenticate(user=self.usuario_cliente)
    def test_actualizacion_perfil_cliente_satisfactoria(self):
        """
        Escenario: Actualización satisfactoria de datos personales, modificando 
        datos permitidos de su perfil con información válida.
        El sistema debe guardar los cambios y debe mostrar la información 
        actualizada en consultas posteriores.
        """
        
        # Datos de prueba: Nueva información válida para los campos permitidos
        # (Modificaremos el nombre y el teléfono, dejando intacto el apellido)
        datos_actualizados = {
            'nombres': 'Ana Maria',
            'telefono': '3229998877'
        }

        # Acción 1: Enviar petición PATCH para actualizar el perfil
        respuesta_patch = self.client.patch(
            self.url_mi_perfil,
            datos_actualizados,
            format='json'
        )

        # Validación 1: El sistema guarda los cambios y responde exitosamente (HTTP 200 OK)
        self.assertEqual(
            respuesta_patch.status_code,
            status.HTTP_200_OK,
            msg=f"Falló la actualización. Respuesta: {respuesta_patch.data}"
        )

        # Acción 2: Consultar nuevamente el perfil para verificar persistencia real
        respuesta_get = self.client.get(self.url_mi_perfil)
        datos_consultados = respuesta_get.data

        # Validación 2: El sistema muestra la información actualizada
        self.assertEqual(
            datos_consultados.get('nombres'),
            datos_actualizados['nombres']
        )
        self.assertEqual(
            datos_consultados.get('telefono'),
            datos_actualizados['telefono']
        )
        
        # Validación 3: Confirmamos que los campos NO enviados (apellidos) no se alteraron
        self.assertEqual(
            datos_consultados.get('apellidos'),
            "Martínez"
        )

        # Bloque de depuración
        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP (PATCH Actualización):", respuesta_patch.status_code)
        print("Estado HTTP (GET Consulta posterior):", respuesta_get.status_code)
        print("Datos modificados enviados:", datos_actualizados)
        print("Datos del perfil en base de datos tras actualizar:", {
            "nombres": datos_consultados.get('nombres'),
            "apellidos": datos_consultados.get('apellidos'),
            "telefono": datos_consultados.get('telefono')
        })

class actualizarDireccionClienteTest(APITestCase):
    def setUp(self):
        """
        Crea un usuario CLIENTE autenticado, listo para registrar
        una nueva dirección principal.
        """
        self.url_direcciones = "/api/usuarios/direcciones/"

        self.usuario_cliente = Usuario.objects.create_user(
            username="cliente_dir@test.com",
            email="cliente_dir@test.com",
            password="ClaveSegura123!",
            first_name="Carlos",
            last_name="Gómez",
        )

        self.perfil_cliente = PerfilUsuario.objects.create(
            usuario=self.usuario_cliente,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3001234567",
        )

        self.client.force_authenticate(user=self.usuario_cliente)

        
        self.nueva_direccion_principal = {
            "direccion": "Calle 5 # 40-100", 
            "ciudad": "Cali",
            "barrio": "Tequendama",
            "es_principal": True,
            "complemento": "Casa esquinera"
        }

    def test_actualizacion_nueva_direccion_principal_satisfactoria(self):
        """
        Un POST a las direcciones del usuario con es_principal=True 
        debe guardarse correctamente apuntando al Usuario directamente.
        """
        response = self.client.post(
            self.url_direcciones,
            data=self.nueva_direccion_principal,
            format="json",
        )

        data_response = response.json()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg="El endpoint debe retornar 201 Created al guardar la nueva dirección.",
        )
        self.assertEqual(
            data_response.get("direccion"),
            "Calle 5 # 40-100",
        )
        self.assertTrue(
            data_response.get("es_principal"),
            msg="La respuesta JSON debe indicar que es la dirección principal.",
        )

        #Buscamos la relación desde el Usuario
        direccion_db = self.usuario_cliente.direcciones.filter(
            es_principal=True
        ).first()

        self.assertIsNotNone(
            direccion_db,
            msg="La nueva dirección principal debe existir en la BD relacionada al usuario.",
        )
        self.assertEqual(
            direccion_db.direccion,
            "Calle 5 # 40-100",
        )
        self.assertEqual(
            direccion_db.complemento,
            "Casa esquinera",
        )

        print(
            "\n[test_actualizacion_nueva_direccion_principal_satisfactoria]",
            "\nStatus HTTP POST:", response.status_code,
            "\nDatos devueltos por la API:", data_response,
            "\nDirección guardada (Usuario BD):", direccion_db.direccion if direccion_db else None,
            "\nComplemento en BD:", direccion_db.complemento if direccion_db else None,
            "\nEs principal en BD:", direccion_db.es_principal if direccion_db else None,
        )

#E4
class actualizarDireccionFallida(APITestCase):
    def setUp(self):
        """
        Crea un usuario CLIENTE autenticado con datos iniciales completos.
        """
        self.url_mi_perfil = "/api/auth/mi-perfil/"

        self.usuario_cliente = Usuario.objects.create_user(
            username="cliente_original@test.com",
            email="cliente_original@test.com",
            password="ClaveSegura123!",
            first_name="Roberto",
            last_name="García",
        )

        self.perfil_cliente = PerfilUsuario.objects.create(
            usuario=self.usuario_cliente,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3001234567",
        )

        self.client.force_authenticate(user=self.usuario_cliente)

        # Simulamos que el usuario borra/omite su nombre y su email (campos requeridos)
        self.datos_incompletos = {
            "nombres": "",
            "apellidos": "García",
            "email": "", 
            "telefono": "3001234567"
        }

    def test_actualizacion_rechazada_por_datos_incompletos(self):
        """
        Un PATCH enviando valores vacíos en campos obligatorios debe devolver 400,
        señalar el error en dichos campos, y no modificar los datos previos en BD.
        """
        response = self.client.patch(
            self.url_mi_perfil,
            data=self.datos_incompletos,
            format="json",
        )

        data_response = response.json()

        # 1. Verifica el rechazo de la actualización
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg="El endpoint debe retornar 400 Bad Request al omitir campos obligatorios.",
        )

        # 2. Verifica que se indiquen los campos pendientes/inválidos
        self.assertIn(
            "nombres",
            data_response,
            msg="El JSON de error debe indicar que 'nombres' falló o es requerido.",
        )
        self.assertIn(
            "email",
            data_response,
            msg="El JSON de error debe indicar que 'email' falló o es requerido.",
        )

        # 3. Verifica que la información previa se conserve (sin cambios)
        self.usuario_cliente.refresh_from_db()
        self.perfil_cliente.refresh_from_db()

        self.assertEqual(
            self.usuario_cliente.first_name,
            "Roberto",
            msg="El nombre original debe conservarse en la base de datos.",
        )
        self.assertEqual(
            self.usuario_cliente.email,
            "cliente_original@test.com",
            msg="El email original debe conservarse en la base de datos.",
        )

        print(
            "\n[test_actualizacion_rechazada_por_datos_incompletos]",
            "\nStatus HTTP PATCH:", response.status_code,
            "\nErrores indicados por la API:", data_response,
            "\nNombre conservado en BD:", self.usuario_cliente.first_name,
            "\nEmail conservado en BD:", self.usuario_cliente.email,
        )

#E5
class actulizarDirreccionFallida2(APITestCase):
    def setUp(self):
        """
        Crea un usuario CLIENTE autenticado con datos iniciales válidos.
        """
        self.url_mi_perfil = "/api/auth/mi-perfil/"

        self.usuario_cliente = Usuario.objects.create_user(
            username="cliente_valido@test.com",
            email="cliente_valido@test.com",
            password="ClaveSegura123!",
            first_name="Luis",
            last_name="Fernández",
        )

        self.perfil_cliente = PerfilUsuario.objects.create(
            usuario=self.usuario_cliente,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3001234567",
        )

        self.client.force_authenticate(user=self.usuario_cliente)

        # Datos que violan las validaciones de los serializadores/modelos
        self.datos_invalidos = {
            "nombres": "Luis Modificado",
            "apellidos": "Fernández",
            "email": "esto_no_es_un_correo",  # Formato inválido
            "telefono": "123456789012345678901"  # Excede max_length=20
        }

    def test_actualizacion_rechazada_por_datos_invalidos(self):
        """
        Un PATCH con datos mal formateados debe devolver 400, mostrar 
        el detalle de los errores y no guardar nada en la base de datos.
        """
        response = self.client.patch(
            self.url_mi_perfil,
            data=self.datos_invalidos,
            format="json",
        )

        data_response = response.json()

        # 1. Verifica el rechazo por formato inválido
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg="El endpoint debe retornar 400 Bad Request al enviar datos inválidos.",
        )

        # 2. Verifica que se indiquen los campos con errores de validación
        self.assertIn(
            "email",
            data_response,
            msg="El JSON de error debe indicar que 'email' no tiene un formato válido.",
        )
        self.assertIn(
            "telefono",
            data_response,
            msg="El JSON de error debe indicar que 'telefono' falló su validación de longitud.",
        )

        # 3. Verifica que la información previa se conserve intacta
        self.usuario_cliente.refresh_from_db()
        self.perfil_cliente.refresh_from_db()

        self.assertEqual(
            self.usuario_cliente.first_name,
            "Luis",
            msg="El nombre no debió actualizarse porque la petición completa fue rechazada.",
        )
        self.assertEqual(
            self.usuario_cliente.email,
            "cliente_valido@test.com",
            msg="El email original debe conservarse intacto.",
        )
        self.assertEqual(
            self.perfil_cliente.telefono,
            "3001234567",
            msg="El teléfono original debe conservarse intacto.",
        )

        print(
            "\n[test_actualizacion_rechazada_por_datos_invalidos]",
            "\nStatus HTTP PATCH:", response.status_code,
            "\nErrores de validación devueltos:", data_response,
            "\nNombre conservado en BD:", self.usuario_cliente.first_name,
            "\nEmail conservado en BD:", self.usuario_cliente.email,
            "\nTeléfono conservado en BD:", self.perfil_cliente.telefono,
        )

class consultarPerfilFallido(APITestCase):
    def setUp(self):
        """
        Crea dos usuarios CLIENTE. Autentica al primero e intenta
        operar sobre la URL del segundo.
        """
        # 1. Creación del cliente activo (el atacante/intruso)
        self.usuario_activo = Usuario.objects.create_user(
            username="cliente_activo@test.com",
            email="cliente_activo@test.com",
            password="ClaveSegura123!",
            first_name="Andrés",
            last_name="Pérez",
        )
        self.perfil_activo = PerfilUsuario.objects.create(
            usuario=self.usuario_activo,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3000000001",
        )

        # 2. Creación del cliente ajeno (la víctima)
        self.usuario_ajeno = Usuario.objects.create_user(
            username="cliente_ajeno@test.com",
            email="cliente_ajeno@test.com",
            password="ClaveSegura123!",
            first_name="Camilo",
            last_name="Sánchez",
        )
        self.perfil_ajeno = PerfilUsuario.objects.create(
            usuario=self.usuario_ajeno,
            rol=PerfilUsuario.Rol.CLIENTE,
            telefono="3000000002",
        )

        # Autenticamos al cliente activo
        self.client.force_authenticate(user=self.usuario_activo)

        # URL dinámica apuntando al recurso del usuario ajeno
        # Ajusta "usuarios-detail" o la estructura según el nombre de tus rutas
        self.url_ajena = f"/api/usuarios/{self.usuario_ajeno.id}/"

        self.datos_maliciosos = {
            "nombres": "Hackeado",
            "telefono": "9999999999"
        }

    def test_consulta_y_modificacion_perfil_ajeno_denegada(self):
        """
        Un cliente autenticado no debe poder hacer GET ni PATCH 
        en el perfil de otro cliente.
        """
        # --- 1. Intento de Consulta (GET) ---
        response_get = self.client.get(self.url_ajena)
        
        # Dependiendo de si filtras el queryset o usas permisos, DRF retorna 403 o 404.
        # Validamos que NO sea un 200 OK.
        self.assertNotEqual(
            response_get.status_code,
            status.HTTP_200_OK,
            msg="El sistema no debe permitir la consulta de un perfil ajeno (esperado 403 o 404).",
        )

        # --- 2. Intento de Modificación (PATCH) ---
        response_patch = self.client.patch(
            self.url_ajena,
            data=self.datos_maliciosos,
            format="json",
        )

        self.assertNotEqual(
            response_patch.status_code,
            status.HTTP_200_OK,
            msg="El sistema no debe permitir modificar un perfil ajeno (esperado 403 o 404).",
        )

        # --- 3. Verificación de Inmutabilidad ---
        self.usuario_ajeno.refresh_from_db()
        self.perfil_ajeno.refresh_from_db()

        self.assertEqual(
            self.usuario_ajeno.first_name,
            "Camilo",
            msg="El nombre del perfil ajeno debió conservarse intacto.",
        )
        self.assertEqual(
            self.perfil_ajeno.telefono,
            "3000000002",
            msg="El teléfono del perfil ajeno debió conservarse intacto.",
        )

        print(
            "\n[test_consulta_y_modificacion_perfil_ajeno_denegada]",
            "\nStatus HTTP GET (Consulta):", response_get.status_code,
            "\nStatus HTTP PATCH (Modificación):", response_patch.status_code,
            "\nNombre real conservado BD:", self.usuario_ajeno.first_name,
            "\nTeléfono real conservado BD:", self.perfil_ajeno.telefono,
        )

