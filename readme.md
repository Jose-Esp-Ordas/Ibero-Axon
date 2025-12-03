# Ibero-Axon Production Tracking API

API Backend para Sistema de Trazabilidad de Producción Industrial con módulo de IA para análisis de riesgos.

## Características

- **Autenticación y Autorización**: Sistema JWT con roles (ADMIN, SUPERVISOR, OPERADOR)
- **Trazabilidad Completa**: Seguimiento de piezas a través de estaciones de producción
- **Métricas en Tiempo Real**: Dashboard con KPIs de producción y calidad
- **Análisis Inteligente**: Módulo de IA con Gemini AI para detección de anomalías y cálculo de riesgo
- **Base de Datos**: MongoDB con Beanie ODM
- **Documentación**: API docs automática con FastAPI (Swagger/OpenAPI)

## Requisitos

- Python 3.10+
- MongoDB 5.0+
- Cuenta de Google AI (para Gemini AI)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/Jose-Esp-Ordas/Ibero-Axon.git
cd Ibero-Axon
```

2. Crear entorno virtual:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

Variables necesarias:
- `MONGODB_URL`: URL de conexión a MongoDB
- `SECRET_KEY`: Clave secreta para JWT (generar una segura)
- `GEMINI_API_KEY`: API Key de Google AI (opcional pero recomendado)

## Ejecución Local

```bash
cd app
python main.py
```

O con uvicorn directamente:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## Tests

Ejecutar tests:
```bash
pytest
```

Con cobertura:
```bash
pytest --cov=app tests/
```

## Estructura del Proyecto

```
Ibero-Axon/
├── app/
│   ├── models/           # Modelos de base de datos (Beanie)
│   │   ├── user.py
│   │   ├── part.py
│   │   ├── station.py
│   │   └── trace_event.py
│   ├── routers/          # Endpoints de la API
│   │   ├── auth_router.py
│   │   ├── users_router.py
│   │   ├── parts_router.py
│   │   ├── stations_router.py
│   │   ├── trace_router.py
│   │   ├── metrics_router.py
│   │   └── ai_router.py
│   ├── services/         # Lógica de negocio
│   │   └── ai_service.py
│   ├── auth.py           # Autenticación JWT
│   ├── dependencies.py   # Dependencias y middlewares
│   ├── schemas.py        # Schemas Pydantic
│   ├── config.py         # Configuración
│   ├── database.py       # Conexión a MongoDB
│   └── main.py           # Aplicación principal
├── tests/                # Tests
│   └── test_api.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Autenticación

### Registro de Usuario
```bash
POST /auth/register
{
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "password": "password123",
  "rol": "OPERADOR"
}
```

### Login
```bash
POST /auth/login
{
  "email": "juan@example.com",
  "password": "password123"
}
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

Usar el token en headers:
```
Authorization: Bearer {access_token}
```

## Endpoints Principales

### Trazabilidad

**Crear Pieza**
```bash
POST /parts/
{
  "serial": "PZA-001",
  "tipo_pieza": "X1",
  "lote": "LOTE-2024-01",
  "status": "EN_PROCESO"
}
```

**Registrar Evento de Trazabilidad**
```bash
POST /trace/events
{
  "part_id": "PZA-001",
  "station_id": "station_id",
  "timestamp_entrada": "2024-12-02T10:00:00",
  "timestamp_salida": "2024-12-02T10:15:00",
  "resultado": "OK",
  "observaciones": "Inspección completa"
}
```

**Historial de Pieza**
```bash
GET /trace/parts/{serial}/history
```

### Métricas (Dashboard)

**Piezas por Estado**
```bash
GET /metrics/parts-by-status
```

**Throughput (Producción por Día)**
```bash
GET /metrics/throughput?from=2024-12-01&to=2024-12-31
```

**Tiempo de Ciclo por Estación**
```bash
GET /metrics/station-cycle-time
```

**Tasa de Scrap**
```bash
GET /metrics/scrap-rate?tipo_pieza=X1
```

### Inteligencia Artificial

**Calcular Riesgo de Falla**
```bash
POST /ai/risk-score
{
  "part_id": "PZA-123",
  "num_retrabajos": 1,
  "tiempo_total_segundos": 850,
  "estacion_actual": "INSPECCION_FINAL",
  "tipo_pieza": "X1"
}
```

Respuesta:
```json
{
  "riesgo_falla": 0.82,
  "nivel": "ALTO",
  "explicacion": "Tiempo total muy superior al promedio y tiene retrabajo."
}
```

**Detectar Anomalías**
```bash
GET /ai/anomalies
```

## Roles y Permisos

- **OPERADOR**: Puede registrar eventos, consultar piezas y usar IA
- **SUPERVISOR**: Todo lo de operador + métricas y dashboards
- **ADMIN**: Acceso completo + gestión de usuarios y estaciones

## Deploy en Render

1. Crear cuenta en [Render.com](https://render.com)

2. Crear MongoDB Atlas (o usar MongoDB de Render):
   - Ir a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Crear cluster gratuito
   - Obtener connection string

3. Crear Web Service en Render:
   - Connect tu repositorio de GitHub
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Configurar Environment Variables:
   ```
   MONGODB_URL=mongodb+srv://...
   SECRET_KEY=your-secret-key-here
   GEMINI_API_KEY=your-gemini-key
   DATABASE_NAME=ibero_axon_production
   DEBUG=False
   ```

5. Deploy automático se ejecutará en cada push a master

URL de ejemplo: `https://ibero-axon.onrender.com`

## Documentación API

Una vez desplegado, la documentación interactiva está disponible en:

- Swagger UI: `https://your-app.onrender.com/docs`
- ReDoc: `https://your-app.onrender.com/redoc`

## Módulo de IA

El sistema incluye dos métodos de análisis:

1. **Análisis Heurístico**: Reglas basadas en estadísticas históricas
   - Comparación con promedios por tipo de pieza
   - Detección de desviaciones estándar
   - Evaluación de retrabajos
   - No requiere configuración adicional

2. **Análisis con Gemini AI**: Enhanced con IA generativa
   - Análisis contextual más sofisticado
   - Explicaciones naturales
   - Requiere `GEMINI_API_KEY`

## Seguridad

- Passwords hasheados con bcrypt
- Tokens JWT con expiración configurable
- Validación de datos con Pydantic
- CORS configurado
- Roles y permisos por endpoint

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **MongoDB + Beanie**: Base de datos NoSQL con ODM
- **JWT**: Autenticación basada en tokens
- **Google Gemini AI**: IA generativa para análisis
- **Pytest**: Testing
- **Pydantic**: Validación de datos

## Autores

- Jose Esp Ordas
- Pablo Urbina Macip

## Licencia

MIT License

## Soporte

Para problemas o preguntas, crear un issue en GitHub.

---

**Ibero-Axon** - Sistema de Trazabilidad Industrial con IA 🏭🤖