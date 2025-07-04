from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date, time
from calendar import monthrange
import json
from .models import Usuario, Cancha, Reserva
from .forms import (
    RegistroJugadorForm, LoginForm, CanchaForm, ReservaForm,
    FiltroReservasForm, PerfilUsuarioForm, BusquedaAvanzadaForm
)
# ============================================================================
# UTILIDADES Y DECORADORES
# ============================================================================
def es_administrador(user):
    """Verifica si el usuario es administrador."""
    return user.is_authenticated and user.es_administrador()
def es_jugador_o_admin(user):
    """Verifica si el usuario es jugador o administrador."""
    return user.is_authenticated and (user.es_jugador() or user.es_administrador())
# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================
def home(request):
    """Página principal del sitio."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Estadísticas básicas para mostrar en home
    total_canchas = Cancha.objects.filter(activa=True).count()
    total_usuarios = Usuario.objects.filter(activo=True, rol='jugador').count()
    
    context = {
        'total_canchas': total_canchas,
        'total_usuarios': total_usuarios,
    }
    return render(request, 'registration/home.html', context)
def registro_view(request):
    """Vista para el registro de nuevos jugadores."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistroJugadorForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request, 
                f'¡Cuenta creada exitosamente para {username}! Ahora puedes iniciar sesión.'
            )
            return redirect('login')
    else:
        form = RegistroJugadorForm()
    
    return render(request, 'registration/registro.html', {'form': form})
