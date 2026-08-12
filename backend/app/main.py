import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.middleware.rate_limiter import LoginRateLimitingMiddleware
from backend.app.routers import (
    health,
    patients,
    vitals,
    predictions,
    alerts,
    auth,
    dashboard,
    edge,
    monitoring,
    demo,
    websocket_router
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack clinical RPM platform powered by Edge AI and real-time WebSockets.",
    version=settings.VERSION
)

# Enforce Security Rate Limiting Middleware
app.add_middleware(LoginRateLimitingMiddleware, max_requests=settings.LOGIN_RATE_LIMIT_PER_MINUTE)

# Enable CORS Middleware with environment configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API & WebSocket Routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(vitals.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(edge.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(websocket_router.router)

# Serve Frontend Static Files & SPA Root
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/patients", response_class=HTMLResponse)
@app.get("/alerts", response_class=HTMLResponse)
@app.get("/history", response_class=HTMLResponse)
@app.get("/monitoring", response_class=HTMLResponse)
@app.get("/settings", response_class=HTMLResponse)
def serve_frontend_spa():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>RPM Edge AI API Backend is Running. Frontend index.html not found.</h2>")
