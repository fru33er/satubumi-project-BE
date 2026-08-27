import sqlite3

conn = sqlite3.connect("satubumi.db")

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS rulebooks (

id INTEGER PRIMARY KEY,

title VARCHAR(255) NOT NULL,

description TEXT,

file_url VARCHAR(500) NOT NULL,

thumbnail_url VARCHAR(500),

status VARCHAR(30),

download_count INTEGER DEFAULT 0,

created_at DATETIME,

updated_at DATETIME

)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS rulebook_downloads (

id INTEGER PRIMARY KEY,

rulebook_id INTEGER,

name VARCHAR(255),

email VARCHAR(255),

phone VARCHAR(50),

institution VARCHAR(255),

created_at DATETIME

)
""")


conn.commit()

conn.close()


print("Rulebook tables created")
