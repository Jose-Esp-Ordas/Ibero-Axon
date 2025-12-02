from beanie import Document, Indexed
from pydantic import Field


class StationType(str):
    """Tipos comunes de estaciones"""
    INSPECCION = "INSPECCION"
    ENSAMBLE = "ENSAMBLE"
    PRUEBA = "PRUEBA"
    INSPECCION_FINAL = "INSPECCION_FINAL"


class Station(Document):
    nombre: str
    tipo: str
    linea: str
    activa: bool = True
    
    class Settings:
        name = "stations"
        
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Estación de Inspección 1",
                "tipo": "INSPECCION",
                "linea": "Línea A",
                "activa": True
            }
        }
