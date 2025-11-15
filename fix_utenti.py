import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "commesse.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE utenti ADD COLUMN ruolo TEXT DEFAULT 'operatore'")
    print("Colonna 'ruolo' aggiunta.")
except Exception as e:
    print("Errore o colonna già esistente:", e)

conn.commit()
conn.close()