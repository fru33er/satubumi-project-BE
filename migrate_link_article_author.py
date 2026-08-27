from app.core.database import SessionLocal
from app.models.article import Article
from app.models.user import User

db = SessionLocal()


articles = db.query(Article).all()


for article in articles:
    # skip kalau sudah ada relasi
    if article.author_id:
        continue

    if not article.author:
        continue

    user = db.query(User).filter(User.full_name == article.author).first()

    if user:
        article.author_id = user.id

        print(f"Linked article {article.id} -> user {user.full_name}")

    else:
        print(f"Tidak ditemukan user untuk: {article.author}")


db.commit()

db.close()


print("Selesai")
