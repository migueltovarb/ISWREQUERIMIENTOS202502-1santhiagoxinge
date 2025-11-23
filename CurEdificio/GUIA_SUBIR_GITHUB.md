# Guía para Subir el Proyecto a GitHub del Profesor

## 📋 Pasos a Seguir

### 1. Obtener la URL del Repositorio del Profesor

Necesitas la URL del repositorio. Puede ser:
- `https://github.com/usuario/nombre-repo.git`
- `git@github.com:usuario/nombre-repo.git`

### 2. Inicializar Git (si no está inicializado)

```bash
git init
```

### 3. Agregar el Repositorio Remoto del Profesor

```bash
git remote add origin [URL_DEL_REPOSITORIO_DEL_PROFESOR]
```

**Ejemplo:**
```bash
git remote add origin https://github.com/profesor/proyecto-final.git
```

### 4. Verificar que se agregó correctamente

```bash
git remote -v
```

Deberías ver algo como:
```
origin  https://github.com/profesor/proyecto-final.git (fetch)
origin  https://github.com/profesor/proyecto-final.git (push)
```

### 5. Agregar todos los archivos al staging

```bash
git add .
```

### 6. Hacer el primer commit

```bash
git commit -m "Sistema de Control de Acceso - Santiago Parra"
```

### 7. Subir al repositorio del profesor

**Si es la primera vez:**
```bash
git push -u origin main
```

**O si la rama se llama `master`:**
```bash
git push -u origin master
```

**Si el profesor ya tiene contenido y necesitas hacer merge:**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## ⚠️ Importante

- **NO subas** la carpeta `venv/` (ya está en .gitignore)
- **NO subas** `db.sqlite3` (ya está en .gitignore)
- **NO subas** archivos temporales

## 🔐 Si te pide autenticación

Si GitHub te pide usuario y contraseña:
1. Usa tu **Personal Access Token** (no tu contraseña)
2. O configura SSH keys

## 📝 Comandos Rápidos (Copia y Pega)

```bash
# 1. Inicializar
git init

# 2. Agregar remoto (REEMPLAZA CON LA URL DEL PROFESOR)
git remote add origin [URL_AQUI]

# 3. Agregar archivos
git add .

# 4. Commit
git commit -m "Sistema de Control de Acceso - Santiago Parra"

# 5. Subir
git push -u origin main
```

