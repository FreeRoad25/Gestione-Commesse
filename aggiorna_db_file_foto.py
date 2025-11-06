import sqlite3

DB_NAME = "commesse.db"

def aggiungi_colonne():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Verifica se le colonne già esistono prima di aggiungerle
    c.execute("PRAGMA table_info(commesse)")
    colonne_esistenti = [col[1] for col in c.fetchall()]

    if "foto" not in colonne_esistenti:
        c.execute("ALTER TABLE commesse ADD COLUMN foto TEXT")
        print("✅ Colonna 'foto' aggiunta con successo.")
    else:
        print("ℹ La colonna 'foto' esiste già, nessuna modifica.")

    if "allegato" not in colonne_esistenti:
        c.execute("ALTER TABLE commesse ADD COLUMN allegato TEXT")
        print("✅ Colonna 'allegato' aggiunta con successo.")
    else:
        print("ℹ La colonna 'allegato' esiste già, nessuna modifica.")

    conn.commit()
    conn.close()
    print("\n✅ Aggiornamento completato con successo!")

if __name__ == "__main__":
    aggiungi_colonne()