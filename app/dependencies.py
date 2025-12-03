from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.auth import decode_token
from app.models import User, UserRole

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener el usuario autenticado actual desde el token JWT"""
    token = credentials.credentials
    payload = decode_token(token)
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = await User.find_one(User.email == email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def require_role(required_roles: list[UserRole]):
    """Dependencia para requerir roles específicos"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}"
            )
        return current_user
    return role_checker


# Dependencias comunes de roles
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Requerir rol ADMIN"""
    if current_user.rol != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_supervisor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Requerir rol SUPERVISOR o ADMIN"""
    if current_user.rol not in [UserRole.SUPERVISOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor or Admin privileges required"
        )
    return current_user
