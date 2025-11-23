from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, datetime
from .models import (
    Usuario, Credencial, Rol, RegistroAcceso, IntentoFallido,
    ConfiguracionVigencia, ConfiguracionHorario, Alerta,
    ConfiguracionSistema, LogAuditoria
)
from .forms import (
    LoginForm, RegistroVisitanteForm, RegistroEmpleadoForm,
    CredencialManualForm, ModificarCredencialForm, ConfiguracionVigenciaForm,
    ConfiguracionHorarioForm, RolForm, ReporteFiltroForm, ConfiguracionSistemaForm
)
from .utils import generar_reporte_pdf, generar_reporte_excel, generar_reporte_csv
import secrets
import string


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Intentar autenticar
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Verificar que el usuario tenga rol
                    try:
                        if not hasattr(user, 'rol') or not user.rol:
                            messages.error(request, 'Su usuario no tiene un rol asignado. Contacte al administrador.')
                            return render(request, 'acceso/login.html', {'form': form})
                        
                        login(request, user)
                        user.ultimo_acceso = timezone.now()
                        user.save()
                        
                        # Verificar que el rol permita acceso
                        if user.rol.nombre not in ['Administrador', 'Seguridad']:
                            logout(request)
                            messages.error(request, 'Acceso denegado. Su rol no tiene permisos para ingresar al sistema.')
                            return render(request, 'acceso/login.html', {'form': form})
                        
                        try:
                            LogAuditoria.objects.create(
                                usuario=user,
                                accion='Inicio de sesión',
                                modulo='Autenticación',
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                        except:
                            pass  # Si falla el log, continuar de todas formas
                        
                        return redirect('dashboard')
                    except Exception as e:
                        messages.error(request, f'Error al iniciar sesión: {str(e)}')
                        return render(request, 'acceso/login.html', {'form': form})
                else:
                    messages.error(request, 'Su cuenta está desactivada.')
            else:
                messages.error(request, 'Credenciales inválidas. Intente nuevamente.')
        else:
            messages.error(request, 'Debe ingresar usuario y contraseña.')
    else:
        form = LoginForm()
    
    return render(request, 'acceso/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    LogAuditoria.objects.create(
        usuario=request.user,
        accion='Cierre de sesión',
        modulo='Autenticación',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    logout(request)
    messages.success(request, 'Ha cerrado sesión correctamente.')
    return redirect('login')


def dashboard(request):
    """Panel principal"""
    # Si no está autenticado, redirigir al login
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Verificar rol
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'Acceso denegado. No tiene permisos para visualizar este módulo.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    # Estadísticas
    total_usuarios = Usuario.objects.filter(activo=True).count()
    total_credenciales_activas = Credencial.objects.filter(estado='Activa').count()
    registros_hoy = RegistroAcceso.objects.filter(
        fecha_hora__date=timezone.now().date()
    ).count()
    alertas_nuevas = Alerta.objects.filter(estado='Nueva').count()
    
    # Últimos registros
    ultimos_registros = RegistroAcceso.objects.all()[:10]
    
    # Alertas recientes
    alertas_recientes = Alerta.objects.filter(estado='Nueva').order_by('-fecha_hora')[:5]
    
    # Configuración del sistema
    configuracion_sistema = ConfiguracionSistema.obtener_configuracion()
    
    context = {
        'total_usuarios': total_usuarios,
        'total_credenciales_activas': total_credenciales_activas,
        'registros_hoy': registros_hoy,
        'alertas_nuevas': alertas_nuevas,
        'ultimos_registros': ultimos_registros,
        'alertas_recientes': alertas_recientes,
        'configuracion_sistema': configuracion_sistema,
    }
    
    return render(request, 'acceso/dashboard.html', context)


@login_required
def registrar_visitante(request):
    """Registro de visitante temporal"""
    if request.method == 'POST':
        form = RegistroVisitanteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Crear usuario
                usuario = form.save(commit=False)
                usuario.username = f"vis_{usuario.numero_identificacion}"
                usuario.set_password(secrets.token_urlsafe(8))  # Contraseña temporal
                
                # Asignar rol de visitante
                rol_visitante = Rol.objects.get_or_create(
                    nombre='Visitante temporal',
                    defaults={'descripcion': 'Visitante temporal del edificio'}
                )[0]
                usuario.rol = rol_visitante
                usuario.save()
                
                # Generar credencial
                codigo = Credencial.generar_codigo(rol_visitante)
                
                # Obtener configuración de vigencia
                config_vigencia = ConfiguracionVigencia.objects.filter(rol=rol_visitante).first()
                fecha_vencimiento = None
                
                if config_vigencia:
                    if config_vigencia.vigencia_horas:
                        fecha_vencimiento = timezone.now() + timedelta(hours=config_vigencia.vigencia_horas)
                    elif config_vigencia.vigencia_dias:
                        fecha_vencimiento = timezone.now() + timedelta(days=config_vigencia.vigencia_dias)
                else:
                    # Por defecto 24 horas
                    fecha_vencimiento = timezone.now() + timedelta(hours=24)
                
                credencial = Credencial.objects.create(
                    codigo=codigo,
                    usuario=usuario,
                    rol=rol_visitante,
                    fecha_vencimiento=fecha_vencimiento
                )
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Registro de visitante: {usuario.get_full_name()}',
                    modulo='Gestión de Usuarios',
                    detalles=f'Credencial generada: {codigo}'
                )
                
                messages.success(request, f'Visitante registrado exitosamente. Credencial generada: {codigo}')
                return redirect('listar_usuarios')
            except Exception as e:
                messages.error(request, f'No se pudo guardar el registro. Verifique la conexión o los datos ingresados. Error: {str(e)}')
    else:
        form = RegistroVisitanteForm()
    
    return render(request, 'acceso/registrar_visitante.html', {'form': form})


@login_required
def registrar_empleado(request):
    """Registro de empleado o personal interno"""
    if request.method == 'POST':
        form = RegistroEmpleadoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                usuario = form.save(commit=False)
                usuario.username = f"emp_{usuario.numero_identificacion}"
                usuario.set_password(secrets.token_urlsafe(12))
                
                # Asignar rol de empleado
                rol_empleado = Rol.objects.get_or_create(
                    nombre='Empleado',
                    defaults={'descripcion': 'Empleado del edificio'}
                )[0]
                usuario.rol = rol_empleado
                usuario.save()
                
                # Generar credencial permanente
                codigo = Credencial.generar_codigo(rol_empleado)
                
                credencial = Credencial.objects.create(
                    codigo=codigo,
                    usuario=usuario,
                    rol=rol_empleado,
                    fecha_vencimiento=None  # Indefinida
                )
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Registro de empleado: {usuario.get_full_name()}',
                    modulo='Gestión de Usuarios',
                    detalles=f'Credencial generada: {codigo}'
                )
                
                messages.success(request, f'Empleado registrado exitosamente. Credencial generada: {codigo}')
                return redirect('listar_usuarios')
            except Exception as e:
                messages.error(request, f'Error al registrar empleado. Verifique la conexión o los datos ingresados. Error: {str(e)}')
    else:
        form = RegistroEmpleadoForm()
    
    return render(request, 'acceso/registrar_empleado.html', {'form': form})


