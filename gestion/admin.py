from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario, Cancha, Reserva
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Configuración del administrador para el modelo Usuario."""
    
    list_display = (
        'username', 
        'get_full_name', 
        'email', 
        'rol', 
        'nivel_habilidad',
        'telefono',
        'is_active',
        'fecha_registro'
    )
    
    list_filter = (
        'rol', 
        'nivel_habilidad', 
        'is_active', 
        'fecha_registro',
        'date_joined'
    )
    
    search_fields = (
        'username', 
        'first_name', 
        'last_name', 
        'email',
        'telefono'
    )
    
    ordering = ('-fecha_registro',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('rol', 'nivel_habilidad', 'telefono', 'activo')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('first_name', 'last_name', 'email', 'rol', 'nivel_habilidad', 'telefono')
        }),
    )
    
    def get_full_name(self, obj):
        """Muestra el nombre completo del usuario."""
        return obj.get_full_name() or obj.username
    get_full_name.short_description = 'Nombre completo'
    
    actions = ['activar_usuarios', 'desactivar_usuarios']
    
    def activar_usuarios(self, request, queryset):
        """Acción para activar usuarios seleccionados."""
        updated = queryset.update(is_active=True, activo=True)
        self.message_user(request, f'{updated} usuarios activados correctamente.')
    activar_usuarios.short_description = "Activar usuarios seleccionados"
    
    def desactivar_usuarios(self, request, queryset):
        """Acción para desactivar usuarios seleccionados."""
        updated = queryset.update(is_active=False, activo=False)
        self.message_user(request, f'{updated} usuarios desactivados correctamente.')
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"
@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    """Configuración del administrador para el modelo Cancha."""
    
    list_display = (
        'nombre',
        'tipo_pista',
        'tarifa_hora_formatted',
        'capacidad_jugadores',
        'estado_cancha',
        'fecha_creacion'
    )
    
    list_filter = (
        'tipo_pista',
        'activa',
        'fecha_creacion'
    )
    
    search_fields = (
        'nombre',
        'descripcion'
    )
    
    ordering = ('nombre',)
    
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'tipo_pista', 'descripcion')
        }),
        ('Configuración operativa', {
            'fields': ('tarifa_hora', 'capacidad_jugadores', 'activa')
        }),
    )
    
    def tarifa_hora_formatted(self, obj):
        """Formatea la tarifa por hora con el símbolo de moneda."""
        return f"Bs. {obj.tarifa_hora:,.2f}"
    tarifa_hora_formatted.short_description = 'Tarifa/hora'
    
    def estado_cancha(self, obj):
        """Muestra el estado de la cancha con colores."""
        if obj.activa:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activa</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Inactiva</span>'
            )
    estado_cancha.short_description = 'Estado'
    
    actions = ['activar_canchas', 'desactivar_canchas']
    
    def activar_canchas(self, request, queryset):
        """Acción para activar canchas seleccionadas."""
        updated = queryset.update(activa=True)
        self.message_user(request, f'{updated} canchas activadas correctamente.')
    activar_canchas.short_description = "Activar canchas seleccionadas"
    
    def desactivar_canchas(self, request, queryset):
        """Acción para desactivar canchas seleccionadas."""
        updated = queryset.update(activa=False)
        self.message_user(request, f'{updated} canchas desactivadas correctamente.')
    desactivar_canchas.short_description = "Desactivar canchas seleccionadas"
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Configuración del administrador para el modelo Reserva."""
    
    list_display = (
        'id',
        'cancha',
        'jugador_nombre',
        'fecha_reserva',
        'hora_inicio',
        'hora_fin',
        'estado_reserva',
        'precio_total_formatted',
        'fecha_creacion'
    )
    
    list_filter = (
        'estado',
        'fecha_reserva',
        'cancha',
        'fecha_creacion'
    )
    
    search_fields = (
        'jugador__username',
        'jugador__first_name',
        'jugador__last_name',
        'jugador__email',
        'cancha__nombre'
    )
    
    ordering = ('-fecha_reserva', '-hora_inicio')
    
    date_hierarchy = 'fecha_reserva'
    
    fieldsets = (
        ('Información de la reserva', {
            'fields': ('cancha', 'jugador', 'fecha_reserva', 'hora_inicio', 'hora_fin')
        }),
        ('Estado y precio', {
            'fields': ('estado', 'precio_total')
        }),
        ('Información adicional', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    
    def jugador_nombre(self, obj):
        """Muestra el nombre completo del jugador."""
        return obj.jugador.get_full_name() or obj.jugador.username
    jugador_nombre.short_description = 'Jugador'
    jugador_nombre.admin_order_field = 'jugador__first_name'
    
    def estado_reserva(self, obj):
        """Muestra el estado de la reserva con colores."""
        colores = {
            'confirmada': 'green',
            'cancelada': 'red',
            'completada': 'blue',
            'no_show': 'orange'
        }
        color = colores.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_reserva.short_description = 'Estado'
    
    def precio_total_formatted(self, obj):
        """Formatea el precio total con el símbolo de moneda."""
        return f"Bs. {obj.precio_total:,.2f}"
    precio_total_formatted.short_description = 'Precio total'
    
    actions = ['cancelar_reservas', 'marcar_completadas', 'marcar_no_show']
    
    def cancelar_reservas(self, request, queryset):
        """Acción para cancelar reservas seleccionadas."""
        count = 0
        for reserva in queryset:
            if reserva.puede_cancelar():
                reserva.cancelar()
                count += 1
        self.message_user(request, f'{count} reservas canceladas correctamente.')
    cancelar_reservas.short_description = "Cancelar reservas seleccionadas"
    
    def marcar_completadas(self, request, queryset):
        """Acción para marcar reservas como completadas."""
        updated = queryset.filter(estado='confirmada').update(estado='completada')
        self.message_user(request, f'{updated} reservas marcadas como completadas.')
    marcar_completadas.short_description = "Marcar como completadas"
    
    def marcar_no_show(self, request, queryset):
        """Acción para marcar reservas como no show."""
        updated = queryset.filter(estado='confirmada').update(estado='no_show')
        self.message_user(request, f'{updated} reservas marcadas como no show.')
    marcar_no_show.short_description = "Marcar como no show"
    
    def get_queryset(self, request):
        """Optimiza las consultas para evitar N+1."""
        return super().get_queryset(request).select_related('cancha', 'jugador')
# Configuración adicional del admin site
admin.site.site_header = "Administración Padel Paraguaná"
admin.site.site_title = "Padel Club Admin"
admin.site.index_title = "Panel de Control - Gestión de Canchas"