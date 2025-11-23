# Sistema de Control de Acceso para un Edificio

Sistema completo de control de acceso desarrollado con Django que permite gestionar usuarios, credenciales digitales, registros de entrada/salida, reportes y configuraciones de seguridad.

## Autor
**Santiago Parra**

## Características Principales

- ✅ Registro de visitantes temporales y empleados
- ✅ Generación automática de credenciales digitales
- ✅ Gestión completa de credenciales (crear, modificar, eliminar)
- ✅ Verificación de acceso en tiempo real
- ✅ Registro de entradas y salidas
- ✅ Sistema de roles y permisos
- ✅ Configuración de horarios por rol
- ✅ Configuración de vigencia de credenciales
- ✅ Reportes exportables (PDF, Excel, CSV)
- ✅ Sistema de alertas de seguridad
- ✅ Bloqueo por intentos fallidos
- ✅ Modo de emergencia
- ✅ Logs de auditoría
- ✅ Autenticación y control de acceso por roles

## Requisitos

- Python 3.8 o superior
- Django 5.2.8
- Pillow (para manejo de imágenes)
- reportlab (para generación de PDFs)
- openpyxl (para generación de Excel)

## Instalación

1. **Clonar el repositorio**
```bash
git clone [URL_DEL_REPOSITORIO]
cd CurEdificio
```

2. **Crear y activar entorno virtual**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Realizar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Inicializar el sistema (crear roles y usuario administrador)**
```bash
python manage.py init_system
```

Este comando creará:
- Los roles básicos del sistema
- Un usuario administrador por defecto:
  - Usuario: `admin`
  - Contraseña: `admin123`
  

6. **Ejecutar el servidor de desarrollo**
```bash
python manage.py runserver
```
```

## Uso del Sistema

### Inicio de Sesión

1. Acceda a `http://127.0.0.1:8000/login/`
2. Ingrese las credenciales del administrador:
   - Usuario: `admin`
   - Contraseña: `admin123`

### Funcionalidades Principales

- **Registro de Usuarios**: Visitantes temporales y empleados
- **Gestión de Credenciales**: Crear, modificar, eliminar credenciales
- **Verificación de Acceso**: Escanear credenciales para entrada/salida
- **Reportes**: Ver y exportar reportes de acceso
- **Configuración**: Configurar vigencia, horarios, roles, etc.
- **Seguridad**: Alertas, intentos fallidos, modo de emergencia

## Tecnologías Utilizadas

- **Backend**: Django 5.2.8
- **Base de Datos**: SQLite (desarrollo)
- **Frontend**: HTML, CSS, JavaScript
- **Librerías**: Pillow, reportlab, openpyxl


## Licencia

Este proyecto es de uso educativo.

