import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commesse.db")

marche = [
    "Volkswagen",
    "Mercedes",
    "Fiat",
    "Ford",
    "Renault",
    "Peugeot",
    "Citroen",
    "Opel",
    "Iveco",
    "Altra marca"
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS marche (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
)
""")

for m in marche:
    try:
        c.execute("INSERT INTO marche (nome) VALUES (?)", (m,))
    except:
        pass  # se esiste già, ignora

conn.commit()
conn.close()

print("Marche inserite correttamente.")