import sqlite3

# Connessione al database esistente
conn = sqlite3.connect('commesse.db')
cursor = conn.cursor()

# Aggiunge le nuove colonne se non esistono già
try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN data_inserimento TEXT")
    print("Aggiunta colonna: data_inserimento")
except:
    print("Colonna 'data_inserimento' già presente")

try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN data_conferma TEXT")
    print("Aggiunta colonna: data_conferma")
except:
    print("Colonna 'data_conferma' già presente")

try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN data_arrivo_materiale TEXT")
    print("Aggiunta colonna: data_arrivo_materiale")
except:
    print("Colonna 'data_arrivo_materiale' già presente")

try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN ore_necessarie INTEGER")
    print("Aggiunta colonna: ore_necessarie")
except:
    print("Colonna 'ore_necessarie' già presente")

try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN tipo_intervento TEXT")
    print("Aggiunta colonna: tipo_intervento")
except:
    print("Colonna 'tipo_intervento' già presente")

conn.commit()
conn.close()

print("✅ Database aggiornato con successo!")