@login_required
def listar_usuarios(request):
    """Lista de usuarios"""
    query = request.GET.get('q', '')
    usuarios = Usuario.objects.all()
    
    if query:
        usuarios = usuarios.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(numero_identificacion__icontains=query)
        )
    
    paginator = Paginator(usuarios, 50)
    page = request.GET.get('page')
    usuarios = paginator.get_page(page)
    
    return render(request, 'acceso/listar_usuarios.html', {'usuarios': usuarios, 'query': query})


@login_required
def asignar_credencial_manual(request):
    """Asignación manual de credenciales"""
    if request.user.rol.nombre != 'Administrador':
        messages.error(request, 'Solo los administradores pueden asignar credenciales manualmente.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CredencialManualForm(request.POST)
        if form.is_valid():
            try:
                nombre_completo = form.cleaned_data['nombre_completo']
                numero_identificacion = form.cleaned_data['numero_identificacion']
                rol = form.cleaned_data['rol']
                codigo_credencial = form.cleaned_data.get('codigo_credencial')
                vigencia_valor = form.cleaned_data['vigencia_valor']
                vigencia_unidad = form.cleaned_data['vigencia_unidad']
                
                # Crear o obtener usuario
                nombres = nombre_completo.split(' ', 1)
                usuario, created = Usuario.objects.get_or_create(
                    numero_identificacion=numero_identificacion,
                    defaults={
                        'first_name': nombres[0] if nombres else nombre_completo,
                        'last_name': nombres[1] if len(nombres) > 1 else '',
                        'username': f"man_{numero_identificacion}",
                        'rol': rol,
                        'contacto': numero_identificacion,
                        'tipo_identificacion': 'CC',
                    }
                )
                
                # Generar código si no se proporcionó
                if not codigo_credencial:
                    codigo_credencial = Credencial.generar_codigo(rol)
                
                # Calcular fecha de vencimiento
                fecha_vencimiento = None
                if vigencia_unidad == 'horas':
                    fecha_vencimiento = timezone.now() + timedelta(hours=vigencia_valor)
                elif vigencia_unidad == 'dias':
                    fecha_vencimiento = timezone.now() + timedelta(days=vigencia_valor)
                
                # Crear credencial
                credencial = Credencial.objects.create(
                    codigo=codigo_credencial,
                    usuario=usuario,
                    rol=rol,
                    fecha_vencimiento=fecha_vencimiento,
                    asignacion_manual=True
                )
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Asignación manual de credencial: {codigo_credencial}',
                    modulo='Gestión de Credenciales',
                    detalles=f'Usuario: {usuario.get_full_name()}'
                )
                
                messages.success(request, 'La credencial ha sido asignada correctamente al usuario.')
                return redirect('listar_credenciales')
            except Exception as e:
                messages.error(request, f'No se pudo guardar la credencial. Intente nuevamente o contacte al soporte. Error: {str(e)}')
    else:
        form = CredencialManualForm()
    
    return render(request, 'acceso/asignar_credencial_manual.html', {'form': form})


