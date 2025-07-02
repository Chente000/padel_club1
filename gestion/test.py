"""
Tests para la aplicación de gestión de canchas de pádel.
Define tests unitarios y de integración para todos los componentes.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from .models import Usuario, Cancha, Reserva
User = get_user_model()
class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario."""
    
    def setUp(self):
        self.jugador = Usuario.objects.create_user(
            username='testjugador',
            email='jugador@test.com',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez',
            rol='jugador'
        )
        
        self.admin = Usuario.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='Sistema',
            rol='administrador'
        )
    
    def test_str_representation(self):
        """Test de representación string del usuario."""
        self.assertEqual(str(self.jugador), "Juan Pérez (jugador)")
    
    def test_es_administrador(self):
        """Test de verificación de rol administrador."""
        self.assertTrue(self.admin.es_administrador())
        self.assertFalse(self.jugador.es_administrador())
    
    def test_es_jugador(self):
        """Test de verificación de rol jugador."""
        self.assertTrue(self.jugador.es_jugador())
        self.assertFalse(self.admin.es_jugador())
class CanchaModelTest(TestCase):
    """Tests para el modelo Cancha."""
    
    def setUp(self):
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test 1',
            tipo_pista='cristal',
            tarifa_hora=50.00,
            descripcion='Cancha de prueba',
            capacidad_jugadores=4
        )
    
    def test_str_representation(self):
        """Test de representación string de la cancha."""
        self.assertEqual(str(self.cancha), "Cancha Test 1 - Cristal")
    
    def test_esta_disponible(self):
        """Test de verificación de disponibilidad."""
        fecha_test = date.today() + timedelta(days=1)
        hora_test = time(10, 0)
        
        # Sin reservas, debe estar disponible
        self.assertTrue(self.cancha.esta_disponible(fecha_test, hora_test))
    
    def test_get_horarios_disponibles(self):
        """Test de obtención de horarios disponibles."""
        fecha_test = date.today() + timedelta(days=1)
        horarios = self.cancha.get_horarios_disponibles(fecha_test)
        
        # Debe tener horarios de 8 AM a 10 PM (14 horarios)
        self.assertEqual(len(horarios), 14)
        self.assertEqual(horarios[0], time(8, 0))
        self.assertEqual(horarios[-1], time(21, 0))
class ReservaModelTest(TestCase):
    """Tests para el modelo Reserva."""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            rol='jugador'
        )
        
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test',
            tipo_pista='cristal',
            tarifa_hora=50.00
        )
        
        self.reserva = Reserva.objects.create(
            cancha=self.cancha,
            jugador=self.usuario,
            fecha_reserva=date.today() + timedelta(days=1),
            hora_inicio=time(10, 0)
        )
    
    def test_str_representation(self):
        """Test de representación string de la reserva."""
        expected = f"{self.cancha.nombre} - {self.reserva.fecha_reserva} {self.reserva.hora_inicio} - {self.usuario.get_full_name() or self.usuario.username}"
        self.assertEqual(str(self.reserva), expected)
    
    def test_save_calculates_precio_total(self):
        """Test que el precio total se calcula automáticamente."""
        self.assertEqual(self.reserva.precio_total, self.cancha.tarifa_hora)
    
    def test_save_calculates_hora_fin(self):
        """Test que la hora de fin se calcula automáticamente."""
        self.assertEqual(self.reserva.hora_fin, time(11, 0))
    
    def test_puede_cancelar(self):
        """Test de verificación si una reserva puede cancelarse."""
        # Reserva futura confirmada debe poder cancelarse
        self.assertTrue(self.reserva.puede_cancelar())
        
        # Reserva cancelada no debe poder cancelarse
        self.reserva.estado = 'cancelada'
        self.assertFalse(self.reserva.puede_cancelar())
    
    def test_cancelar(self):
        """Test de cancelación de reserva."""
        self.assertTrue(self.reserva.cancelar())
        self.assertEqual(self.reserva.estado, 'cancelada')
