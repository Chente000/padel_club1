from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, time
import bcrypt
class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Incluye roles de Administrador y Jugador.
    """
    
    ROLES = [
        ('jugador', 'Jugador'),
        ('administrador', 'Administrador'),
    ]
    
    NIVELES_HABILIDAD = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('profesional', 'Profesional'),
    ]
    
    # Campos adicionales
    rol = models.CharField(
        max_length=20, 
        choices=ROLES, 
        default='jugador',
        verbose_name='Rol'
    )
    
    nivel_habilidad = models.CharField(
        max_length=20, 
        choices=NIVELES_HABILIDAD, 
        blank=True, 
        null=True,
        verbose_name='Nivel de habilidad'
    )
    
    telefono = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Teléfono'
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Usuario activo'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"
    
    def es_administrador(self):
        """Verifica si el usuario es administrador."""
        return self.rol == 'administrador'
    
    def es_jugador(self):
        """Verifica si el usuario es jugador."""
        return self.rol == 'jugador'
    
    def get_reservas_activas(self):
        """Obtiene las reservas activas del usuario."""
        return self.reservas.filter(
            estado='confirmada',
            fecha_reserva__gte=timezone.now().date()
        ).order_by('fecha_reserva', 'hora_inicio')
    
    def get_historial_reservas(self):
        """Obtiene el historial completo de reservas del usuario."""
        return self.reservas.all().order_by('-fecha_reserva', '-hora_inicio')
class Cancha(models.Model):
    """
    Modelo que representa una cancha de pádel.
    """
    
    TIPOS_PISTA = [
        ('cristal', 'Cristal'),
        ('muro', 'Muro'),
        ('mixta', 'Mixta'),
    ]
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la cancha'
    )
    
    tipo_pista = models.CharField(
        max_length=20,
        choices=TIPOS_PISTA,
        default='cristal',
        verbose_name='Tipo de pista'
    )
    
    tarifa_hora = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Tarifa por hora (Bs.)'
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción'
    )
    
    capacidad_jugadores = models.IntegerField(
        default=4,
        validators=[MinValueValidator(2), MaxValueValidator(6)],
        verbose_name='Capacidad de jugadores'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Cancha activa'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Cancha'
        verbose_name_plural = 'Canchas'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_pista_display()}"
    
    def esta_disponible(self, fecha, hora_inicio, hora_fin=None):
        """
        Verifica si la cancha está disponible en la fecha y hora especificadas.
        """
        if not self.activa:
            return False
        
        # Si no se especifica hora_fin, asume 1 hora
        if hora_fin is None:
            hora_fin = time(hour=(hora_inicio.hour + 1) % 24)
        
        # Verificar conflictos con reservas existentes
        conflictos = self.reservas.filter(
            fecha_reserva=fecha,
            estado='confirmada'
        ).filter(
            models.Q(hora_inicio__lt=hora_fin) & 
            models.Q(hora_fin__gt=hora_inicio)
        )
        
        return not conflictos.exists()
    
    def get_reservas_del_dia(self, fecha):
        """Obtiene todas las reservas confirmadas de la cancha para una fecha específica."""
        return self.reservas.filter(
            fecha_reserva=fecha,
            estado='confirmada'
        ).order_by('hora_inicio')
    
    def get_horarios_disponibles(self, fecha):
        """
        Obtiene los horarios disponibles para una fecha específica.
        Horarios de funcionamiento: 8:00 AM - 10:00 PM
        """
        if not self.activa:
            return []
        
        horarios_funcionamiento = []
        for hora in range(8, 22):  # 8 AM a 10 PM
            horarios_funcionamiento.append(time(hour=hora))
        
        reservas_del_dia = self.get_reservas_del_dia(fecha)
        horarios_ocupados = [reserva.hora_inicio for reserva in reservas_del_dia]
        
        horarios_disponibles = [
            horario for horario in horarios_funcionamiento 
            if horario not in horarios_ocupados
        ]
        
        return horarios_disponibles
class Reserva(models.Model):
    """
    Modelo que representa una reserva de cancha.
    """
    
    ESTADOS = [
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
        ('no_show', 'No se presentó'),
    ]
    
    cancha = models.ForeignKey(
        Cancha,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Cancha'
    )
    
    jugador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Jugador'
    )
    
    fecha_reserva = models.DateField(
        verbose_name='Fecha de la reserva'
    )
    
    hora_inicio = models.TimeField(
        verbose_name='Hora de inicio'
    )
    
    hora_fin = models.TimeField(
        verbose_name='Hora de fin'
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='confirmada',
        verbose_name='Estado'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de modificación'
    )
    
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas adicionales'
    )
    
    precio_total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Precio total (Bs.)'
    )
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_reserva', '-hora_inicio']
        
        # Constraint para evitar reservas duplicadas
        constraints = [
            models.UniqueConstraint(
                fields=['cancha', 'fecha_reserva', 'hora_inicio'],
                condition=models.Q(estado='confirmada'),
                name='unique_confirmed_reservation'
            )
        ]
    
    def __str__(self):
        return f"{self.cancha.nombre} - {self.fecha_reserva} {self.hora_inicio} - {self.jugador.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para calcular automáticamente el precio total
        y la hora de fin si no se especifica.
        """
        # Calcular precio total basado en la tarifa de la cancha
        if not self.precio_total and self.cancha:
            self.precio_total = self.cancha.tarifa_hora
        
        # Si no hay hora_fin, asumir 1 hora de duración
        if not self.hora_fin and self.hora_inicio:
            hora_fin_int = (self.hora_inicio.hour + 1) % 24
            self.hora_fin = time(hour=hora_fin_int, minute=self.hora_inicio.minute)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validaciones personalizadas del modelo."""
        from django.core.exceptions import ValidationError
        
        # Validar que la fecha de reserva no sea en el pasado
        if self.fecha_reserva and self.fecha_reserva < timezone.now().date():
            raise ValidationError('No se pueden hacer reservas para fechas pasadas.')
        
        # Validar que la hora de fin sea posterior a la hora de inicio
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        
        # Validar disponibilidad de la cancha
        if self.cancha and not self.cancha.esta_disponible(
            self.fecha_reserva, self.hora_inicio, self.hora_fin
        ):
            # Excepto si es la misma reserva (para actualizaciones)
            reservas_conflicto = Reserva.objects.filter(
                cancha=self.cancha,
                fecha_reserva=self.fecha_reserva,
                estado='confirmada'
            ).filter(
                models.Q(hora_inicio__lt=self.hora_fin) & 
                models.Q(hora_fin__gt=self.hora_inicio)
            ).exclude(pk=self.pk)
            
            if reservas_conflicto.exists():
                raise ValidationError('La cancha no está disponible en el horario seleccionado.')
    
    def puede_cancelar(self):
        """
        Verifica si la reserva puede ser cancelada.
        Solo se pueden cancelar reservas confirmadas y futuras.
        """
        return (
            self.estado == 'confirmada' and
            self.fecha_reserva >= timezone.now().date()
        )
    
    def cancelar(self, usuario_cancelacion=None):
        """Cancela la reserva."""
        if self.puede_cancelar():
            self.estado = 'cancelada'
            if usuario_cancelacion:
                self.notas = f"Cancelada por: {usuario_cancelacion.get_full_name()}"
            self.save()
            return True
        return False
    
    def get_duracion_horas(self):
        """Calcula la duración de la reserva en horas."""
        if self.hora_inicio and self.hora_fin:
            inicio = datetime.combine(self.fecha_reserva, self.hora_inicio)
            fin = datetime.combine(self.fecha_reserva, self.hora_fin)
            duracion = fin - inicio
            return duracion.total_seconds() / 3600
        return 1  # Por defecto 1 hora