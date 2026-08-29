import importlib
import os
import pkgutil

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text

from app.core.database import Base
import app.models


load_dotenv()


SQLITE_URL = "sqlite:///./satubumi.db"

POSTGRES_URL = os.getenv(
    "SUPABASE_DATABASE_URL"
)


if not POSTGRES_URL:
    raise RuntimeError(
        "SUPABASE_DATABASE_URL belum diisi di .env"
    )


# SQLAlchemy membutuhkan postgresql://
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )


# =========================================
# LOAD SEMUA MODEL
# =========================================

for module_info in pkgutil.iter_modules(
    app.models.__path__
):
    module_name = (
        f"app.models.{module_info.name}"
    )

    try:
        importlib.import_module(
            module_name
        )

        print(
            f"Model loaded: {module_name}"
        )

    except Exception as exc:
        print(
            f"Warning gagal load "
            f"{module_name}: {exc}"
        )


# =========================================
# ENGINE
# =========================================

sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={
        "check_same_thread": False
    },
)


postgres_engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,
)


# =========================================
# TEST CONNECTION
# =========================================

print("\nTesting SQLite...")

with sqlite_engine.connect() as conn:
    conn.execute(
        text("SELECT 1")
    )

print("SQLite OK")


print("Testing PostgreSQL...")

with postgres_engine.connect() as conn:
    conn.execute(
        text("SELECT 1")
    )

print("PostgreSQL OK")


# =========================================
# CREATE TABLES
# =========================================

print(
    "\nCreating tables "
    "in PostgreSQL..."
)

Base.metadata.create_all(
    postgres_engine
)

print("Tables ready")


# =========================================
# CHECK TARGET EMPTY
# =========================================

print(
    "\nChecking target database..."
)

with postgres_engine.connect() as conn:
    non_empty_tables = []

    for table in Base.metadata.sorted_tables:
        count = conn.execute(
            select(
                func.count()
            ).select_from(table)
        ).scalar_one()

        if count > 0:
            non_empty_tables.append(
                (
                    table.name,
                    count,
                )
            )


if non_empty_tables:
    print(
        "\nMIGRATION DIBATALKAN."
    )

    print(
        "PostgreSQL sudah memiliki data:"
    )

    for table_name, count in non_empty_tables:
        print(
            f"- {table_name}: "
            f"{count} rows"
        )

    print(
        "\nScript sengaja berhenti "
        "agar tidak membuat duplicate data."
    )

    raise SystemExit(1)


# =========================================
# COPY DATA
# =========================================

print(
    "\nStarting migration..."
)


with sqlite_engine.connect() as source_conn:
    with postgres_engine.begin() as target_conn:

        for table in Base.metadata.sorted_tables:

            try:
                rows = (
                    source_conn.execute(
                        select(table)
                    )
                    .mappings()
                    .all()
                )

            except Exception as exc:
                print(
                    f"Skip {table.name}: "
                    f"{exc}"
                )
                continue


            if not rows:
                print(
                    f"{table.name}: "
                    "0 rows"
                )
                continue


            target_conn.execute(
                table.insert(),
                [
                    dict(row)
                    for row in rows
                ],
            )

            print(
                f"{table.name}: "
                f"{len(rows)} rows copied"
            )


# =========================================
# RESET POSTGRES SEQUENCES
# =========================================

print(
    "\nResetting PostgreSQL "
    "ID sequences..."
)


with postgres_engine.begin() as conn:

    for table in Base.metadata.sorted_tables:

        if "id" not in table.c:
            continue

        id_column = table.c.id

        if not id_column.primary_key:
            continue

        try:
            result = conn.execute(
                text(
                    """
                    SELECT MAX(id)
                    FROM "{}"
                    """.format(
                        table.name
                    )
                )
            )

            max_id = result.scalar()

            if max_id is None:
                continue


            conn.execute(
                text(
                    """
                    SELECT setval(
                        pg_get_serial_sequence(
                            :table_name,
                            'id'
                        ),
                        :max_id,
                        true
                    )
                    """
                ),
                {
                    "table_name":
                        table.name,

                    "max_id":
                        max_id,
                },
            )

            print(
                f"{table.name}: "
                f"sequence -> {max_id}"
            )

        except Exception as exc:
            print(
                f"Sequence skip "
                f"{table.name}: {exc}"
            )


# =========================================
# VERIFY
# =========================================

print(
    "\nVerification:"
)


with sqlite_engine.connect() as sqlite_conn:
    with postgres_engine.connect() as postgres_conn:

        for table in Base.metadata.sorted_tables:

            try:
                sqlite_count = (
                    sqlite_conn.execute(
                        select(
                            func.count()
                        ).select_from(table)
                    )
                    .scalar_one()
                )

            except Exception:
                continue


            postgres_count = (
                postgres_conn.execute(
                    select(
                        func.count()
                    ).select_from(table)
                )
                .scalar_one()
            )


            status = (
                "OK"
                if sqlite_count
                == postgres_count
                else "MISMATCH"
            )


            print(
                f"{table.name}: "
                f"SQLite={sqlite_count}, "
                f"PostgreSQL="
                f"{postgres_count} "
                f"[{status}]"
            )


print(
    "\nMigration selesai."
)