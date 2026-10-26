from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from .models import PerfilUsuario
from usuarios.models import PerfilUsuario, Direccion

Usuario = get_user_model()

class AutenticacionAPITest(APITestCase):
    datos_registro = {
        'nombres': 'Ana',
        'apellidos': 'Gomez',
        'email': 'ana@example.com',
        'password': 'ClaveSegura123!',
        'password_confirmacion': 'ClaveSegura123!',
        'rol': PerfilUsuario.Rol.CLIENTE,
        'telefono': '3001234567',
    }

    def test_registro_inicio_sesion_y_consulta_perfil(self):
        registro = self.client.post('/api/auth/registro/', self.datos_registro, format='json')
        self.assertEqual(registro.status_code, status.HTTP_201_CREATED)
        self.assertEqual(registro.data['rol'], PerfilUsuario.Rol.CLIENTE)

        inicio = self.client.post(
            '/api/auth/iniciar-sesion/',
            {'email': self.datos_registro['email'], 'password': self.datos_registro['password']},
            format='json',
        )
        self.assertEqual(inicio.status_code, status.HTTP_200_OK)
        # los tokens ya no viajan en el body (se revisa el JSON crudo que ve el navegador)
        self.assertNotIn(b'access', inicio.content)
        self.assertNotIn(b'refresh', inicio.content)
        self.assertTrue(inicio.cookies['access']['httponly'])
        self.assertTrue(inicio.cookies['refresh']['httponly'])

        perfil = self.client.get('/api/auth/mi-perfil/')  # el cliente de pruebas reenvia las cookies solo
        self.assertEqual(perfil.status_code, status.HTTP_200_OK)
        self.assertEqual(perfil.data['email'], self.datos_registro['email'])

        renovar = self.client.post('/api/auth/renovar-token/')
        self.assertEqual(renovar.status_code, status.HTTP_200_OK)
        self.assertIn('access', renovar.cookies)

        # con cookie de sesion, un PATCH sin token CSRF debe rechazarse
        sin_csrf = APIClient(enforce_csrf_checks=True)
        sin_csrf.cookies = self.client.cookies
        self.assertEqual(sin_csrf.patch('/api/auth/mi-perfil/', {}, format='json').status_code, status.HTTP_403_FORBIDDEN)

        salida = self.client.post('/api/auth/cerrar-sesion/')
        self.assertEqual(salida.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(salida.cookies['access'].value, '')
        self.assertEqual(self.client.get('/api/auth/mi-perfil/').status_code, status.HTTP_401_UNAUTHORIZED)



#Ejecución #001
#E1

    def test_registro_satisfactorio_como_cliente(self):
        """
        Escenario: Registro satisfactorio como Cliente, ingresando credenciales válidas.
        - Datos obligatorios completos
        - Formato válido
        - Contraseña válida según condiciones
        """
        datos_prueba_cliente = {
            'nombres': 'Carlos',
            'apellidos': 'Ramirez',
            'email': 'carlos.cliente@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3109876543',
        }

        # Simula la acción de "presionar registrar" enviando el payload al endpoint
        respuesta = self.client.post('/api/auth/registro/', datos_prueba_cliente, format='json')

        # Verificaciones esperadas para un registro exitoso
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['rol'], PerfilUsuario.Rol.CLIENTE)
        self.assertEqual(respuesta.data['email'], datos_prueba_cliente['email'])
        self.assertIn('id', respuesta.data) # Verifica que se haya generado y devuelto el identificador del usuario

