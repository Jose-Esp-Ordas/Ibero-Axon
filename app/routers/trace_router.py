from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from app.models import TraceEvent, Part, Station, User, EventResult, PartStatus
from app.schemas import SeguimientoResponse, SeguimientoIn, SeguimientoUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/trace", tags=["Traceability"])


@router.post("/events", response_model=SeguimientoResponse, status_code=status.HTTP_201_CREATED)
async def create_trace_event(
    event_data: SeguimientoIn,
    current_user: User = Depends(get_current_user)
):
    """Crear un nuevo evento de trazabilidad - registrar el paso de una pieza por una estación"""
    # Verificar que la pieza existe
    part = await Part.find_one(Part.serial == event_data.serial)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part with serial {event_data.serial} not found"
        )
    
    # Verificar que la estación existe
    station = await Station.find_one(Station.nombre == event_data.nombre_estacion)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    
    # Si no se proporciona operador, usar el usuario actual
    operador = event_data.operador or current_user.nombre
    
    # Crear evento de trazabilidad
    new_event = TraceEvent(
        part_id=event_data.serial,
        station_id=str(station.id),
        timestamp_entrada=event_data.timestamp_entrada,
        timestamp_salida=event_data.timestamp_salida,
        resultado=event_data.resultado,
        operador_id=str(current_user.id),
        observaciones=event_data.observaciones
    )
    await new_event.insert()
    
    # Actualizar el estado de la pieza si el evento tiene un resultado y está completo (tiene timestamp_salida)
    if event_data.resultado and event_data.timestamp_salida:
        if event_data.resultado == EventResult.SCRAP:
            part.status = PartStatus.SCRAP
        elif event_data.resultado == EventResult.RETRABAJO:
            part.status = PartStatus.RETRABAJO
        elif event_data.resultado == EventResult.OK:
            # Solo marcar como OK si no estaba ya en SCRAP o en RETRABAJO
            if part.status == PartStatus.EN_PROCESO:
                part.status = PartStatus.OK
        
        await part.save()
    
    return SeguimientoResponse(
        serial=new_event.part_id,
        nombre_estacion=station.nombre,
        timestamp_entrada=new_event.timestamp_entrada,
        timestamp_salida=new_event.timestamp_salida,
        resultado=new_event.resultado,
        operador=operador,
        observaciones=new_event.observaciones
    )


@router.get("/events", response_model=List[SeguimientoResponse])
async def list_trace_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    station_id: Optional[str] = None,
    resultado: Optional[EventResult] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Listar eventos de trazabilidad con filtros"""
    query_filters = []
    
    if station_id:
        query_filters.append(TraceEvent.station_id == station_id)
    if resultado:
        query_filters.append(TraceEvent.resultado == resultado)
    if fecha_desde:
        query_filters.append(TraceEvent.timestamp_entrada >= fecha_desde)
    if fecha_hasta:
        query_filters.append(TraceEvent.timestamp_entrada <= fecha_hasta)
    
    if query_filters:
        events = await TraceEvent.find(*query_filters).skip(skip).limit(limit).to_list()
    else:
        events = await TraceEvent.find_all().skip(skip).limit(limit).to_list()
    
    result = []
    for event in events:
        station = await Station.get(PydanticObjectId(event.station_id))
        user = await User.get(PydanticObjectId(event.operador_id)) if event.operador_id else None
        result.append(
            SeguimientoResponse(
                serial=event.part_id,
                nombre_estacion=station.nombre if station else event.station_id,
                timestamp_entrada=event.timestamp_entrada,
                timestamp_salida=event.timestamp_salida,
                resultado=event.resultado,
                operador=user.nombre if user else None,
                observaciones=event.observaciones
            )
        )
    return result


@router.get("/parts/{part_serial}/history", response_model=List[SeguimientoResponse])
async def get_part_history(
    part_serial: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener el historial completo de una pieza (todos los eventos de trazabilidad en orden cronológico)"""
    # Verificar que la pieza existe
    part = await Part.find_one(Part.serial == part_serial)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part with serial {part_serial} not found"
        )
    
    # Obtener todos los eventos para esta pieza, ordenados por timestamp_entrada
    events = await TraceEvent.find(
        TraceEvent.part_id == part_serial
    ).sort("+timestamp_entrada").to_list()
    
    result = []
    for event in events:
        station = await Station.get(PydanticObjectId(event.station_id))
        user = await User.get(PydanticObjectId(event.operador_id)) if event.operador_id else None
        result.append(
            SeguimientoResponse(
                serial=event.part_id,
                nombre_estacion=station.nombre if station else event.station_id,
                timestamp_entrada=event.timestamp_entrada,
                timestamp_salida=event.timestamp_salida,
                resultado=event.resultado,
                operador=user.nombre if user else None,
                observaciones=event.observaciones
            )
        )
    return result


@router.put("/events/{event_id}", response_model=SeguimientoResponse)
async def update_trace_event(
    event_id: str,
    event_update: SeguimientoUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar evento de trazabilidad (por ejemplo, completar un evento con timestamp de salida y resultado)"""
    event = await TraceEvent.get(PydanticObjectId(event_id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace event not found"
        )
    
    # Actualizar campos
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await event.save()
    
    # Actualizar el estado de la pieza si se proporciona resultado
    if event_update.resultado:
        part = await Part.find_one(Part.serial == event.part_id)
        if part:
            if event_update.resultado == EventResult.SCRAP:
                part.status = PartStatus.SCRAP
            elif event_update.resultado == EventResult.RETRABAJO:
                part.status = PartStatus.RETRABAJO
            elif event_update.resultado == EventResult.OK:
                if part.status == PartStatus.EN_PROCESO:
                    part.status = PartStatus.OK
            
            await part.save()
    
    station = await Station.get(PydanticObjectId(event.station_id))
    user = await User.get(PydanticObjectId(event.operador_id)) if event.operador_id else None
    return SeguimientoResponse(
        serial=event.part_id,
        nombre_estacion=station.nombre if station else event.station_id,
        timestamp_entrada=event.timestamp_entrada,
        timestamp_salida=event.timestamp_salida,
        resultado=event.resultado,
        operador=user.nombre if user else None,
        observaciones=event.observaciones
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar evento de trazabilidad"""
    event = await TraceEvent.get(PydanticObjectId(event_id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace event not found"
        )
    
    await event.delete()
    return None
