from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from usuarios.models import Direccion, PerfilProveedor, PerfilUsuario, ZonaAtencion

Usuario = get_user_model()


#HU-05
#E1
class ConsultaPerfilProfesionalTests(APITestCase):

    def setUp(self):
        """
        Crea un usuario PROVEEDOR autenticado, con su información 
        profesional y zonas de atención pre-cargadas en la base de datos.
        """
        self.url_perfil_profesional = "/api/proveedores/mi-perfil/"

        # 1. Creación del Usuario y Perfil base
        self.usuario_proveedor = Usuario.objects.create_user(
            username="proveedor@test.com",
            email="proveedor@test.com",
            password="ClaveSegura123!",
            first_name="Javier",
            last_name="Ramírez",
        )

        self.perfil_base = PerfilUsuario.objects.create(
            usuario=self.usuario_proveedor,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3150001122",
        )

        # 2. Creación de la Información Profesional
        self.perfil_proveedor = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base,
            descripcion_profesional="Fisioterapia a domicilio",
        )

        # 3. Creación de las Zonas de Atención (ajustado a barrio_sector y perfil_proveedor)
        ZonaAtencion.objects.create(
            perfil_proveedor=self.perfil_proveedor,
            ciudad="Cali",
            barrio_sector="Norte",
        )
        ZonaAtencion.objects.create(
            perfil_proveedor=self.perfil_proveedor,
            ciudad="Cali",
            barrio_sector="Sur",
        )

        # Autenticación del proveedor
        self.client.force_authenticate(user=self.usuario_proveedor)

    def test_consulta_perfil_profesional_satisfactoria(self):
        """
        Un GET al endpoint del perfil profesional debe devolver la data
        del proveedor, incluyendo un arreglo anidado con sus zonas de atención.
        """
        response = self.client.get(self.url_perfil_profesional)
        data_response = response.json()

        # 1. Validación de estado HTTP
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg="El endpoint debe retornar 200 OK al consultar el perfil profesional propio.",
        )

        # 2. Validación de la información profesional básica
        self.assertEqual(
            data_response.get("descripcion_profesional"),
            "Fisioterapia a domicilio",
            msg="El JSON debe contener la descripcion_profesional correcta.",
        )

        # 3. Validación de las zonas de atención anidadas
        zonas = data_response.get("zonas_atencion", [])
        
        self.assertIsInstance(
            zonas,
            list,
            msg="Las zonas de atención deben devolverse como una lista (array).",
        )
        self.assertEqual(
            len(zonas), 2,
            
            msg="El sistema debe devolver exactamente las 2 zonas registradas.",
        )
        
        # Verificamos el contenido de al menos una zona para asegurar correcta serialización
        ciudades_zonas = [z.get("ciudad") for z in zonas if isinstance(z, dict)]
        barrios_zonas = [z.get("barrio_sector") for z in zonas if isinstance(z, dict)]
        
        self.assertIn(
            "Cali",
            ciudades_zonas,
            msg="La ciudad 'Cali' debe estar presente en los objetos de zonas_atencion.",
        )
        self.assertIn(
            "Norte",
            barrios_zonas,
            msg="El barrio_sector 'Norte' debe estar presente en los objetos de zonas_atencion.",
        )

        print(
            "\n[test_consulta_perfil_profesional_satisfactoria]",
            "\nStatus HTTP GET:", response.status_code,
            "\nDescripción profesional devuelta:", data_response.get("descripcion_profesional"),
            "\nZonas de atención encontradas:", len(zonas),
            "\nEstructura de las zonas devueltas:", zonas,
        )
