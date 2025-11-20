import psycopg2
import os

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

        # --- COMMESSE ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commesse (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo_intervento TEXT,
            marca_veicolo TEXT,
            modello_veicolo TEXT,
            dimensioni TEXT,
            data_conferma DATE,
            data_arrivo_materiali DATE,
            data_inizio DATE,
            ore_necessarie REAL,
            ore_eseguite REAL DEFAULT 0,
            ore_rimanenti REAL DEFAULT 0,
            data_consegna DATE,
            note_importanti TEXT
        );
        """)

        # --- MARCHE ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS marche (
            id SERIAL PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        );
        """)

        # --- ARTICOLI MAGAZZINO ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS articoli (
            id SERIAL PRIMARY KEY,
            codice TEXT UNIQUE NOT NULL,
            descrizione TEXT NOT NULL,
            unita TEXT,
            quantita REAL DEFAULT 0,
            codice_barre TEXT,
            fornitore TEXT,
            scorta_minima REAL DEFAULT 0,
            costo_netto REAL DEFAULT 0
        );
        """)

        # --- COMMESSE MATERIALI ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commesse_materiali (
            id SERIAL PRIMARY KEY,
            id_commessa INTEGER REFERENCES commesse(id),
            id_articolo INTEGER REFERENCES articoli(id),
            quantita REAL NOT NULL
        );
        """)

        # --- OPERATORI ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS operatori (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            costo_orario REAL DEFAULT 0
        );
        """)

        # --- ORE LAVORATE ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ore_lavorate (
            id SERIAL PRIMARY KEY,
            id_operatore INTEGER REFERENCES operatori(id),
            id_commessa INTEGER REFERENCES commesse(id),
            ore REAL,
            data_imputazione DATE
        );
        """)

        # --- MOVIMENTI MAGAZZINO ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS movimenti_magazzino (
            id SERIAL PRIMARY KEY,
            id_articolo INTEGER REFERENCES articoli(id),
            tipo_movimento TEXT CHECK (tipo_movimento IN ('Carico','Scarico')),
            quantita REAL NOT NULL,
            data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_commessa INTEGER REFERENCES commesse(id),
            note TEXT
        );
        """)

        # --- FILE COMMESSE ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commessa_files (
            id SERIAL PRIMARY KEY,
            id_commessa INTEGER REFERENCES commesse(id),
            filename TEXT NOT NULL,
            original_name TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # --- COMMESSE CONSEGNATE ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS commesse_consegnate (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo_intervento TEXT,
            marca_veicolo TEXT,
            modello_veicolo TEXT,
            data_consegna DATE,
            saldata TEXT CHECK (saldata IN ('Si','No')) DEFAULT 'No'
        );
        """)

        conn.commit()
        cur.close()
        conn.close()

        print("✅ DATABASE POSTGRES COMPLETAMENTE CREATO")

    except Exception as e:
        print("❌ ERRORE CREAZIONE TABELLE:", e)

if _name_ == "_main_":
    create_tables()