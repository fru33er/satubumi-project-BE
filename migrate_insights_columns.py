"""Tambah kolom insights + bilingual jika belum ada."""

from sqlalchemy import text

from app.core.database import engine

COLS = [
    ("title_en", "VARCHAR(255)"),
    ("content_en", "TEXT"),
    ("topic", "VARCHAR(50)"),
    ("is_featured", "BOOLEAN DEFAULT 0"),
    ("view_count", "INTEGER DEFAULT 0"),
]

with engine.connect() as conn:
    existing = {
        row[1] for row in conn.execute(text("PRAGMA table_info(articles)")).fetchall()
    }
    for name, typedef in COLS:
        if name not in existing:
            conn.execute(text(f"ALTER TABLE articles ADD COLUMN {name} {typedef}"))
            print(f"[OK] added column: {name}")
        else:
            print(f"[SKIP] already exists: {name}")
    conn.commit()

print("Done.")
