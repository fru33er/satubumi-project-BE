from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.models.article import Article
from app.api.v1.auth import router as auth_router
from app.api.v1.rapid_fs import router as rapid_fs_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.reports import router as reports_router
from app.api.v1.contact import router as contact_router
from app.api.v1.articles import router as articles_router
from app.api.v1.users import router as users_router

# Inisialisasi tabel DB saat startup (jika belum ada)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="RESTful API Backend Service untuk Satubumi.org & Rapid-FS Carbon Feasibility Scoring Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

@app.get("/")
def root():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "message": "Satubumi API Engine is running smoothly."
    }
