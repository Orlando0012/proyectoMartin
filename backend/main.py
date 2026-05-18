from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI(title="Sistema de Logs - Robot Martín")

# Se conecta a MongoDB usando la variable de entorno que definimos en el docker-compose
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/logs_robotica")
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    logs_collection = db["eventos"]
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")

# Modelo de datos que debe enviar el robot o cliente
class Evento(BaseModel):
    componente: str  # Ejemplo: "Motor Izquierdo", "Sensor UltraSonido", "WiFi"
    tipo_accion: str # Ejemplo: "INFO", "WARNING", "ERROR"
    descripcion: str # Ejemplo: "Obstáculo detectado a 10cm"

@app.get("/")
def inicio():
    return {"mensaje": "Servidor de Logs de Martín Activo"}

# Endpoint para recibir los logs (¡Requerimiento del proyecto!)
@app.post("/api/logs")
def registrar_evento(evento: Evento):
    try:
        # Transformamos el modelo a un diccionario de Python y le agregamos el timestamp del servidor
        log_dict = evento.model_dump()
        log_dict["timestamp"] = datetime.utcnow()
        
        # Guardamos en MongoDB
        resultado = logs_collection.insert_one(log_dict)
        
        return {
            "estado": "guardado", 
            "id_registro": str(resultado.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar el log: {str(e)}")

# Endpoint para que el Frontend consuma los datos (¡Requerimiento del proyecto!)
@app.get("/api/logs")
def obtener_logs():
    try:
        # Trae los últimos 50 logs ordenados del más reciente al más antiguo
        registros = list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")