#E2
class ActualizacionPerfilProfesionalTests(APITestCase):

    def setUp(self):
        """
        Crea un usuario PROVEEDOR autenticado, listo para recibir un PATCH
        sobre su perfil profesional.
        """
        self.url_perfil_profesional = "/api/proveedores/mi-perfil/"

        self.usuario_proveedor = Usuario.objects.create_user(
            username="proveedor_act@test.com",
            email="proveedor_act@test.com",
            password="ClaveSegura123!",
            first_name="Laura",
            last_name="Gómez",
        )

        self.perfil_base = PerfilUsuario.objects.create(
            usuario=self.usuario_proveedor,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3201234567",
        )

        self.perfil_proveedor = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base,
            descripcion_profesional="Servicios generales de enfermería.",
        )

        self.client.force_authenticate(user=self.usuario_proveedor)

        self.datos_actualizados = {
            "descripcion_profesional": "Enfermera especialista en cuidados intensivos a domicilio.",
        }

    def test_actualizacion_perfil_profesional_satisfactoria(self):
        """
        Un PATCH con datos válidos sobre la descripción profesional debe 
        guardarse correctamente, y un GET posterior debe reflejar los cambios.
        """
        # 1. Ejecutar la actualización (PATCH)
        response_patch = self.client.patch(
            self.url_perfil_profesional,
            data=self.datos_actualizados,
            format="json",
        )

        data_patch = response_patch.json()

        self.assertEqual(
            response_patch.status_code,
            status.HTTP_200_OK,
            msg="El endpoint debe retornar 200 OK al actualizar correctamente.",
        )
        self.assertEqual(
            data_patch.get("descripcion_profesional"),
            "Enfermera especialista en cuidados intensivos a domicilio.",
        )

        # 2. Verificar la persistencia con una consulta posterior (GET)
        response_get = self.client.get(self.url_perfil_profesional)
        data_get = response_get.json()

        self.assertEqual(
            response_get.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            data_get.get("descripcion_profesional"),
            "Enfermera especialista en cuidados intensivos a domicilio.",
            msg="El GET posterior debe devolver la descripción actualizada.",
        )

        # 3. Verificar directamente en la base de datos
        self.perfil_proveedor.refresh_from_db()

        self.assertEqual(
            self.perfil_proveedor.descripcion_profesional,
            "Enfermera especialista en cuidados intensivos a domicilio.",
            msg="La descripción profesional debe haberse guardado en la base de datos.",
        )

        print(
            "\n[test_actualizacion_perfil_profesional_satisfactoria]",
            "\nStatus PATCH:", response_patch.status_code,
            "\nDescripción devuelta en PATCH:", data_patch.get("descripcion_profesional"),
            "\nStatus GET posterior:", response_get.status_code,
            "\nDescripción devuelta en GET:", data_get.get("descripcion_profesional"),
            "\nDescripción en BD:", self.perfil_proveedor.descripcion_profesional,
        )
