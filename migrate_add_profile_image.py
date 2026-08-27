import sqlite3

conn = sqlite3.connect("satubumi.db")

cursor = conn.cursor()


cursor.execute("""
ALTER TABLE users
ADD COLUMN profile_image TEXT
""")


conn.commit()

conn.close()


print("profile_image added")
