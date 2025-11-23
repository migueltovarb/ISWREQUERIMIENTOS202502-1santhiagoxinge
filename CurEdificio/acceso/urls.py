from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de usuarios
    path('registrar-visitante/', views.registrar_visitante, name='registrar_visitante'),
    path('registrar-empleado/', views.registrar_empleado, name='registrar_empleado'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    
    # Gestión de credenciales
    path('credenciales/', views.listar_credenciales, name='listar_credenciales'),
    path('asignar-credencial-manual/', views.asignar_credencial_manual, name='asignar_credencial_manual'),
    path('modificar-credencial/<int:credencial_id>/', views.modificar_credencial, name='modificar_credencial'),
    path('eliminar-credencial/<int:credencial_id>/', views.eliminar_credencial, name='eliminar_credencial'),
    
    # Control de acceso
    path('verificar-acceso/', views.verificar_acceso, name='verificar_acceso'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('intentos-fallidos/', views.intentos_fallidos, name='intentos_fallidos'),
    
    # Configuración
    path('configurar-vigencia/', views.configurar_vigencia, name='configurar_vigencia'),
    path('configurar-horarios/', views.configurar_horarios, name='configurar_horarios'),
    path('gestionar-roles/', views.gestionar_roles, name='gestionar_roles'),
    path('eliminar-rol/<int:rol_id>/', views.eliminar_rol, name='eliminar_rol'),
    path('configuracion-sistema/', views.configuracion_sistema, name='configuracion_sistema'),
    
    # Alertas y seguridad
    path('alertas/', views.alertas, name='alertas'),
    path('marcar-alerta/<int:alerta_id>/', views.marcar_alerta, name='marcar_alerta'),
    path('modo-emergencia/', views.modo_emergencia, name='modo_emergencia'),
]




