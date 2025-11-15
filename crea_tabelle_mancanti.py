import sqlite3

conn = sqlite3.connect("commesse.db")
cur = conn.cursor()

# Tabella magazzino
cur.execute("""
CREATE TABLE IF NOT EXISTS magazzino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT UNIQUE NOT NULL,
    descrizione TEXT NOT NULL,
    giacenza INTEGER DEFAULT 0,
    scorta_minima INTEGER DEFAULT 0
);
""")

# Tabella movimenti magazzino
cur.execute("""
CREATE TABLE IF NOT EXISTS movimenti_magazzino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER,
    quantita INTEGER,
    tipo TEXT,
    data_movimento TEXT,
    commessa_id INTEGER,
    FOREIGN KEY (articolo_id) REFERENCES magazzino(id)
);
""")

# Tabella archivio consegnate
cur.execute("""
CREATE TABLE IF NOT EXISTS consegnate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_commessa INTEGER,
    nome TEXT,
    tipo_intervento TEXT,
    data_consegna TEXT,
    note TEXT
);
""")

conn.commit()
conn.close()

print("Tabelle mancanti create correttamente!")