from app.core.database import SessionLocal, engine, Base
from app.models.insight_topic import InsightTopic

Base.metadata.create_all(bind=engine)

SEED = [
    ("carbon", "Karbon", "Carbon"),
    ("esg", "ESG", "ESG"),
    ("policy", "Kebijakan", "Policy"),
    ("nature", "Alam & Bentang", "Nature & Landscape"),
    ("other", "Lainnya", "Other"),
]

db = SessionLocal()
try:
    for slug, lid, len_ in SEED:
        if not db.query(InsightTopic).filter(InsightTopic.slug == slug).first():
            db.add(
                InsightTopic(
                    slug=slug,
                    label_id=lid,
                    label_en=len_,
                    created_by="system",
                )
            )
            print(f"[OK] {slug}")
        else:
            print(f"[SKIP] {slug}")
    db.commit()
finally:
    db.close()
print("Done.")