@login_required
def listar_credenciales(request):
    """Lista de credenciales"""
    query = request.GET.get('q', '')
    credenciales = Credencial.objects.select_related('usuario', 'rol').all()
    
    if query:
        credenciales = credenciales.filter(
            Q(codigo__icontains=query) |
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query) |
            Q(usuario__numero_identificacion__icontains=query)
        )
    
    paginator = Paginator(credenciales, 50)
    page = request.GET.get('page')
    credenciales = paginator.get_page(page)
    
    return render(request, 'acceso/listar_credenciales.html', {'credenciales': credenciales, 'query': query})


@login_required
def modificar_credencial(request, credencial_id):
    """Modificación de credenciales"""
    credencial = get_object_or_404(Credencial, pk=credencial_id)
    
    if request.method == 'POST':
        form = ModificarCredencialForm(request.POST, instance=credencial)
        if form.is_valid():
            try:
                credencial_modificada = form.save()
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Modificación de credencial: {credencial.codigo}',
                    modulo='Gestión de Credenciales',
                    detalles=f'Rol: {credencial_modificada.rol.nombre}, Estado: {credencial_modificada.estado}'
                )
                
                messages.success(request, 'La credencial se ha modificado correctamente.')
                return redirect('listar_credenciales')
            except Exception as e:
                messages.error(request, f'Error al actualizar los datos. Intente nuevamente. Error: {str(e)}')
    else:
        form = ModificarCredencialForm(instance=credencial)
    
    return render(request, 'acceso/modificar_credencial.html', {'form': form, 'credencial': credencial})


@login_required
def eliminar_credencial(request, credencial_id):
    """Eliminación de credenciales"""
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'No tiene permisos para realizar esta acción.')
        return redirect('listar_credenciales')
    
    credencial = get_object_or_404(Credencial, pk=credencial_id)
    
    if request.method == 'POST':
        try:
            codigo = credencial.codigo
            credencial.delete()
            
            LogAuditoria.objects.create(
                usuario=request.user,
                accion=f'Eliminación de credencial: {codigo}',
                modulo='Gestión de Credenciales'
            )
            
            messages.success(request, 'La credencial ha sido eliminada correctamente.')
            return redirect('listar_credenciales')
        except Exception as e:
            messages.error(request, f'Error al eliminar la credencial. Intente nuevamente. Error: {str(e)}')
    
    return render(request, 'acceso/eliminar_credencial.html', {'credencial': credencial})


