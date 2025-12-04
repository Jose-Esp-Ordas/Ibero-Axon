from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


# ==================== Enums ====================
class Rol(str, Enum):
    OPERADOR = "OPERADOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class ParteStatus(str, Enum):
    EN_PROCESO = "EN_PROCESO"
    OK = "OK"
    SCRAP = "SCRAP"
    RETRABAJO = "RETRABAJO"


class Estaciones(str, Enum):
    INSPECCION = "INSPECCION"
    ENSAMBLE = "ENSAMBLE"
    PRUEBA = "PRUEBA"
    INSPECCION_FINAL = "INSPECCION_FINAL"


class Resultados(str, Enum):
    OK = "OK"
    SCRAP = "SCRAP"
    RETRABAJO = "RETRABAJO"


# ==================== Schemas de Autenticación ====================
class UsuarioLogin(BaseModel):
    """Schema para login de usuario"""
    email: str
    password: str


class UsuarioRegister(BaseModel):
    """Schema para registro de usuario"""
    nombre: str
    email: EmailStr
    password: str
    rol: Rol = Rol.OPERADOR


class UsuarioResponse(BaseModel):
    """Schema de respuesta de usuario"""
    id: Optional[str] = None  # Opcional para compatibilidad
    nombre: str
    email: str
    rol: Rol
    activo: Optional[bool] = None  # Opcional para compatibilidad
    fecha_registro: datetime
    
    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    """Schema para actualización de usuario"""
    nombre: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None
    rol: Optional[Rol] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ==================== Schemas de Partes ====================
class ParteCreate(BaseModel):
    """Schema para crear una pieza"""
    tipo_pieza: str
    lote: str
    status: ParteStatus = ParteStatus.EN_PROCESO


class ParteResponse(ParteCreate):
    """Schema de respuesta de pieza"""
    id: Optional[str] = None  # Opcional para compatibilidad
    serial: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


class ParteUpdate(BaseModel):
    """Schema para actualizar una pieza"""
    status: ParteStatus


# ==================== Schemas de Estación de Trabajo ====================
class EstacionCreate(BaseModel):
    """Schema para crear una estación"""
    nombre: str
    tipo: Estaciones
    linea: str
    activa: bool = True


# Alias para respuesta (mismo que create según especificación)
EstacionResponse = EstacionCreate


class EstacionUpdate(BaseModel):
    """Schema para actualizar una estación"""
    nombre: Optional[str] = None
    tipo: Optional[Estaciones] = None
    linea: Optional[str] = None
    activa: Optional[bool] = None


# ==================== Schemas de Seguimiento ====================
class SeguimientoIn(BaseModel):
    """Schema para crear un seguimiento"""
    serial: str
    nombre_estacion: str
    timestamp_entrada: datetime
    timestamp_salida: Optional[datetime] = None
    resultado: Optional[Resultados] = None
    operador: Optional[str] = None
    observaciones: Optional[str] = None


# Alias para respuesta (mismo que input según especificación)
SeguimientoResponse = SeguimientoIn


class SeguimientoUpdate(BaseModel):
    """Schema para actualizar un seguimiento"""
    timestamp_salida: Optional[datetime] = None
    resultado: Optional[Resultados] = None
    observaciones: Optional[str] = None


# ==================== Schemas de IA ====================
class PeticionRiesgo(BaseModel):
    """Schema para solicitar análisis de riesgo"""
    serial: str
    num_retrabajos: int
    tiempo_total_segundos: float
    estacion_actual: str
    tipo_pieza: str


class PeticionRiesgoRespuesta(BaseModel):
    """Schema de respuesta de análisis de riesgo"""
    riesgo_falla: float
    nivel: str
    explicacion: str


class AnomaliaRespuesta(BaseModel):
    """Schema de respuesta para detección de anomalías"""
    serial: str
    tipo_pieza: str
    tiempo_total_segundos: float
    num_retrabajos: int
    promedio_tipo: float
    desviacion: float
    es_anomalia: bool
    razon: str
