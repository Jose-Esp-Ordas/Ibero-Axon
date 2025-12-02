from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field
from enum import Enum


class PartStatus(str, Enum):
    EN_PROCESO = "EN_PROCESO"
    OK = "OK"
    SCRAP = "SCRAP"
    RETRABAJO = "RETRABAJO"


class Part(Document):
    serial: Indexed(str, unique=True)  # id/serial de la pieza
    tipo_pieza: str
    lote: str
    status: PartStatus = PartStatus.EN_PROCESO
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "parts"
        
    class Config:
        json_schema_extra = {
            "example": {
                "serial": "PZA-001",
                "tipo_pieza": "X1",
                "lote": "LOTE-2024-01",
                "status": "EN_PROCESO"
            }
        }
