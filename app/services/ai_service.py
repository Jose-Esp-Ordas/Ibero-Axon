import google.generativeai as genai
from typing import Optional, Dict, Any
from app.config import settings
from app.models import TraceEvent, Part, EventResult
from statistics import mean, stdev
from collections import defaultdict


class AIService:
    def __init__(self):
        """Inicializar servicio de Gemini AI"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        else:
            self.model = None
    
    async def calculate_risk_score_heuristic(
        self,
        part_id: str,
        num_retrabajos: int,
        tiempo_total_segundos: float,
        estacion_actual: str,
        tipo_pieza: str
    ) -> Dict[str, Any]:
        """
        Calcular puntuación de riesgo usando reglas heurísticas y datos históricos
        """
        # Obtener datos históricos para este tipo de pieza
        parts_same_type = await Part.find(Part.tipo_pieza == tipo_pieza).to_list()
        part_ids = [p.serial for p in parts_same_type]
        
        # Obtener todos los eventos para piezas del mismo tipo
        from beanie.operators import In
        events = await TraceEvent.find(
            In(TraceEvent.part_id, part_ids),
            TraceEvent.timestamp_salida != None
        ).to_list()
        
        # Calcular tiempos de ciclo promedio y conteo de retrabajos
        cycle_times = []
        retrabajo_counts = defaultdict(int)
        
        for event in events:
            if event.timestamp_salida and event.timestamp_entrada:
                cycle_time = (event.timestamp_salida - event.timestamp_entrada).total_seconds()
                cycle_times.append(cycle_time)
            
            if event.resultado == EventResult.RETRABAJO:
                retrabajo_counts[event.part_id] += 1
        
        # Calcular estadísticas
        avg_cycle_time = mean(cycle_times) if cycle_times else 600  # Por defecto 10 min
        std_cycle_time = stdev(cycle_times) if len(cycle_times) > 1 else avg_cycle_time * 0.3
        avg_retrabajos = mean(retrabajo_counts.values()) if retrabajo_counts else 0
        
        # Factores de cálculo de riesgo
        risk_factors = []
        risk_score = 0.0
        
        # Factor 1: Desviación de tiempo del promedio (0-0.4)
        if tiempo_total_segundos > avg_cycle_time:
            time_deviation = (tiempo_total_segundos - avg_cycle_time) / avg_cycle_time
            time_risk = min(0.4, time_deviation * 0.4)
            risk_score += time_risk
            if time_risk > 0.2:
                risk_factors.append(f"Tiempo {int(time_deviation * 100)}% superior al promedio")
        
        # Factor 2: Número de retrabajos (0-0.35)
        if num_retrabajos > 0:
            retrabajo_risk = min(0.35, num_retrabajos * 0.15)
            risk_score += retrabajo_risk
            risk_factors.append(f"Tiene {num_retrabajos} retrabajo(s)")
        
        # Factor 3: Tipo de estación (0-0.15)
        critical_stations = ["INSPECCION_FINAL", "PRUEBA"]
        if any(critical in estacion_actual.upper() for critical in critical_stations):
            risk_score += 0.15
            risk_factors.append("En estación crítica")
        
        # Factor 4: Valores de tiempo extremos (0-0.1)
        if tiempo_total_segundos > avg_cycle_time + (2 * std_cycle_time):
            risk_score += 0.1
            risk_factors.append("Tiempo extremadamente alto")
        
        # Determinar nivel de riesgo
        if risk_score >= 0.7:
            nivel = "ALTO"
        elif risk_score >= 0.4:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"
        
        # Generar explicación
        explicacion = " | ".join(risk_factors) if risk_factors else "Dentro de parámetros normales"
        
        return {
            "riesgo_falla": round(min(1.0, risk_score), 2),
            "nivel": nivel,
            "explicacion": explicacion,
            "estadisticas": {
                "tiempo_promedio": round(avg_cycle_time, 2),
                "tiempo_actual": round(tiempo_total_segundos, 2),
                "retrabajos_promedio": round(avg_retrabajos, 2),
                "retrabajos_actual": num_retrabajos
            }
        }
    
    async def calculate_risk_score_with_ai(
        self,
        part_id: str,
        num_retrabajos: int,
        tiempo_total_segundos: float,
        estacion_actual: str,
        tipo_pieza: str
    ) -> Dict[str, Any]:
        """
        Calcular puntuación de riesgo usando Gemini AI (si está disponible)
        """
        # Primero obtener cálculo heurístico
        heuristic_result = await self.calculate_risk_score_heuristic(
            part_id, num_retrabajos, tiempo_total_segundos, estacion_actual, tipo_pieza
        )
        
        # Si Gemini AI no está configurado, retornar resultado heurístico
        if not self.model:
            print("⚠️  Gemini AI no configurado - usando solo heurística")
            return heuristic_result
        
        try:
            print("🤖 Consultando Gemini AI para análisis de riesgo...")
            # Preparar contexto para IA
            prompt = f"""
            Analiza el siguiente caso de una pieza en producción y evalúa el riesgo de falla:
            
            - ID de Pieza: {part_id}
            - Tipo de Pieza: {tipo_pieza}
            - Número de Retrabajos: {num_retrabajos}
            - Tiempo Total en Producción: {tiempo_total_segundos} segundos
            - Estación Actual: {estacion_actual}
            - Tiempo Promedio para este Tipo: {heuristic_result['estadisticas']['tiempo_promedio']} segundos
            - Retrabajos Promedio para este Tipo: {heuristic_result['estadisticas']['retrabajos_promedio']}
            
            Análisis Heurístico:
            - Riesgo Calculado: {heuristic_result['riesgo_falla']}
            - Nivel: {heuristic_result['nivel']}
            - Factores: {heuristic_result['explicacion']}
            
            Proporciona:
            1. Un score de riesgo ajustado (0.0 a 1.0)
            2. Nivel de riesgo (BAJO/MEDIO/ALTO)
            3. Una explicación breve (máximo 150 caracteres)
            
            Formato de respuesta:
            SCORE: [número]
            NIVEL: [nivel]
            EXPLICACION: [texto]
            """
            
            response = self.model.generate_content(prompt)
            ai_text = response.text
            
            # Parsear respuesta de IA
            lines = ai_text.split('\n')
            ai_score = heuristic_result['riesgo_falla']
            ai_nivel = heuristic_result['nivel']
            ai_explicacion = heuristic_result['explicacion']
            
            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        ai_score = float(line.split(':')[1].strip())
                    except:
                        pass
                elif line.startswith('NIVEL:'):
                    ai_nivel = line.split(':')[1].strip()
                elif line.startswith('EXPLICACION:'):
                    ai_explicacion = line.split(':', 1)[1].strip()
            
            print(f"✅ Gemini AI completado - Score: {ai_score}, Nivel: {ai_nivel}")
            
            return {
                "riesgo_falla": round(min(1.0, ai_score), 2),
                "nivel": ai_nivel,
                "explicacion": ai_explicacion,
                "estadisticas": heuristic_result['estadisticas'],
                "ai_enhanced": True
            }
        
        except Exception as e:
            print(f"❌ Error en Gemini AI: {str(e)} - usando heurística")
            # Si la IA falla, retornar resultado heurístico
            heuristic_result["ai_enhanced"] = False
            heuristic_result["ai_error"] = str(e)
            return heuristic_result
    
    async def detect_anomalies(self) -> list[Dict[str, Any]]:
        """
        Detectar piezas anómalas basadas en tiempo de ciclo y conteo de retrabajos
        """
        # Obtener todas las piezas
        parts = await Part.find_all().to_list()
        
        # Agrupar por tipo_pieza
        parts_by_type = defaultdict(list)
        for part in parts:
            parts_by_type[part.tipo_pieza].append(part)
        
        anomalies = []
        
        for tipo_pieza, parts_list in parts_by_type.items():
            # Obtener eventos para estas piezas
            part_ids = [p.serial for p in parts_list]
            from beanie.operators import In
            events = await TraceEvent.find(
                In(TraceEvent.part_id, part_ids),
                TraceEvent.timestamp_salida != None
            ).to_list()
            
            # Calcular tiempo total y retrabajos por pieza
            part_stats = defaultdict(lambda: {"tiempo_total": 0, "num_retrabajos": 0})
            
            for event in events:
                if event.timestamp_salida and event.timestamp_entrada:
                    cycle_time = (event.timestamp_salida - event.timestamp_entrada).total_seconds()
                    part_stats[event.part_id]["tiempo_total"] += cycle_time
                
                if event.resultado == EventResult.RETRABAJO:
                    part_stats[event.part_id]["num_retrabajos"] += 1
            
            # Calcular promedio y desviación estándar
            tiempos = [stats["tiempo_total"] for stats in part_stats.values() if stats["tiempo_total"] > 0]
            retrabajos = [stats["num_retrabajos"] for stats in part_stats.values()]
            
            if not tiempos:
                continue
            
            avg_tiempo = mean(tiempos)
            std_tiempo = stdev(tiempos) if len(tiempos) > 1 else avg_tiempo * 0.3
            avg_retrabajos = mean(retrabajos) if retrabajos else 0
            
            # Detectar anomalías (>2 desviaciones estándar o retrabajos excesivos)
            for part_id, stats in part_stats.items():
                tiempo = stats["tiempo_total"]
                num_retrabajos = stats["num_retrabajos"]
                
                is_anomaly = False
                razon = []
                
                # Anomalía de tiempo
                if tiempo > avg_tiempo + (2 * std_tiempo):
                    is_anomaly = True
                    desviacion = ((tiempo - avg_tiempo) / avg_tiempo) * 100
                    razon.append(f"Tiempo {int(desviacion)}% superior al promedio")
                
                # Anomalía de retrabajo
                if num_retrabajos > avg_retrabajos + 1 and num_retrabajos > 1:
                    is_anomaly = True
                    razon.append(f"{num_retrabajos} retrabajos (promedio: {avg_retrabajos:.1f})")
                
                if is_anomaly:
                    anomalies.append({
                        "part_id": part_id,
                        "tipo_pieza": tipo_pieza,
                        "tiempo_total_segundos": round(tiempo, 2),
                        "num_retrabajos": num_retrabajos,
                        "promedio_tipo": round(avg_tiempo, 2),
                        "desviacion": round(((tiempo - avg_tiempo) / avg_tiempo * 100) if avg_tiempo > 0 else 0, 2),
                        "es_anomalia": True,
                        "razon": " | ".join(razon)
                    })
        
        return sorted(anomalies, key=lambda x: x["desviacion"], reverse=True)


# Instancia singleton
ai_service = AIService()
