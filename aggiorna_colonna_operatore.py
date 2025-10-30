import sqlite3

DB_NAME = "commesse.db"

def rinomina_colonna():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Verifica se la colonna giusta esiste già
        cursor.execute("PRAGMA table_info(ore_lavorate)")
        colonne = [r[1] for r in cursor.fetchall()]

        if "id_operatore" not in colonne:
            cursor.execute("ALTER TABLE ore_lavorate ADD COLUMN id_operatore INTEGER;")
            print("✅ Colonna 'id_operatore' aggiunta con successo!")
        else:
            print("⚠️ Colonna 'id_operatore' già presente.")
    except Exception as e:
        print("❌ Errore durante l'aggiornamento:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    rinomina_colonna()
