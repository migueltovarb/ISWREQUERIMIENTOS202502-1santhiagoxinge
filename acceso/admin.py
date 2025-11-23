from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Credencial, Rol, RegistroAcceso, IntentoFallido,
    ConfiguracionVigencia, ConfiguracionHorario, Alerta,
    ConfiguracionSistema, LogAuditoria
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'numero_identificacion', 'rol', 'activo', 'ultimo_acceso']
    list_filter = ['rol', 'activo', 'tipo_identificacion']
    search_fields = ['username', 'first_name', 'last_name', 'numero_identificacion']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('tipo_identificacion', 'numero_identificacion', 'rol', 'cargo_dependencia',
                      'contacto', 'correo_institucional', 'fotografia', 'activo', 'ultimo_acceso')
        }),
    )


@admin.register(Credencial)
class CredencialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usuario', 'rol', 'estado', 'fecha_creacion', 'fecha_vencimiento']
    list_filter = ['estado', 'rol', 'asignacion_manual']
    search_fields = ['codigo', 'usuario__first_name', 'usuario__last_name', 'usuario__numero_identificacion']
    readonly_fields = ['codigo', 'fecha_creacion']


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'nivel_acceso', 'activo']
    search_fields = ['nombre', 'descripcion']


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ['fecha_hora', 'usuario', 'tipo', 'estado', 'punto_acceso']
    list_filter = ['tipo', 'estado', 'fecha_hora']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'credencial__codigo']
    readonly_fields = ['fecha_hora']
    date_hierarchy = 'fecha_hora'


@admin.register(IntentoFallido)
class IntentoFallidoAdmin(admin.ModelAdmin):
    list_display = ['fecha_hora', 'credencial_codigo', 'usuario', 'punto_acceso', 'motivo']
    list_filter = ['fecha_hora', 'punto_acceso']
    search_fields = ['credencial_codigo', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['fecha_hora']


@admin.register(ConfiguracionVigencia)
class ConfiguracionVigenciaAdmin(admin.ModelAdmin):
    list_display = ['rol', 'vigencia_horas', 'vigencia_dias', 'fecha_modificacion']
    list_filter = ['rol']


@admin.register(ConfiguracionHorario)
class ConfiguracionHorarioAdmin(admin.ModelAdmin):
    list_display = ['rol', 'dia_semana', 'hora_entrada', 'hora_salida']
    list_filter = ['rol', 'dia_semana']


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'estado', 'fecha_hora', 'usuario_relacionado', 'punto_acceso']
    list_filter = ['tipo', 'estado', 'fecha_hora']
    search_fields = ['descripcion', 'usuario_relacionado__first_name']


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['periodo_retencion_logs', 'tiempo_inactividad_minutos', 'modo_emergencia']


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'accion', 'modulo', 'fecha_hora']
    list_filter = ['modulo', 'fecha_hora']
    search_fields = ['usuario__username', 'accion', 'modulo']
    readonly_fields = ['fecha_hora']
    date_hierarchy = 'fecha_hora'