@login_required
def verificar_acceso(request):
    """Verificación y registro de acceso"""
    if request.method == 'POST':
        codigo_credencial = request.POST.get('codigo_credencial', '').strip().upper()
        tipo = request.POST.get('tipo', 'Entrada')
        punto_acceso = request.POST.get('punto_acceso', 'Principal')
        
        try:
            credencial = Credencial.objects.select_related('usuario', 'rol').get(codigo=codigo_credencial)
            
            # Verificar estado
            if credencial.estado == 'Inactiva':
                RegistroAcceso.objects.create(
                    credencial=credencial,
                    usuario=credencial.usuario,
                    tipo=tipo,
                    estado='Denegado',
                    punto_acceso=punto_acceso,
                    motivo_denegacion='Credencial inactiva'
                )
                IntentoFallido.objects.create(
                    credencial_codigo=codigo_credencial,
                    usuario=credencial.usuario,
                    punto_acceso=punto_acceso,
                    motivo='Credencial inactiva'
                )
                return JsonResponse({
                    'exito': False,
                    'mensaje': 'Acceso denegado: credencial inactiva.'
                })
            
            # Verificar vencimiento
            if credencial.esta_vencida():
                RegistroAcceso.objects.create(
                    credencial=credencial,
                    usuario=credencial.usuario,
                    tipo=tipo,
                    estado='Denegado',
                    punto_acceso=punto_acceso,
                    motivo_denegacion='Credencial expirada'
                )
                IntentoFallido.objects.create(
                    credencial_codigo=codigo_credencial,
                    usuario=credencial.usuario,
                    punto_acceso=punto_acceso,
                    motivo='Credencial expirada'
                )
                Alerta.objects.create(
                    tipo='Credencial vencida',
                    descripcion=f'Intento de acceso con credencial vencida: {codigo_credencial}',
                    usuario_relacionado=credencial.usuario,
                    punto_acceso=punto_acceso
                )
                return JsonResponse({
                    'exito': False,
                    'mensaje': 'Acceso denegado: credencial expirada.'
                })
            
            # Verificar bloqueo
            if credencial.esta_bloqueada():
                return JsonResponse({
                    'exito': False,
                    'mensaje': 'Credencial bloqueada por intentos fallidos. Intente más tarde o contacte al administrador.'
                })
            
            # Verificar permisos del rol
            if credencial.rol.nombre not in ['Empleado', 'Administrador', 'Seguridad', 'Visitante temporal', 'Proveedor']:
                RegistroAcceso.objects.create(
                    credencial=credencial,
                    usuario=credencial.usuario,
                    tipo=tipo,
                    estado='Denegado',
                    punto_acceso=punto_acceso,
                    motivo_denegacion='Rol no autorizado'
                )
                return JsonResponse({
                    'exito': False,
                    'mensaje': 'Acceso denegado: rol no autorizado.'
                })
            
            # Verificar horarios
            if not verificar_horario(credencial.rol):
                RegistroAcceso.objects.create(
                    credencial=credencial,
                    usuario=credencial.usuario,
                    tipo=tipo,
                    estado='Denegado',
                    punto_acceso=punto_acceso,
                    motivo_denegacion='Fuera del horario permitido'
                )
                Alerta.objects.create(
                    tipo='Fuera de horario',
                    descripcion=f'Intento de acceso fuera de horario: {credencial.usuario.get_full_name()}',
                    usuario_relacionado=credencial.usuario,
                    punto_acceso=punto_acceso
                )
                return JsonResponse({
                    'exito': False,
                    'mensaje': 'Acceso denegado: fuera del horario permitido.'
                })
            
            # Verificar modo de emergencia
            config = ConfiguracionSistema.obtener_configuracion()
            if config.modo_emergencia:
                # En modo emergencia, permitir acceso
                RegistroAcceso.objects.create(
                    credencial=credencial,
                    usuario=credencial.usuario,
                    tipo=tipo,
                    estado='Permitido',
                    punto_acceso=punto_acceso
                )
                return JsonResponse({
                    'exito': True,
                    'mensaje': f'Acceso permitido. Bienvenido {credencial.usuario.get_full_name()}.',
                    'usuario': credencial.usuario.get_full_name()
                })
            
            # Verificar entrada previa para salidas
            if tipo == 'Salida':
                entrada_previa = RegistroAcceso.objects.filter(
                    credencial=credencial,
                    tipo='Entrada',
                    estado='Permitido'
                ).exclude(
                    id__in=RegistroAcceso.objects.filter(
                        credencial=credencial,
                        tipo='Salida',
                        estado='Permitido'
                    ).values_list('id', flat=True)
                ).order_by('-fecha_hora').first()
                
                if not entrada_previa:
                    return JsonResponse({
                        'exito': False,
                        'mensaje': 'No se encontró una sesión activa para esta credencial.'
                    })
            
            # Acceso permitido
            RegistroAcceso.objects.create(
                credencial=credencial,
                usuario=credencial.usuario,
                tipo=tipo,
                estado='Permitido',
                punto_acceso=punto_acceso
            )
            
            # Reiniciar intentos fallidos
            credencial.intentos_fallidos = 0
            credencial.save()
            
            return JsonResponse({
                'exito': True,
                'mensaje': f'Acceso permitido. Bienvenido {credencial.usuario.get_full_name()}.',
                'usuario': credencial.usuario.get_full_name()
            })
            
        except Credencial.DoesNotExist:
            IntentoFallido.objects.create(
                credencial_codigo=codigo_credencial,
                punto_acceso=punto_acceso,
                motivo='Credencial no registrada'
            )
            return JsonResponse({
                'exito': False,
                'mensaje': 'Acceso denegado: credencial no registrada.'
            })
        except Exception as e:
            return JsonResponse({
                'exito': False,
                'mensaje': f'Error en el sistema: {str(e)}'
            })
    
    return render(request, 'acceso/verificar_acceso.html')


