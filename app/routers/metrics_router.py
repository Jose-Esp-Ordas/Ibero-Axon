from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from app.models import Part, TraceEvent, Station, User, PartStatus, EventResult
from app.dependencies import get_current_user, require_supervisor_or_admin

router = APIRouter(prefix="/metricas", tags=["Dashboard Metrics"])


@router.get("/piezas-por-estado")
async def get_parts_by_status(
    current_user: User = Depends(require_supervisor_or_admin)
) -> Dict[str, int]:
    """
    Obtener conteo de piezas por estado
    Retorna: {"OK": 10, "SCRAP": 2, "EN_PROCESO": 5, "RETRABAJO": 1}
    """
    parts = await Part.find_all().to_list()
    
    status_counts = {
        PartStatus.OK.value: 0,
        PartStatus.SCRAP.value: 0,
        PartStatus.EN_PROCESO.value: 0,
        PartStatus.RETRABAJO.value: 0
    }
    
    for part in parts:
        status_counts[part.status.value] += 1
    
    return status_counts


@router.get("/produccion")
async def get_throughput(
    fecha_desde: datetime = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    fecha_hasta: datetime = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(require_supervisor_or_admin)
) -> List[Dict[str, Any]]:
    """
    Obtener piezas producidas por día en el rango de fechas
    Retorna: [{"fecha": "2024-12-01", "cantidad": 15}, ...]
    """
    parts = await Part.find(
        Part.fecha_creacion >= fecha_desde,
        Part.fecha_creacion <= fecha_hasta
    ).to_list()
    
    # Agrupar por fecha
    daily_counts = defaultdict(int)
    for part in parts:
        date_key = part.fecha_creacion.strftime("%Y-%m-%d")
        daily_counts[date_key] += 1
    
    # Convertir a lista ordenada
    result = [
        {"fecha": date, "cantidad": count}
        for date, count in sorted(daily_counts.items())
    ]
    
    return result


@router.get("/tiempo-ciclo-estacion")
async def get_station_cycle_time(
    current_user: User = Depends(require_supervisor_or_admin)
) -> List[Dict[str, Any]]:
    """
    Obtener tiempo de ciclo promedio por estación (en segundos)
    Retorna: [{"station_id": "...", "station_name": "...", "avg_cycle_time_seconds": 150.5}, ...]
    """
    # Obtener todos los eventos completos (aquellos con timestamp_salida)
    events = await TraceEvent.find(
        TraceEvent.timestamp_salida != None
    ).to_list()
    
    # Calcular tiempos de ciclo por estación
    station_times = defaultdict(list)
    for event in events:
        if event.timestamp_salida and event.timestamp_entrada:
            cycle_time = (event.timestamp_salida - event.timestamp_entrada).total_seconds()
            station_times[event.station_id].append(cycle_time)
    
    # Calcular promedios y obtener nombres de estaciones
    result = []
    for station_id, times in station_times.items():
        avg_time = sum(times) / len(times) if times else 0
        
        # Obtener nombre de la estación
        station = await Station.get(station_id)
        station_name = station.nombre if station else "Unknown"
        
        result.append({
            "station_id": station_id,
            "station_name": station_name,
            "avg_cycle_time_seconds": round(avg_time, 2),
            "sample_count": len(times)
        })
    
    return sorted(result, key=lambda x: x["avg_cycle_time_seconds"], reverse=True)


