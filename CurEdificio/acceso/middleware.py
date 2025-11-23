from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from datetime import timedelta
from .models import ConfiguracionSistema


class SessionTimeoutMiddleware:
    """Middleware para cerrar sesión por inactividad"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            config = ConfiguracionSistema.obtener_configuracion()
            tiempo_inactividad = timedelta(minutes=config.tiempo_inactividad_minutos)
            
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity = timezone.datetime.fromisoformat(last_activity)
                if timezone.now() - last_activity > tiempo_inactividad:
                    # Cerrar sesión
                    from django.contrib.auth import logout
                    logout(request)
                    messages.warning(request, 'Su sesión ha sido cerrada por inactividad.')
                    return redirect('login')
            
            request.session['last_activity'] = timezone.now().isoformat()
        
        response = self.get_response(request)
        return response


class RoleAccessMiddleware:
    """Middleware para controlar acceso según roles"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs públicas
        public_urls = ['/login/', '/logout/', '/admin/login/', '/admin/logout/']
        
        # Permitir acceso a URLs públicas y archivos estáticos
        if request.path in public_urls or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        if request.user.is_authenticated:
            # Verificar si el usuario tiene rol
            try:
                if hasattr(request.user, 'rol') and request.user.rol:
                    rol_nombre = request.user.rol.nombre
                    # Solo Administrador y Seguridad pueden acceder
                    if rol_nombre not in ['Administrador', 'Seguridad']:
                        messages.error(request, 'Acceso denegado. Su rol no tiene permisos para ingresar al sistema.')
                        from django.contrib.auth import logout
                        logout(request)
                        return redirect('login')
                else:
                    # Si el usuario no tiene rol, redirigir al login
                    messages.error(request, 'Su usuario no tiene un rol asignado. Contacte al administrador.')
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login')
            except Exception as e:
                # Si hay algún error, permitir el acceso pero registrar el error
                pass
        
        response = self.get_response(request)
        return response

