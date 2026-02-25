# 🚩 HackArena CTF

**Plataforma web de Capture The Flag (CTF)** desarrollada como Trabajo Fin de Máster para el curso de Hacking Ético en Campus Cámara Sevilla.

Permite a organizadores crear retos de ciberseguridad y a participantes registrarse, resolver challenges y competir en un leaderboard en tiempo real.

---

## ✨ Características

- **Registro y autenticación** de usuarios con perfiles personalizados
- **Retos por categorías**: Web, Crypto, Forensics, Reversing, Pwn, OSINT, Steganography, Networking, Misc
- **Sistema de puntuación** con niveles de dificultad (Fácil, Media, Difícil, Insane)
- **First Blood** 🩸: bonus de puntos al primer usuario que resuelve un reto
- **Equipos**: crear equipo, invitar por código, ranking grupal
- **Pistas (Hints)**: desbloqueo con penalización de puntos
- **Challenges con tiempo límite**: fecha de inicio y fin configurable
- **Leaderboard**: ranking individual y por equipos con desempate temporal
- **Panel de Administración**: gestión completa de retos, categorías, usuarios y logs
- **Registro de intentos**: log de todas las flag submissions (IP, timestamp, resultado)
- **Archivos adjuntos**: soporte para ficheros descargables en los retos
- **Tema oscuro** estilo hacker con diseño responsive

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3 + Flask |
| Base de Datos | MySQL / MariaDB |
| ORM | SQLAlchemy + Flask-Migrate |
| Autenticación | Flask-Login + Werkzeug |
| Frontend | Bootstrap 5 + Bootstrap Icons |
| Servidor | Gunicorn + Nginx |
| SO | Ubuntu Server |

---

## 🚀 Instalación Rápida (Ubuntu Server)

### Opción 1: Script automático

```bash
git clone https://github.com/ByCoffy/CTFArena
cd hackarena-ctf
sudo bash install.sh
```

El script instala todas las dependencias, configura MariaDB, crea la base de datos, y despliega con Gunicorn + Nginx.

### Opción 2: Instalación manual

#### 1. Requisitos previos

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv mariadb-server
```

#### 2. Configurar base de datos

```bash
sudo mysql
```

```sql
CREATE DATABASE ctf_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ctf_user'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON ctf_platform.* TO 'ctf_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. Configurar la aplicación

```bash
git clone https://github.com/tu-usuario/hackarena-ctf.git
cd hackarena-ctf

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Variables de entorno

Edita `config.py` o crea un archivo `.env`:

```env
SECRET_KEY=tu_clave_secreta_muy_larga
DATABASE_URL=mysql+pymysql://ctf_user:tu_contraseña@localhost/ctf_platform
CTF_NAME=HackArena CTF
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@tudominio.com
ADMIN_PASSWORD=TuContraseñaSegura123!
FIRST_BLOOD_BONUS=50
```

#### 5. Inicializar base de datos

```bash
python setup_db.py
```

#### 6. Ejecutar

```bash
# Desarrollo
python run.py

# Producción
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 run:app
```

---

## 📖 Uso

### Para Administradores

1. Inicia sesión con las credenciales de admin
2. Accede al **Panel de Administración** desde la navbar
3. Crea **categorías** para organizar los retos
4. Crea **retos** con: título, descripción, flag, puntos, dificultad, pistas opcionales y tiempo límite
5. Monitoriza los **logs de intentos** para detectar posibles trampas

### Para Participantes

1. **Regístrate** con usuario, email y contraseña
2. Crea o únete a un **equipo** con código de invitación
3. Explora los **retos** por categoría y dificultad
4. Lee la descripción, descarga archivos adjuntos si los hay
5. Envía la **flag** (formato: `FLAG{...}`)
6. Desbloquea **pistas** si te atascas (con penalización de puntos)
7. Compite en el **leaderboard**

---

## 📁 Estructura del Proyecto

```
hackarena-ctf/
├── app/
│   ├── __init__.py          # Factory de la app Flask
│   ├── models.py            # Modelos de base de datos
│   ├── routes.py            # Rutas principales
│   ├── auth/                # Autenticación (login, registro)
│   ├── challenges/          # Gestión de retos y flags
│   ├── teams/               # Sistema de equipos
│   ├── leaderboard/         # Rankings
│   ├── admin/               # Panel de administración
│   ├── static/              # CSS, JS, uploads
│   └── templates/           # Plantillas HTML (Jinja2)
├── config.py                # Configuración
├── run.py                   # Punto de entrada
├── setup_db.py              # Inicialización de BD
├── install.sh               # Script de instalación automática
├── requirements.txt         # Dependencias Python
└── README.md
```

---

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug (PBKDF2 + SHA256)
- Protección contra acceso no autorizado al panel admin
- Registro de IPs y timestamps en todos los intentos de flag
- Validación de inputs en formularios
- Sesiones seguras con Flask-Login

---

## 📜 Licencia

Proyecto académico — TFM de Hacking Ético  
Campus Cámara Sevilla © 2025

---

## 👤 Autor

Desarrollado como Trabajo Fin de Máster del curso de **Hacking Ético** impartido por el profesor **Carlos Basulto Pardo** en **Campus Cámara Sevilla**.
