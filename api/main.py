"""
Gestor de Consorcios - FastAPI Backend
Puerto: 8000  |  Frontend Tauri: localhost:1420
"""
import sys
import os

# Asegurar que el proyecto raiz este en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import consorcios, finanzas, dashboard, config_router, reportes
from api.database import DB_PATH, run_migrations

run_migrations(DB_PATH)

app = FastAPI(
    title="Gestor Consorcios API",
    description="Backend REST para el Gestor de Consorcios",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: permitir peticiones desde Tauri WebView
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://localhost:5173",   # Vite dev server
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(consorcios.router, prefix="/api")
app.include_router(finanzas.router,   prefix="/api")
app.include_router(dashboard.router,  prefix="/api")
app.include_router(config_router.router, prefix="/api")
app.include_router(reportes.router,    prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
