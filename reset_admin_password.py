import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "commesse.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

nuova_pw = generate_password_hash("admin")

cursor.execute("UPDATE utenti SET password_hash=? WHERE username='admin'", (nuova_pw,))
conn.commit()
conn.close()

print("Password admin reimpostata correttamente.")