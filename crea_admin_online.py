import sqlite3
import os
from werkzeug.security import generate_password_hash

# stesso percorso del DB usato da app.py
DB_PATH = os.path.join(os.getcwd(), "commesse.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

username = "admin"
password = "admin"  # cambiala dopo il primo accesso
password_hash = generate_password_hash(password)
ruolo = "amministratore"

cur.execute("""
INSERT OR IGNORE INTO utenti (username, password_hash, ruolo)
VALUES (?, ?, ?)
""", (username, password_hash, ruolo))

conn.commit()
conn.close()

print("Utente amministratore creato: admin / admin")