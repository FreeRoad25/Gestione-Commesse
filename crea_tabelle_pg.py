import psycopg2
import os

# Legge le variabili di Render (localmente saranno None, è normale)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_tables():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        # === CREAZIONE TABELLE ===
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commesse (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo_intervento TEXT,
            marca_veicolo TEXT,
            modello_veicolo TEXT,
            data_conferma TEXT,
            data_arrivo_materiali TEXT,
            ore_necessarie INTEGER,
            stato TEXT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS materiali (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            quantita INTEGER,
            prezzo REAL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS utenti (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            ruolo TEXT
        );
        """)

        conn.commit()
        cur.close()
        conn.close()

        print("TABELLE POSTGRES CREATE ✓")

    except Exception as e:
        print("ERRORE CREAZIONE TABELLE:", e)

if __name__ == "__main__":
    print("Avvio creazione tabelle Postgres…")
    create_tables()