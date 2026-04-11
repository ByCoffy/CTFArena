# 🚩 HackArena CTF

**Plataforma web de Capture The Flag (CTF)** desarrollada como Trabajo Fin de Máster para el curso de Hacking Ético en Campus Cámara Sevilla.

Permite a organizadores crear retos de ciberseguridad y a participantes registrarse, resolver challenges y competir en un leaderboard en tiempo real. Incluye soporte para **retos Docker interactivos** con terminal web en tiempo real.

---

## ✨ Características

- **Registro y autenticación** de usuarios con perfiles personalizados
- **Retos por categorías**: Web, Crypto, Forensics, Reversing, Pwn, OSINT, Steganography, Networking, Misc
- **Sistema de puntuación** con niveles de dificultad (Fácil, Media, Difícil, Insane)
- **First Blood** 🩸: bonus de puntos al primer usuario que resuelve un reto
- **Equipos**: crear equipo, invitar por código, ranking grupal
- **Pistas (Hints)**: desbloqueo con penalización de puntos
- **Challenges con tiempo límite**: fecha de inicio y fin configurable
- **Retos Docker interactivos**: contenedores aislados por usuario con terminal xterm.js en tiempo real vía WebSocket
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
| WebSockets | Flask-SocketIO + eventlet |
| Contenedores | Docker CE (API Python) |
| Terminal web | xterm.js 5.5.0 |
| Base de Datos | MySQL / MariaDB |
| ORM | SQLAlchemy + Flask-Migrate |
| Autenticación | Flask-Login + Werkzeug |
| Frontend | Bootstrap 5 + Bootstrap Icons |
| Servidor | Gunicorn (eventlet) + Nginx |
| SO | Ubuntu Server / Debian / Kali Linux |

---

## 🚀 Instalación Rápida

### Opción 1: Script automático

```bash
git clone https://github.com/tu-usuario/hackarena-ctf.git
cd hackarena-ctf
sudo bash install.sh
```

El script instala todas las dependencias (MariaDB, Nginx, Docker CE), configura la base de datos, construye las imágenes Docker de retos incluidos, y despliega con Gunicorn + Nginx + WebSocket.

> **Nota Kali Linux**: El script detecta automáticamente Kali y usa el repositorio Debian `bookworm` para instalar Docker CE.

### Opción 2: Instalación manual

#### 1. Requisitos previos

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv mariadb-server gcc
```

#### 2. Instalar Docker CE

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker
```

**Kali Linux** (no reconocido por Docker, usar repo bookworm):
```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker && sudo systemctl start docker
```

#### 3. Configurar base de datos

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

#### 4. Configurar la aplicación

```bash
git clone https://github.com/tu-usuario/hackarena-ctf.git
cd hackarena-ctf

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn eventlet
```

#### 5. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu_clave_secreta_muy_larga
DATABASE_URL=mysql+pymysql://ctf_user:tu_contraseña@localhost/ctf_platform
CTF_NAME=HackArena CTF
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@tudominio.com
ADMIN_PASSWORD=TuContraseñaSegura123!
FIRST_BLOOD_BONUS=50
```

#### 6. Inicializar base de datos

```bash
python setup_db.py
```

#### 7. Construir imágenes Docker de retos

```bash
# Construir los retos incluidos
cd docker_challenges
sudo bash build.sh

# O manualmente uno a uno:
sudo docker build -t ctfarena/sqli-lab:latest ./sqli-lab/
sudo docker build -t ctfarena/privesc:latest ./privesc/
```

#### 8. Ejecutar

```bash
# Desarrollo (con WebSocket)
python run.py

