import pytest
from httpx import AsyncClient
from app.main import app
from app.models import User, Part, Station, TraceEvent, UserRole, PartStatus
from app.database import init_db
from app.auth import get_password_hash


@pytest.fixture(scope="session")
async def test_db():
    """Inicializar base de datos de prueba"""
    await init_db()
    yield
    # Limpieza después de las pruebas
    await User.find_all().delete()
    await Part.find_all().delete()
    await Station.find_all().delete()
    await TraceEvent.find_all().delete()


@pytest.fixture
async def test_admin_user(test_db):
    """Crear un usuario administrador de prueba"""
    user = User(
        nombre="Test Admin",
        email="admin@teset.com",
        password=get_password_hash("admin123"),
        rol=UserRole.ADMIN
    )
    await user.insert()
    yield user
    await user.delete()


@pytest.fixture
async def test_operator_user(test_db):
    """Crear un usuario operador de prueba"""
    user = User(
        nombre="Test Operator",
        email="operator@test.com",
        password=get_password_hash("operator123"),
        rol=UserRole.OPERADOR
    )
    await user.insert()
    yield user
    await user.delete()


@pytest.fixture
async def admin_token(test_admin_user):
    """Obtener token de autenticación de administrador"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "admin@teset.com", "password": "admin123"}
        )
        return response.json()["access_token"]


@pytest.fixture
async def operator_token(test_operator_user):
    """Obtener token de autenticación de operador"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "operator@test.com", "password": "operator123"}
        )
        return response.json()["access_token"]


# ==================== Pruebas de Autenticación ====================

@pytest.mark.asyncio
async def test_register_user():
    """Probar registro de usuario"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "nombre": "New User",
                "email": "newuser@test.com",
                "password": "password123",
                "rol": "OPERADOR"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["nombre"] == "New User"
        
        # Limpieza
        user = await User.find_one(User.email == "newuser@test.com")
        await user.delete()


@pytest.mark.asyncio
async def test_login(test_admin_user):
    """Probar inicio de sesión de usuario"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user(admin_token):
    """Probar obtención de información del usuario actual"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["rol"] == "ADMIN"


# ==================== Pruebas de Piezas ====================

@pytest.mark.asyncio
async def test_create_part(operator_token):
    """Probar creación de una nueva pieza"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/parts/",
            json={
                "serial": "TEST-001",
                "tipo_pieza": "X1",
                "lote": "LOTE-TEST-01",
                "status": "EN_PROCESO"
            },
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["serial"] == "TEST-001"
        assert data["tipo_pieza"] == "X1"
        
        # Limpieza
        part = await Part.find_one(Part.serial == "TEST-001")
        await part.delete()


@pytest.mark.asyncio
async def test_list_parts(operator_token):
    """Probar listado de piezas"""
    # Crear pieza de prueba
    part = Part(serial="TEST-002", tipo_pieza="X1", lote="LOTE-TEST-01", status=PartStatus.EN_PROCESO)
    await part.insert()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/parts/",
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    # Limpieza
    await part.delete()


# ==================== Pruebas de Estaciones ====================

@pytest.mark.asyncio
async def test_create_station(admin_token):
    """Probar creación de una estación (solo administrador)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/stations/",
            json={
                "nombre": "Test Station",
                "tipo": "INSPECCION",
                "linea": "Linea A",
                "activa": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Test Station"
        
        # Limpieza
        station = await Station.find_one(Station.nombre == "Test Station")
        await station.delete()


@pytest.mark.asyncio
async def test_create_station_forbidden(operator_token):
    """Probar que los operadores no pueden crear estaciones"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/stations/",
            json={
                "nombre": "Test Station",
                "tipo": "INSPECCION",
                "linea": "Linea A"
            },
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        assert response.status_code == 403


# ==================== Pruebas de Métricas ====================

@pytest.mark.asyncio
async def test_get_parts_by_status(admin_token):
    """Probar obtención de conteo de piezas por estatus"""
    # Create test parts
    part1 = Part(serial="METRIC-001", tipo_pieza="X1", lote="LOTE-01", status=PartStatus.OK)
    part2 = Part(serial="METRIC-002", tipo_pieza="X1", lote="LOTE-01", status=PartStatus.SCRAP)
    await part1.insert()
    await part2.insert()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/metrics/parts-by-status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "OK" in data
        assert "SCRAP" in data
        assert isinstance(data["OK"], int)
    
    # Limpieza
    await part1.delete()
    await part2.delete()


# ==================== Pruebas de IA ====================

@pytest.mark.asyncio
async def test_risk_score_calculation(operator_token):
    """Probar cálculo de puntuación de riesgo con IA"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/ai/risk-score?use_ai=false",  # Usar solo heurística para pruebas
            json={
                "part_id": "TEST-AI-001",
                "num_retrabajos": 2,
                "tiempo_total_segundos": 1500,
                "estacion_actual": "INSPECCION_FINAL",
                "tipo_pieza": "X1"
            },
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "riesgo_falla" in data
        assert "nivel" in data
        assert "explicacion" in data
        assert 0.0 <= data["riesgo_falla"] <= 1.0
        assert data["nivel"] in ["BAJO", "MEDIO", "ALTO"]
