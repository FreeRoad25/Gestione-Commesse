import sqlite3

DB_NAME = "commesse.db"

def aggiorna_tabella_ore_lavorate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE ore_lavorate ADD COLUMN data TEXT;")
        print("✅ Colonna 'data' aggiunta con successo!")
    except sqlite3.OperationalError:
        print("⚠️ Colonna 'data' già presente o errore nella modifica.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    aggiorna_tabella_ore_lavorate()