# Producción (eventlet obligatorio para WebSocket)
gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 run:app
```

> **Importante**: Para WebSocket se necesita `-k eventlet -w 1` (un solo worker con eventlet). No usar múltiples workers.

---

## 🐳 Retos Docker Interactivos

### Cómo funcionan

Los retos Docker crean un contenedor aislado por usuario con un terminal interactivo en el navegador. Cada usuario recibe su propia instancia con límite de tiempo, memoria y CPU.

### Retos incluidos

| Reto | Imagen | Dificultad | Descripción |
|---|---|---|---|
| SQL Injection Lab | `ctfarena/sqli-lab:latest` | Fácil | Explotar inyección SQL en una tienda web |
| Privilege Escalation | `ctfarena/privesc:latest` | Media | Escalar privilegios abusando de un binario SUID |

### Crear tu propio reto Docker

#### 1. Crear la estructura del reto

```
docker_challenges/mi-reto/
├── Dockerfile
├── mi_app.py          # (opcional) aplicación vulnerable
└── archivos_extra/    # (opcional) archivos necesarios
```

#### 2. Escribir el Dockerfile

Reglas importantes:
- Crear un usuario no privilegiado (`ctfuser`) — los participantes entran como este usuario
- Colocar la flag en un lugar que requiera explotar la vulnerabilidad
- El contenedor debe tener `/bin/bash` disponible (la terminal se conecta a bash)
- Instalar solo lo necesario para el reto

**Ejemplo — Reto de inyección de comandos:**

```dockerfile
FROM python:3.11-slim

# Instalar herramientas necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN useradd -m -s /bin/bash ctfuser

WORKDIR /app

# Copiar la aplicación vulnerable
COPY app.py /app/app.py

# Colocar la flag (solo legible resolviendo el reto)
RUN echo "FLAG{mi_flag_personalizada}" > /root/flag.txt && \
    chmod 600 /root/flag.txt

# Pista para el usuario
RUN echo "Bienvenido al reto. Encuentra la flag en /root/flag.txt" > /home/ctfuser/README.txt && \
    chown ctfuser:ctfuser /home/ctfuser/README.txt

USER ctfuser
WORKDIR /home/ctfuser

CMD ["/bin/bash"]
```

**Ejemplo — Reto web con servidor interno:**

```dockerfile
FROM python:3.11-slim

RUN useradd -m -s /bin/bash ctfuser
WORKDIR /app

COPY app.py /app/app.py
COPY setup_db.py /app/setup_db.py

RUN pip install --no-cache-dir flask
RUN python setup_db.py

# La flag está en la base de datos, hay que explotar SQLi para llegar
RUN chown -R ctfuser:ctfuser /app

USER ctfuser
EXPOSE 80
CMD ["python", "/app/app.py"]
```

#### 3. Construir la imagen

```bash
sudo docker build -t ctfarena/mi-reto:latest ./docker_challenges/mi-reto/
```

#### 4. Registrar el reto en HackArena

1. Entra al **Panel de Administración** → **Challenges** → **Crear Challenge**
2. Rellena los campos:
   - **Título**: nombre del reto
   - **Descripción**: contexto y pistas para el participante
   - **Flag**: la flag exacta (ej: `FLAG{mi_flag_personalizada}`)
   - **Tipo**: `docker`
   - **Imagen Docker**: `ctfarena/mi-reto:latest`
   - **Timeout** (minutos): tiempo máximo por instancia (default: 30)
   - **Memoria**: límite RAM (ej: `256m`, `512m`)
   - **CPU**: límite CPU (ej: `0.5` = medio core)
   - **Puertos** (JSON, opcional): `{"80": "http", "22": "ssh"}` si el reto expone servicios
3. **Guardar** y probar iniciando una instancia

#### 5. Verificar que funciona

```bash
# Ver imágenes disponibles
sudo docker images | grep ctfarena

# Probar el contenedor manualmente
sudo docker run --rm -it ctfarena/mi-reto:latest

