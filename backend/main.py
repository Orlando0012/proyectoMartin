from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI(title="Sistema de Logs - Robot Martín")

# ====================================================================
# CONFIGURACIÓN DE CORS (Soluciona el error de conexión en el Frontend)
# ====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que tu frontend acceda desde cualquier navegador
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST y opciones de prueba
    allow_headers=["*"],
)

# Conexión a MongoDB mediante la variable de entorno de Docker
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/logs_robotica")
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    logs_collection = db["eventos"]
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")

# ====================================================================
# MODELO DE DATOS (Soporta ambos formatos para evitar errores 422)
# ====================================================================
class Evento(BaseModel):
    componente: str  
    tipo: str | None = None         # Formato usado en frontend y pruebas cortas
    tipo_accion: str | None = None  # Formato original del backend anterior
    descripcion: str 

@app.get("/")
def inicio():
    return {"mensaje": "Servidor de Logs de Martín Activo"}

# ====================================================================
# ENDPOINT POST: Recibe los logs del robot o scripts de prueba
# ====================================================================
@app.post("/api/logs")
def registrar_evento(evento: Evento):
    try:
        log_dict = evento.model_dump()
        
        # Homologación: Si mandan 'tipo_accion', lo guardamos como 'tipo' para la tabla
        if log_dict.get("tipo_accion") and not log_dict.get("tipo"):
            log_dict["tipo"] = log_dict["tipo_accion"]
            
        # Limpiamos el campo duplicado para mantener la BD limpia
        log_dict.pop("tipo_accion", None)
        
        # Guardamos la fecha en formato ISO String, ideal para leer en JavaScript
        log_dict["timestamp"] = datetime.utcnow().isoformat()
        
        # Inserción en la base de datos MongoDB
        resultado = logs_collection.insert_one(log_dict)
        
        return {
            "estado": "guardado", 
            "id_registro": str(resultado.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar el log: {str(e)}")

# ====================================================================
# ENDPOINT GET: Envía los logs guardados hacia el Dashboard web
# ====================================================================
@app.get("/api/logs")
def obtener_logs():
    try:
        # Extrae los últimos 50 logs del más reciente al más antiguo
        registros = list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")