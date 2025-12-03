from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import User, Part, Station, TraceEvent
from app.config import settings


async def init_db():
    """Inicializar conexión a la base de datos y Beanie ODM"""
    # Crear cliente Motor
    client = AsyncIOMotorClient(settings.mongodb_url)
    
    # Obtener base de datos
    database = client[settings.database_name]
    
    # Inicializar Beanie con modelos de documentos
    await init_beanie(
        database=database,
        document_models=[
            User,
            Part,
            Station,
            TraceEvent
        ]
    )
    
    print(f"✅ Database initialized: {settings.database_name}")
