import sqlite3

DB_NAME = "commesse.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Aggiunta nuovi campi se non esistono già
campi = {
    "tipo_intervento": "TEXT",
    "data_conferma": "TEXT",
    "data_arrivo_materiali": "TEXT",
    "data_inizio": "TEXT",
    "ore_necessarie": "INTEGER",
    "marca_veicolo": "TEXT",
    "modello_veicolo": "TEXT",
    "dimensioni": "TEXT",
    "data_consegna": "TEXT"
}

for nome_campo, tipo in campi.items():
    try:
        c.execute(f"ALTER TABLE commesse ADD COLUMN {nome_campo} {tipo}")
        print(f"Aggiunto campo: {nome_campo}")
    except sqlite3.OperationalError:
        print(f"Campo già esistente: {nome_campo}")

conn.commit()
conn.close()

print("\n✅ Aggiornamento database completato!")
