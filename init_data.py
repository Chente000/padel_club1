#!/usr/bin/env python
"""
Script de inicialización de datos para el sistema de gestión de canchas de pádel.
Este script crea datos de ejemplo para probar el sistema:
- Usuario administrador
- Canchas de ejemplo
- Algunos usuarios jugadores
- Reservas de ejemplo
Ejecutar con: python manage.py shell < init_data.py
"""
import os
import sys
import django
from datetime import date, time, timedelta
# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padel_club.settings')
django.setup()
from django.contrib.auth import get_user_model
from gestion.models import Usuario, Cancha, Reserva
User = get_user_model()
def crear_datos_iniciales():
    """Crea los datos iniciales del sistema."""
    
    print("🏓 Inicializando datos del sistema Padel Paraguaná...")
    
    # ============================================================================
    # CREAR USUARIO ADMINISTRADOR
    # ============================================================================
    
    print("\n👑 Creando usuario administrador...")
    
    if not Usuario.objects.filter(username='admin').exists():
        admin = Usuario.objects.create_user(
            username='admin',
            email='admin@padelparaguaná.com',
            password='admin123',  # Cambiar en producción
            first_name='Administrador',
            last_name='Sistema',
            rol='administrador',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Usuario administrador creado: {admin.username}")
    else:
        print("⚠️  Usuario administrador ya existe")
    
    # ============================================================================
    # CREAR CANCHAS DE EJEMPLO
    # ============================================================================
    
    print("\n🏟️  Creando canchas de ejemplo...")
    
    canchas_data = [
        {
            'nombre': 'Cancha Central',
            'tipo_pista': 'cristal',
            'tarifa_hora': 80.00,
            'descripcion': 'Cancha principal con vista panorámica y la mejor iluminación.',
            'capacidad_jugadores': 4
        },
        {
            'nombre': 'Cancha Norte',
            'tipo_pista': 'muro',
            'tarifa_hora': 60.00,
            'descripcion': 'Cancha con muros tradicionales, perfecta para principiantes.',
            'capacidad_jugadores': 4
        },
        {
            'nombre': 'Cancha Sur',
            'tipo_pista': 'cristal',
            'tarifa_hora': 75.00,
            'descripcion': 'Cancha de cristal con excelente ventilación natural.',
            'capacidad_jugadores': 4
        },
        {
            'nombre': 'Cancha VIP',
            'tipo_pista': 'mixta',
            'tarifa_hora': 100.00,
            'descripcion': 'Cancha premium con servicios exclusivos y área de descanso.',
            'capacidad_jugadores': 4
        },
        {
            'nombre': 'Cancha Entrenamiento',
            'tipo_pista': 'muro',
            'tarifa_hora': 45.00,
            'descripción': 'Cancha especial para entrenamientos y clases.',
            'capacidad_jugadores': 6
        }
    ]
    
    for cancha_info in canchas_data:
        if not Cancha.objects.filter(nombre=cancha_info['nombre']).exists():
            cancha = Cancha.objects.create(**cancha_info)
            print(f"✅ Cancha creada: {cancha.nombre} - Bs. {cancha.tarifa_hora}/hora")
        else:
            print(f"⚠️  Cancha ya existe: {cancha_info['nombre']}")
    
    # ============================================================================
    # CREAR USUARIOS JUGADORES DE EJEMPLO
    # ============================================================================
    
    print("\n🏓 Creando usuarios jugadores de ejemplo...")
    
    jugadores_data = [
        {
            'username': 'juan.perez',
            'email': 'juan.perez@email.com',
            'password': 'jugador123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'telefono': '0424-1234567',
            'nivel_habilidad': 'intermedio'
        },
        {
            'username': 'maria.garcia',
            'email': 'maria.garcia@email.com',
            'password': 'jugador123',
            'first_name': 'María',
            'last_name': 'García',
            'telefono': '0414-2345678',
            'nivel_habilidad': 'avanzado'
        },
        {
            'username': 'carlos.rodriguez',
            'email': 'carlos.rodriguez@email.com',
            'password': 'jugador123',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'telefono': '0426-3456789',
            'nivel_habilidad': 'principiante'
        },
        {
            'username': 'ana.martinez',
            'email': 'ana.martinez@email.com',
            'password': 'jugador123',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'telefono': '0412-4567890',
            'nivel_habilidad': 'intermedio'
        },
        {
            'username': 'luis.gonzalez',
            'email': 'luis.gonzalez@email.com',
            'password': 'jugador123',
            'first_name': 'Luis',
            'last_name': 'González',
            'telefono': '0424-5678901',
            'nivel_habilidad': 'profesional'
        }
    ]
    
    for jugador_info in jugadores_data:
        if not Usuario.objects.filter(username=jugador_info['username']).exists():
            jugador = Usuario.objects.create_user(
                username=jugador_info['username'],
                email=jugador_info['email'],
                password=jugador_info['password'],
                first_name=jugador_info['first_name'],
                last_name=jugador_info['last_name'],
                telefono=jugador_info['telefono'],
                nivel_habilidad=jugador_info['nivel_habilidad'],
                rol='jugador'
            )
            print(f"✅ Jugador creado: {jugador.get_full_name()} ({jugador.nivel_habilidad})")
        else:
            print(f"⚠️  Jugador ya existe: {jugador_info['username']}")
    
    # ============================================================================
    # CREAR RESERVAS DE EJEMPLO
    # ============================================================================
    
    print("\n📅 Creando reservas de ejemplo...")
    
    # Obtener canchas y jugadores
    canchas = list(Cancha.objects.all())
    jugadores = list(Usuario.objects.filter(rol='jugador'))
    
    if canchas and jugadores:
        # Crear reservas para los próximos días
        reservas_data = [
            # Hoy
            {
                'cancha': canchas[0],
                'jugador': jugadores[0],
                'fecha_reserva': date.today(),
                'hora_inicio': time(10, 0),
                'estado': 'confirmada',
                'notas': 'Partida matutina'
            },
            {
                'cancha': canchas[1],
                'jugador': jugadores[1],
                'fecha_reserva': date.today(),
                'hora_inicio': time(16, 0),
                'estado': 'confirmada',
                'notas': 'Entrenamiento vespertino'
            },
            # Mañana
            {
                'cancha': canchas[2],
                'jugador': jugadores[2],
                'fecha_reserva': date.today() + timedelta(days=1),
                'hora_inicio': time(9, 0),
                'estado': 'confirmada',
                'notas': 'Clase de principiantes'
            },
            {
                'cancha': canchas[0],
                'jugador': jugadores[3],
                'fecha_reserva': date.today() + timedelta(days=1),
                'hora_inicio': time(18, 0),
                'estado': 'confirmada',
                'notas': 'Partida de torneos'
            },
            # Pasado mañana
            {
                'cancha': canchas[3],
                'jugador': jugadores[4],
                'fecha_reserva': date.today() + timedelta(days=2),
                'hora_inicio': time(11, 0),
                'estado': 'confirmada',
                'notas': 'Sesión VIP'
            },
            # Una reserva cancelada
            {
                'cancha': canchas[1],
                'jugador': jugadores[0],
                'fecha_reserva': date.today() + timedelta(days=3),
                'hora_inicio': time(15, 0),
                'estado': 'cancelada',
                'notas': 'Cancelada por lluvia'
            }
        ]
        
        for reserva_info in reservas_data:
            # Verificar que no exista conflicto
            conflicto = Reserva.objects.filter(
                cancha=reserva_info['cancha'],
                fecha_reserva=reserva_info['fecha_reserva'],
                hora_inicio=reserva_info['hora_inicio'],
                estado='confirmada'
            ).exists()
            
            if not conflicto:
                reserva = Reserva.objects.create(**reserva_info)
                print(f"✅ Reserva creada: {reserva.cancha.nombre} - {reserva.fecha_reserva} {reserva.hora_inicio}")
            else:
                print(f"⚠️  Conflicto de horario: {reserva_info['cancha'].nombre} - {reserva_info['fecha_reserva']} {reserva_info['hora_inicio']}")
    
    # ============================================================================
    # ESTADÍSTICAS FINALES
    # ============================================================================
    
    print("\n📊 Estadísticas del sistema:")
    print(f"👥 Total usuarios: {Usuario.objects.count()}")
    print(f"🎾 Jugadores: {Usuario.objects.filter(rol='jugador').count()}")
    print(f"👑 Administradores: {Usuario.objects.filter(rol='administrador').count()}")
    print(f"🏟️  Total canchas: {Cancha.objects.count()}")
    print(f"📅 Total reservas: {Reserva.objects.count()}")
    print(f"✅ Reservas confirmadas: {Reserva.objects.filter(estado='confirmada').count()}")
    print(f"❌ Reservas canceladas: {Reserva.objects.filter(estado='cancelada').count()}")
    
    print("\n🎉 ¡Datos iniciales creados exitosamente!")
    print("\n📋 Credenciales de acceso:")
    print("🔐 Administrador:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("\n🔐 Jugadores de ejemplo:")
    for jugador in Usuario.objects.filter(rol='jugador')[:3]:
        print(f"   Usuario: {jugador.username}")
        print(f"   Contraseña: jugador123")
    
    print("\n🚀 ¡El sistema está listo para usar!")
    print("💡 Accede al admin en: http://localhost:8000/admin/")
    print("🌐 Página principal: http://localhost:8000/")
if __name__ == '__main__':
    crear_datos_iniciales()