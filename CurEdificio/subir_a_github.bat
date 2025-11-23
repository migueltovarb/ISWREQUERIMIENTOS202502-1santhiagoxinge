@echo off
echo ========================================
echo Subir Proyecto a GitHub del Profesor
echo ========================================
echo.

cd /d "%~dp0"

echo Paso 1: Inicializando Git...
git init

echo.
echo Paso 2: Agregando archivos...
git add .

echo.
echo Paso 3: Haciendo commit...
git commit -m "Sistema de Control de Acceso - Santiago Parra"

echo.
echo ========================================
echo IMPORTANTE: Necesitas agregar el remoto
echo ========================================
echo.
echo Ejecuta este comando (reemplaza URL_DEL_PROFESOR):
echo.
echo git remote add origin URL_DEL_PROFESOR
echo.
echo Luego ejecuta:
echo.
echo git push -u origin main
echo.
echo O si la rama es master:
echo.
echo git push -u origin master
echo.
pause

