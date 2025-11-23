from .models import ConfiguracionSistema


def configuracion_sistema(request):
    """Context processor para incluir la configuración del sistema en todos los templates"""
    if request.user.is_authenticated:
        try:
            config = ConfiguracionSistema.obtener_configuracion()
            return {'configuracion_sistema': config}
        except:
            return {'configuracion_sistema': None}
    return {'configuracion_sistema': None}




