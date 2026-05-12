"""
API simplificada CASTUO-SYSTEM: sensores y recomendaciones Sabionda.
Puedes ejecutar con: uvicorn api_simple:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="CASTUO-SYSTEM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    light: float


@app.get("/")
def read_root():
    return {"message": "CASTUO-SYSTEM API"}


@app.post("/sensors/")
async def create_sensor_data(data: SensorData):
    return {"status": "success", "data": data.model_dump()}


@app.get("/sabionda/recommendations")
async def get_recommendations():
    return {
        "recommendations": [
            {"id": "rec_001", "description": "Ajustar riego para optimizar el crecimiento de la rúcula."},
            {"id": "rec_002", "description": "Aumentar la iluminación en el lote LOT-2026-0002."},
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
