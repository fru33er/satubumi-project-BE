"""
alembic/env.py — Konfigurasi Alembic untuk SATUBUMI Backend

- Membaca DATABASE_URL dari app.core.config.settings (via .env)
- Mengimport seluruh Base + model agar autogenerate dapat mendeteksi schema
- Mendukung SQLite (dev) dan PostgreSQL (production)
- render_as_batch=True untuk kompatibilitas SQLite ALTER TABLE
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Path ──────────────────────────────────────────────────────────────────────
# Pastikan root project ada di sys.path agar import app.* berjalan
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── App Config & Models ───────────────────────────────────────────────────────
from app.core.config import settings
from app.core.database import Base

# Import semua model agar Base.metadata mengenali semua tabel
# (Alembic autogenerate membutuhkan semua model terdaftar sebelum comparison)
from app.models.user import User
from app.models.article import Article
from app.models.assessment import Assessment
from app.models.insight_topic import InsightTopic
from app.models.project import Project
from app.models.monitor import (
    ProjectActivity,
    TreeRecord,
    TreeMeasurement,
    FieldReport,
    Alert,
    BiodiversityObservation,
    CommunityData,
    CarbonRecord,
    MonitoringPlot,
    LandscapeSnapshot,
    ProjectMember,
)

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Setup logging dari alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url dengan nilai dari settings (membaca .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata untuk autogenerate
target_metadata = Base.metadata


# ── Migration Functions ───────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (tanpa koneksi database aktif)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # render_as_batch diperlukan untuk SQLite ALTER TABLE compatibility
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (koneksi database aktif)."""
    db_url = settings.DATABASE_URL

    # SQLite membutuhkan connect_args khusus
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # render_as_batch=True diperlukan untuk SQLite
            # karena SQLite tidak support ALTER COLUMN / ADD CONSTRAINT native
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
