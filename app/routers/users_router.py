from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from beanie import PydanticObjectId
from app.models import User, UserRole
from app.schemas import UserResponse, UserCreate, UserUpdate
from app.dependencies import require_admin, get_current_user
from app.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    rol: Optional[UserRole] = None,
    activo: Optional[bool] = None,
    current_user: User = Depends(require_admin)
):
    """Listar todos los usuarios (Solo administradores)"""
    query_filters = []
    
    if rol is not None:
        query_filters.append(User.rol == rol)
    if activo is not None:
        query_filters.append(User.activo == activo)
    
    if query_filters:
        users = await User.find(*query_filters).skip(skip).limit(limit).to_list()
    else:
        users = await User.find_all().skip(skip).limit(limit).to_list()
    
    return [
        UserResponse(
            id=str(user.id),
            nombre=user.nombre,
            email=user.email,
            rol=user.rol,
            activo=user.activo,
            fecha_registro=user.fecha_registro
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Obtener usuario por ID (Solo administradores)"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        nombre=user.nombre,
        email=user.email,
        rol=user.rol,
        activo=user.activo,
        fecha_registro=user.fecha_registro
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    """Actualizar usuario (Solo administradores)"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Actualizar campos
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await user.save()
    
    return UserResponse(
        id=str(user.id),
        nombre=user.nombre,
        email=user.email,
        rol=user.rol,
        activo=user.activo,
        fecha_registro=user.fecha_registro
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Eliminar usuario (Solo administradores)"""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user.delete()
    return None
