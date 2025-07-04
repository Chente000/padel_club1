from django.apps import AppConfig
class GestionConfig(AppConfig):
    """Configuración de la aplicación gestion."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'
    verbose_name = 'Gestión de Canchas de Pádel'
    
    def ready(self):
        """Código que se ejecuta cuando la aplicación está lista."""
        # Aquí se pueden importar señales u otras configuraciones
        pass