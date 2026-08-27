import sqlite3

DATABASE = "satubumi.db"


conn = sqlite3.connect(DATABASE)

cursor = conn.cursor()


# cek apakah kolom sudah ada
cursor.execute("PRAGMA table_info(articles)")

columns = [column[1] for column in cursor.fetchall()]


if "author_id" not in columns:
    cursor.execute(
        """
        ALTER TABLE articles
        ADD COLUMN author_id INTEGER
        """
    )

    print("author_id added to articles")

else:
    print("author_id already exists")


conn.commit()

conn.close()