def verificar_horario(rol):
    """Verifica si el acceso está dentro del horario permitido"""
    dia_actual = timezone.now().strftime('%A')
    dia_espanol = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    dia = dia_espanol.get(dia_actual, 'Lunes')
    
    horario = ConfiguracionHorario.objects.filter(rol=rol, dia_semana=dia).first()
    
    if not horario:
        # Si no hay horario configurado, permitir acceso
        return True
    
    hora_actual = timezone.now().time()
    
    # Administradores pueden acceder 24/7
    if rol.nombre == 'Administrador':
        return True
    
    return horario.hora_entrada <= hora_actual <= horario.hora_salida


@login_required
def reportes(request):
    """Generación de reportes"""
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'Acceso denegado. No tiene permisos para visualizar este módulo.')
        return redirect('dashboard')
    
    form = ReporteFiltroForm(request.GET or None)
    registros = RegistroAcceso.objects.select_related('usuario', 'credencial', 'credencial__rol').all()
    
    if form.is_valid():
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')
        rol = form.cleaned_data.get('rol')
        tipo = form.cleaned_data.get('tipo')
        estado = form.cleaned_data.get('estado')
        
        if fecha_inicio:
            registros = registros.filter(fecha_hora__date__gte=fecha_inicio)
        if fecha_fin:
            registros = registros.filter(fecha_hora__date__lte=fecha_fin)
        if rol:
            registros = registros.filter(credencial__rol=rol)
        if tipo:
            registros = registros.filter(tipo=tipo)
        if estado:
            registros = registros.filter(estado=estado)
    else:
        # Por defecto, mostrar registros del día actual
        registros = registros.filter(fecha_hora__date=timezone.now().date())
    
    registros = registros.order_by('-fecha_hora')
    
    # Paginación
    paginator = Paginator(registros, 50)
    page = request.GET.get('page')
    registros = paginator.get_page(page)
    
    # Exportación
    formato = request.GET.get('exportar')
    if formato:
        if formato == 'pdf':
            return generar_reporte_pdf(registros)
        elif formato == 'excel':
            return generar_reporte_excel(registros)
        elif formato == 'csv':
            return generar_reporte_csv(registros)
    
    return render(request, 'acceso/reportes.html', {
        'form': form,
        'registros': registros
    })