#E2

    def test_registro_satisfactorio_como_proveedor(self):
        """
        Escenario: Registro satisfactorio como Proveedor, ingresando credenciales válidas.
        - Tipo de Usuario: Proveedor
        - Datos obligatorios completos
        - Formato válido
        - Contraseña válida según condiciones
        """
        datos_prueba_proveedor = {
            'nombres': 'Roberto',
            'apellidos': 'Fernandez',
            'email': 'roberto.proveedor@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.PROVEEDOR,
            'telefono': '3209876543',
        }

        # Simula la acción de "presionar registrar" enviando el payload al endpoint
        respuesta = self.client.post('/api/auth/registro/', datos_prueba_proveedor, format='json')

        # Verificaciones esperadas para un registro exitoso
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['rol'], PerfilUsuario.Rol.PROVEEDOR)
        self.assertEqual(respuesta.data['email'], datos_prueba_proveedor['email'])
        self.assertIn('id', respuesta.data)
        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#E3

    
    def test_registro_con_correo_invalido(self):
        """
        Escenario: Registro con correo electrónico inválido.
        """

        datos_prueba_correo_invalido = {
            'nombres': 'Laura',
            'apellidos': 'Martinez',
            'email': 'laura.martinez_sin_dominio.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3309876543',
        }

        respuesta = self.client.post(
            '/api/auth/registro/',
            datos_prueba_correo_invalido,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertIn('email', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#E4

    def test_registro_con_datos_incompletos(self):
        """
        Escenario: Registro con datos obligatorios incompletos, omitiendo datos y presionando registrar.
        """

        datos_prueba_incompletos = {
            # Se omiten 'nombres' y 'email' intencionalmente
            'apellidos': 'Perez',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3409876543',
        }

        respuesta = self.client.post(
            '/api/auth/registro/',
            datos_prueba_incompletos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertIn('nombres', respuesta.data)
        self.assertIn('email', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#E5
    def test_registro_con_tipo_usuario_invalido(self):
        """
        Escenario: Selección del tipo de usuario, seleccionando un tipo no permitido.
        El sistema solo debe permitir las opciones "Cliente" y "Proveedor".
        """

        datos_prueba_rol_invalido = {
            'nombres': 'Diana',
            'apellidos': 'Rios',
            'email': 'diana.rios@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': 'ADMINISTRADOR', # Tipo de usuario no permitido o inexistente
            'telefono': '3509876543',
        }

        respuesta = self.client.post(
            '/api/auth/registro/',
            datos_prueba_rol_invalido,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        # Verifica que el error provenga específicamente de la validación del campo 'rol'
        self.assertIn('rol', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#E6
    def test_validacion_backend_datos_obligatorios(self):
        """
        Escenario: Validación de los datos recibidos, enviando una solicitud de registro.
        El backend debe validar los datos obligatorios y sus formatos y no depender 
        únicamente de las validaciones de la interfaz.
        """

        # Se envía un payload completamente vacío para simular una petición directa a la API
        # evadiendo cualquier validación de un formulario frontend
        datos_prueba_vacios = {}

        respuesta = self.client.post(
            '/api/auth/registro/',
            datos_prueba_vacios,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        
        # Se verifica que el backend responda con errores exigiendo cada campo obligatorio
        self.assertIn('nombres', respuesta.data)
        self.assertIn('apellidos', respuesta.data)
        self.assertIn('email', respuesta.data)
        self.assertIn('password', respuesta.data)
        self.assertIn('rol', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#HU-02
#E1
    def test_inicio_sesion_satisfactorio(self):
        """
        Escenario: Inicio de sesión satisfactorio, ingresando las credenciales y solicitando iniciar sesión.
        Precondiciones: El Cliente o Proveedor se encuentra registrado.
        """
        
        # 1. Precondición: Registrar al usuario en el sistema para poder iniciar sesión
        datos_registro = {
            'nombres': 'Alejandro',
            'apellidos': 'Marquez',
            'email': 'alejo@gmail.com',
            'password': 'Marquez93',
            'password_confirmacion': 'Marquez93',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3100000000',
        }
        self.client.post(
            '/api/auth/registro/', 
            datos_registro, 
            format='json'
        )

        # 2. Datos de prueba: Credenciales del usuario
        credenciales_login = {
            'email': 'alejo@gmail.com',
            'password': 'Marquez93'
        }

        # 3. Acción: Solicitando iniciar sesión
        respuesta = self.client.post(
            '/api/auth/iniciar-sesion/',
            credenciales_login,
            format='json'
        )

        # 4. Validaciones
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )
        
        # Se verifica que por seguridad los tokens no vengan en el JSON
        self.assertNotIn(b'access', respuesta.content)
        self.assertNotIn(b'refresh', respuesta.content)
        
        # Se verifica que las cookies de sesión se hayan creado y sean HttpOnly
        self.assertTrue(respuesta.cookies['access']['httponly'])
        self.assertTrue(respuesta.cookies['refresh']['httponly'])

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("Cookies establecidas:", list(respuesta.cookies.keys()))
#E2
    def test_inicio_sesion_con_credenciales_incorrectas1(self):
        """
        Escenario: Rechazo de credenciales incorrectas, ingresando credenciales 
        incorrectas y solicitando iniciar sesión.
        """
        
        # 1. Precondición: Registrar al usuario en el sistema para evaluar el rechazo
        datos_registro = {
            'nombres': 'Alejandro',
            'apellidos': 'Marquez',
            'email': 'alejo@gmail.com',
            'password': 'Marquez93',
            'password_confirmacion': 'Marquez93',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3100000000',
        }
        self.client.post(
            '/api/auth/registro/', 
            datos_registro, 
            format='json'
        )

        # 2. Datos de prueba: Credenciales con contraseña incorrecta
        credenciales_incorrectas = {
            'email': 'alejo@gmail.com',
            'password': 'ClaveEquivocada2026'
        }

        # 3. Acción: Solicitando iniciar sesión
        respuesta = self.client.post(
            '/api/auth/iniciar-sesion/',
            credenciales_incorrectas,
            format='json'
        )

        # 4. Validaciones
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        
        
        self.assertIn('detail', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

    def test_inicio_sesion_con_credenciales_incorrectas2(self):
        """
        Escenario: Rechazo de credenciales incorrectas, ingresando credenciales 
        incorrectas y solicitando iniciar sesión.
        """
        
        # 1. Precondición: Registrar al usuario en el sistema para evaluar el rechazo
        datos_registro = {
            'nombres': 'Alejandro',
            'apellidos': 'Marquez',
            'email': 'alejo@gmail.com',
            'password': 'Marquez93',
            'password_confirmacion': 'Marquez93',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3100000000',
        }
        self.client.post(
            '/api/auth/registro/', 
            datos_registro, 
            format='json'
        )

        # 2. Datos de prueba: Credenciales con contraseña incorrecta
        credenciales_incorrectas = {
            'email': 'equivocado@gmail.com',
            'password': 'Marquez93'
        }

        # 3. Acción: Solicitando iniciar sesión
        respuesta = self.client.post(
            '/api/auth/iniciar-sesion/',
            credenciales_incorrectas,
            format='json'
        )

        # 4. Validaciones
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        
        # Verifica que el backend retorne un mensaje de error (usualmente bajo la llave 'detail' en DRF/SimpleJWT)
        self.assertIn('detail', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("HTML de respuesta:", respuesta.content.decode('utf-8'))

#E3
    def test_inicio_sesion_con_datos_incompletos(self):
        """
        Escenario: Validación de campos obligatorios, omitiendo datos y 
        solicitando iniciar sesión.
        El sistema no debe procesar satisfactoriamente la autenticación, 
        debe indicar los campos obligatorios pendientes y no debe crear 
        una sesión autenticada.
        """

        # Datos de prueba: Se envían credenciales vacías, omitiendo email y password
        credenciales_incompletas = {}

        # Acción: Solicitando iniciar sesión
        respuesta = self.client.post(
            '/api/auth/iniciar-sesion/',
            credenciales_incompletas,
            format='json'
        )

        # Validaciones: El backend debe rechazar la solicitud por validación (HTTP 400)
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        
        # Verifica que el sistema indica exactamente cuáles campos hacen falta
        self.assertIn('email', respuesta.data)
        self.assertIn('password', respuesta.data)

        # Verifica que NO se establecieron cookies de sesión (evitando la autenticación)
        self.assertNotIn('access', respuesta.cookies)
        self.assertNotIn('refresh', respuesta.cookies)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)
        print("Cookies establecidas:", list(respuesta.cookies.keys()))

#E4
    def test_autorizacion_funcionalidades_cliente(self):
        """
        Escenario: Autorización de funcionalidades para un Cliente.
        El sistema debe permitir la operación en funcionalidades de cliente 
        y debe impedir el acceso a las funcionalidades exclusivas del Proveedor.
        """
        
        # 1. Precondiciones: Registrar al usuario CLIENTE
        datos_cliente = {
            'nombres': 'Elena',
            'apellidos': 'Torres',
            'email': 'elena.cliente@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3201112233',
        }
        self.client.post('/api/auth/registro/', datos_cliente, format='json')

        # Iniciar sesión correctamente para obtener las cookies de autenticación
        self.client.post(
            '/api/auth/iniciar-sesion/',
            {'email': datos_cliente['email'], 'password': datos_cliente['password']},
            format='json'
        )

        # 2. Datos de prueba / Acción: Acceder a funcionalidad autorizada para clientes
        endpoint_cliente = '/api/usuarios/direcciones/' 
        respuesta_permitida = self.client.get(endpoint_cliente)

        # 3. Validación: El sistema permite la operación
        # (Se asume 200 OK, ajusta a 201 si es un POST según tu endpoint)
        self.assertEqual(
            respuesta_permitida.status_code,
            status.HTTP_200_OK
        )

        # 4. Acción: Intentar acceder a funcionalidad exclusiva de Proveedor
        
        endpoint_proveedor = '/api/proveedores/mis-zonas/'
        respuesta_denegada = self.client.get(endpoint_proveedor)

        # 5. Validación: El sistema impide el acceso por falta de permisos (403 Forbidden)
        self.assertEqual(
            respuesta_denegada.status_code,
            status.HTTP_403_FORBIDDEN
        )

        print("\n--- Resultado de la prueba ---")
        print(f"Estado HTTP (Acceso Cliente - {endpoint_cliente}):", respuesta_permitida.status_code)
        print(f"Estado HTTP (Acceso Proveedor - {endpoint_proveedor}):", respuesta_denegada.status_code)
        print("Mensaje del sistema (Rechazo):", respuesta_denegada.data)

#E5

    def test_autorizacion_funcionalidades_proveedor(self):
            """
            Escenario: Autorización de funcionalidades para un Proveedor.
            El sistema debe permitir la operación en funcionalidades de proveedor 
            y debe impedir el acceso a las funcionalidades exclusivas del Cliente.
            """
            
            # 1. Precondiciones: Registrar al usuario PROVEEDOR
            datos_proveedor = {
                'nombres': 'Jorge',
                'apellidos': 'Giraldo',
                'email': 'jorge.proveedor@example.com',
                'password': 'PasswordValida2026!',
                'password_confirmacion': 'PasswordValida2026!',
                'rol': PerfilUsuario.Rol.PROVEEDOR,
                'telefono': '3001122334',
            }
            self.client.post('/api/auth/registro/', datos_proveedor, format='json')

            # Iniciar sesión correctamente para obtener las cookies de autenticación
            self.client.post(
                '/api/auth/iniciar-sesion/',
                {'email': datos_proveedor['email'], 'password': datos_proveedor['password']},
                format='json'
            )

            # 2. Datos de prueba / Acción: Acceder a funcionalidad autorizada para proveedores
            endpoint_proveedor = '/api/proveedores/mis-zonas/'
            respuesta_permitida = self.client.get(endpoint_proveedor)

            # 3. Validación: El sistema permite la operación
            # (Se asume 200 OK, ajusta a 201 si es un POST según tu endpoint)
            self.assertEqual(
                respuesta_permitida.status_code,
                status.HTTP_200_OK
            )

            # 4. Acción: Intentar acceder a funcionalidad exclusiva de Cliente
            endpoint_cliente = '/api/usuarios/direcciones/' 
            respuesta_denegada = self.client.get(endpoint_cliente)

            # 5. Validación: El sistema impide el acceso por falta de permisos (403 Forbidden)
            self.assertEqual(
                respuesta_denegada.status_code,
                status.HTTP_403_FORBIDDEN
            )

            print("\n--- Resultado de la prueba ---")
            print(f"Estado HTTP (Acceso Proveedor - {endpoint_proveedor}):", respuesta_permitida.status_code)
            print(f"Estado HTTP (Acceso Cliente - {endpoint_cliente}):", respuesta_denegada.status_code)
            print("Mensaje del sistema (Rechazo):", respuesta_denegada.data)
#6
    def test_acceso_recurso_restringido_sin_autenticacion(self):
        """
        Escenario: Intento de acceso a un recurso restringido sin autenticación.
        El sistema debe denegar el acceso, no debe mostrar la información 
        protegida y debe solicitar que la persona inicie sesión.
        """
        
        # 1. Precondiciones: Asegurarnos de que no haya ninguna sesión activa
        # DRF APITestCase inicia sin autenticación por defecto, pero podemos 
        # limpiar las cookies por seguridad para representar explícitamente este estado
        self.client.cookies.clear()

        # 2. Datos de prueba / Acción: Intentar acceder a una funcionalidad restringida
        # Utilizaremos la ruta de direcciones de usuario que guardamos previamente
        endpoint_restringido = '/api/usuarios/direcciones/'
        
        respuesta = self.client.get(endpoint_restringido)

        # 3. Validación: El sistema deniega el acceso (401 Unauthorized)
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        
        # 4. Validación: El sistema responde con el mensaje estándar de DRF 
        # indicando que no se enviaron credenciales de autenticación
        self.assertIn('detail', respuesta.data)

        print("\n--- Resultado de la prueba ---")
        print(f"Estado HTTP (Intento de acceso a {endpoint_restringido}):", respuesta.status_code)
        print("Mensaje del sistema:", respuesta.data)

#E7

    def test_cierre_de_sesion_activa(self):
        """
        Escenario: Cierre de una sesión activa, seleccionando la opción de cerrar sesión.
        El sistema debe finalizar la sesión, invalidar el acceso previamente concedido 
        y requerir iniciar sesión nuevamente para acceder a recursos protegidos.
        """
        
        # 1. Precondiciones: Registrar un usuario e iniciar sesión para tener una sesión activa
        datos_usuario = {
            'nombres': 'Andres',
            'apellidos': 'Vargas',
            'email': 'andres.vargas@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3112223344',
        }
        
        self.client.post(
            '/api/auth/registro/', 
            datos_usuario, 
            format='json'
        )

        self.client.post(
            '/api/auth/iniciar-sesion/',
            {'email': datos_usuario['email'], 'password': datos_usuario['password']},
            format='json'
        )

        # 2. Acción: Seleccionando la opción de cerrar sesión (POST al endpoint de logout)
        respuesta_salida = self.client.post(
            '/api/auth/cerrar-sesion/',
            format='json'
        )

        # 3. Validación: El sistema debe finalizar la sesión (usualmente 204 No Content)
        self.assertEqual(
            respuesta_salida.status_code,
            status.HTTP_204_NO_CONTENT
        )
        
        # 4. Validación: El sistema invalida el acceso sobrescribiendo la cookie con un valor vacío
        self.assertEqual(
            respuesta_salida.cookies['access'].value, 
            ''
        )

        # 5. Validación: Se impide el acceso a funcionalidades protegidas exigiendo nuevo inicio de sesión
        respuesta_perfil = self.client.get('/api/auth/mi-perfil/')
        self.assertEqual(
            respuesta_perfil.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP (Cerrar sesión):", respuesta_salida.status_code)
        print("Valor cookie 'access' eliminada:", repr(respuesta_salida.cookies['access'].value))
        print("Estado HTTP (Intento acceso posterior):", respuesta_perfil.status_code)

#E8
    def test_acceso_recurso_despues_de_cerrar_sesion(self):
        """
        Escenario: Intento de acceso después de cerrar sesión, intentando acceder 
        a un recurso restringido sin autenticarse nuevamente.
        El sistema debe denegar el acceso, no debe mostrar información protegida 
        y debe solicitar un nuevo inicio de sesión.
        """
        
        # 1. Precondiciones: Registrar, iniciar sesión y luego cerrar sesión
        datos_usuario = {
            'nombres': 'Sofia',
            'apellidos': 'Gomez',
            'email': 'sofia.gomez@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3009998877',
        }
        
        self.client.post('/api/auth/registro/', datos_usuario, format='json')

        self.client.post(
            '/api/auth/iniciar-sesion/',
            {'email': datos_usuario['email'], 'password': datos_usuario['password']},
            format='json'
        )

        # Se ejecuta el cierre de sesión para dejar al usuario sin credenciales válidas
        self.client.post('/api/auth/cerrar-sesion/', format='json')

        # 2. Datos de prueba / Acción: Intentar acceder a un recurso restringido
        endpoint_restringido = '/api/usuarios/direcciones/'
        respuesta_denegada = self.client.get(endpoint_restringido)

        # 3. Validación: El sistema deniega el acceso (401 Unauthorized)
        self.assertEqual(
            respuesta_denegada.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        
        # 4. Validación: El sistema no muestra datos y envía el mensaje de autenticación requerida
        self.assertIn('detail', respuesta_denegada.data)

        print("\n--- Resultado de la prueba ---")
        print(f"Estado HTTP (Acceso posterior a cierre - {endpoint_restringido}):", respuesta_denegada.status_code)
        print("Mensaje del sistema:", respuesta_denegada.data)

#HU-03
#E1
    def test_solicitud_recuperacion_password_satisfactoria(self):
        """
        Escenario: Solicitud satisfactoria de recuperación, ingresando el 
        correo electrónico y solicitando recuperar su contraseña.
        El sistema debe iniciar el proceso, generar un código OTP o enlace 
        y enviarlo al correo electrónico registrado.
        """
        from django.core import mail  # Importación local para verificar la bandeja de salida

        # 1. Precondiciones: Registrar al usuario (Cliente o Proveedor)
        datos_usuario = {
            'nombres': 'Lucia',
            'apellidos': 'Mendez',
            'email': 'lucia.mendez@example.com',
            'password': 'PasswordValida2026!',
            'password_confirmacion': 'PasswordValida2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3001239988',
        }
        self.client.post('/api/auth/registro/', datos_usuario, format='json')

        # Limpiar la bandeja de salida de correos de prueba por precaución
        mail.outbox = []

        # 2. Datos de prueba / Acción: Enviar la solicitud de recuperación
        
        respuesta = self.client.post(
            '/recuperar-password/', 
            {'email': datos_usuario['email']}
        )

        # 3. Validación: La vista nativa de Django redirige (302) a la ruta de "enviado"
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_302_FOUND
        )

        # 4. Validación: El sistema generó y envió un correo electrónico
        self.assertEqual(len(mail.outbox), 1)
        
        # 5. Validación: El correo fue enviado al destinatario correcto
        correo_enviado = mail.outbox[0]
        self.assertEqual(correo_enviado.to, [datos_usuario['email']])
        
        # 6. Validación: El cuerpo del correo contiene la ruta base de restablecimiento 
        self.assertIn('restablecer', correo_enviado.body)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Redirige a:", respuesta.url)
        print("Correos enviados:", len(mail.outbox))
        if mail.outbox:
            print("Destinatario del correo:", correo_enviado.to)
            print("Asunto del correo:", correo_enviado.subject)
#E2
    def test_solicitud_recuperacion_correo_no_registrado(self):
        """
        Escenario: Solicitud mediante un correo no asociado a una cuenta, 
        proporcionando un correo electrónico y solicitando recuperar su contraseña.
        El sistema no debe iniciar un restablecimiento válido y debe presentar una 
        respuesta que no revele información sensible sobre las cuentas registradas.
        """
        from django.core import mail

        # 1. Precondiciones: Bandeja de salida limpia. No registramos ningún usuario.
        mail.outbox = []

        # 2. Datos de prueba / Acción: Enviar la solicitud con un correo inexistente
        correo_no_registrado = 'usuario_fantasma@example.com'
        
        respuesta = self.client.post(
            '/recuperar-password/', 
            {'email': correo_no_registrado}
        )

        # 3. Validación de Seguridad: Para evitar la enumeración de usuarios 
        # (revelar quién está registrado y quién no), la vista nativa de Django 
        # responde exactamente igual que si el correo existiera (redirige con 302).
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_302_FOUND
        )

        # 4. Validación Crucial: A pesar de simular éxito en la interfaz, 
        # internamente NO se debe haber generado ni enviado ningún correo.
        self.assertEqual(len(mail.outbox), 0)

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP (Simula éxito por seguridad):", respuesta.status_code)
        print("Redirige a:", respuesta.url)
        print("Correos enviados (debe ser 0):", len(mail.outbox))

#E3
    def test_validacion_satisfactoria_enlace_recuperacion(self):
        """
        Escenario: Validación satisfactoria del mecanismo de recuperación, 
        proporcionando el código correcto o utilizando el enlace válido.
        El sistema debe validar el mecanismo y debe permitir establecer una nueva contraseña.
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        # 1. Precondiciones: Registrar al usuario a través de la API
        datos_usuario = {
            'nombres': 'Carlos',
            'apellidos': 'Recupera',
            'email': 'carlos.recupera@example.com',
            'password': 'PasswordVieja2026!',
            'password_confirmacion': 'PasswordVieja2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3109990000',
        }
        self.client.post('/api/auth/registro/', datos_usuario, format='json')

        # Obtenemos la instancia del usuario recién creado en la base de datos
        # (Necesario para generar el token nativo de Django)
        Usuario = get_user_model()
        usuario = Usuario.objects.get(email=datos_usuario['email'])

        # 2. Datos de prueba: Generar el uidb64 y un token VÁLIDO (simulando el link del correo)
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)

        # 3. Acción: El usuario "hace clic" en el enlace (petición GET al endpoint configurado)
        ruta_enlace = f'/restablecer/{uidb64}/{token}/'
        respuesta = self.client.get(ruta_enlace)

        # 4. Validación: El sistema acepta el token y muestra el formulario (HTTP 200 OK)
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )

        # 5. Validación: Verificamos que la vista confirme que el enlace es válido.
        # (La vista nativa PasswordResetConfirmView de Django inyecta la variable 
        # 'validlink' en el contexto cuando el token pasa las pruebas de seguridad).
        self.assertTrue(respuesta.context['validlink'])

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP (Acceso al enlace):", respuesta.status_code)
        print("Ruta probada:", ruta_enlace)
        print("¿Enlace considerado válido por el sistema?:", respuesta.context['validlink'])

#E4
    def test_validacion_fallida_enlace_recuperacion(self):
        """
        Escenario: Uso de un mecanismo de recuperación inválido, proporcionando 
        un código OTP incorrecto o utilizando un enlace no válido.
        El sistema debe rechazar el mecanismo y no debe permitir establecer una nueva contraseña.
        """
        from django.contrib.auth import get_user_model
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        # 1. Precondiciones: Registrar al usuario
        datos_usuario = {
            'nombres': 'Daniel',
            'apellidos': 'Prueba',
            'email': 'daniel.invalido@example.com',
            'password': 'PasswordVieja2026!',
            'password_confirmacion': 'PasswordVieja2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3200001111',
        }
        self.client.post('/api/auth/registro/', datos_usuario, format='json')

        Usuario = get_user_model()
        usuario = Usuario.objects.get(email=datos_usuario['email'])

        # 2. Datos de prueba: Generar el uidb64 correcto del usuario pero un token INVÁLIDO
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        token_invalido = 'token-falso-e-invalido-123'

        # 3. Acción: Intentar acceder con el enlace manipulado/incorrecto
        ruta_enlace_invalido = f'/restablecer/{uidb64}/{token_invalido}/'
        respuesta = self.client.get(ruta_enlace_invalido)

        # 4. Validación: El sistema responde cargando la página HTML (200 OK)
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK,
            msg=f"Se esperaba 200, pero devolvió {respuesta.status_code}."
        )

        # 5. Validación Crucial: La vista nativa de Django detecta que el token 
        # no es válido y envía la variable 'validlink' como False al contexto. 
        # Esto hace que la plantilla HTML no muestre el formulario para cambiar 
        # la contraseña, sino un mensaje de error ("El enlace es inválido...").
        self.assertFalse(respuesta.context['validlink'])

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Ruta probada:", ruta_enlace_invalido)
        print("¿Enlace considerado válido por el sistema?:", respuesta.context['validlink'])

#E5
    def test_validacion_fallida_enlace_recuperacion_vencido(self):
        """
        Escenario: Uso de un mecanismo de recuperación vencido, intentando utilizar 
        el código OTP o enlace temporal.
        El sistema debe rechazar el restablecimiento y debe informar que el 
        mecanismo ya no es válido (enlace expirado).
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.test import override_settings # Importante para manipular el tiempo de vida del token

        # 1. Precondiciones: Registrar al usuario
        datos_usuario = {
            'nombres': 'Andrea',
            'apellidos': 'Tiempo',
            'email': 'andrea.tiempo@example.com',
            'password': 'PasswordVieja2026!',
            'password_confirmacion': 'PasswordVieja2026!',
            'rol': PerfilUsuario.Rol.CLIENTE,
            'telefono': '3300002222',
        }
        self.client.post('/api/auth/registro/', datos_usuario, format='json')

        Usuario = get_user_model()
        usuario = Usuario.objects.get(email=datos_usuario['email'])

        # 2. Datos de prueba: Generar el uidb64 y un token VÁLIDO generado AHORA mismo
        uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        ruta_enlace = f'/restablecer/{uidb64}/{token}/'

        # 3. Acción: Simulamos que el tiempo pasó. En lugar de detener el test por días, 
        # usamos 'override_settings' para decirle a Django que el tiempo de expiración 
        # (PASSWORD_RESET_TIMEOUT) sea -1 segundo. Esto hará que cualquier token 
        # nazca inmediatamente vencido.
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            respuesta = self.client.get(ruta_enlace)

        # 4. Validación: El sistema responde cargando la página HTML (200 OK)
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK,
            msg=f"Se esperaba 200, pero devolvió {respuesta.status_code}."
        )

        # 5. Validación Crucial: La vista de Django analiza la marca de tiempo 
        # incrustada en el token, se da cuenta de que superó la vigencia y  
        # envía 'validlink' como False para que el HTML muestre el error de vencimiento.
        self.assertFalse(respuesta.context['validlink'])

        print("\n--- Resultado de la prueba ---")
        print("Estado HTTP:", respuesta.status_code)
        print("Ruta probada:", ruta_enlace)
        print("¿Enlace vencido rechazado con éxito? (validlink = False):", not respuesta.context['validlink'])

#E6
#E7

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
