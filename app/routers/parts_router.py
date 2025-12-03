from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from app.models import Part, PartStatus, User, TraceEvent
from app.schemas import PartResponse, PartCreate, PartUpdate
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/parts", tags=["Parts"])


@router.post("/", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
async def create_part(
    part_data: PartCreate,
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva pieza"""
    # Verificar si el serial ya existe
    existing_part = await Part.find_one(Part.serial == part_data.serial)
    if existing_part:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Part with serial {part_data.serial} already exists"
        )
    
    new_part = Part(
        serial=part_data.serial,
        tipo_pieza=part_data.tipo_pieza,
        lote=part_data.lote,
        status=part_data.status
    )
    await new_part.insert()
    
    return PartResponse(
        id=str(new_part.id),
        serial=new_part.serial,
        tipo_pieza=new_part.tipo_pieza,
        lote=new_part.lote,
        status=new_part.status,
        fecha_creacion=new_part.fecha_creacion
    )


@router.get("/", response_model=List[PartResponse])
async def list_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[PartStatus] = None,
    tipo_pieza: Optional[str] = None,
    lote: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Listar piezas con filtros"""
    query_filters = []
    
    if status is not None:
        query_filters.append(Part.status == status)
    if tipo_pieza:
        query_filters.append(Part.tipo_pieza == tipo_pieza)
    if lote:
        query_filters.append(Part.lote == lote)
    if fecha_desde:
        query_filters.append(Part.fecha_creacion >= fecha_desde)
    if fecha_hasta:
        query_filters.append(Part.fecha_creacion <= fecha_hasta)
    
    if query_filters:
        parts = await Part.find(*query_filters).skip(skip).limit(limit).to_list()
    else:
        parts = await Part.find_all().skip(skip).limit(limit).to_list()
    
    return [
        PartResponse(
            id=str(part.id),
            serial=part.serial,
            tipo_pieza=part.tipo_pieza,
            lote=part.lote,
            status=part.status,
            fecha_creacion=part.fecha_creacion
        )
        for part in parts
    ]


@router.get("/{part_id}", response_model=PartResponse)
async def get_part(
    part_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener pieza por ID"""
    part = await Part.get(PydanticObjectId(part_id))
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    return PartResponse(
        id=str(part.id),
        serial=part.serial,
        tipo_pieza=part.tipo_pieza,
        lote=part.lote,
        status=part.status,
        fecha_creacion=part.fecha_creacion
    )


@router.get("/serial/{serial}", response_model=PartResponse)
async def get_part_by_serial(
    serial: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener pieza por número de serie"""
    part = await Part.find_one(Part.serial == serial)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part with serial {serial} not found"
        )
    
    return PartResponse(
        id=str(part.id),
        serial=part.serial,
        tipo_pieza=part.tipo_pieza,
        lote=part.lote,
        status=part.status,
        fecha_creacion=part.fecha_creacion
    )


@router.put("/{part_id}", response_model=PartResponse)
async def update_part(
    part_id: str,
    part_update: PartUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar pieza"""
    part = await Part.get(PydanticObjectId(part_id))
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    # Actualizar campos
    update_data = part_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(part, field, value)
    
    await part.save()
    
    return PartResponse(
        id=str(part.id),
        serial=part.serial,
        tipo_pieza=part.tipo_pieza,
        lote=part.lote,
        status=part.status,
        fecha_creacion=part.fecha_creacion
    )


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(
    part_id: str,
    current_user: User = Depends(require_admin)
):
    """Eliminar pieza (Solo administradores)"""
    part = await Part.get(PydanticObjectId(part_id))
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found"
        )
    
    # También eliminar todos los eventos de trazabilidad para esta pieza
    await TraceEvent.find(TraceEvent.part_id == part.serial).delete()
    
    await part.delete()
    return None
