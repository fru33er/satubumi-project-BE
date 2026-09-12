"""
Migrate script: Add carbon MRV fields to monitoring_plots table in SQLite / PostgreSQL.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("Starting migration for monitoring_plots...")
    with engine.connect() as conn:
        columns_to_add = [
            ("stratum", "VARCHAR(100)"),
            ("elevation_mdpl", "FLOAT"),
            ("slope_pct", "FLOAT"),
            ("shape_type", "VARCHAR(50) DEFAULT 'rectangle'"),
            ("dimension_length_m", "FLOAT"),
            ("dimension_width_m", "FLOAT"),
            ("azimuth_deg", "FLOAT"),
            ("established_date", "DATE"),
            ("last_survey_date", "DATE"),
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE monitoring_plots ADD COLUMN {col_name} {col_type};"))
                conn.commit()
                print(f"Added column {col_name} ({col_type})")
            except Exception as e:
                # Column might already exist
                print(f"Column {col_name} note/skip: {e}")
                
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
