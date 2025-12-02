from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models import UserRole, PartStatus, EventResult


# ==================== User Schemas ====================
class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: UserRole = UserRole.OPERADOR


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    rol: UserRole
    activo: bool
    fecha_registro: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[UserRole] = None
    activo: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ==================== Part Schemas ====================
class PartCreate(BaseModel):
    serial: str
    tipo_pieza: str
    lote: str
    status: PartStatus = PartStatus.EN_PROCESO


class PartResponse(BaseModel):
    id: str
    serial: str
    tipo_pieza: str
    lote: str
    status: PartStatus
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


class PartUpdate(BaseModel):
    tipo_pieza: Optional[str] = None
    lote: Optional[str] = None
    status: Optional[PartStatus] = None


# ==================== Station Schemas ====================
class StationCreate(BaseModel):
    nombre: str
    tipo: str
    linea: str
    activa: bool = True


class StationResponse(BaseModel):
    id: str
    nombre: str
    tipo: str
    linea: str
    activa: bool
    
    class Config:
        from_attributes = True


class StationUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    linea: Optional[str] = None
    activa: Optional[bool] = None


# ==================== TraceEvent Schemas ====================
class TraceEventCreate(BaseModel):
    part_id: str
    station_id: str
    timestamp_entrada: datetime
    timestamp_salida: Optional[datetime] = None
    resultado: Optional[EventResult] = None
    operador_id: Optional[str] = None
    observaciones: Optional[str] = None


class TraceEventResponse(BaseModel):
    id: str
    part_id: str
    station_id: str
    timestamp_entrada: datetime
    timestamp_salida: Optional[datetime]
    resultado: Optional[EventResult]
    operador_id: Optional[str]
    observaciones: Optional[str]
    
    class Config:
        from_attributes = True


class TraceEventUpdate(BaseModel):
    timestamp_salida: Optional[datetime] = None
    resultado: Optional[EventResult] = None
    observaciones: Optional[str] = None


# ==================== AI Schemas ====================
class RiskScoreRequest(BaseModel):
    part_id: str
    num_retrabajos: int
    tiempo_total_segundos: float
    estacion_actual: str
    tipo_pieza: str


class RiskScoreResponse(BaseModel):
    riesgo_falla: float
    nivel: str
    explicacion: str


class AnomalyResponse(BaseModel):
    part_id: str
    tipo_pieza: str
    tiempo_total_segundos: float
    num_retrabajos: int
    promedio_tipo: float
    desviacion: float
    es_anomalia: bool
    razon: str
