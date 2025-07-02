"""
Configuración de URLs para la aplicación de gestión de canchas de pádel.
Define todas las rutas de la aplicación organizadas por funcionalidad.
"""
from django.urls import path
from . import views
urlpatterns = [
    # ============================================================================
    # PÁGINAS PRINCIPALES Y AUTENTICACIÓN
    # ============================================================================
    
    # Página principal
    path('', views.home, name='home'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/jugador/', views.dashboard_jugador, name='dashboard_jugador'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # ============================================================================
    # GESTIÓN DE RESERVAS - JUGADORES
    # ============================================================================
    
    # Crear reservas
    path('reservas/crear/', views.crear_reserva, name='crear_reserva'),
    path('reservas/rapida/', views.reserva_rapida, name='reserva_rapida'),
    
    # Ver reservas
    path('reservas/mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('reservas/calendario/', views.calendario_reservas, name='calendario_reservas'),
    
    # Gestionar reservas
    path('reservas/cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    
    # Búsqueda de canchas
    path('canchas/buscar/', views.buscar_canchas, name='buscar_canchas'),
    
    # ============================================================================
    # ADMINISTRACIÓN - SOLO ADMINISTRADORES
    # ============================================================================
    
    # Gestión de canchas
    path('gestion-admin/canchas/', views.admin_canchas, name='admin_canchas'),
    path('gestion-admin/canchas/crear/', views.crear_cancha, name='crear_cancha'),
    path('gestion-admin/canchas/editar/<int:cancha_id>/', views.editar_cancha, name='editar_cancha'),
    path('gestion-admin/canchas/eliminar/<int:cancha_id>/', views.eliminar_cancha, name='eliminar_cancha'),

    # Gestión de reservas (administrador)
    path('gestion-admin/reservas/', views.admin_reservas, name='admin_reservas'),
    
    # Gestión de usuarios
    path('gestion-admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    
    # Reportes y estadísticas
    path('gestion-admin/reportes/', views.reportes_admin, name='reportes_admin'),

    # ============================================================================
    # PERFIL DE USUARIO
    # ============================================================================
    
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    
    # ============================================================================
    # APIs AJAX
    # ============================================================================
    
    # API para obtener horarios disponibles
    path('api/horarios-disponibles/', views.get_horarios_disponibles, name='api_horarios_disponibles'),
]