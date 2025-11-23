from django import forms
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import (
    Usuario, Credencial, Rol, ConfiguracionVigencia,
    ConfiguracionHorario, ConfiguracionSistema
)
import re


class LoginForm(forms.Form):
    """Formulario de inicio de sesión"""
    username = forms.CharField(
        label='Usuario o correo electrónico',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario o correo'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )


class RegistroVisitanteForm(forms.ModelForm):
    """Formulario para registro de visitante temporal"""
    motivo_ingreso = forms.CharField(
        label='Motivo de ingreso',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'tipo_identificacion',
            'numero_identificacion', 'contacto', 'fotografia', 'motivo_ingreso'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'fotografia': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'tipo_identificacion': 'Tipo de identificación',
            'numero_identificacion': 'Número de identificación',
            'contacto': 'Contacto (teléfono o correo)',
            'fotografia': 'Fotografía (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_identificacion'].choices = [
            ('CC', 'Cédula de Ciudadanía'),
            ('TI', 'Tarjeta de Identidad'),
            ('Otro', 'Otro'),
        ]
    
    def clean_numero_identificacion(self):
        numero = self.cleaned_data.get('numero_identificacion')
        if Usuario.objects.filter(numero_identificacion=numero).exists():
            raise ValidationError('Este número de identificación ya está registrado.')
        return numero
    
    def clean_contacto(self):
        contacto = self.cleaned_data.get('contacto')
        # Validar si es email o teléfono
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        telefono_pattern = r'^[0-9+\-\s()]+$'
        
        if not (re.match(email_pattern, contacto) or re.match(telefono_pattern, contacto)):
            raise ValidationError('El contacto debe ser un correo electrónico válido o un número telefónico.')
        return contacto
    
    def clean_fotografia(self):
        foto = self.cleaned_data.get('fotografia')
        if foto:
            if foto.size > 5 * 1024 * 1024:  # 5 MB
                raise ValidationError('La imagen no puede superar los 5 MB.')
            if not foto.content_type in ['image/jpeg', 'image/png', 'image/gif']:
                raise ValidationError('Solo se permiten formatos JPG, PNG o GIF.')
        return foto


class RegistroEmpleadoForm(forms.ModelForm):
    """Formulario para registro de empleado"""
    cargo_dependencia = forms.CharField(
        label='Cargo o dependencia',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    correo_institucional = forms.EmailField(
        label='Correo institucional',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'tipo_identificacion',
            'numero_identificacion', 'contacto', 'correo_institucional',
            'cargo_dependencia', 'fotografia'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_institucional': forms.EmailInput(attrs={'class': 'form-control'}),
            'cargo_dependencia': forms.TextInput(attrs={'class': 'form-control'}),
            'fotografia': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/gif'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_identificacion'].choices = [
            ('CC', 'Cédula de Ciudadanía'),
            ('Otro', 'Otro'),
        ]
    
    def clean_numero_identificacion(self):
        numero = self.cleaned_data.get('numero_identificacion')
        if self.instance.pk:
            if Usuario.objects.filter(numero_identificacion=numero).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este número de identificación ya está registrado.')
        else:
            if Usuario.objects.filter(numero_identificacion=numero).exists():
                raise ValidationError('Este número de identificación ya está registrado.')
        return numero
    
    def clean_correo_institucional(self):
        correo = self.cleaned_data.get('correo_institucional')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            raise ValidationError('El correo institucional debe seguir el formato: nombre.apellido@organizacion.com')
        return correo
    
    def clean_fotografia(self):
        foto = self.cleaned_data.get('fotografia')
        if foto:
            if foto.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede superar los 5 MB.')
            if not foto.content_type in ['image/jpeg', 'image/png', 'image/gif']:
                raise ValidationError('Solo se permiten formatos JPG, PNG o GIF.')
        return foto


class CredencialManualForm(forms.ModelForm):
    """Formulario para asignación manual de credenciales"""
    nombre_completo = forms.CharField(
        label='Nombre completo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
        required=True
    )
    numero_identificacion = forms.CharField(
        label='Número de identificación',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    codigo_credencial = forms.CharField(
        label='Código de credencial (opcional)',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        max_length=10,
        min_length=6
    )
    vigencia_valor = forms.IntegerField(
        label='Vigencia',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        required=True
    )
    vigencia_unidad = forms.ChoiceField(
        label='Unidad',
        choices=[('horas', 'Horas'), ('dias', 'Días')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = Credencial
        fields = ['rol']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_codigo_credencial(self):
        codigo = self.cleaned_data.get('codigo_credencial')
        if codigo:
            if len(codigo) < 6 or len(codigo) > 10:
                raise ValidationError('El código debe tener entre 6 y 10 caracteres.')
            if not re.match(r'^[A-Za-z0-9]+$', codigo):
                raise ValidationError('El código solo puede contener letras y números.')
            if Credencial.objects.filter(codigo=codigo.upper()).exists():
                raise ValidationError('El código de credencial ingresado ya está asignado. Intente con otro.')
        return codigo.upper() if codigo else None
    
    def clean_vigencia_valor(self):
        valor = self.cleaned_data.get('vigencia_valor')
        if valor > 365:
            raise ValidationError('El valor de vigencia excede el máximo permitido (365 días).')
        return valor


class ModificarCredencialForm(forms.ModelForm):
    """Formulario para modificar credenciales"""
    class Meta:
        model = Credencial
        fields = ['rol', 'estado']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }


class ConfiguracionVigenciaForm(forms.ModelForm):
    """Formulario para configurar vigencia por rol"""
    vigencia_valor = forms.IntegerField(
        label='Vigencia',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        required=False
    )
    vigencia_unidad = forms.ChoiceField(
        label='Unidad',
        choices=[('horas', 'Horas'), ('dias', 'Días'), ('indefinida', 'Indefinida')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = ConfiguracionVigencia
        fields = ['rol']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_vigencia_valor(self):
        unidad = self.cleaned_data.get('vigencia_unidad')
        valor = self.cleaned_data.get('vigencia_valor')
        
        if unidad == 'indefinida':
            return None
        
        if not valor:
            raise ValidationError('Debe ingresar un valor de vigencia.')
        
        if unidad == 'dias' and valor > 365:
            raise ValidationError('La vigencia no puede exceder 365 días.')
        
        if unidad == 'horas' and valor > 8760:  # 365 días en horas
            raise ValidationError('La vigencia no puede exceder 8760 horas (365 días).')
        
        return valor


class ConfiguracionHorarioForm(forms.ModelForm):
    """Formulario para configurar horarios de acceso"""
    class Meta:
        model = ConfiguracionHorario
        fields = ['rol', 'dia_semana', 'hora_entrada', 'hora_salida']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
            'hora_entrada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_salida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        hora_entrada = cleaned_data.get('hora_entrada')
        hora_salida = cleaned_data.get('hora_salida')
        
        if hora_entrada and hora_salida:
            if hora_salida <= hora_entrada:
                raise ValidationError('La hora de salida debe ser mayor que la de entrada.')
        
        return cleaned_data


class RolForm(forms.ModelForm):
    """Formulario para gestión de roles"""
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'nivel_acceso']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 200}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-control'}),
        }


class ReporteFiltroForm(forms.Form):
    """Formulario de filtros para reportes"""
    fecha_inicio = forms.DateField(
        label='Fecha inicio',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    fecha_fin = forms.DateField(
        label='Fecha fin',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    rol = forms.ModelChoiceField(
        label='Rol',
        queryset=Rol.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo = forms.ChoiceField(
        label='Tipo',
        choices=[('', 'Todos'), ('Entrada', 'Entrada'), ('Salida', 'Salida')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', 'Todos'), ('Permitido', 'Permitido'), ('Denegado', 'Denegado')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ConfiguracionSistemaForm(forms.ModelForm):
    """Formulario para configuración del sistema"""
    class Meta:
        model = ConfiguracionSistema
        fields = [
            'periodo_retencion_logs',
            'tiempo_inactividad_minutos',
            'max_intentos_fallidos',
            'tiempo_bloqueo_minutos'
        ]
        widgets = {
            'periodo_retencion_logs': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tiempo_inactividad_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 30}),
            'max_intentos_fallidos': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'tiempo_bloqueo_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

