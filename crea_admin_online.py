import sqlite3
import os
from werkzeug.security import generate_password_hash

# Path al database (stesso usato da app.py)
DB_PATH = os.path.join(os.getcwd(), "commesse.db")
print("CREA ADMIN DB_PATH:", DB_PATH)

def crea_admin_se_manca():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Controlla se esiste già un admin
    cur.execute("SELECT * FROM utenti WHERE ruolo = 'amministratore'")
    esiste = cur.fetchone()

    if esiste:
        print("Admin già presente, nessuna azione necessaria.")
        conn.close()
        return

    # Crea admin solo se NON esiste
    username = "admin"
    password = "admin"   # Cambiala dopo il primo accesso
    password_hash = generate_password_hash(password)
    ruolo = "amministratore"

    cur.execute("""
        INSERT OR IGNORE INTO utenti (username, password_hash, ruolo)
        VALUES (?, ?, ?)
    """, (username, password_hash, ruolo))

    conn.commit()
    conn.close()
    print("Admin creato automaticamente: admin / admin")


# Esegui automaticamente allo start del server
if __name__ == "__main__":
    crea_admin_se_manca()