from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.config import settings
from app.models import User
from app.schemas import (
    UsuarioRegister, UsuarioLogin, UsuarioResponse, Token
)
from app.auth import (
    authenticate_user, create_access_token, get_password_hash
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
        "/registro",
        response_model=UsuarioResponse,
        status_code=status.HTTP_201_CREATED
        )
async def register_user(user_data: UsuarioRegister):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Crear nuevo usuario con contraseña hasheada
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        nombre=user_data.nombre,
        email=user_data.email,
        password=hashed_password,
        rol=user_data.rol
    )
    await new_user.insert()

    return UsuarioResponse(
        id=str(new_user.id),
        nombre=new_user.nombre,
        email=new_user.email,
        rol=new_user.rol,
        activo=new_user.activo,
        fecha_registro=new_user.fecha_registro
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UsuarioLogin):
    """Iniciar sesión y recibir token JWT"""
    user = await authenticate_user(
        user_credentials.email,
        user_credentials.password
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
        )
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol.value},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
        ):
    """Obtener información del usuario actual"""
    return UsuarioResponse(
            id=str(current_user.id),
            nombre=current_user.nombre,
            email=current_user.email,
            rol=current_user.rol,
            activo=current_user.activo,
            fecha_registro=current_user.fecha_registro
        )
