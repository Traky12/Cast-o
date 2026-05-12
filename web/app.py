"""
Sitio ligero Castúo (contenido Markdown + dashboard de nodos de maquetación).
Ejecutar desde la raíz del repo: uvicorn web.app:app --reload --app-dir .
"""

from pathlib import Path

import markdown
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Castúo-System Web", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))


def _read_md(name: str) -> str:
    p = BASE / "content" / name
    if not p.is_file():
        return f"_(Falta {p.name})_"
    return p.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    body = _read_md("educational.md")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "content": markdown.markdown(body, extensions=["tables", "fenced_code"])},
    )


@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    body = _read_md("security.md")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "content": markdown.markdown(body, extensions=["tables", "fenced_code"])},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Serie sintética para maquetación UI (sustituir por API/DB real).
    nodes = [
        {
            "id": f"Nodo-{i:03d}",
            "location": "Extremadura",
            "security_status": "Integridad local (demo)",
            "yield": round(94.0 + (i % 9) * 0.4, 1),
        }
        for i in range(1, 368)
    ]
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "nodes": nodes},
    )