# Dentro del contenedor, simular resolver el reto
```

### Consejos para crear buenos retos

- **No pongas la flag en texto plano accesible** — debe requerir explotar algo
- **Incluye un README.txt** con pistas en el home del usuario
- **Pruébalo antes**: ejecuta `docker run --rm -it tu-imagen` y resuelve el reto tú mismo
- **Limita las herramientas**: no instales `curl`, `wget`, etc. si no son necesarios
- **Usa permisos**: `chmod 600` en archivos sensibles, SUID en binarios vulnerables
- **Mantén las imágenes pequeñas**: usa `-slim` o `alpine` como base

---

## 🖥️ Configuración de Producción

### Nginx con WebSocket

El archivo de Nginx debe incluir soporte para WebSocket (el terminal interactivo lo necesita):

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket para terminal interactivo
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    location /static {
        alias /opt/hackarena-ctf/app/static;
        expires 1d;
    }
}
```

### Servicio systemd

```ini
[Unit]
Description=HackArena CTF Platform
After=network.target mariadb.service docker.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/hackarena-ctf
Environment="PATH=/opt/hackarena-ctf/venv/bin"
EnvironmentFile=/opt/hackarena-ctf/.env
ExecStart=/opt/hackarena-ctf/venv/bin/gunicorn -k eventlet -w 1 --bind 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

> El usuario `www-data` debe estar en el grupo `docker`: `sudo usermod -aG docker www-data`

---

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug (PBKDF2 + SHA256)
- Contenedores Docker aislados con `no-new-privileges`, límites de memoria/CPU/PIDs
- Protección contra acceso no autorizado al panel admin
- Registro de IPs y timestamps en todos los intentos de flag
- Validación de inputs en formularios
- Sesiones seguras con Flask-Login
- Red Docker `internal: true` (sin acceso a Internet desde los contenedores)

---

## 📖 Uso

### Para Administradores

1. Inicia sesión con las credenciales de admin
2. Accede al **Panel de Administración** desde la navbar
3. Crea **categorías** para organizar los retos
4. Crea **retos estáticos** con: título, descripción, flag, puntos, dificultad
5. Crea **retos Docker** seleccionando tipo `docker`, indicando la imagen y límites
6. Monitoriza los **logs de intentos** para detectar posibles trampas

### Para Participantes

1. **Regístrate** con usuario, email y contraseña
2. Crea o únete a un **equipo** con código de invitación
3. Explora los **retos** por categoría y dificultad
4. Para retos Docker: pulsa **Iniciar Reto** → usa la terminal interactiva → encuentra la flag
5. Envía la **flag** (formato: `FLAG{...}`)
6. Desbloquea **pistas** si te atascas (con penalización de puntos)
7. Compite en el **leaderboard**

---

## 📁 Estructura del Proyecto

```
hackarena-ctf/
├── app/
│   ├── __init__.py              # Factory de la app Flask + SocketIO
│   ├── models.py                # Modelos SQLAlchemy
│   ├── routes.py                # Rutas principales
│   ├── auth/                    # Autenticación (login, registro)
│   ├── challenges/              # Gestión de retos y flags
│   ├── docker_challenges/       # Blueprint Docker
│   │   ├── routes.py            # Start/stop/restart contenedores
│   │   └── events.py            # WebSocket terminal I/O
│   ├── services/
│   │   └── docker_service.py    # API Docker (crear, parar, exec)
│   ├── teams/                   # Sistema de equipos
│   ├── leaderboard/             # Rankings
│   ├── admin/                   # Panel de administración
│   ├── static/                  # CSS, uploads
│   └── templates/               # Plantillas Jinja2
├── docker_challenges/           # Dockerfiles de retos incluidos
│   ├── build.sh                 # Construir todas las imágenes
│   ├── sqli-lab/                # Reto SQL Injection
│   └── privesc/                 # Reto Privilege Escalation
├── config.py
├── run.py
├── setup_db.py
├── install.sh
├── requirements.txt
└── README.md
```

---

## 📜 Licencia

Proyecto académico — TFM de Hacking Ético  
Campus Cámara Sevilla © 2025

---

## 👤 Autor

Desarrollado como Trabajo Fin de Máster del curso de **Hacking Ético** impartido por el profesor **Carlos Basulto Pardo** en **Campus Cámara Sevilla**.
