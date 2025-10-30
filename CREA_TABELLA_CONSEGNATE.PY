import sqlite3

conn = sqlite3.connect("commesse.db")
c = conn.cursor()

# Creiamo la tabella se non esiste già
c.execute('''CREATE TABLE IF NOT EXISTS commesse_consegnate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo_intervento TEXT,
                data_conferma TEXT,
                data_arrivo_materiali TEXT,
                data_inizio TEXT,
                ore_necessarie REAL,
                ore_eseguite REAL,
                ore_rimanenti REAL,
                marca_veicolo TEXT,
                modello_veicolo TEXT,
                dimensioni TEXT,
                data_consegna TEXT,
                saldata TEXT CHECK(saldata IN ('Si','No'))
            )''')

conn.commit()
conn.close()

print("✅ Tabella 'commesse_consegnate' creata o già presente.")
