"""
Script Seeder untuk membuat artikel awal Halaman About dan Services di Database Backend
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.article import Article

DEFAULT_ARTICLES = [
    {
        "category": "about",
        "title": "Pengembangan Solusi Iklim & Keberlanjutan",
        "slug": "pengembangan-solusi-iklim",
        "author": "Satubumi Team",
        "content": "Satubumi adalah perusahaan konsultansi yang berfokus pada pengembangan solusi iklim dan keberlanjutan melalui pendekatan ilmiah, kolaboratif, dan berbasis dampak.",
        "status": "published",
        "tags": "about, sustainability"
    },
    {
        "category": "services",
        "title": "Pengembangan Proyek Karbon (Carbon Project Development)",
        "slug": "pengembangan-proyek-karbon",
        "author": "Advisory Team",
        "content": "Mendampingi klien dalam seluruh tahapan pengembangan proyek karbon, mulai dari kelayakan, perancangan, penyusunan dokumen, hingga MRV.",
        "status": "published",
        "tags": "services, carbon"
    },
    {
        "category": "services",
        "title": "Penilaian Kondisi Dasar (Baseline Assessment)",
        "slug": "baseline-assessment",
        "author": "Advisory Team",
        "content": "Layanan pengumpulan dan analisis data tutupan lahan, keanekaragaman hayati, dan cadangan karbon.",
        "status": "published",
        "tags": "services, baseline"
    }
]

def seed_articles():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for art_data in DEFAULT_ARTICLES:
            existing = db.query(Article).filter(Article.slug == art_data["slug"]).first()
            if not existing:
                new_art = Article(**art_data)
                db.add(new_art)
                print(f"[OK] Artikel berhasil dibuat: {art_data['title']}")
            else:
                print(f"[INFO] Artikel sudah ada: {art_data['title']}")
        db.commit()
        print("\n[OK] Seeding artikel selesai!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding artikel gagal: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_articles()
