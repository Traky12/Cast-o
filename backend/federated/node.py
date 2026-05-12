from __future__ import annotations

import os

from fastapi import FastAPI

from .routes import router as federated_router


app = FastAPI(
    title="Castuo Federated Edge Node",
    description="Nodo edge federado TRL9 para farmers / RPi4.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(federated_router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "TRL9_FEDERATED_LIVE",
        "node_type": "edge",
        "node_id": os.getenv("NODE_ID", "edge-node"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("FEDERATED_EDGE_PORT", "8001")))

