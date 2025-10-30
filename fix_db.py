import sqlite3

conn = sqlite3.connect("commesse.db")
cursor = conn.cursor()

colonne = [row[1] for row in cursor.execute("PRAGMA table_info(commesse);").fetchall()]

if "ore_eseguite" not in colonne:
    cursor.execute("ALTER TABLE commesse ADD COLUMN ore_eseguite REAL DEFAULT 0")
    print("✅ Colonna 'ore_eseguite' aggiunta.")
else:
    print("ℹ️ Colonna 'ore_eseguite' già esistente.")

if "ore_rimanenti" not in colonne:
    cursor.execute("ALTER TABLE commesse ADD COLUMN ore_rimanenti REAL DEFAULT 0")
    print("✅ Colonna 'ore_rimanenti' aggiunta.")
else:
    print("ℹ️ Colonna 'ore_rimanenti' già esistente.")

conn.commit()
conn.close()

print("🏁 Database aggiornato correttamente.")
