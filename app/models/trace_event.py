from datetime import datetime
from typing import Optional
from beanie import Document, Link
from pydantic import Field
from enum import Enum
from .part import Part
from .station import Station
from .user import User


class EventResult(str, Enum):
    OK = "OK"
    SCRAP = "SCRAP"
    RETRABAJO = "RETRABAJO"


class TraceEvent(Document):
    part_id: str  # Serial de la pieza que pasó por la estación
    station_id: str  # ID de la estación donde ocurrió el evento
    timestamp_entrada: datetime
    timestamp_salida: Optional[datetime] = None
    resultado: Optional[EventResult] = None
    operador_id: Optional[str] = None  # ID del operador que procesó la pieza
    observaciones: Optional[str] = None
    
    class Settings:
        name = "trace_events"
        
    class Config:
        json_schema_extra = {
            "example": {
                "part_id": "PZA-001",
                "station_id": "station_id_here",
                "timestamp_entrada": "2024-12-02T10:00:00",
                "timestamp_salida": "2024-12-02T10:15:00",
                "resultado": "OK",
                "operador_id": "user_id_here",
                "observaciones": "Inspección completa sin problemas"
            }
        }
