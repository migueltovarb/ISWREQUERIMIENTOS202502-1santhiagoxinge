from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from datetime import timedelta
import secrets
import string


class Rol(models.Model):
    """Modelo para gestionar roles del sistema"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)
    nivel_acceso = models.CharField(
        max_length=10,
        choices=[('Alto', 'Alto'), ('Medio', 'Medio'), ('Bajo', 'Bajo')],
        default='Bajo'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Modelo de usuario personalizado"""
    TIPO_IDENTIFICACION_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('Otro', 'Otro'),
    ]
    
    tipo_identificacion = models.CharField(
        max_length=10,
        choices=TIPO_IDENTIFICACION_CHOICES,
        default='CC'
    )
    numero_identificacion = models.CharField(max_length=20, unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios')
    cargo_dependencia = models.CharField(max_length=100, blank=True)
    contacto = models.CharField(max_length=100)  # Teléfono o email
    correo_institucional = models.EmailField(blank=True)
    motivo_ingreso = models.TextField(blank=True, help_text="Motivo de ingreso (para visitantes)")
    fotografia = models.ImageField(upload_to='fotos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.numero_identificacion}"


class ConfiguracionVigencia(models.Model):
    """Configuración de vigencia por rol"""
    rol = models.OneToOneField(Rol, on_delete=models.CASCADE, related_name='config_vigencia')
    vigencia_horas = models.IntegerField(null=True, blank=True)  # None = indefinida
    vigencia_dias = models.IntegerField(null=True, blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configuraciones_modificadas'
    )
    
    class Meta:
        verbose_name = "Configuración de Vigencia"
        verbose_name_plural = "Configuraciones de Vigencia"
    
    def __str__(self):
        if self.vigencia_horas:
            return f"{self.rol.nombre}: {self.vigencia_horas} horas"
        elif self.vigencia_dias:
            return f"{self.rol.nombre}: {self.vigencia_dias} días"
        else:
            return f"{self.rol.nombre}: Indefinida"


class Credencial(models.Model):
    """Modelo para credenciales digitales"""
    ESTADO_CHOICES = [
        ('Activa', 'Activa'),
        ('Inactiva', 'Inactiva'),
        ('Vencida', 'Vencida'),
        ('Bloqueada', 'Bloqueada'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='credenciales')
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activa')
    asignacion_manual = models.BooleanField(default=False)
    intentos_fallidos = models.IntegerField(default=0)
    fecha_bloqueo = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Credencial"
        verbose_name_plural = "Credenciales"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.codigo} - {self.usuario.get_full_name()}"
    
    def esta_vencida(self):
        if self.fecha_vencimiento is None:
            return False
        return timezone.now() > self.fecha_vencimiento
    
    def esta_bloqueada(self):
        if self.estado == 'Bloqueada':
            if self.fecha_bloqueo:
                # Desbloquear después de 15 minutos
                tiempo_bloqueo = timedelta(minutes=15)
                if timezone.now() > self.fecha_bloqueo + tiempo_bloqueo:
                    self.estado = 'Activa'
                    self.intentos_fallidos = 0
                    self.fecha_bloqueo = None
                    self.save()
                    return False
            return True
        return False
    
    @staticmethod
    def generar_codigo(rol):
        """Genera un código único según el rol"""
        prefijos = {
            'Empleado': 'EMP',
            'Personal interno': 'EMP',
            'Visitante temporal': 'VIS',
            'Visitante': 'VIS',
            'Proveedor': 'EXT',
            'Personal externo': 'EXT',
            'Administrador': 'ADM',
        }
        
        prefijo = prefijos.get(rol.nombre, 'GEN')
        
        while True:
            # Generar código alfanumérico de 6-10 caracteres
            longitud = 6
            caracteres = string.ascii_uppercase + string.digits
            sufijo = ''.join(secrets.choice(caracteres) for _ in range(longitud))
            codigo = f"{prefijo}{sufijo}"
            
            if not Credencial.objects.filter(codigo=codigo).exists():
                return codigo


class RegistroAcceso(models.Model):
    """Registro de entradas y salidas"""
    TIPO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]
    
    ESTADO_CHOICES = [
        ('Permitido', 'Permitido'),
        ('Denegado', 'Denegado'),
    ]
    
    credencial = models.ForeignKey(
        Credencial,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registros'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    punto_acceso = models.CharField(max_length=50, default='Principal')
    motivo_denegacion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Registro de Acceso"
        verbose_name_plural = "Registros de Acceso"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario} - {self.fecha_hora}"


class IntentoFallido(models.Model):
    """Registro de intentos fallidos de acceso"""
    credencial_codigo = models.CharField(max_length=10, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    punto_acceso = models.CharField(max_length=50)
    motivo = models.CharField(max_length=200)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Intento Fallido"
        verbose_name_plural = "Intentos Fallidos"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"Intento fallido - {self.fecha_hora}"


class ConfiguracionHorario(models.Model):
    """Configuración de horarios de acceso por rol"""
    DIA_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]
    
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=10, choices=DIA_CHOICES)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        verbose_name = "Configuración de Horario"
        verbose_name_plural = "Configuraciones de Horarios"
        unique_together = ['rol', 'dia_semana']
    
    def __str__(self):
        return f"{self.rol.nombre} - {self.dia_semana}: {self.hora_entrada} - {self.hora_salida}"


class Alerta(models.Model):
    """Sistema de alertas de seguridad"""
    TIPO_CHOICES = [
        ('Intento fallido', 'Intento fallido'),
        ('Fuera de horario', 'Fuera de horario'),
        ('Credencial vencida', 'Credencial vencida'),
        ('Credencial bloqueada', 'Credencial bloqueada'),
        ('Acceso no autorizado', 'Acceso no autorizado'),
    ]
    
    ESTADO_CHOICES = [
        ('Nueva', 'Nueva'),
        ('Revisada', 'Revisada'),
        ('Resuelta', 'Resuelta'),
    ]
    
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Nueva')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario_relacionado = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    punto_acceso = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.tipo} - {self.fecha_hora}"


class ConfiguracionSistema(models.Model):
    """Configuraciones generales del sistema"""
    periodo_retencion_logs = models.IntegerField(
        default=6,
        help_text="Meses de retención de logs (3, 6, 12 o 0 para indefinido)"
    )
    tiempo_inactividad_minutos = models.IntegerField(default=10)
    max_intentos_fallidos = models.IntegerField(default=3)
    tiempo_bloqueo_minutos = models.IntegerField(default=15)
    modo_emergencia = models.BooleanField(default=False)
    fecha_activacion_emergencia = models.DateTimeField(null=True, blank=True)
    usuario_activacion_emergencia = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencias_activadas'
    )
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
    
    def __str__(self):
        return "Configuración del Sistema"
    
    @classmethod
    def obtener_configuracion(cls):
        """Obtiene o crea la configuración del sistema"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class LogAuditoria(models.Model):
    """Logs de auditoría del sistema"""
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=200)
    modulo = models.CharField(max_length=50)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    detalles = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.accion} - {self.fecha_hora}"