def login_view(request):
    """Vista personalizada para el inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Configurar duración de sesión
                if not remember_me:
                    request.session.set_expiry(0)  # Termina cuando se cierra el navegador
                
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                
                # Redirigir según el tipo de usuario
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})
def logout_view(request):
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')
# ============================================================================
# DASHBOARD Y VISTAS PRINCIPALES
# ============================================================================
@login_required
def dashboard(request):
    """Dashboard principal que se adapta según el rol del usuario."""
    if request.user.es_administrador():
        return dashboard_admin(request)
    else:
        return dashboard_jugador(request)
@login_required
@user_passes_test(es_jugador_o_admin)
def dashboard_jugador(request):
    """Dashboard para jugadores."""
    # Reservas próximas del usuario
    reservas_proximas = request.user.get_reservas_activas()[:5]
    
    # Canchas disponibles hoy
    hoy = timezone.now().date()
    canchas_disponibles = []
    
    for cancha in Cancha.objects.filter(activa=True):
        horarios_disponibles = cancha.get_horarios_disponibles(hoy)
        if horarios_disponibles:
            canchas_disponibles.append({
                'cancha': cancha,
                'horarios_count': len(horarios_disponibles)
            })
    
    # Estadísticas del usuario
    total_reservas = request.user.reservas.count()
    reservas_completadas = request.user.reservas.filter(estado='completada').count()
    reservas_canceladas = request.user.reservas.filter(estado='cancelada').count()
    
    context = {
        'reservas_proximas': reservas_proximas,
        'canchas_disponibles': canchas_disponibles,
        'total_reservas': total_reservas,
        'reservas_completadas': reservas_completadas,
        'reservas_canceladas': reservas_canceladas,
    }
    return render(request, 'gestion/dashboard_jugador.html', context)
@login_required
@user_passes_test(es_administrador)
def dashboard_admin(request):
    """Dashboard para administradores."""
    hoy = timezone.now().date()
    
    # Estadísticas generales
    total_usuarios = Usuario.objects.filter(activo=True).count()
    total_jugadores = Usuario.objects.filter(rol='jugador', activo=True).count()
    total_canchas = Cancha.objects.filter(activa=True).count()
    
    # Reservas de hoy
    reservas_hoy = Reserva.objects.filter(fecha_reserva=hoy)
    reservas_confirmadas_hoy = reservas_hoy.filter(estado='confirmada').count()
    
    # Reservas por estado (últimos 30 días)
    fecha_limite = hoy - timedelta(days=30)
    reservas_recientes = Reserva.objects.filter(fecha_reserva__gte=fecha_limite)
    
    estadisticas_reservas = {
        'confirmadas': reservas_recientes.filter(estado='confirmada').count(),
        'canceladas': reservas_recientes.filter(estado='cancelada').count(),
        'completadas': reservas_recientes.filter(estado='completada').count(),
        'no_show': reservas_recientes.filter(estado='no_show').count(),
    }
    
    # Ingresos del mes actual
    primer_dia_mes = hoy.replace(day=1)
    ingresos_mes = reservas_recientes.filter(
        fecha_reserva__gte=primer_dia_mes,
        estado__in=['confirmada', 'completada']
    ).aggregate(total=Sum('precio_total'))['total'] or 0
    
    # Canchas más reservadas (últimos 30 días)
    canchas_populares = Cancha.objects.filter(
        reservas__fecha_reserva__gte=fecha_limite,
        reservas__estado='confirmada'
    ).annotate(
        total_reservas=Count('reservas')
    ).order_by('-total_reservas')[:5]
    
    # Reservas próximas (siguiente semana)
    fecha_limite_futuro = hoy + timedelta(days=7)
    reservas_proximas = Reserva.objects.filter(
        fecha_reserva__range=[hoy, fecha_limite_futuro],
        estado='confirmada'
    ).order_by('fecha_reserva', 'hora_inicio')[:10]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_jugadores': total_jugadores,
        'total_canchas': total_canchas,
        'reservas_confirmadas_hoy': reservas_confirmadas_hoy,
        'estadisticas_reservas': estadisticas_reservas,
        'ingresos_mes': ingresos_mes,
        'canchas_populares': canchas_populares,
        'reservas_proximas': reservas_proximas,
    }
    return render(request, 'gestion/dashboard_admin.html', context)
# ============================================================================
# GESTIÓN DE RESERVAS
# ============================================================================
@login_required
@user_passes_test(es_jugador_o_admin)
def crear_reserva(request):
    """Vista para crear una nueva reserva."""
    if request.method == 'POST':
        form = ReservaForm(request.POST, usuario=request.user)
        if form.is_valid():
            reserva = form.save()
            messages.success(
                request, 
                f'Reserva creada exitosamente para {reserva.cancha.nombre} '
                f'el {reserva.fecha_reserva} a las {reserva.hora_inicio}'
            )
            return redirect('mis_reservas')
    else:
        form = ReservaForm(usuario=request.user)
    
    return render(request, 'gestion/crear_reserva.html', {'form': form})
@login_required
@user_passes_test(es_jugador_o_admin)
def mis_reservas(request):
    """Vista para mostrar las reservas del usuario logueado."""
    reservas_list = request.user.get_historial_reservas()
    
    # Paginación
    paginator = Paginator(reservas_list, 10)
    page_number = request.GET.get('page')
    reservas = paginator.get_page(page_number)
    
    context = {
        'reservas': reservas,
        'total_reservas': reservas_list.count(),
    }
    return render(request, 'gestion/mis_reservas.html', context)
@login_required
def cancelar_reserva(request, reserva_id):
    """Vista para cancelar una reserva."""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos
    if not (request.user == reserva.jugador or request.user.es_administrador()):
        return HttpResponseForbidden("No tienes permiso para cancelar esta reserva.")
    
    if request.method == 'POST':
        if reserva.puede_cancelar():
            reserva.cancelar(request.user)
            messages.success(request, 'Reserva cancelada exitosamente.')
        else:
            messages.error(request, 'No se puede cancelar esta reserva.')
    
    if request.user.es_administrador():
        return redirect('admin_reservas')
    else:
        return redirect('mis_reservas')
    
@login_required
@user_passes_test(es_jugador_o_admin)
def calendario_reservas(request):
    """Vista del calendario de reservas."""
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_seleccionada = timezone.now().date()
    else:
        fecha_seleccionada = timezone.now().date()

    canchas = Cancha.objects.filter(activa=True).order_by('nombre')
    print(f"\n--- DEBUG: Canchas activas (ordenadas por nombre):")
    for c in canchas:
        print(f"  ID: {c.id}, Nombre: {c.nombre}")
    print("--- FIN DEBUG: Canchas ---\n")

    horarios_del_dia = [time(hour=h) for h in range(8, 22)] # Horarios de 8 AM a 9 PM (hasta antes de las 10 PM)

    reservas_confirmadas_hoy = Reserva.objects.filter(
        fecha_reserva=fecha_seleccionada,
        estado='confirmada'
    ).select_related('cancha', 'jugador') # Optimiza la carga de objetos relacionados

    reservas_por_cancha_hora = {}
    print(f"\n--- DEBUG: Reservas confirmadas para {fecha_seleccionada}:")
    if not reservas_confirmadas_hoy:
        print("  No hay reservas confirmadas para esta fecha.")
    for reserva in reservas_confirmadas_hoy:
        key = (reserva.cancha.id, reserva.hora_inicio)
        reservas_por_cancha_hora[key] = reserva
        print(f"  Reserva ID: {reserva.id}, Cancha ID: {reserva.cancha.id}, Hora: {reserva.hora_inicio}, Jugador: {reserva.jugador.username}, Cancha Nombre (desde reserva): {reserva.cancha.nombre}")
    print("--- FIN DEBUG: Reservas ---\n")

    calendario_data = []
    print("\n--- DEBUG: Construyendo calendario_data:")
    for hora in horarios_del_dia:
        hora_data = {
            'hora': hora,
            'canchas': [] # Lista de diccionarios para cada cancha en esta hora
        }
        for cancha in canchas:
            reserva = reservas_por_cancha_hora.get((cancha.id, hora))
            
            es_mi_reserva = False
            if reserva and request.user.is_authenticated and reserva.jugador == request.user:
                es_mi_reserva = True

            cancha_info_for_cell = {
                'cancha': cancha, # El objeto Cancha completo
                'reserva': reserva, # El objeto Reserva o None
                'disponible': not bool(reserva), # True si no hay reserva, False si la hay
                'es_mi_reserva': es_mi_reserva
            }
            hora_data['canchas'].append(cancha_info_for_cell)
        calendario_data.append(hora_data)
    print("--- FIN DEBUG: calendario_data ---\n")

    # --- DEBUG: Imprimir la estructura final de calendario_data en JSON ---
    print("\n--- DEBUG: Estructura final de calendario_data antes de renderizar (JSON):")
    serializable_calendario_data = []
    for hora_data_item in calendario_data:
        serializable_hora_data = {
            'hora': hora_data_item['hora'].isoformat(timespec='minutes'),
            'canchas': []
        }
        for cancha_data_item in hora_data_item['canchas']:
            serializable_cancha_data = {
                'cancha_id': cancha_data_item['cancha'].id,
                'cancha_nombre': cancha_data_item['cancha'].nombre,
                'disponible': cancha_data_item['disponible'],
                'es_mi_reserva': cancha_data_item['es_mi_reserva'],
                'reserva_id': cancha_data_item['reserva'].id if cancha_data_item['reserva'] else None,
                'reserva_jugador': cancha_data_item['reserva'].jugador.username if cancha_data_item['reserva'] else None
            }
            serializable_hora_data['canchas'].append(serializable_cancha_data)
        serializable_calendario_data.append(serializable_hora_data)
    
    print(json.dumps(serializable_calendario_data, indent=2))
    print("--- FIN DEBUG: Estructura final de calendario_data (JSON) ---\n")
    # --- FIN DEBUG ---

    fecha_anterior = fecha_seleccionada - timedelta(days=1)
    fecha_siguiente = fecha_seleccionada + timedelta(days=1)

    context = {
        'fecha_seleccionada': fecha_seleccionada,
        'fecha_anterior': fecha_anterior,
        'fecha_siguiente': fecha_siguiente,
        'canchas': canchas, # Lista de objetos Cancha para el encabezado de columnas (thead)
        'horarios': horarios_del_dia, # Lista de objetos time para las filas (primer td)
        'calendario_data': calendario_data, # La matriz de datos para el cuerpo de la tabla
    }
    return render(request, 'gestion/calendario_reservas.html', context)


@login_required
@user_passes_test(es_jugador_o_admin)
def reserva_rapida(request):
    """Vista para hacer una reserva rápida desde el calendario."""
    if request.method == 'POST':
        cancha_id = request.POST.get('cancha_id')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        
        try:
            cancha = Cancha.objects.get(id=cancha_id, activa=True)
            fecha_reserva = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_str, '%H:%M').time()
            
            # Verificar disponibilidad
            if cancha.esta_disponible(fecha_reserva, hora_inicio):
                # Crear la reserva
                reserva = Reserva.objects.create(
                    cancha=cancha,
                    jugador=request.user,
                    fecha_reserva=fecha_reserva,
                    hora_inicio=hora_inicio,
                    precio_total=cancha.tarifa_hora
                )
                
                messages.success(
                    request,
                    f'Reserva creada exitosamente: {cancha.nombre} - '
                    f'{fecha_reserva} a las {hora_inicio}'
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'El horario ya no está disponible.'
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Error al crear la reserva.'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})
# ============================================================================
# GESTIÓN DE CANCHAS (Solo Administradores)
# ============================================================================
@login_required
@user_passes_test(es_administrador)
def admin_canchas(request):
    """Vista para gestionar canchas (solo administradores)."""
    canchas_list = Cancha.objects.all().order_by('nombre')
    
    # Paginación
    paginator = Paginator(canchas_list, 10)
    page_number = request.GET.get('page')
    canchas = paginator.get_page(page_number)
    
    context = {
        'canchas': canchas,
        'total_canchas': canchas_list.count(),
    }
    return render(request, 'gestion/admin_canchas.html', context)
@login_required
@user_passes_test(es_administrador)
def crear_cancha(request):
    """Vista para crear una nueva cancha."""
    if request.method == 'POST':
        form = CanchaForm(request.POST)
        if form.is_valid():
            cancha = form.save()
            messages.success(request, f'Cancha "{cancha.nombre}" creada exitosamente.')
            return redirect('admin_canchas')
    else:
        form = CanchaForm()
    
    return render(request, 'gestion/crear_cancha.html', {'form': form})
@login_required
@user_passes_test(es_administrador)
def editar_cancha(request, cancha_id):
    """Vista para editar una cancha existente."""
    cancha = get_object_or_404(Cancha, id=cancha_id)
    
    if request.method == 'POST':
        form = CanchaForm(request.POST, instance=cancha)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cancha "{cancha.nombre}" actualizada exitosamente.')
            return redirect('admin_canchas')
    else:
        form = CanchaForm(instance=cancha)
    
    context = {
        'form': form,
        'cancha': cancha,
    }
    return render(request, 'gestion/editar_cancha.html', context)
@login_required
@user_passes_test(es_administrador)
def eliminar_cancha(request, cancha_id):
    """
    Vista para eliminar (desactivar) una cancha.
    Antes de renderizar el template, anota la cancha con conteos de reservas
    para mostrar estadísticas en la página de confirmación.
    """
    
    # Obtener la cancha y ANOTAR los conteos de reservas.
    # Usamos .annotate() en la QuerySet antes de get_object_or_404
    # para que los conteos sean parte del objeto 'cancha' que se pasa al template.
    cancha = get_object_or_404(Cancha.objects.annotate(
        # Conteo total de todas las reservas de esta cancha
        total_reservas_cancha=Count('reservas'),
        
        # Conteo de reservas con estado 'confirmada'
        reservas_confirmadas_cancha=Count('reservas', filter=Q(reservas__estado='confirmada')),
        
        # Conteo de reservas con estado 'completada'
        reservas_completadas_cancha=Count('reservas', filter=Q(reservas__estado='completada')),
        
        # Conteo de reservas futuras y confirmadas
        # Usamos __gte (greater than or equal) para incluir la fecha actual y futuras
        reservas_futuras_confirmadas_cancha=Count(
            'reservas', 
            filter=Q(reservas__estado='confirmada', reservas__fecha_reserva__gte=timezone.now().date())
        )
    ), id=cancha_id) # Finalmente, obtenemos el objeto específico por su ID
    
    if request.method == 'POST':
        # Lógica para desactivar la cancha (establecer 'activa' a False)
        cancha.activa = False
        cancha.save()
        messages.success(request, f'Cancha "{cancha.nombre}" desactivada exitosamente.')
        return redirect('admin_canchas')
    
    context = {
        'cancha': cancha, # Pasamos el objeto 'cancha' que ahora incluye los conteos anotados
        # No es necesario pasar 'today' por separado si el filtro ya se hizo en annotate
    }
    return render(request, 'gestion/confirmar_eliminar_cancha.html', context)
# ============================================================================
# ADMINISTRACIÓN DE RESERVAS
# ============================================================================
@login_required
@user_passes_test(es_administrador)
def admin_reservas(request):
    """Vista para gestionar todas las reservas (solo administradores)."""
    # Filtros
    form = FiltroReservasForm(request.GET)
    reservas_queryset = Reserva.objects.select_related('cancha', 'jugador')
    
    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            reservas_queryset = reservas_queryset.filter(
                fecha_reserva__gte=form.cleaned_data['fecha_desde']
            )
        
        if form.cleaned_data.get('fecha_hasta'):
            reservas_queryset = reservas_queryset.filter(
                fecha_reserva__lte=form.cleaned_data['fecha_hasta']
            )
        
        if form.cleaned_data.get('cancha'):
            reservas_queryset = reservas_queryset.filter(
                cancha=form.cleaned_data['cancha']
            )
        
        if form.cleaned_data.get('estado'):
            reservas_queryset = reservas_queryset.filter(
                estado=form.cleaned_data['estado']
            )
        
        if form.cleaned_data.get('jugador'):
            jugador_query = form.cleaned_data['jugador']
            reservas_queryset = reservas_queryset.filter(
                Q(jugador__first_name__icontains=jugador_query) |
                Q(jugador__last_name__icontains=jugador_query) |
                Q(jugador__username__icontains=jugador_query)
            )
    
    # Ordenar por fecha más reciente
    reservas_list = reservas_queryset.order_by('-fecha_reserva', '-hora_inicio')
    
    # Paginación
    paginator = Paginator(reservas_list, 15)
    page_number = request.GET.get('page')
    reservas = paginator.get_page(page_number)
    
    context = {
        'reservas': reservas,
        'form': form,
        'total_reservas': reservas_list.count(),
    }
    return render(request, 'gestion/admin_reservas.html', context)
# ============================================================================
# GESTIÓN DE USUARIOS
# ============================================================================
@login_required
@user_passes_test(es_administrador)
def admin_usuarios(request):
    """Vista para gestionar usuarios (solo administradores)."""
    usuarios_list_anotated = Usuario.objects.filter(activo=True).annotate(
        reservas_confirmadas_count=Count('reservas', filter=Q(reservas__estado='confirmada'))
    ).order_by('-fecha_registro')

    # Paginación
    paginator = Paginator(usuarios_list_anotated, 15)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios_list_anotated.count(),
    }
    return render(request, 'gestion/admin_usuarios.html', context)
# ============================================================================
# PERFIL DE USUARIO
# ============================================================================
@login_required
def perfil_usuario(request):
    """Vista para ver y editar el perfil del usuario."""
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=request.user)
    
    # Estadísticas del usuario
    total_reservas = request.user.reservas.count()
    reservas_completadas = request.user.reservas.filter(estado='completada').count()
    reservas_activas = request.user.get_reservas_activas().count()
    
    context = {
        'form': form,
        'total_reservas': total_reservas,
        'reservas_completadas': reservas_completadas,
        'reservas_activas': reservas_activas,
    }
    return render(request, 'gestion/perfil_usuario.html', context)
# ============================================================================
# BÚSQUEDA Y CONSULTAS
# ============================================================================
@login_required
@user_passes_test(es_jugador_o_admin)
def buscar_canchas(request):
    """Vista para búsqueda avanzada de canchas disponibles."""
    form = BusquedaAvanzadaForm(request.GET)
    canchas_disponibles = []
    
    if form.is_valid():
        fecha = form.cleaned_data.get('fecha')
        hora_inicio = form.cleaned_data.get('hora_inicio')
        tipo_pista = form.cleaned_data.get('tipo_pista')
        tarifa_maxima = form.cleaned_data.get('tarifa_maxima')
        
        # Filtrar canchas según criterios
        canchas_queryset = Cancha.objects.filter(activa=True)
        
        if tipo_pista:
            canchas_queryset = canchas_queryset.filter(tipo_pista=tipo_pista)
        
        if tarifa_maxima:
            canchas_queryset = canchas_queryset.filter(tarifa_hora__lte=tarifa_maxima)
        
        # Verificar disponibilidad para cada cancha
        for cancha in canchas_queryset:
            if cancha.esta_disponible(fecha, hora_inicio):
                canchas_disponibles.append(cancha)
    
    context = {
        'form': form,
        'canchas_disponibles': canchas_disponibles,
    }
    return render(request, 'gestion/buscar_canchas.html', context)
# ============================================================================
# REPORTES Y ESTADÍSTICAS
# ============================================================================
@login_required
@user_passes_test(es_administrador)
def reportes_admin(request):
    """Vista de reportes para administradores."""
    hoy = timezone.now().date()
    
    # Parámetros de fecha
    fecha_desde_str = request.GET.get('fecha_desde')
    fecha_hasta_str = request.GET.get('fecha_hasta')
    
    try:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date() if fecha_desde_str else hoy - timedelta(days=30)
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date() if fecha_hasta_str else hoy
    except ValueError:
        fecha_desde = hoy - timedelta(days=30)
        fecha_hasta = hoy
    
    # Reservas en el período
    reservas_periodo = Reserva.objects.filter(
        fecha_reserva__range=[fecha_desde, fecha_hasta]
    )
    
    # Estadísticas generales
    estadisticas = {
        'total_reservas': reservas_periodo.count(),
        'reservas_confirmadas': reservas_periodo.filter(estado='confirmada').count(),
        'reservas_completadas': reservas_periodo.filter(estado='completada').count(),
        'reservas_canceladas': reservas_periodo.filter(estado='cancelada').count(),
        'reservas_no_show': reservas_periodo.filter(estado='no_show').count(),
    }
    
    # Ingresos
    ingresos_total = reservas_periodo.filter(
        estado__in=['confirmada', 'completada']
    ).aggregate(total=Sum('precio_total'))['total'] or 0
    
    # Canchas más utilizadas
    canchas_stats = Cancha.objects.filter(
        reservas__fecha_reserva__range=[fecha_desde, fecha_hasta]
    ).annotate(
        total_reservas=Count('reservas'),
        ingresos=Sum('reservas__precio_total')
    ).order_by('-total_reservas')
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estadisticas': estadisticas,
        'ingresos_total': ingresos_total,
        'canchas_stats': canchas_stats,
    }
    return render(request, 'gestion/reportes_admin.html', context)
# ============================================================================
# APIs AJAX
# ============================================================================
@login_required
def get_horarios_disponibles(request):
    """API para obtener horarios disponibles de una cancha en una fecha."""
    cancha_id = request.GET.get('cancha_id')
    fecha_str = request.GET.get('fecha')
    
    try:
        cancha = Cancha.objects.get(id=cancha_id, activa=True)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        horarios_disponibles = cancha.get_horarios_disponibles(fecha)
        horarios_data = [
            {
                'hora': horario.strftime('%H:%M'),
                'hora_display': horario.strftime('%I:%M %p')
            }
            for horario in horarios_disponibles
        ]
        
        return JsonResponse({
            'success': True,
            'horarios': horarios_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })