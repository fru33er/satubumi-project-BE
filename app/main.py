import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import insight_topics, rulebooks
from app.api.v1.articles import router as articles_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.contact import router as contact_router
from app.api.v1.monitor import router as monitor_router  # SATUBUMI MONITOR
from app.api.v1.projects import router as projects_router  # SATUBUMI MONITOR
from app.api.v1.rapid_fs import router as rapid_fs_router
from app.api.v1.reports import router as reports_router
from app.api.v1.users import router as users_router
from app.api.v1 import team_member
from app.api.v1 import activity
from app.core.config import settings
from app.core.database import Base, engine

# Buat folder upload jika belum ada
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Inisialisasi tabel DB saat startup (jika belum ada)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="RESTful API Backend Service untuk Satubumi.org & Rapid-FS Carbon Feasibility Scoring Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Serve static files (gambar upload artikel)
# Akses via: GET /static/uploads/{filename}
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers API v1
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(articles_router, prefix=api_v1_prefix)
app.include_router(users_router, prefix=api_v1_prefix)
app.include_router(rapid_fs_router, prefix=api_v1_prefix)
app.include_router(assessments_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)
app.include_router(contact_router, prefix=api_v1_prefix)
app.include_router(insight_topics.router, prefix=api_v1_prefix)
app.include_router(rulebooks.router, prefix="/api/v1")
app.include_router(
    projects_router, prefix=api_v1_prefix
)  # SATUBUMI MONITOR — CRUD Proyek
app.include_router(team_member.router,prefix="/api/v1")
app.include_router(
    monitor_router, prefix=api_v1_prefix
)  # SATUBUMI MONITOR — Data Sub-modul
app.include_router(activity.router,prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "message": "Satubumi API Engine is running smoothly.",
    }
