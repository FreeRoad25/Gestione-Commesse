import sqlite3

conn = sqlite3.connect("commesse.db")
cur = conn.cursor()

# CREA TABELLA ARTICOLI (Magazzino)
cur.execute("""
CREATE TABLE IF NOT EXISTS articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT UNIQUE,
    descrizione TEXT NOT NULL,
    quantita INTEGER DEFAULT 0,
    scorta_minima INTEGER DEFAULT 0,
    prezzo REAL DEFAULT 0
)
""")
print("Tabella articoli OK")

# CREA TABELLA CONSEGNATI (Archivio)
cur.execute("""
CREATE TABLE IF NOT EXISTS consegnati (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_commessa TEXT,
    data_consegna TEXT,
    note TEXT
)
""")
print("Tabella consegnati OK")

conn.commit()
conn.close()
print("Tutto creato.")