class ViewsTest(TestCase):
    """Tests para las vistas."""
    
    def setUp(self):
        self.client = Client()
        self.jugador = Usuario.objects.create_user(
            username='jugador',
            email='jugador@test.com',
            password='testpass123',
            rol='jugador'
        )
        
        self.admin = Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            rol='administrador'
        )
        
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test',
            tipo_pista='cristal',
            tarifa_hora=50.00
        )
    
    def test_home_view(self):
        """Test de la vista home."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Padel Paraguaná')
    
    def test_login_view(self):
        """Test de la vista de login."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Test de login exitoso
        response = self.client.post(reverse('login'), {
            'username': 'jugador',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_dashboard_jugador_requires_login(self):
        """Test que el dashboard requiere login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_jugador_logged_in(self):
        """Test del dashboard con usuario logueado."""
        self.client.login(username='jugador', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mi Dashboard')
    
    def test_admin_views_require_admin_role(self):
        """Test que las vistas admin requieren rol administrador."""
        # Login como jugador
        self.client.login(username='jugador', password='testpass123')
        
        # Intentar acceder a vista admin
        response = self.client.get(reverse('admin_canchas'))
        self.assertEqual(response.status_code, 302)  # Redirect or forbidden
    
    def test_admin_views_with_admin_user(self):
        """Test de vistas admin con usuario administrador."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('admin_canchas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestionar Canchas')
    
    def test_crear_reserva_view(self):
        """Test de la vista crear reserva."""
        self.client.login(username='jugador', password='testpass123')
        
        response = self.client.get(reverse('crear_reserva'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nueva Reserva')
        
        # Test de creación de reserva
        fecha_futura = date.today() + timedelta(days=1)
        response = self.client.post(reverse('crear_reserva'), {
            'cancha': self.cancha.id,
            'fecha_reserva': fecha_futura,
            'hora_inicio': '10:00',
            'notas': 'Reserva de test'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que se creó la reserva
        self.assertTrue(Reserva.objects.filter(
            cancha=self.cancha,
            jugador=self.jugador,
            fecha_reserva=fecha_futura
        ).exists())
class FormsTest(TestCase):
    """Tests para los formularios."""
    
    def setUp(self):
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test',
            tipo_pista='cristal',
            tarifa_hora=50.00
        )
    
    def test_registro_jugador_form_valid(self):
        """Test de formulario de registro válido."""
        from .forms import RegistroJugadorForm
        
        form_data = {
            'username': 'nuevojugador',
            'first_name': 'Nuevo',
            'last_name': 'Jugador',
            'email': 'nuevo@test.com',
            'password1': 'testpass123456',
            'password2': 'testpass123456',
            'telefono': '0424-1234567',
            'nivel_habilidad': 'intermedio'
        }
        
        form = RegistroJugadorForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registro_jugador_form_invalid_email(self):
        """Test de formulario con email duplicado."""
        from .forms import RegistroJugadorForm
        
        # Crear usuario existente
        Usuario.objects.create_user(
            username='existente',
            email='existente@test.com',
            password='testpass123'
        )
        
        form_data = {
            'username': 'nuevojugador',
            'first_name': 'Nuevo',
            'last_name': 'Jugador',
            'email': 'existente@test.com',  # Email duplicado
            'password1': 'testpass123456',
            'password2': 'testpass123456'
        }
        
        form = RegistroJugadorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_reserva_form_valid(self):
        """Test de formulario de reserva válido."""
        from .forms import ReservaForm
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='jugador'
        )
        
        fecha_futura = date.today() + timedelta(days=1)
        form_data = {
            'cancha': self.cancha.id,
            'fecha_reserva': fecha_futura,
            'hora_inicio': '10:00',
            'notas': 'Reserva de test'
        }
        
        form = ReservaForm(data=form_data, usuario=usuario)
        self.assertTrue(form.is_valid())
    
    def test_reserva_form_fecha_pasada(self):
        """Test de formulario con fecha en el pasado."""
        from .forms import ReservaForm
        
        usuario = Usuario.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='jugador'
        )
        
        fecha_pasada = date.today() - timedelta(days=1)
        form_data = {
            'cancha': self.cancha.id,
            'fecha_reserva': fecha_pasada,
            'hora_inicio': '10:00'
        }
        
        form = ReservaForm(data=form_data, usuario=usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_reserva', form.errors)
class IntegrationTest(TestCase):
    """Tests de integración."""
    
    def setUp(self):
        self.client = Client()
        self.jugador = Usuario.objects.create_user(
            username='jugador',
            email='jugador@test.com',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez',
            rol='jugador'
        )
        
        self.cancha = Cancha.objects.create(
            nombre='Cancha Test',
            tipo_pista='cristal',
            tarifa_hora=50.00
        )
    
    def test_flujo_completo_reserva(self):
        """Test del flujo completo de reserva."""
        # 1. Login
        self.client.login(username='jugador', password='testpass123')
        
        # 2. Ir a crear reserva
        response = self.client.get(reverse('crear_reserva'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Crear reserva
        fecha_futura = date.today() + timedelta(days=1)
        response = self.client.post(reverse('crear_reserva'), {
            'cancha': self.cancha.id,
            'fecha_reserva': fecha_futura,
            'hora_inicio': '10:00',
            'notas': 'Test de integración'
        })
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar que la reserva existe
        reserva = Reserva.objects.get(
            cancha=self.cancha,
            jugador=self.jugador,
            fecha_reserva=fecha_futura
        )
        self.assertEqual(reserva.hora_inicio, time(10, 0))
        self.assertEqual(reserva.estado, 'confirmada')
        
        # 5. Ver mis reservas
        response = self.client.get(reverse('mis_reservas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancha Test')
        
        # 6. Cancelar reserva
        response = self.client.post(reverse('cancelar_reserva', args=[reserva.id]))
        self.assertEqual(response.status_code, 302)
        
        # 7. Verificar cancelación
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')
    
    def test_api_horarios_disponibles(self):
        """Test de la API de horarios disponibles."""
        self.client.login(username='jugador', password='testpass123')
        
        fecha_test = date.today() + timedelta(days=1)
        response = self.client.get(reverse('api_horarios_disponibles'), {
            'cancha_id': self.cancha.id,
            'fecha': fecha_test.strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['horarios']), 14)  # 8 AM - 10 PM