#E3
class RegistroZonasAtencionTests(APITestCase):

    def setUp(self):
        """
        Crea un usuario PROVEEDOR autenticado y su perfil base y profesional,
        listo para registrar nuevas zonas de atención.
        """
        # Ajusta esta URL a la ruta real de tu API para gestionar zonas
        self.url_zonas = "/api/proveedores/mis-zonas/"

        # 1. Creación del Usuario y Perfiles
        self.usuario_proveedor = Usuario.objects.create_user(
            username="proveedor_zonas@test.com",
            email="proveedor_zonas@test.com",
            password="ClaveSegura123!",
            first_name="Diana",
            last_name="Ríos",
        )

        self.perfil_base = PerfilUsuario.objects.create(
            usuario=self.usuario_proveedor,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3009998877",
        )

        self.perfil_proveedor = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base,
            descripcion_profesional="Terapia ocupacional infantil.",
        )

        # 2. Autenticación
        self.client.force_authenticate(user=self.usuario_proveedor)

        # 3. Datos de prueba: Zonas a registrar
        self.zona_1 = {
            "ciudad": "Cali",
            "barrio_sector": "Ciudad Jardín"
        }
        self.zona_2 = {
            "ciudad": "Palmira",
            "barrio_sector": "Centro"
        }

    def test_registro_zonas_atencion_satisfactorio(self):
        """
        Un POST al endpoint de zonas con datos válidos debe registrar 
        la nueva zona asociándola automáticamente al perfil del proveedor autenticado.
        """
        # --- 1. Registrar la primera zona ---
        response_zona_1 = self.client.post(
            self.url_zonas,
            data=self.zona_1,
            format="json",
        )

        self.assertEqual(
            response_zona_1.status_code,
            status.HTTP_201_CREATED,
            msg="El endpoint debe retornar 201 Created al registrar la primera zona.",
        )

        # --- 2. Registrar la segunda zona (demostrando "una o más") ---
        response_zona_2 = self.client.post(
            self.url_zonas,
            data=self.zona_2,
            format="json",
        )

        self.assertEqual(
            response_zona_2.status_code,
            status.HTTP_201_CREATED,
            msg="El endpoint debe retornar 201 Created al registrar una zona adicional.",
        )

        # --- 3. Verificación de persistencia y asociación en BD ---
        # Consultamos las zonas directamente asociadas a este perfil
        zonas_en_bd = ZonaAtencion.objects.filter(perfil_proveedor=self.perfil_proveedor)
        
        self.assertEqual(
            zonas_en_bd.count(),
            2,
            msg="El sistema debe conservar las 2 zonas registradas asociadas al perfil profesional.",
        )

        # Verificamos que los datos guarden coherencia
        ciudades_registradas = list(zonas_en_bd.values_list("ciudad", flat=True))
        barrios_registrados = list(zonas_en_bd.values_list("barrio_sector", flat=True))

        self.assertIn("Cali", ciudades_registradas)
        self.assertIn("Palmira", ciudades_registradas)
        self.assertIn("Ciudad Jardín", barrios_registrados)
        self.assertIn("Centro", barrios_registrados)

        print(
            "\n[test_registro_zonas_atencion_satisfactorio]",
            "\nStatus HTTP Zona 1:", response_zona_1.status_code,
            "\nStatus HTTP Zona 2:", response_zona_2.status_code,
            "\nDatos devueltos Zona 1:", response_zona_1.json(),
            "\nTotal zonas en BD para el proveedor:", zonas_en_bd.count(),
            "\nCiudades guardadas:", ciudades_registradas,
            "\nBarrios/Sectores guardados:", barrios_registrados,
        )

#E4
class ZonasAtencionInformativasTests(APITestCase):

    def setUp(self):
        """
        Crea un usuario PROVEEDOR autenticado con zonas de atención base.
        """
        # Endpoint donde se consultan los datos del perfil y sus zonas
        self.url_perfil_profesional = "/api/proveedores/mi-perfil/"

        self.usuario_proveedor = Usuario.objects.create_user(
            username="proveedor_info@test.com",
            email="proveedor_info@test.com",
            password="ClaveSegura123!",
            first_name="Héctor",
            last_name="Vargas",
        )

        self.perfil_base = PerfilUsuario.objects.create(
            usuario=self.usuario_proveedor,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3001112233",
        )

        self.perfil_proveedor = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base,
            descripcion_profesional="Servicios de plomería general.",
        )

        # Registramos un par de zonas informativas
        ZonaAtencion.objects.create(
            perfil_proveedor=self.perfil_proveedor,
            ciudad="Cali",
            barrio_sector="San Fernando",
        )
        ZonaAtencion.objects.create(
            perfil_proveedor=self.perfil_proveedor,
            ciudad="Palmira",
            barrio_sector="Centro",
        )

        self.client.force_authenticate(user=self.usuario_proveedor)

    def test_consulta_zonas_puramente_informativas(self):
        """
        Al consultar las zonas, el payload JSON debe contener únicamente
        los datos de texto registrados, sin campos de cálculo geográfico.
        """
        response = self.client.get(self.url_perfil_profesional)
        data_response = response.json()
        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        zonas = data_response.get("zonas_atencion", [])

        self.assertGreater(
            len(zonas),
            0,
            msg="El perfil debe tener zonas de atención registradas para la prueba.",
        )

        # Iteramos sobre cada zona devuelta para verificar el contrato de la API
        for zona in zonas:
            # 1. Verificamos que SÍ contenga la información orientativa esperada
            self.assertIn(
                "ciudad",
                zona,
                msg="La zona debe incluir la ciudad como información orientativa.",
            )
            self.assertIn(
                "barrio_sector",
                zona,
                msg="La zona debe incluir el barrio/sector como información orientativa.",
            )

            # 2. Verificamos que NO contenga lógica de geolocalización o distancias
            claves_prohibidas = [
                "distancia", 
                "distancia_km", 
                "cobertura", 
                "en_rango", 
                "latitud", 
                "longitud",
                "lat",
                "lng"
            ]
            
            for clave in claves_prohibidas:
                self.assertNotIn(
                    clave,
                    zona,
                    msg=f"El sistema NO debe calcular ni devolver el campo '{clave}' "
                        f"ya que las zonas son estrictamente orientativas.",
                )

        print(
            "\n[test_consulta_zonas_puramente_informativas]",
            "\nStatus HTTP GET:", response.status_code,
            "\nZonas devueltas:", len(zonas),
            "\nMuestra de una zona (verificando estructura limpia):", zonas[0] if zonas else None,
            "\nValidación superada: No se detectaron campos de distancia ni validación geográfica.",
        )