@router.get("/tasa-desecho")
async def get_scrap_rate(
    tipo_pieza: str = Query(None, description="Filter by part type"),
    station_id: str = Query(None, description="Filter by station"),
    current_user: User = Depends(require_supervisor_or_admin)
) -> Dict[str, Any]:
    """
    Obtener tasa de scrap (porcentaje de piezas con resultado SCRAP)
    Puede filtrarse por tipo de pieza y/o estación
    """
    # Construir query para eventos
    query_filters = [TraceEvent.resultado != None]
    
    if station_id:
        query_filters.append(TraceEvent.station_id == station_id)
    
    events = await TraceEvent.find(*query_filters).to_list()
    
    # Filtrar por tipo_pieza si se especifica
    if tipo_pieza:
        # Obtener todas las piezas de este tipo
        parts_of_type = await Part.find(Part.tipo_pieza == tipo_pieza).to_list()
        part_serials = {part.serial for part in parts_of_type}
        events = [e for e in events if e.part_id in part_serials]
    
    # Calcular tasa de scrap
    total_events = len(events)
    scrap_events = sum(1 for e in events if e.resultado == EventResult.SCRAP)
    
    scrap_rate = (scrap_events / total_events * 100) if total_events > 0 else 0
    
    # Agrupar por tipo_pieza para desglose detallado
    part_type_stats = defaultdict(lambda: {"total": 0, "scrap": 0})
    
    for event in events:
        part = await Part.find_one(Part.serial == event.part_id)
        if part:
            part_type_stats[part.tipo_pieza]["total"] += 1
            if event.resultado == EventResult.SCRAP:
                part_type_stats[part.tipo_pieza]["scrap"] += 1
    
    # Calcular tasas por tipo
    breakdown = []
    for tipo, stats in part_type_stats.items():
        rate = (stats["scrap"] / stats["total"] * 100) if stats["total"] > 0 else 0
        breakdown.append({
            "tipo_pieza": tipo,
            "total_eventos": stats["total"],
            "scrap_eventos": stats["scrap"],
            "scrap_rate_percent": round(rate, 2)
        })
    
    return {
        "overall_scrap_rate_percent": round(scrap_rate, 2),
        "total_eventos": total_events,
        "scrap_eventos": scrap_events,
        "breakdown_by_type": breakdown,
        "filters": {
            "tipo_pieza": tipo_pieza,
            "station_id": station_id
        }
    }


@router.get("/resumen")
async def get_quality_summary(
    current_user: User = Depends(require_supervisor_or_admin)
) -> Dict[str, Any]:
    """
    Obtener resumen general de métricas de calidad
    """
    # Obtener todas las piezas
    parts = await Part.find_all().to_list()
    total_parts = len(parts)
    
    # Contar por estado
    ok_parts = sum(1 for p in parts if p.status == PartStatus.OK)
    scrap_parts = sum(1 for p in parts if p.status == PartStatus.SCRAP)
    retrabajo_parts = sum(1 for p in parts if p.status == PartStatus.RETRABAJO)
    en_proceso_parts = sum(1 for p in parts if p.status == PartStatus.EN_PROCESO)
    
    # Obtener todos los eventos
    events = await TraceEvent.find(TraceEvent.resultado != None).to_list()
    total_events = len(events)
    
    # Contar eventos por resultado
    ok_events = sum(1 for e in events if e.resultado == EventResult.OK)
    scrap_events = sum(1 for e in events if e.resultado == EventResult.SCRAP)
    retrabajo_events = sum(1 for e in events if e.resultado == EventResult.RETRABAJO)
    
    return {
        "total_parts": total_parts,
        "parts_by_status": {
            "OK": ok_parts,
            "SCRAP": scrap_parts,
            "RETRABAJO": retrabajo_parts,
            "EN_PROCESO": en_proceso_parts
        },
        "parts_percentages": {
            "ok_percent": round((ok_parts / total_parts * 100) if total_parts > 0 else 0, 2),
            "scrap_percent": round((scrap_parts / total_parts * 100) if total_parts > 0 else 0, 2),
            "retrabajo_percent": round((retrabajo_parts / total_parts * 100) if total_parts > 0 else 0, 2)
        },
        "total_events": total_events,
        "events_by_result": {
            "OK": ok_events,
            "SCRAP": scrap_events,
            "RETRABAJO": retrabajo_events
        },
        "first_pass_yield": round((ok_events / total_events * 100) if total_events > 0 else 0, 2)
    }
