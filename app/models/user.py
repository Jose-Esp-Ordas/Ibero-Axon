from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from enum import Enum


class UserRole(str, Enum):
    OPERADOR = "OPERADOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class User(Document):
    nombre: str
    email: Indexed(EmailStr, unique=True)
    password: str  # Stored as hashed password
    rol: UserRole = UserRole.OPERADOR
    activo: bool = True
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "email": "juan@example.com",
                "password": "hashed_password",
                "rol": "OPERADOR",
                "activo": True
            }
        }