#E5
class PrivacidadPerfilProveedorAjenoTests(APITestCase):

    def setUp(self):
        """
        Crea dos usuarios PROVEEDOR. Autentica al primero e intenta
        modificar los datos del segundo.
        """
        # 1. Creación del proveedor activo (el atacante/intruso)
        self.usuario_activo = Usuario.objects.create_user(
            username="proveedor_activo@test.com",
            email="proveedor_activo@test.com",
            password="ClaveSegura123!",
            first_name="Miguel",
            last_name="Torres",
        )
        self.perfil_base_activo = PerfilUsuario.objects.create(
            usuario=self.usuario_activo,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3100000001",
        )
        self.perfil_proveedor_activo = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base_activo,
            descripcion_profesional="Electricista residencial.",
        )

        # 2. Creación del proveedor ajeno (la víctima)
        self.usuario_ajeno = Usuario.objects.create_user(
            username="proveedor_ajeno@test.com",
            email="proveedor_ajeno@test.com",
            password="ClaveSegura123!",
            first_name="Carlos",
            last_name="Ruiz",
        )
        self.perfil_base_ajeno = PerfilUsuario.objects.create(
            usuario=self.usuario_ajeno,
            rol=PerfilUsuario.Rol.PROVEEDOR,
            telefono="3100000002",
        )
        self.perfil_proveedor_ajeno = PerfilProveedor.objects.create(
            perfil_usuario=self.perfil_base_ajeno,
            descripcion_profesional="Carpintero especialista.",
        )

        # Autenticamos al proveedor activo
        self.client.force_authenticate(user=self.usuario_activo)

        # URL dinámica apuntando al recurso del perfil profesional ajeno
        # Ajusta la ruta a la estructura de tu ViewSet (ej. /api/proveedores/perfiles/<id>/)
        self.url_ajena = f"/api/proveedores/perfiles/{self.perfil_proveedor_ajeno.id}/"

        self.datos_maliciosos = {
            "descripcion_profesional": "Descripción alterada por un intruso."
        }

    def test_modificacion_perfil_profesional_ajeno_denegada(self):
        """
        Un proveedor autenticado no debe poder hacer PATCH 
        en el perfil profesional de otro proveedor.
        """
        response_patch = self.client.patch(
            self.url_ajena,
            data=self.datos_maliciosos,
            format="json",
        )

        # 1. Validamos que el sistema rechace la operación (403 o 404). NO debe ser 200 OK.
        self.assertNotEqual(
            response_patch.status_code,
            status.HTTP_200_OK,
            msg="El sistema no debe permitir modificar el perfil profesional ajeno (esperado 403 o 404).",
        )

        # 2. Verificación de Inmutabilidad
        self.perfil_proveedor_ajeno.refresh_from_db()

        self.assertEqual(
            self.perfil_proveedor_ajeno.descripcion_profesional,
            "Carpintero especialista.",
            msg="La descripción profesional del perfil ajeno debió conservarse intacta.",
        )

        print(
            "\n[test_modificacion_perfil_profesional_ajeno_denegada]",
            "\nStatus HTTP PATCH (Intento de Modificación):", response_patch.status_code,
            "\nDescripción real conservada BD:", self.perfil_proveedor_ajeno.descripcion_profesional,
        )