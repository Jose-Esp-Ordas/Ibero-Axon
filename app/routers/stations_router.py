from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from beanie import PydanticObjectId
from app.models import Station, User
from app.schemas import EstacionResponse, EstacionCreate, EstacionUpdate
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/estaciones", tags=["Stations"])


@router.post(
        "/",
        response_model=EstacionResponse,
        status_code=status.HTTP_201_CREATED
        )
async def create_station(
    station_data: EstacionCreate,
    current_user: User = Depends(require_admin)
):
    """Crear una nueva estación (Solo administradores)"""
    new_station = Station(
        nombre=station_data.nombre,
        tipo=station_data.tipo,
        linea=station_data.linea,
        activa=station_data.activa
    )
    await new_station.insert()
    
    return EstacionResponse(
        id=str(new_station.id),
        nombre=new_station.nombre,
        tipo=new_station.tipo,
        linea=new_station.linea,
        activa=new_station.activa
    )


@router.get("/", response_model=List[EstacionResponse])
async def list_stations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    tipo: Optional[str] = None,
    linea: Optional[str] = None,
    activa: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Listar todas las estaciones"""
    query_filters = []
    
    if tipo:
        query_filters.append(Station.tipo == tipo)
    if linea:
        query_filters.append(Station.linea == linea)
    if activa is not None:
        query_filters.append(Station.activa == activa)
    
    if query_filters:
        stations = await Station.find(
            *query_filters).skip(skip).limit(limit).to_list()
    else:
        stations = await Station.find_all(
            ).skip(skip).limit(limit).to_list()
    
    return [
        EstacionResponse(
            id=str(station.id),
            nombre=station.nombre,
            tipo=station.tipo,
            linea=station.linea,
            activa=station.activa
        )
        for station in stations
    ]


@router.get("/{station_id}", response_model=EstacionResponse)
async def get_station(
    station_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener estación por ID"""
    station = await Station.get(PydanticObjectId(station_id))
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    return EstacionResponse(
        id=str(station.id),
        nombre=station.nombre,
        tipo=station.tipo,
        linea=station.linea,
        activa=station.activa
    )


@router.put("/{station_id}", response_model=EstacionResponse)
async def update_station(
    station_id: str,
    station_update: EstacionUpdate,
    current_user: User = Depends(require_admin)
):
    """Actualizar estación (Solo administradores)"""
    station = await Station.get(PydanticObjectId(station_id))
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    # Actualizar campos
    update_data = station_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)
    
    await station.save()
    
    return EstacionResponse(
        id=str(station.id),
        nombre=station.nombre,
        tipo=station.tipo,
        linea=station.linea,
        activa=station.activa
    )


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: str,
    current_user: User = Depends(require_admin)
):
    """Eliminar estación (Solo administradores)"""
    station = await Station.get(PydanticObjectId(station_id))
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    await station.delete()
    return None
