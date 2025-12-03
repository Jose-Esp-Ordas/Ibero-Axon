"""
Script para inicializar datos de ejemplo en la base de datos
Ejecutar: python scripts/init_data.py
"""
import asyncio
from datetime import datetime, timedelta
from app.database import init_db
from app.models import User, Part, Station, TraceEvent, UserRole, PartStatus, EventResult, StationType
from app.auth import get_password_hash


async def create_sample_data():
    """Crear datos de ejemplo para pruebas"""
    print("🔄 Inicializando base de datos...")
    await init_db()
    
    # Clear existing data
    print("🗑️ Clearing existing data...")
    await User.find_all().delete()
    await Part.find_all().delete()
    await Station.find_all().delete()
    await TraceEvent.find_all().delete()
    
    # Crear usuarios
    print("👥 Creando usuarios...")
    admin = User(
        nombre="Administrator",
        email="admin@iberoaxon.com",
        password=get_password_hash("admin123"),
        rol=UserRole.ADMIN
    )
    await admin.insert()
    
    supervisor = User(
        nombre="Supervisor Principal",
        email="supervisor@iberoaxon.com",
        password=get_password_hash("supervisor123"),
        rol=UserRole.SUPERVISOR
    )
    await supervisor.insert()
    
    operator1 = User(
        nombre="Operador 1",
        email="operador1@iberoaxon.com",
        password=get_password_hash("operador123"),
        rol=UserRole.OPERADOR
    )
    await operator1.insert()
    
    operator2 = User(
        nombre="Operador 2",
        email="operador2@iberoaxon.com",
        password=get_password_hash("operador123"),
        rol=UserRole.OPERADOR
    )
    await operator2.insert()
    
    print(f"  ✅ Creados {await User.count()} usuarios")
    
    # Crear estaciones
    print("🏭 Creando estaciones...")
    stations = [
        Station(nombre="Ensamble Inicial", tipo=StationType.ENSAMBLE, linea="Línea A"),
        Station(nombre="Inspección Visual", tipo=StationType.INSPECCION, linea="Línea A"),
        Station(nombre="Prueba Funcional", tipo=StationType.PRUEBA, linea="Línea A"),
        Station(nombre="Inspección Final", tipo=StationType.INSPECCION_FINAL, linea="Línea A"),
        Station(nombre="Ensamble B1", tipo=StationType.ENSAMBLE, linea="Línea B"),
        Station(nombre="Prueba B1", tipo=StationType.PRUEBA, linea="Línea B"),
    ]
    
    for station in stations:
        await station.insert()
    
    print(f"  ✅ Creadas {len(stations)} estaciones")
    
    # Crear piezas y eventos de trazabilidad
    print("📦 Creando piezas y eventos de trazabilidad...")
    base_time = datetime.utcnow() - timedelta(days=7)
    
    part_types = ["X1", "X2", "Y1"]
    lotes = ["LOTE-2024-12-01", "LOTE-2024-12-02"]
    
    parts_created = 0
    events_created = 0
    
    for i in range(50):
        tipo_pieza = part_types[i % len(part_types)]
        lote = lotes[i % len(lotes)]
        
        # Determinar estatus final (80% OK, 10% SCRAP, 10% RETRABAJO)
        rand_val = i % 10
        if rand_val < 8:
            final_status = PartStatus.OK
        elif rand_val == 8:
            final_status = PartStatus.SCRAP
        else:
            final_status = PartStatus.RETRABAJO
        
        part = Part(
            serial=f"PZA-{i+1:04d}",
            tipo_pieza=tipo_pieza,
            lote=lote,
            status=final_status,
            fecha_creacion=base_time + timedelta(hours=i)
        )
        await part.insert()
        parts_created += 1
        
        # Crear eventos de trazabilidad para cada pieza a través de las estaciones
        current_time = part.fecha_creacion
        
        for station in stations[:4]:  # Usar las primeras 4 estaciones para Línea A
            # Simular tiempo de ciclo (300-900 segundos)
            cycle_time = 300 + (i * 13) % 600
            timestamp_entrada = current_time
            timestamp_salida = current_time + timedelta(seconds=cycle_time)
            
            # Determinar resultado
            if station.tipo == StationType.INSPECCION_FINAL:
                if final_status == PartStatus.SCRAP:
                    resultado = EventResult.SCRAP
                elif final_status == PartStatus.RETRABAJO:
                    resultado = EventResult.RETRABAJO
                else:
                    resultado = EventResult.OK
            else:
                # Estaciones anteriores mayormente OK
                if i % 15 == 0:
                    resultado = EventResult.RETRABAJO
                else:
                    resultado = EventResult.OK
            
            event = TraceEvent(
                part_id=part.serial,
                station_id=str(station.id),
                timestamp_entrada=timestamp_entrada,
                timestamp_salida=timestamp_salida,
                resultado=resultado,
                operador_id=str(operator1.id) if i % 2 == 0 else str(operator2.id),
                observaciones=f"Procesado correctamente" if resultado == EventResult.OK else f"Requiere atención"
            )
            await event.insert()
            events_created += 1
            
            current_time = timestamp_salida + timedelta(minutes=5)
            
            # Si es SCRAP, detener procesamiento
            if resultado == EventResult.SCRAP:
                break
    
    # Crear algunas piezas aún en proceso
    for i in range(5):
        part = Part(
            serial=f"PZA-PROC-{i+1:03d}",
            tipo_pieza=part_types[i % len(part_types)],
            lote=lotes[0],
            status=PartStatus.EN_PROCESO,
            fecha_creacion=datetime.utcnow() - timedelta(hours=i)
        )
        await part.insert()
        parts_created += 1
        
        # Crear trazabilidad parcial (solo primeras 2 estaciones)
        current_time = part.fecha_creacion
        for station in stations[:2]:
            event = TraceEvent(
                part_id=part.serial,
                station_id=str(station.id),
                timestamp_entrada=current_time,
                timestamp_salida=current_time + timedelta(minutes=10),
                resultado=EventResult.OK,
                operador_id=str(operator1.id),
                observaciones="En proceso"
            )
            await event.insert()
            events_created += 1
            current_time += timedelta(minutes=15)
    
    print(f"  ✅ Creadas {parts_created} piezas")
    print(f"  ✅ Creados {events_created} eventos de trazabilidad")
    
    # Resumen
    print("\n" + "="*50)
    print("✅ ¡BASE DE DATOS INICIALIZADA EXITOSAMENTE!")
    print("="*50)
    print("\n📊 Resumen:")
    print(f"  Usuarios: {await User.count()}")
    print(f"  Estaciones: {await Station.count()}")
    print(f"  Piezas: {await Part.count()}")
    print(f"  Eventos de Trazabilidad: {await TraceEvent.count()}")
    
    print("\n🔐 Credenciales de Acceso:")
    print("  Admin:")
    print("    Email: admin@iberoaxon.com")
    print("    Password: admin123")
    print("  Supervisor:")
    print("    Email: supervisor@iberoaxon.com")
    print("    Password: supervisor123")
    print("  Operator:")
    print("    Email: operador1@iberoaxon.com")
    print("    Password: operador123")
    
    print("\n🚀 Ahora puedes iniciar el servidor API:")
    print("   cd app")
    print("   python main.py")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
