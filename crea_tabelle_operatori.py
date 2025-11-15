import sqlite3

DB_NAME = "commesse.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Crea tabella operatori
cursor.execute("""
CREATE TABLE IF NOT EXISTS operatori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
""")

# Crea tabella ore_lavorate
cursor.execute("""
CREATE TABLE IF NOT EXISTS ore_lavorate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_operatore INTEGER,
    id_commessa INTEGER,
    ore REAL,
    data_imputazione TEXT,
    FOREIGN KEY (id_operatore) REFERENCES operatori(id),
    FOREIGN KEY (id_commessa) REFERENCES commesse(id)
)
""")

conn.commit()
conn.close()

print("✅ Tabelle 'operatori' e 'ore_lavorate' create o già esistenti!")