@login_required
def configurar_vigencia(request):
    """Configuración de vigencia por rol"""
    if request.method == 'POST':
        form = ConfiguracionVigenciaForm(request.POST)
        if form.is_valid():
            try:
                rol = form.cleaned_data['rol']
                vigencia_valor = form.cleaned_data.get('vigencia_valor')
                vigencia_unidad = form.cleaned_data['vigencia_unidad']
                
                config, created = ConfiguracionVigencia.objects.get_or_create(rol=rol)
                
                if vigencia_unidad == 'indefinida':
                    config.vigencia_horas = None
                    config.vigencia_dias = None
                elif vigencia_unidad == 'horas':
                    config.vigencia_horas = vigencia_valor
                    config.vigencia_dias = None
                elif vigencia_unidad == 'dias':
                    config.vigencia_dias = vigencia_valor
                    config.vigencia_horas = None
                
                config.usuario_modificacion = request.user
                config.save()
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Configuración de vigencia para rol: {rol.nombre}',
                    modulo='Configuración'
                )
                
                messages.success(request, f'La vigencia para el rol {rol.nombre} ha sido actualizada correctamente.')
                return redirect('configurar_vigencia')
            except Exception as e:
                messages.error(request, f'Error al guardar los cambios. Verifique los datos o la conexión. Error: {str(e)}')
    else:
        form = ConfiguracionVigenciaForm()
    
    configuraciones = ConfiguracionVigencia.objects.select_related('rol', 'usuario_modificacion').all()
    
    return render(request, 'acceso/configurar_vigencia.html', {
        'form': form,
        'configuraciones': configuraciones
    })


@login_required
def configurar_horarios(request):
    """Configuración de horarios de acceso"""
    if request.method == 'POST':
        form = ConfiguracionHorarioForm(request.POST)
        if form.is_valid():
            try:
                horario = form.save(commit=False)
                horario.usuario_modificacion = request.user
                horario.save()
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Configuración de horario: {horario.rol.nombre} - {horario.dia_semana}',
                    modulo='Configuración'
                )
                
                messages.success(request, 'Horario de acceso actualizado correctamente.')
                return redirect('configurar_horarios')
            except Exception as e:
                messages.error(request, f'No se pudo guardar la configuración. Intente nuevamente. Error: {str(e)}')
    else:
        form = ConfiguracionHorarioForm()
    
    horarios = ConfiguracionHorario.objects.select_related('rol', 'usuario_modificacion').all()
    
    return render(request, 'acceso/configurar_horarios.html', {
        'form': form,
        'horarios': horarios
    })


@login_required
def gestionar_roles(request):
    """Gestión de roles"""
    if request.user.rol.nombre != 'Administrador':
        messages.error(request, 'Solo los administradores pueden gestionar roles.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            try:
                rol = form.save()
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion=f'Creación de rol: {rol.nombre}',
                    modulo='Gestión de Roles'
                )
                
                messages.success(request, 'El rol ha sido guardado correctamente.')
                return redirect('gestionar_roles')
            except Exception as e:
                if 'unique' in str(e).lower():
                    messages.error(request, 'El rol ingresado ya existe en el sistema.')
                else:
                    messages.error(request, f'Error al guardar los cambios. Intente nuevamente. Error: {str(e)}')
    else:
        form = RolForm()
    
    roles = Rol.objects.all()
    
    return render(request, 'acceso/gestionar_roles.html', {
        'form': form,
        'roles': roles
    })


@login_required
def eliminar_rol(request, rol_id):
    """Eliminación de roles"""
    if request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tiene permisos para realizar esta acción.')
        return redirect('gestionar_roles')
    
    rol = get_object_or_404(Rol, pk=rol_id)
    
    if request.method == 'POST':
        # Verificar si tiene credenciales asociadas
        if Credencial.objects.filter(rol=rol).exists():
            messages.error(request, 'No es posible eliminar este rol, tiene credenciales asociadas.')
            return redirect('gestionar_roles')
        
        try:
            nombre = rol.nombre
            rol.delete()
            
            LogAuditoria.objects.create(
                usuario=request.user,
                accion=f'Eliminación de rol: {nombre}',
                modulo='Gestión de Roles'
            )
            
            messages.success(request, 'El rol ha sido eliminado correctamente.')
            return redirect('gestionar_roles')
        except Exception as e:
            messages.error(request, f'Error al eliminar el rol. Error: {str(e)}')
    
    return render(request, 'acceso/eliminar_rol.html', {'rol': rol})


