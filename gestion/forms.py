"""
Formularios para la aplicación de gestión de canchas de pádel.
Define todos los formularios necesarios para el registro de usuarios,
autenticación, gestión de canchas y reservas.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import Usuario, Cancha, Reserva
class RegistroJugadorForm(UserCreationForm):
    """Formulario para el registro de nuevos jugadores."""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        }),
        label='Apellido'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo electrónico'
    )
    
    telefono = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0424-1234567'
        }),
        label='Teléfono (opcional)'
    )
    
    nivel_habilidad = forms.ChoiceField(
        choices=Usuario.NIVELES_HABILIDAD,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Nivel de habilidad'
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 
                'nivel_habilidad', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar campos heredados
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['username'].label = 'Nombre de usuario'
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password1'].label = 'Contraseña'
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password2'].label = 'Confirmar contraseña'
    
    def clean_email(self):
        """Validar que el email no esté ya registrado."""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        """Guardar el usuario con el rol de jugador."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telefono = self.cleaned_data.get('telefono')
        user.nivel_habilidad = self.cleaned_data.get('nivel_habilidad')
        user.rol = 'jugador'  # Siempre es jugador en registro público
        
        if commit:
            user.save()
        return user
class LoginForm(AuthenticationForm):
    """Formulario personalizado de inicio de sesión."""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario o email'
        }),
        label='Usuario'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        label='Contraseña'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Recordarme'
    )
class CanchaForm(forms.ModelForm):
    """Formulario para crear y editar canchas."""
    
    class Meta:
        model = Cancha
        fields = ['nombre', 'tipo_pista', 'tarifa_hora', 'descripcion', 
                'capacidad_jugadores', 'activa']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Cancha 1'
            }),
            'tipo_pista': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tarifa_hora': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej. 50.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la cancha...'
            }),
            'capacidad_jugadores': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2',
                'max': '6',
                'value': '4'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nombre': 'Nombre de la cancha',
            'tipo_pista': 'Tipo de pista',
            'tarifa_hora': 'Tarifa por hora (Bs.)',
            'descripcion': 'Descripción',
            'capacidad_jugadores': 'Capacidad de jugadores',
            'activa': 'Cancha activa'
        }
    
    def clean_tarifa_hora(self):
        """Validar que la tarifa sea positiva."""
        tarifa = self.cleaned_data.get('tarifa_hora')
        if tarifa and tarifa <= 0:
            raise ValidationError('La tarifa debe ser un valor positivo.')
        return tarifa
    
class ReservaForm(forms.ModelForm):
    """Formulario para crear reservas."""
    
    class Meta:
        model = Reserva
        fields = ['cancha', 'fecha_reserva', 'hora_inicio', 'notas']
        
        widgets = {
            'cancha': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fecha_reserva': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)...'
            })
        }
        
        labels = {
            'cancha': 'Cancha',
            'fecha_reserva': 'Fecha de reserva',
            'hora_inicio': 'Hora de inicio',
            'notas': 'Notas adicionales'
        }
    
    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Solo mostrar canchas activas
        self.fields['cancha'].queryset = Cancha.objects.filter(activa=True)
        
        # Establecer fecha mínima como hoy
        self.fields['fecha_reserva'].widget.attrs['min'] = timezone.now().date().isoformat()
    
    def clean_fecha_reserva(self):
        """Validar que la fecha no sea en el pasado."""
        fecha = self.cleaned_data.get('fecha_reserva')
        if fecha and fecha < timezone.now().date():
            raise ValidationError('No se pueden hacer reservas para fechas pasadas.')
        return fecha
    
    def clean_hora_inicio(self):
        """Validar que la hora esté dentro del horario de funcionamiento."""
        hora = self.cleaned_data.get('hora_inicio')
        if hora:
            if hora.hour < 8 or hora.hour >= 22:
                raise ValidationError('El horario de funcionamiento es de 8:00 AM a 10:00 PM.')
        return hora
    
    def clean(self):
        """Validaciones adicionales del formulario."""
        cleaned_data = super().clean()
        cancha = cleaned_data.get('cancha')
        fecha_reserva = cleaned_data.get('fecha_reserva')
        hora_inicio = cleaned_data.get('hora_inicio')
        
        if cancha and fecha_reserva and hora_inicio:
            # Calcular hora de fin (1 hora después)
            hora_fin = time(hour=(hora_inicio.hour + 1) % 24, minute=hora_inicio.minute)
            
            # Verificar disponibilidad
            if not cancha.esta_disponible(fecha_reserva, hora_inicio, hora_fin):
                raise ValidationError(
                    'La cancha no está disponible en el horario seleccionado. '
                    'Por favor, selecciona otro horario.'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar la reserva con el usuario logueado."""
        reserva = super().save(commit=False)
        if self.usuario:
            reserva.jugador = self.usuario
        
        # Calcular hora de fin automáticamente (1 hora después)
        if reserva.hora_inicio:
            hora_fin_int = (reserva.hora_inicio.hour + 1) % 24
            reserva.hora_fin = time(hour=hora_fin_int, minute=reserva.hora_inicio.minute)
        
        if commit:
            reserva.save()
        return reserva
class FiltroReservasForm(forms.Form):
    """Formulario para filtrar reservas en el panel administrativo."""
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    cancha = forms.ModelChoiceField(
        queryset=Cancha.objects.filter(activa=True),
        required=False,
        empty_label="Todas las canchas",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Cancha'
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Reserva.ESTADOS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Estado'
    )
    
    jugador = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del jugador...'
        }),
        label='Jugador'
    )
class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para editar el perfil del usuario."""
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'nivel_habilidad']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0424-1234567'
            }),
            'nivel_habilidad': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'nivel_habilidad': 'Nivel de habilidad'
        }
    
    def clean_email(self):
        """Validar que el email no esté ya registrado por otro usuario."""
        email = self.cleaned_data.get('email')
        if email:
            # Excluir el usuario actual de la validación
            otros_usuarios = Usuario.objects.filter(email=email).exclude(pk=self.instance.pk)
            if otros_usuarios.exists():
                raise ValidationError('Este correo electrónico ya está registrado.')
        return email
class BusquedaAvanzadaForm(forms.Form):
    """Formulario para búsqueda avanzada de canchas disponibles."""
    
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha'
    )
    
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora preferida'
    )
    
    tipo_pista = forms.ChoiceField(
        choices=[('', 'Cualquier tipo')] + Cancha.TIPOS_PISTA,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Tipo de pista'
    )
    
    tarifa_maxima = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Ej. 100.00'
        }),
        label='Tarifa máxima (Bs.)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fecha mínima como hoy
        self.fields['fecha'].widget.attrs['min'] = timezone.now().date().isoformat()
    
    def clean_fecha(self):
        """Validar que la fecha no sea en el pasado."""
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < timezone.now().date():
            raise ValidationError('No se pueden buscar canchas para fechas pasadas.')
        return fecha