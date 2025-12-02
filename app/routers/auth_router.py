from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.config import settings
from app.models import User, UserRole
from app.schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate, Token
)
from app.auth import (
    authenticate_user, create_access_token, get_password_hash
)
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        nombre=user_data.nombre,
        email=user_data.email,
        password=hashed_password,
        rol=user_data.rol
    )
    await new_user.insert()
    
    return UserResponse(
        id=str(new_user.id),
        nombre=new_user.nombre,
        email=new_user.email,
        rol=new_user.rol,
        activo=new_user.activo,
        fecha_registro=new_user.fecha_registro
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login and receive JWT token"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol.value},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        nombre=current_user.nombre,
        email=current_user.email,
        rol=current_user.rol,
        activo=current_user.activo,
        fecha_registro=current_user.fecha_registro
    )
