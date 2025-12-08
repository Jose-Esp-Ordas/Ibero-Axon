from fastapi import APIRouter, Depends
from typing import List
from app.models import User
from app.schemas import (
    PeticionRiesgo,
    PeticionRiesgoRespuesta,
    AnomaliaRespuesta
    )
from app.services.ai_service import ai_service
from app.dependencies import get_current_user, require_supervisor_or_admin

router = APIRouter(prefix="/ai", tags=["AI Analytics"])


@router.post("/puntaje-riesgo", response_model=PeticionRiesgoRespuesta)
async def calculate_risk_score(
    request: PeticionRiesgo,
    use_ai: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Calcular puntaje de riesgo para una pieza basado en métricas de producción
    
    Parámetros:
    - serial: Serial de la pieza
    - num_retrabajos: Número de operaciones de retrabajo
    - tiempo_total_segundos: Tiempo total en producción (segundos)
    - estacion_actual: Nombre de la estación actual
    - tipo_pieza: Tipo de pieza
    - use_ai: Usar mejora de Gemini AI (por defecto: True)
    
    Retorna puntaje de riesgo, nivel de riesgo y explicación
    """
    if use_ai:
        result = await ai_service.calculate_risk_score_with_ai(
            part_id=request.serial,
            num_retrabajos=request.num_retrabajos,
            tiempo_total_segundos=request.tiempo_total_segundos,
            estacion_actual=request.estacion_actual,
            tipo_pieza=request.tipo_pieza
        )
    else:
        result = await ai_service.calculate_risk_score_heuristic(
            part_id=request.serial,
            num_retrabajos=request.num_retrabajos,
            tiempo_total_segundos=request.tiempo_total_segundos,
            estacion_actual=request.estacion_actual,
            tipo_pieza=request.tipo_pieza
        )
    
    return PeticionRiesgoRespuesta(
        riesgo_falla=result["riesgo_falla"],
        nivel=result["nivel"],
        explicacion=result["explicacion"]
    )


@router.get("/anomalias", response_model=List[AnomaliaRespuesta])
async def detect_anomalies(
    current_user: User = Depends(require_supervisor_or_admin)
):
    """
    Detectar piezas anómalas basándose en tiempo de ciclos o retrabajos
    
    Retorna lista de piezas que se desvían del promedio de su tipo
    """
    anomalies = await ai_service.detect_anomalies()
    
    return [
        AnomaliaRespuesta(
            part_id=anomaly["part_id"],
            tipo_pieza=anomaly["tipo_pieza"],
            tiempo_total_segundos=anomaly["tiempo_total_segundos"],
            num_retrabajos=anomaly["num_retrabajos"],
            promedio_tipo=anomaly["promedio_tipo"],
            desviacion=anomaly["desviacion"],
            es_anomalia=anomaly["es_anomalia"],
            razon=anomaly["razon"]
        )
        for anomaly in anomalies
    ]
