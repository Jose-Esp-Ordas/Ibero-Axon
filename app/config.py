from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Configuración de MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "ibero_axon_db"
    
    # Configuración de JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuración de Gemini AI
    gemini_api_key: Optional[str] = None
    
    # Configuración de la Aplicación
    app_name: str = "Ibero-Axon Production API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
