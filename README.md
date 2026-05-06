# 🎓 AcademiaCore — Sistema de Gestión Académica

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Academic%20Project-blue?style=flat-square)]()
[![UPTC](https://img.shields.io/badge/UPTC-Ing.%20Sistemas-red?style=flat-square)](https://www.uptc.edu.co/)

> Aplicación web full-stack para la gestión de estudiantes, docentes, materias y matrículas universitarias. Desarrollada como proyecto final de la asignatura Electiva II — Ingeniería de Sistemas y Computación, UPTC.

---

## Tabla de Contenidos

- [Vista general](#-vista-general)
- [Características](#-características)
- [Stack tecnológico](#-stack-tecnológico)
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Requisitos previos](#-requisitos-previos)
- [Instalación y configuración](#-instalación-y-configuración)
- [Variables de entorno](#-variables-de-entorno)
- [Uso](#-uso)
- [Estructura de la base de datos](#-estructura-de-la-base-de-datos)
- [API de rutas](#-api-de-rutas)
- [Decisiones de diseño y deuda técnica](#️-decisiones-de-diseño-y-deuda-técnica)
- [Contribución](#-contribución)
- [Autor](#-autor)

---

## Vista general

AcademiaCore es un sistema de información académica que permite a administradores universitarios gestionar el ciclo completo de una matrícula: desde el registro de docentes y materias hasta la inscripción de estudiantes, con control de cupos, créditos y generación de reportes estadísticos.

La aplicación implementa autenticación con roles (`admin` / `usuario`), transacciones atómicas en MongoDB para operaciones críticas, e importación masiva de datos vía archivos JSON.

---

## Características

- **Autenticación y autorización** — Registro, inicio de sesión y cierre de sesión con control de roles (admin/usuario) mediante decoradores personalizados.
- **Gestión de docentes** — CRUD completo con carga de foto de perfil y asignación de materias.
- **Gestión de estudiantes** — CRUD completo con código único, foto y seguimiento de créditos acumulados.
- **Gestión de materias** — CRUD con control de cupos disponibles, horario, carrera y créditos.
- **Sistema de matrículas** — Inscripción y desinscripción con validación de cupos y límite de 20 créditos por estudiante, ejecutada en transacciones atómicas.
- **Importación masiva** — Carga de docentes, estudiantes y materias desde archivos JSON.
- **Reportes y estadísticas** — Visualización de materias por carrera, distribución de créditos y ocupación de cupos.
- **Panel de base de datos** — Monitoreo en tiempo real del estado de la conexión y estadísticas de colecciones.
- **Manejo de errores** — Páginas personalizadas para errores 404 y 500, con registro automático en la base de datos.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.10+, Flask 3.0 |
| Base de datos | MongoDB Atlas (pymongo 4.6) |
| Autenticación | Werkzeug (hash bcrypt), Flask Sessions |
| Formularios | WTForms, Flask-WTF |
| Frontend | Jinja2, Bootstrap (vía plantillas), JavaScript vanilla |
| Procesamiento de imágenes | Pillow 10 |
| Configuración | python-dotenv |

---

## Arquitectura del proyecto

```
academiacore/
│
├── app.py                  # Punto de entrada, rutas principales y configuración de la app
├── auth.py                 # Blueprint de autenticación y decoradores de autorización
├── models.py               # Clase Database — abstracción de la conexión y colecciones
├── forms.py                # Definición de formularios con WTForms
├── utils.py                # Utilidades: manejo de archivos, generación de avatares
│
├── templates/
│   ├── base.html           # Layout principal heredado por todas las vistas
│   ├── dashboard.html      # Panel principal con estadísticas
│   ├── database_info.html  # Monitoreo de la base de datos
│   ├── auth/               # Vistas de login y registro
│   ├── students/           # CRUD de estudiantes
│   ├── teachers/           # CRUD de docentes
│   ├── subjects/           # CRUD de materias
│   ├── import/             # Vistas de importación masiva
│   ├── reports/            # Reportes y gráficos
│   └── errors/             # Páginas de error 404 y 500
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   ├── avatars/            # Avatar por defecto
│   └── uploads/            # Fotos subidas por usuarios (no se versiona)
│
├── requirements.txt
├── .env.example            # Plantilla de variables de entorno
└── .gitignore
```

---

## Requisitos previos

- Python 3.10 o superior
- Una cuenta en [MongoDB Atlas](https://www.mongodb.com/atlas) (tier gratuito es suficiente) o una instancia local de MongoDB 5.0+ (requerido para soporte de transacciones)
- `pip` o `pipenv`

> **Nota:** Las transacciones de MongoDB (`start_session` / `start_transaction`) solo están disponibles en **replica sets**. MongoDB Atlas las soporta en todos sus tiers por defecto. Si usas una instancia local standalone, las operaciones de matrícula lanzarán una excepción.

---

## Instalación y configuración

**1. Clona el repositorio**

```bash
git clone https://github.com/julianReyes-dev/academiacore.git
cd academiacore
```

**2. Crea y activa un entorno virtual**

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**3. Instala las dependencias**

```bash
pip install -r requirements.txt
```

**4. Configura las variables de entorno**

```bash
cp .env.example .env
# Edita .env con tus credenciales reales (ver sección siguiente)
```

**5. Ejecuta la aplicación**

```bash
python app.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

---

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`. **Nunca subir el archivo `.env` real a Git.**

```env
# Cadena de conexión a MongoDB Atlas
MONGO_URI="mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"

# Nombre de la base de datos
DB_NAME="school_management"

# Clave secreta para firmar las sesiones de Flask
# Genera una segura con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY="reemplaza-con-un-valor-seguro-generado"
```

> **¿Por qué importa la `SECRET_KEY`?** Flask usa esta clave para firmar criptográficamente las cookies de sesión. Si es predecible o corta, un atacante puede forjar sesiones y suplantar a cualquier usuario, incluyendo administradores.

---

## Uso

Al iniciar la aplicación por primera vez, navega a `/register` para crear el primer usuario administrador. Marca la casilla "Administrador" para obtener acceso completo.

| Rol | Acceso |
|---|---|
| **Admin** | CRUD completo, importación, reportes, panel DB |
| **Usuario** | Solo lectura (listados de docentes, estudiantes y materias) |

Para probar la importación masiva, los archivos JSON deben tener el siguiente formato:

```json
// Docentes
[{ "name": "Ana Gómez", "age": 38, "email": "ana@uptc.edu.co", "titles": ["MSc Ingeniería"] }]

// Estudiantes  
[{ "name": "Carlos Ruiz", "student_code": "202312345", "email": "carlos@uptc.edu.co" }]

// Materias
[{ "name": "Bases de Datos", "schedule": "Lunes 8-10", "credits": 3, "group": "A", "career": "Ingeniería de Sistemas", "total_slots": 30, "teacher_email": "ana@uptc.edu.co" }]
```

---

## Estructura de la base de datos

La aplicación usa cinco colecciones en MongoDB:

```
users          → { username, password (hash), is_admin, created_at, updated_at }
teachers       → { name, age, email*, photo, titles[], subject_ids[], created_at, updated_at }
students       → { name, student_code*, email, photo, created_at, updated_at }
subjects       → { name, schedule, credits, group, career, total_slots, available_slots, teacher_id, created_at, updated_at }
enrollments    → { student_id, subject_id, enrollment_date }
```

Los campos marcados con `*` tienen índice único. La combinación `(name, group, career)` en `subjects` también es única.

---

## API de rutas

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET/POST` | `/login` | — | Inicio de sesión |
| `GET/POST` | `/register` | — | Registro de usuario |
| `GET` | `/logout` | ✓ | Cerrar sesión |
| `GET` | `/` | ✓ | Dashboard |
| `GET` | `/teachers` | ✓ | Listar docentes |
| `GET/POST` | `/teachers/add` | Admin | Crear docente |
| `GET/POST` | `/teachers/edit/<id>` | Admin | Editar docente |
| `GET` | `/teachers/delete/<id>` | Admin | Eliminar docente |
| `GET` | `/students` | ✓ | Listar estudiantes |
| `GET/POST` | `/students/add` | Admin | Crear estudiante |
| `GET/POST` | `/students/edit/<id>` | Admin | Editar / gestionar matrículas |
| `GET` | `/students/delete/<id>` | Admin | Eliminar estudiante |
| `GET` | `/subjects` | ✓ | Listar materias |
| `GET/POST` | `/subjects/add` | Admin | Crear materia |
| `GET/POST` | `/subjects/edit/<id>` | Admin | Editar materia |
| `GET` | `/subjects/delete/<id>` | Admin | Eliminar materia |
| `GET` | `/enroll/<student_id>/<subject_id>` | Admin | Matricular estudiante |
| `GET` | `/unenroll/<student_id>/<subject_id>` | Admin | Desmatricular estudiante |
| `GET/POST` | `/import/teachers` | Admin | Importar docentes JSON |
| `GET/POST` | `/import/students` | Admin | Importar estudiantes JSON |
| `GET/POST` | `/import/subjects` | Admin | Importar materias JSON |
| `GET` | `/reports` | Admin | Reportes estadísticos |
| `GET` | `/database-info` | Admin | Panel de la base de datos |

---

## Decisiones de diseño y deuda técnica

Esta sección documenta de forma transparente las limitaciones conocidas del proyecto. En un entorno académico es válido tomar atajos por restricciones de tiempo; lo profesional es reconocerlos y saber cómo resolverlos.

### Problemas de seguridad (alta prioridad en producción)

**1. Credenciales expuestas en el repositorio**

El archivo `.env` original fue subido a Git con credenciales reales de MongoDB Atlas y una `SECRET_KEY` débil (`"pass"`). Esto compromete la base de datos de forma permanente en el historial de Git, incluso si se borra el archivo después.

*Solución:* Rotar inmediatamente las credenciales de MongoDB Atlas, regenerar la `SECRET_KEY` con `secrets.token_hex(32)`, agregar `.env` al `.gitignore` **antes** del primer commit, y usar un `.env.example` como plantilla sin valores reales.

**2. Archivos subidos por usuarios en control de versiones**

La carpeta `static/uploads/` contiene imágenes subidas por usuarios y está dentro del repositorio. Esto infla el tamaño del repo y puede exponer datos.

*Solución:* Agregar `static/uploads/*` y `static/avatars/` (excepto `default.png`) al `.gitignore`. En producción, usar un servicio de almacenamiento externo como AWS S3 o Cloudinary.

**3. Rutas de eliminación via GET**

Las rutas `/teachers/delete/<id>`, `/students/delete/<id>` y `/subjects/delete/<id>` usan el método HTTP `GET`. Cualquier enlace externo, imagen embebida o bot de indexación puede disparar una eliminación sin que el usuario lo intente.

*Solución:* Usar formularios con método `POST` o peticiones `DELETE` vía JavaScript (fetch/axios) con confirmación explícita del usuario.

**4. Inyección de colecciones en el contexto de Jinja2**

`app.py` expone los objetos de colección de MongoDB directamente en todas las plantillas mediante `inject_collections()`. Esto acopla la capa de presentación con la de datos.

*Solución:* Crear una capa de servicios (funciones en módulos separados) que encapsulen las consultas y solo pasen los datos necesarios a las plantillas.

### Calidad del código (mejoras recomendadas)

**5. Inconsistencia en el idioma del código**

Los mensajes flash y comentarios mezclan español e inglés dentro del mismo archivo. Esto dificulta la lectura y colaboración.

*Solución:* Adoptar un idioma consistente. Para proyectos de portafolio profesional, el inglés es estándar; para proyectos institucionales colombianos, el español es igualmente válido. Lo importante es ser consistente.

**6. `models.py` sin uso efectivo**

Se define una clase `Database` en `models.py` pero `app.py` recrea la conexión directamente sin usar esa clase. El código duplicado puede llevar a estados inconsistentes.

*Solución:* Elegir un solo patrón. Si se usa `models.py`, importar su instancia `db` en `app.py` y eliminar la conexión duplicada.

**7. Manejo de excepciones genéricas**

Varios bloques `except Exception as e` capturan cualquier error y lo muestran al usuario. En producción, esto puede exponer trazas de error con información sensible del servidor.

*Solución:* Capturar excepciones específicas, registrar el error completo en un sistema de logging (no mostrarlo al usuario) y presentar un mensaje genérico amigable.

**8. `app.run(debug=True)` en el código fuente**

El modo debug de Flask nunca debe activarse en producción: expone un depurador interactivo en el navegador que permite ejecución arbitraria de código en el servidor.

*Solución:* Controlar el modo debug con una variable de entorno: `app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')`.

### Mejoras futuras (buenas ideas para iterar)

- Añadir pruebas unitarias e integración con `pytest`.
- Implementar paginación en los listados (actualmente carga todos los documentos de cada colección).
- Agregar un Dockerfile para facilitar el despliegue reproducible.
- Implementar rate limiting en las rutas de autenticación para prevenir ataques de fuerza bruta.
- Migrar a Flask Blueprints para todas las entidades (teachers, students, subjects) y mejorar la organización del código.

---

## Contribución

Este es un proyecto académico, pero las sugerencias son bienvenidas.

1. Haz un fork del repositorio.
2. Crea una rama descriptiva: `git checkout -b feature/paginacion-estudiantes`.
3. Realiza tus cambios con commits atómicos y mensajes claros.
4. Abre un Pull Request describiendo qué cambia y por qué.

---

## Autor

**Julian Camilo Reyes Uribe**  
Estudiante de Ingeniería de Sistemas y Computación  
Universidad Pedagógica y Tecnológica de Colombia — UPTC

[![GitHub](https://img.shields.io/badge/GitHub-tu--usuario-181717?style=flat-square&logo=github)](https://github.com/tu-usuario)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-tu--perfil-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/julian-camilo-reyes-uribe-538a763a0/)

---

> Proyecto desarrollado para la asignatura **Electiva II** · Semestre 2025-1 · UPTC Tunja
