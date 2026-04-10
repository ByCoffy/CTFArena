# 🚩 HackArena CTF — Documentación Técnica (Ingeniería Inversa)

> Documentación generada mediante ingeniería inversa completa del código fuente de la plataforma HackArena CTF.

---

## 📋 Índice

1. [Visión General](#1-visión-general)
2. [Arquitectura de la Aplicación](#2-arquitectura-de-la-aplicación)
3. [Esquema de Base de Datos](#3-esquema-de-base-de-datos)
4. [Sistema de Autenticación y Autorización](#4-sistema-de-autenticación-y-autorización)
5. [Mapa Completo de Rutas (API)](#5-mapa-completo-de-rutas-api)
6. [Sistema de Puntuación](#6-sistema-de-puntuación)
7. [Sistema de Equipos](#7-sistema-de-equipos)
8. [Sistema de Retos (Challenges)](#8-sistema-de-retos-challenges)
9. [Panel de Administración](#9-panel-de-administración)
10. [Configuración](#10-configuración)
11. [Frontend y Plantillas](#11-frontend-y-plantillas)
12. [Seguridad](#12-seguridad)
13. [Despliegue](#13-despliegue)
14. [Estructura de Archivos](#14-estructura-de-archivos)

---

## 1. Visión General

**HackArena CTF** es una plataforma web de Capture The Flag (CTF) desarrollada con Python/Flask. Permite a organizadores crear retos de ciberseguridad categorizados y a participantes competir individualmente o por equipos resolviendo challenges y enviando flags.

### Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | Flask | 3.1.0 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Migraciones | Flask-Migrate (Alembic) | 4.0.7 |
| Autenticación | Flask-Login | 0.6.3 |
| Hashing | Werkzeug (PBKDF2+SHA256) | 3.1.3 |
| Base de Datos | MySQL/MariaDB (PyMySQL) | 1.1.1 |
| Criptografía | cryptography | 44.0.0 |
| Frontend | Bootstrap 5 + Bootstrap Icons | CDN |
| Servidor producción | Gunicorn + Nginx | — |

---

## 2. Arquitectura de la Aplicación

### 2.1 Patrón Application Factory

La app usa el patrón **Application Factory** de Flask, implementado en `app/__init__.py`:

```python
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Inicializa extensiones, registra blueprints, inyecta contexto
    return app
```

### 2.2 Extensiones Globales

Se inicializan como objetos globales y luego se vinculan a la app en `create_app()`:

| Extensión | Variable | Propósito |
|-----------|----------|-----------|
| `SQLAlchemy` | `db` | ORM y gestión de base de datos |
| `LoginManager` | `login_manager` | Gestión de sesiones de usuario |
| `Migrate` | `migrate` | Migraciones de esquema de BD |

### 2.3 Blueprints (Módulos)

La aplicación se divide en **6 blueprints** independientes:

| Blueprint | Prefijo URL | Archivo | Propósito |
|-----------|-------------|---------|-----------|
| `main` | `/` | `app/routes.py` | Página principal y perfiles |
| `auth` | `/auth` | `app/auth/routes.py` | Login, registro, edición de perfil |
| `challenges` | `/challenges` | `app/challenges/routes.py` | Listado, detalle y envío de flags |
| `teams` | `/teams` | `app/teams/routes.py` | Creación, unión y gestión de equipos |
| `leaderboard` | `/leaderboard` | `app/leaderboard/routes.py` | Rankings individual y por equipos |
| `admin` | `/admin` | `app/admin/routes.py` | Panel de administración completo |

### 2.4 Context Processor

Se inyectan automáticamente en todas las plantillas:

```python
@app.context_processor
def inject_ctf_info():
    return {
        'ctf_name': app.config['CTF_NAME'],
        'ctf_description': app.config['CTF_DESCRIPTION']
    }
```

### 2.5 Flujo de Inicialización

```
run.py
  └─> create_app()
        ├─> Carga Config
        ├─> Crea directorio de uploads
        ├─> Inicializa db, login_manager, migrate
        ├─> Registra 6 blueprints
        ├─> Registra context processor
        └─> Importa models
```

---

## 3. Esquema de Base de Datos

### 3.1 Diagrama Entidad-Relación

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   users      │────<│    solves     │>────│ challenges   │
│              │     └──────────────┘     │              │
│ id (PK)      │                          │ id (PK)      │
│ username     │     ┌──────────────┐     │ title        │
│ email        │────<│submission_logs│>────│ flag         │
│ password_hash│     └──────────────┘     │ points       │
│ is_admin     │                          │ difficulty   │
│ is_active    │     ┌──────────────┐     │ category_id  │>──┐
│ team_id (FK) │>──┐ │ hint_unlocks │     │ is_active    │   │
│ bio          │   │ │  (M2M table) │     │ starts_at    │   │
│ avatar_url   │   │ └──────┬───────┘     │ ends_at      │   │
│ created_at   │   │        │             │ attachment   │   │
│ last_seen    │   │        v             │ challenge_url│   │
└──────┬───────┘   │  ┌──────────┐        └──────┬───────┘   │
       │           │  │  hints   │               │           │
       │           │  │          │>──────────────-┘           │
       │           │  │ id (PK)  │                           │
       │           │  │ content  │        ┌─────────────┐    │
       │           │  │ cost     │        │ categories   │<───┘
       v           │  │ order    │        │              │
┌──────────────┐   │  └──────────┘        │ id (PK)      │
│   teams       │<─┘                      │ name         │
│              │                          │ description  │
│ id (PK)      │                          │ icon         │
│ name         │                          │ color        │
│ description  │                          └─────────────┘
│ invite_code  │
│ owner_id(FK) │
│ created_at   │
└──────────────┘
```

### 3.2 Tablas de Asociación (Many-to-Many)

#### `team_members` (no utilizada directamente — la relación se maneja via `User.team_id`)
```
user_id  (FK → users.id)   PK
team_id  (FK → teams.id)   PK
joined_at  DateTime
```
> **Nota**: Aunque esta tabla existe en el modelo, la relación de equipo se gestiona principalmente a través de `User.team_id` (FK directa). La tabla `team_members` está definida pero no se usa activamente en las rutas.

#### `hint_unlocks`
```
user_id  (FK → users.id)   PK
hint_id  (FK → hints.id)   PK
unlocked_at  DateTime
```

### 3.3 Modelos Detallados

#### `User` (tabla: `users`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK, autoincrement | Identificador único |
| `username` | String(64) | UNIQUE, NOT NULL, INDEX | Nombre de usuario |
| `email` | String(120) | UNIQUE, NOT NULL, INDEX | Correo electrónico |
| `password_hash` | String(256) | NOT NULL | Hash PBKDF2+SHA256 |
| `is_admin` | Boolean | default=False | ¿Es administrador? |
| `is_active_user` | Boolean | default=True | ¿Cuenta activa? |
| `created_at` | DateTime | default=utcnow | Fecha de registro |
| `last_seen` | DateTime | default=utcnow | Última actividad |
| `bio` | String(500) | default='' | Biografía del perfil |
| `avatar_url` | String(256) | default='' | URL del avatar |
| `team_id` | Integer | FK → teams.id, nullable | Equipo actual |

**Relaciones**:
- `solves` → Solve (1:N, backref `user`)
- `owned_team` → Team (1:N via `Team.owner_id`)
- `unlocked_hints` → Hint (M2M via `hint_unlocks`)
- `submissions` → SubmissionLog (1:N, backref `user`)
- `team_ref` → Team (N:1 via `team_id`)

**Métodos**:
- `set_password(password)` → Genera hash con `generate_password_hash()`
- `check_password(password)` → Verifica con `check_password_hash()`
- `has_solved(challenge)` → Boolean, si ya resolvió un reto
- `get_score()` → Calcula puntuación total (puntos + first blood bonus − coste de pistas)
- `get_solve_count()` → Número de retos resueltos

#### `Team` (tabla: `teams`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `name` | String(64) | UNIQUE, NOT NULL, INDEX | Nombre del equipo |
| `description` | String(500) | default='' | Descripción |
| `invite_code` | String(32) | UNIQUE, NOT NULL | Código de invitación |
| `owner_id` | Integer | FK → users.id, NOT NULL | Creador del equipo |
| `created_at` | DateTime | default=utcnow | Fecha de creación |

**Métodos**:
- `get_score()` → Suma de puntuaciones de todos los miembros
- `get_solve_count()` → Suma de solves de todos los miembros
- `member_count()` → Número de miembros

#### `Category` (tabla: `categories`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `name` | String(64) | UNIQUE, NOT NULL | Nombre (Web, Crypto, etc.) |
| `description` | String(256) | default='' | Descripción de la categoría |
| `icon` | String(64) | default='bi-puzzle' | Clase Bootstrap Icons |
| `color` | String(7) | default='#00ff88' | Color hexadecimal |

**Categorías por defecto** (creadas en `setup_db.py`):
Web, Crypto, Forensics, Reversing, Pwn, OSINT, Misc, Steganography, Networking

#### `Challenge` (tabla: `challenges`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `title` | String(128) | NOT NULL | Título del reto |
| `description` | Text | NOT NULL | Descripción (soporta HTML/Markdown) |
| `flag` | String(256) | NOT NULL | Flag correcta (formato `FLAG{...}`) |
| `points` | Integer | NOT NULL, default=100 | Puntos base |
| `difficulty` | String(20) | NOT NULL, default='medium' | easy/medium/hard/insane |
| `category_id` | Integer | FK → categories.id, NOT NULL | Categoría |
| `is_active` | Boolean | default=True | ¿Visible para jugadores? |
| `created_at` | DateTime | default=utcnow | Fecha de creación |
| `author` | String(64) | default='Admin' | Autor del reto |
| `starts_at` | DateTime | nullable | Inicio de disponibilidad |
| `ends_at` | DateTime | nullable | Fin de disponibilidad |
| `attachment_filename` | String(256) | nullable | Archivo adjunto |
| `challenge_url` | String(512) | nullable | URL externa (Docker, etc.) |

**Métodos**:
- `solve_count()` → Número de resoluciones
- `is_available()` → Verifica si está activo y dentro de ventana temporal
- `is_timed()` → ¿Tiene límite temporal?
- `time_remaining()` → Timedelta restante (o None)
- `get_first_blood()` → Primer solve ordenado por fecha
- `get_solvers()` → Lista de solves ordenados cronológicamente
- `get_difficulty_badge()` → Tupla (nombre_español, clase_bootstrap)

#### `Solve` (tabla: `solves`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `user_id` | Integer | FK → users.id, NOT NULL | Usuario que resolvió |
| `challenge_id` | Integer | FK → challenges.id, NOT NULL | Reto resuelto |
| `solved_at` | DateTime | default=utcnow, INDEX | Momento de resolución |
| `is_first_blood` | Boolean | default=False | ¿Es el primero en resolver? |

**Constraint**: `UNIQUE(user_id, challenge_id)` — Un usuario solo puede resolver un reto una vez.

#### `Hint` (tabla: `hints`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `challenge_id` | Integer | FK → challenges.id, NOT NULL | Reto al que pertenece |
| `content` | Text | NOT NULL | Contenido de la pista |
| `cost` | Integer | NOT NULL, default=25 | Penalización en puntos |
| `order` | Integer | default=0 | Orden de visualización |

#### `SubmissionLog` (tabla: `submission_logs`)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | Integer | PK | Identificador |
| `user_id` | Integer | FK → users.id, NOT NULL | Usuario que envió |
| `challenge_id` | Integer | FK → challenges.id, NOT NULL | Reto objetivo |
| `submitted_flag` | String(256) | NOT NULL | Flag enviada |
| `is_correct` | Boolean | NOT NULL | ¿Fue correcta? |
| `ip_address` | String(45) | nullable | IP del cliente |
| `submitted_at` | DateTime | default=utcnow | Timestamp del intento |

---

## 4. Sistema de Autenticación y Autorización

### 4.1 Autenticación (Flask-Login)

**Configuración del LoginManager**:
- `login_view = 'auth.login'` → Redirige aquí cuando se necesita login
- `login_message = 'Inicia sesión para acceder a esta página.'`
- `login_message_category = 'warning'`

**User Loader**:
```python
@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))
```

**Hashing de contraseñas**: `werkzeug.security.generate_password_hash()` / `check_password_hash()` (PBKDF2 + SHA256)

### 4.2 Flujo de Login

1. El usuario envía `username` (o email) + `password`
2. Se busca por `username` **O** `email` (login flexible)
3. Se verifica `check_password()` y `is_active_user`
4. Se actualiza `last_seen`
5. Soporte para `remember me` (sesiones persistentes)
6. Redirección segura: solo acepta `next` que empiece por `/` (previene open redirect)

### 4.3 Validaciones de Registro

- Username: mínimo 3 caracteres, único
- Email: debe contener `@`, único
- Password: mínimo 8 caracteres
- Confirmación de contraseña obligatoria

### 4.4 Niveles de Autorización

| Nivel | Decorador | Descripción |
|-------|-----------|-------------|
| Público | (ninguno) | Acceso libre |
| Autenticado | `@login_required` | Requiere sesión activa |
| Admin | `@admin_required` | Requiere `is_admin=True` |

**Decorador `admin_required`** (custom):
```python
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
```

### 4.5 Sesiones

- Duración: **12 horas** (`PERMANENT_SESSION_LIFETIME`)
- Gestión via Flask-Login con soporte `remember_me`

---

## 5. Mapa Completo de Rutas (API)

### 5.1 Rutas Principales (`/`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET | `/` | — | `index()` | Página principal con stats, categorías y actividad reciente |
| GET | `/profile/<username>` | — | `profile()` | Perfil público de usuario con ranking y solves |

### 5.2 Autenticación (`/auth`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET/POST | `/auth/register` | — | `register()` | Formulario de registro |
| GET/POST | `/auth/login` | — | `login()` | Formulario de login (username o email) |
| GET | `/auth/logout` | Login | `logout()` | Cerrar sesión |
| GET/POST | `/auth/profile/edit` | Login | `edit_profile()` | Editar bio, email y contraseña |

### 5.3 Retos (`/challenges`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET | `/challenges/` | — | `challenge_list()` | Listado con filtros por categoría y dificultad |
| GET | `/challenges/<id>` | Login | `challenge_detail()` | Detalle del reto, pistas, solvers |
| POST | `/challenges/<id>/submit` | Login | `submit_flag()` | Enviar flag para validación |
| POST | `/challenges/<id>/hint/<hint_id>/unlock` | Login | `unlock_hint()` | Desbloquear pista con penalización |

### 5.4 Equipos (`/teams`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET | `/teams/` | — | `team_list()` | Listado de equipos ordenados por puntuación |
| GET | `/teams/<id>` | — | `team_detail()` | Detalle del equipo, miembros y puntuación |
| GET/POST | `/teams/create` | Login | `create_team()` | Crear equipo nuevo |
| GET/POST | `/teams/join` | Login | `join_team()` | Unirse a equipo con código de invitación |
| POST | `/teams/leave` | Login | `leave_team()` | Abandonar equipo actual |

### 5.5 Leaderboard (`/leaderboard`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET | `/leaderboard/` | — | `scoreboard()` | Ranking individual (default) o por equipos (`?view=teams`) |

**Parámetros de query**:
- `view=individual` (default) → Ranking de jugadores
- `view=teams` → Ranking de equipos

### 5.6 Administración (`/admin`)

| Método | Ruta | Auth | Función | Descripción |
|--------|------|------|---------|-------------|
| GET | `/admin/` | Admin | `dashboard()` | Dashboard con estadísticas y últimos envíos |
| GET | `/admin/categories` | Admin | `categories()` | Listar categorías |
| GET/POST | `/admin/categories/create` | Admin | `create_category()` | Crear categoría |
| GET/POST | `/admin/categories/<id>/edit` | Admin | `edit_category()` | Editar categoría |
| POST | `/admin/categories/<id>/delete` | Admin | `delete_category()` | Eliminar categoría (solo si no tiene retos) |
| GET | `/admin/challenges` | Admin | `challenges()` | Listar todos los retos |
| GET/POST | `/admin/challenges/create` | Admin | `create_challenge()` | Crear reto con pistas y archivo |
| GET/POST | `/admin/challenges/<id>/edit` | Admin | `edit_challenge()` | Editar reto |
| POST | `/admin/challenges/<id>/delete` | Admin | `delete_challenge()` | Eliminar reto y datos asociados |
| POST | `/admin/challenges/<id>/toggle` | Admin | `toggle_challenge()` | Activar/desactivar reto |
| GET | `/admin/users` | Admin | `users()` | Listar usuarios |
| POST | `/admin/users/<id>/toggle` | Admin | `toggle_user()` | Activar/desactivar usuario |
| POST | `/admin/users/<id>/make-admin` | Admin | `make_admin()` | Promover/degradar admin |
| GET | `/admin/logs` | Admin | `submission_logs()` | Logs paginados (50/página) |

---

## 6. Sistema de Puntuación

### 6.1 Cálculo de Puntuación Individual

```
Puntuación = Σ(puntos_reto + bonus_first_blood) − Σ(coste_pistas_desbloqueadas)
Puntuación_final = max(Puntuación, 0)   // Nunca negativa
```

### 6.2 Componentes

| Concepto | Valor | Descripción |
|----------|-------|-------------|
| Puntos base | Variable (por reto) | Definido al crear el challenge |
| First Blood Bonus | 50 pts (configurable) | Bonus al primer usuario que resuelve |
| Coste de pista | Variable (por pista) | Default: 25 pts, se resta del score |

### 6.3 Niveles de Dificultad

| Dificultad | Clave | Badge Bootstrap | Puntos sugeridos |
|------------|-------|-----------------|------------------|
| Fácil | `easy` | `success` (verde) | Bajo |
| Media | `medium` | `warning` (amarillo) | Medio |
| Difícil | `hard` | `danger` (rojo) | Alto |
| Insane | `insane` | `dark` (negro) | Muy alto |

### 6.4 First Blood 🩸

- Se determina verificando `challenge.solve_count() == 0` en el momento del envío
- Se marca `Solve.is_first_blood = True`
- El bonus se suma automáticamente en `User.get_score()`
- Se muestra visualmente en las vistas de reto y leaderboard

### 6.5 Puntuación de Equipo

```
Puntuación_equipo = Σ(puntuación_individual de cada miembro)
```

### 6.6 Desempate en Leaderboard

**Individual**: Se ordena por puntuación descendente. En caso de empate, gana quien obtuvo su último solve **más temprano** (menor `solved_at`).

**Equipos**: Se ordena solo por puntuación descendente.

---

## 7. Sistema de Equipos

### 7.1 Flujo de Creación

1. Usuario sin equipo accede a `/teams/create`
2. Proporciona nombre (min 3 chars) y descripción opcional
3. Se genera `invite_code` con `secrets.token_hex(8)` (16 caracteres hex)
4. El creador se asigna como `owner_id` y se une automáticamente
5. El `invite_code` se muestra solo al owner en la vista de detalle

### 7.2 Flujo de Unión

1. Usuario sin equipo accede a `/teams/join`
2. Introduce el código de invitación
3. Se valida que el equipo no esté lleno (`MAX_TEAM_SIZE`, default: 5)
4. Se asigna `user.team_id = team.id`

### 7.3 Flujo de Abandono

- **Miembro normal**: Se limpia `user.team_id`
- **Owner con otros miembros**: La propiedad se transfiere al primer miembro restante
- **Owner último miembro**: El equipo se elimina completamente

### 7.4 Restricciones

- Un usuario solo puede estar en **un equipo** a la vez
- Debe abandonar antes de crear/unirse a otro
- Tamaño máximo configurable (default: 5)

---

## 8. Sistema de Retos (Challenges)

### 8.1 Ciclo de Vida de un Reto

```
Creación (Admin) → Activo/Inactivo → Disponible (ventana temporal) → Resuelto/Expirado
```

### 8.2 Disponibilidad Temporal

Un reto `is_available()` cuando:
1. `is_active == True`
2. Si `starts_at` existe: `now >= starts_at`
3. Si `ends_at` existe: `now <= ends_at`

### 8.3 Validación de Flags

```python
# Comparación exacta (case-sensitive):
submitted_flag == challenge.flag
```

- Formato esperado: `FLAG{...}` (configurable en config)
- Se registra **cada intento** (correcto e incorrecto) en `SubmissionLog`
- Se captura IP del cliente (`request.remote_addr`)
- Un usuario **no puede enviar** si ya resolvió el reto

### 8.4 Sistema de Pistas (Hints)

- Cada reto puede tener múltiples pistas ordenadas por `order`
- Cada pista tiene un `cost` (penalización en puntos)
- Una vez desbloqueada, la relación se guarda en `hint_unlocks` (M2M)
- El coste se resta permanentemente de la puntuación del usuario

### 8.5 Archivos Adjuntos

- Se suben archivos hasta **50 MB** (`MAX_CONTENT_LENGTH`)
- Se guardan en `app/static/uploads/` con nombre sanitizado (`secure_filename`)
- Se sirven como recursos estáticos descargables

### 8.6 Filtrado de Retos

En `/challenges/`, los usuarios pueden filtrar por:
- **Categoría**: Dropdown con todas las categorías
- **Dificultad**: easy, medium, hard, insane

---

## 9. Panel de Administración

### 9.1 Dashboard

Muestra estadísticas globales:
- Total de usuarios, equipos, retos, solves, submissions
- Últimos 20 envíos de flags con detalle

### 9.2 Gestión de Categorías (CRUD)

- **Crear**: nombre, descripción, icono (Bootstrap Icons), color (hex)
- **Editar**: todos los campos
- **Eliminar**: solo si no tiene retos asignados (protección referencial)

### 9.3 Gestión de Retos (CRUD)

- **Crear**: título, descripción, flag, puntos, dificultad, categoría, autor, URL externa, archivo adjunto, ventana temporal, pistas (dinámicas)
- **Editar**: todos los campos. Las pistas se reemplazan completamente (delete + recreate)
- **Eliminar**: cascada manual — elimina Solves, SubmissionLogs, Hints asociados
- **Toggle**: activar/desactivar sin eliminar

### 9.4 Gestión de Usuarios

- **Toggle activo**: desactivar/reactivar cuentas (no se puede desactivar la propia)
- **Toggle admin**: promover/degradar permisos de administrador

### 9.5 Logs de Envíos

- Vista paginada (50 por página) de todos los `SubmissionLog`
- Campos visibles: fecha, usuario, reto, flag enviada, resultado, IP
- Ordenados por fecha descendente

---

## 10. Configuración

### 10.1 Variables de Configuración (`config.py`)

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `SECRET_KEY` | `'ctf-platform-secret-key-change-in-production'` | Clave secreta de Flask (sesiones, CSRF) |
| `SQLALCHEMY_DATABASE_URI` | `'mysql+pymysql://ctf_user:ctf_password@localhost/ctf_platform'` | Cadena de conexión a MySQL |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | Desactiva eventos de SQLAlchemy |
| `PERMANENT_SESSION_LIFETIME` | `12 horas` | Duración de la sesión |
| `CTF_NAME` | `'HackArena CTF'` | Nombre mostrado en la UI |
| `CTF_DESCRIPTION` | `'Plataforma de Capture The Flag'` | Descripción general |
| `FIRST_BLOOD_BONUS` | `50` | Puntos extra por first blood |
| `MAX_TEAM_SIZE` | `5` | Límite de miembros por equipo |
| `FLAG_FORMAT` | `'FLAG{}'` | Formato esperado de flags |
| `UPLOAD_FOLDER` | `app/static/uploads` | Directorio de archivos adjuntos |
| `MAX_CONTENT_LENGTH` | `50 MB` | Tamaño máximo de upload |
| `ADMIN_USERNAME` | `'admin'` | Username del admin inicial |
| `ADMIN_EMAIL` | `'admin@hackarena.local'` | Email del admin inicial |
| `ADMIN_PASSWORD` | `'AdminCTF2025!'` | Contraseña del admin inicial |

### 10.2 Variables de Entorno

Todas las variables se pueden sobreescribir con variables de entorno:
`SECRET_KEY`, `DATABASE_URL`, `CTF_NAME`, `CTF_DESCRIPTION`, `FIRST_BLOOD_BONUS`, `MAX_TEAM_SIZE`, `FLAG_FORMAT`, `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`

---

## 11. Frontend y Plantillas

### 11.1 Sistema de Templates (Jinja2)

**Herencia de plantillas**: Todas las páginas extienden `base.html`.

```
base.html
  ├── index.html
  ├── profile.html
  ├── auth/
  │   ├── login.html
  │   ├── register.html
  │   └── edit_profile.html
  ├── challenges/
  │   ├── list.html
  │   └── detail.html
  ├── teams/
  │   ├── list.html
  │   ├── detail.html
  │   ├── create.html
  │   └── join.html
  ├── leaderboard/
  │   └── scoreboard.html
  └── admin/
      ├── dashboard.html
      ├── categories.html
      ├── category_form.html
      ├── challenges.html
      ├── challenge_form.html
      ├── logs.html
      └── users.html
```

### 11.2 Layout Base (`base.html`)

- **Navbar**: Logo/nombre CTF, enlaces a Retos/Equipos/Leaderboard, menú de usuario (Login/Registro o Perfil/Admin/Logout)
- **Flash messages**: Alertas con auto-dismiss animado
- **Footer**: Créditos
- **Dependencias CDN**: Bootstrap 5 CSS/JS, Bootstrap Icons

### 11.3 Tema Visual

- **Tema oscuro** estilo hacker
- Color principal: `--ctf-green: #00ff88`
- Fondo oscuro: `--ctf-dark: #0a0a0f`
- Font monospace para elementos de código
- Efectos hover con `translateY` y sombras verdes
- Scrollbar personalizado
- Animación `slideDown` para alertas

### 11.4 Componentes Visuales Clave

- **Challenge cards**: Indicador solved/unsolved, badge de dificultad, first blood, categoría
- **Leaderboard**: Medallas 🥇🥈🥉 para top 3, filas destacadas
- **Team detail**: Código de invitación visible solo para el owner
- **Admin tables**: Acciones inline con confirmación para eliminación

---

## 12. Seguridad

### 12.1 Medidas Implementadas

| Medida | Implementación |
|--------|---------------|
| Hashing de contraseñas | PBKDF2 + SHA256 via Werkzeug |
| Protección admin | Decorador `@admin_required` custom |
| Prevención open redirect | Valida que `next` empiece por `/` |
| Logging de intentos | Tabla `submission_logs` con IP y timestamp |
| Sanitización de filenames | `werkzeug.utils.secure_filename()` |
| Límite de uploads | 50 MB máximo |
| Cuenta desactivable | Campo `is_active_user`, verificado en login |
| Sesiones con timeout | 12 horas de duración |
| Unicidad de solves | Constraint `UNIQUE(user_id, challenge_id)` |
| Auto-protección admin | No puede desactivar su propia cuenta |

### 12.2 Registro de Auditoría

Cada envío de flag genera un registro con:
- ID del usuario
- ID del reto
- Flag enviada (literal)
- Resultado (correcto/incorrecto)
- Dirección IP
- Timestamp

---

## 13. Despliegue

### 13.1 Desarrollo Local

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
python setup_db.py              # Inicializa BD + admin + categorías
python run.py                   # Servidor en 0.0.0.0:5000 con debug=True
```

### 13.2 Producción (Ubuntu Server)

El script `install.sh` automatiza:

1. Instala paquetes: Python 3, pip, venv, MariaDB, Nginx, Certbot
2. Crea base de datos `ctf_platform` con usuario `ctf_user` y password aleatorio
3. Copia la app a `/opt/hackarena-ctf`
4. Crea venv e instala dependencias + Gunicorn
5. Genera `.env` con `SECRET_KEY` aleatorio y `ADMIN_PASSWORD` aleatorio
6. Ejecuta `setup_db.py`
7. Configura servicio systemd (`hackarena-ctf.service`)
   - 4 workers Gunicorn en `127.0.0.1:5000`
   - Auto-restart, ejecuta como `www-data`
8. Configura Nginx como reverse proxy
   - Proxy a `127.0.0.1:5000`
   - Headers: `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`
   - Archivos estáticos servidos directamente con caché de 1 día
   - Límite de upload: 50 MB

### 13.3 Script de Inicialización (`setup_db.py`)

1. Crea todas las tablas con `db.create_all()`
2. Crea usuario admin si no existe (con config de `config.py`)
3. Crea 9 categorías por defecto si no existen
4. Commit final e imprime credenciales

---

## 14. Estructura de Archivos

```
CTFArena/
├── config.py                          # Clase Config con todas las variables
├── run.py                             # Punto de entrada (Flask dev server)
├── setup_db.py                        # Inicialización de BD, admin y categorías
├── install.sh                         # Script de despliegue automático (Ubuntu)
├── requirements.txt                   # 7 dependencias Python
├── README.md                          # Documentación original
├── .gitignore                         # Exclusiones de Git
│
└── app/
    ├── __init__.py                    # Application Factory + extensiones
    ├── models.py                      # 7 modelos + 2 tablas de asociación
    ├── routes.py                      # Blueprint 'main': index, profile
    │
    ├── auth/
    │   ├── __init__.py                # Blueprint 'auth'
    │   └── routes.py                  # register, login, logout, edit_profile
    │
    ├── challenges/
    │   ├── __init__.py                # Blueprint 'challenges'
    │   └── routes.py                  # list, detail, submit_flag, unlock_hint
    │
    ├── teams/
    │   ├── __init__.py                # Blueprint 'teams'
    │   └── routes.py                  # list, detail, create, join, leave
    │
    ├── leaderboard/
    │   ├── __init__.py                # Blueprint 'leaderboard'
    │   └── routes.py                  # scoreboard (individual + teams)
    │
    ├── admin/
    │   ├── __init__.py                # Blueprint 'admin'
    │   └── routes.py                  # CRUD categorías, retos, usuarios, logs
    │
    ├── static/
    │   ├── css/
    │   │   └── style.css              # Tema oscuro personalizado
    │   └── uploads/                   # Archivos adjuntos de retos
    │       └── .gitkeep
    │
    └── templates/
        ├── base.html                  # Layout maestro (navbar, footer, flash)
        ├── index.html                 # Página principal
        ├── profile.html               # Perfil público de usuario
        ├── auth/
        │   ├── login.html             # Formulario de login
        │   ├── register.html          # Formulario de registro
        │   └── edit_profile.html      # Edición de perfil
        ├── challenges/
        │   ├── list.html              # Listado filtrable de retos
        │   └── detail.html            # Detalle + envío de flag + pistas
        ├── teams/
        │   ├── list.html              # Listado de equipos
        │   ├── detail.html            # Detalle de equipo + miembros
        │   ├── create.html            # Formulario crear equipo
        │   └── join.html              # Formulario unirse con código
        ├── leaderboard/
        │   └── scoreboard.html        # Rankings individual/equipos
        └── admin/
            ├── dashboard.html         # Panel principal admin
            ├── categories.html        # Gestión de categorías
            ├── category_form.html     # Form crear/editar categoría
            ├── challenges.html        # Gestión de retos
            ├── challenge_form.html    # Form crear/editar reto + pistas
            ├── users.html             # Gestión de usuarios
            └── logs.html              # Logs de envíos paginados
```

---

## Apéndice: Dependencias Python

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| Flask | 3.1.0 | Framework web WSGI |
| Flask-SQLAlchemy | 3.1.1 | ORM integrado con Flask |
| Flask-Login | 0.6.3 | Gestión de sesiones de autenticación |
| Flask-Migrate | 4.0.7 | Migraciones de base de datos (Alembic) |
| PyMySQL | 1.1.1 | Driver MySQL para Python |
| Werkzeug | 3.1.3 | Utilidades WSGI, hashing de contraseñas |
| cryptography | 44.0.0 | Soporte criptográfico (requerido por PyMySQL) |

---

> 📄 Documento generado mediante ingeniería inversa del código fuente completo de HackArena CTF.
