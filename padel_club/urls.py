"""
Configuración de URLs para el proyecto padel_club.
La lista `urlpatterns` enruta URLs a vistas. Para más información, ver:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),
]
# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Configuración del admin site
admin.site.site_header = "Administración Padel Paraguaná"
admin.site.site_title = "Padel Club Admin"
admin.site.index_title = "Panel de Administración"