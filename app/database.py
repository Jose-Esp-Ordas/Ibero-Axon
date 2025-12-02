from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import User, Part, Station, TraceEvent
from app.config import settings


async def init_db():
    """Initialize database connection and Beanie ODM"""
    # Create Motor client
    client = AsyncIOMotorClient(settings.mongodb_url)
    
    # Get database
    database = client[settings.database_name]
    
    # Initialize Beanie with document models
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
