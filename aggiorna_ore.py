import sqlite3

# Connessione al database
conn = sqlite3.connect("commesse.db")
cursor = conn.cursor()

# Aggiunge le colonne se non esistono già
try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN ore_eseguite REAL DEFAULT 0")
    print("✅ Colonna 'ore_eseguite' aggiunta con successo.")
except sqlite3.OperationalError:
    print("⚠️ Colonna 'ore_eseguite' già esistente.")

try:
    cursor.execute("ALTER TABLE commesse ADD COLUMN ore_rimanenti REAL DEFAULT 0")
    print("✅ Colonna 'ore_rimanenti' aggiunta con successo.")
except sqlite3.OperationalError:
    print("⚠️ Colonna 'ore_rimanenti' già esistente.")

conn.commit()
conn.close()

print("🏁 Aggiornamento completato.")
