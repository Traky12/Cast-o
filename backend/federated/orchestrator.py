from __future__ import annotations

import os

from fastapi import FastAPI

from .routes import router as federated_router


app = FastAPI(
    title="Castuo Federated Orchestrator",
    description="Coordinador federado para Shopware + CTAEX + farmers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(federated_router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "TRL9_FEDERATED_LIVE",
        "node_type": "orchestrator",
        "node_id": os.getenv("NODE_ID", "orchestrator"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("FEDERATED_ORCHESTRATOR_PORT", "8002")))

