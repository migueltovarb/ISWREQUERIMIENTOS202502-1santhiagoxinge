from django.core.management.base import BaseCommand
from acceso.models import Rol, Usuario, ConfiguracionSistema
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Inicializa el sistema creando roles básicos y usuario administrador'

    def handle(self, *args, **options):
        # Crear roles básicos
        roles_data = [
            {'nombre': 'Administrador', 'descripcion': 'Administrador del sistema con acceso completo', 'nivel_acceso': 'Alto'},
            {'nombre': 'Seguridad', 'descripcion': 'Personal de seguridad', 'nivel_acceso': 'Alto'},
            {'nombre': 'Empleado', 'descripcion': 'Empleado del edificio', 'nivel_acceso': 'Medio'},
            {'nombre': 'Personal interno', 'descripcion': 'Personal interno del edificio', 'nivel_acceso': 'Medio'},
            {'nombre': 'Visitante temporal', 'descripcion': 'Visitante temporal del edificio', 'nivel_acceso': 'Bajo'},
            {'nombre': 'Visitante', 'descripcion': 'Visitante del edificio', 'nivel_acceso': 'Bajo'},
            {'nombre': 'Proveedor', 'descripcion': 'Proveedor o personal externo', 'nivel_acceso': 'Bajo'},
            {'nombre': 'Personal externo', 'descripcion': 'Personal externo', 'nivel_acceso': 'Bajo'},
        ]
        
        for rol_data in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults=rol_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol creado: {rol.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'Rol ya existe: {rol.nombre}'))
        
        # Crear configuración del sistema
        config, created = ConfiguracionSistema.objects.get_or_create(pk=1)
        if created:
            self.stdout.write(self.style.SUCCESS('Configuración del sistema creada'))
        
        # Crear usuario administrador si no existe
        if not Usuario.objects.filter(username='admin').exists():
            rol_admin = Rol.objects.get(nombre='Administrador')
            admin = Usuario.objects.create_user(
                username='admin',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                numero_identificacion='1234567890',
                tipo_identificacion='CC',
                rol=rol_admin,
                contacto='admin@sistema.com',
                correo_institucional='admin@organizacion.com',
                cargo_dependencia='Administrador del Sistema',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado'))
            self.stdout.write(self.style.WARNING('Usuario: admin'))
            self.stdout.write(self.style.WARNING('Contraseña: admin123'))
            self.stdout.write(self.style.WARNING('¡IMPORTANTE: Cambie la contraseña después del primer inicio de sesión!'))
        else:
            self.stdout.write(self.style.WARNING('Usuario administrador ya existe'))
        
        self.stdout.write(self.style.SUCCESS('Sistema inicializado correctamente'))




