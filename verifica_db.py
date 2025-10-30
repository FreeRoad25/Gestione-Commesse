import sqlite3

# Connessione al database
conn = sqlite3.connect("commesse.db")
cursor = conn.cursor()

# Mostra tutte le colonne della tabella commesse
cursor.execute("PRAGMA table_info(commesse)")
columns = cursor.fetchall()

print("📋 Colonne presenti nella tabella 'commesse':\n")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()