@login_required
def alertas(request):
    """Módulo de alertas"""
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'Acceso denegado. No tiene permisos para visualizar este módulo.')
        return redirect('dashboard')
    
    estado = request.GET.get('estado', 'Nueva')
    alertas_list = Alerta.objects.select_related('usuario_relacionado').filter(estado=estado).order_by('-fecha_hora')
    
    paginator = Paginator(alertas_list, 50)
    page = request.GET.get('page')
    alertas_list = paginator.get_page(page)
    
    return render(request, 'acceso/alertas.html', {
        'alertas': alertas_list,
        'estado_actual': estado
    })


@login_required
def marcar_alerta(request, alerta_id):
    """Marcar alerta como revisada o resuelta"""
    alerta = get_object_or_404(Alerta, pk=alerta_id)
    accion = request.GET.get('accion', 'revisada')
    
    if accion == 'revisada':
        alerta.estado = 'Revisada'
    elif accion == 'resuelta':
        alerta.estado = 'Resuelta'
    
    alerta.save()
    messages.success(request, 'Alerta actualizada correctamente.')
    return redirect('alertas')


@login_required
def modo_emergencia(request):
    """Activación/desactivación de modo de emergencia"""
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'No tiene permisos para realizar esta acción.')
        return redirect('dashboard')
    
    config = ConfiguracionSistema.obtener_configuracion()
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'activar':
            if request.user.rol.nombre != 'Administrador':
                messages.error(request, 'Solo los administradores pueden activar el modo de emergencia.')
                return redirect('dashboard')
            
            config.modo_emergencia = True
            config.fecha_activacion_emergencia = timezone.now()
            config.usuario_activacion_emergencia = request.user
            config.save()
            
            LogAuditoria.objects.create(
                usuario=request.user,
                accion='Activación de modo de emergencia',
                modulo='Seguridad'
            )
            
            messages.warning(request, 'MODO DE EMERGENCIA ACTIVADO – TODAS LAS PUERTAS DESBLOQUEADAS.')
            
        elif accion == 'desactivar':
            if request.user.rol.nombre != 'Administrador':
                messages.error(request, 'Solo los administradores pueden desactivar el modo de emergencia.')
                return redirect('dashboard')
            
            config.modo_emergencia = False
            config.save()
            
            LogAuditoria.objects.create(
                usuario=request.user,
                accion='Desactivación de modo de emergencia',
                modulo='Seguridad'
            )
            
            messages.success(request, 'Modo de emergencia desactivado. Sistema operativo normal.')
        
        return redirect('dashboard')
    
    return render(request, 'acceso/modo_emergencia.html', {'config': config})


@login_required
def configuracion_sistema(request):
    """Configuración general del sistema"""
    if request.user.rol.nombre != 'Administrador':
        messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
        return redirect('dashboard')
    
    config = ConfiguracionSistema.obtener_configuracion()
    
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST, instance=config)
        if form.is_valid():
            try:
                form.save()
                
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion='Actualización de configuración del sistema',
                    modulo='Configuración'
                )
                
                messages.success(request, 'Configuración actualizada correctamente.')
                return redirect('configuracion_sistema')
            except Exception as e:
                messages.error(request, f'Error al guardar la configuración. Error: {str(e)}')
    else:
        form = ConfiguracionSistemaForm(instance=config)
    
    return render(request, 'acceso/configuracion_sistema.html', {'form': form, 'config': config})


@login_required
def intentos_fallidos(request):
    """Visualización de intentos fallidos"""
    if request.user.rol.nombre not in ['Administrador', 'Seguridad']:
        messages.error(request, 'Acceso denegado. No tiene permisos para visualizar este módulo.')
        return redirect('dashboard')
    
    intentos = IntentoFallido.objects.select_related('usuario').all().order_by('-fecha_hora')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio:
        intentos = intentos.filter(fecha_hora__date__gte=fecha_inicio)
    if fecha_fin:
        intentos = intentos.filter(fecha_hora__date__lte=fecha_fin)
    
    paginator = Paginator(intentos, 50)
    page = request.GET.get('page')
    intentos = paginator.get_page(page)
    
    return render(request, 'acceso/intentos_fallidos.html', {'intentos': intentos})

