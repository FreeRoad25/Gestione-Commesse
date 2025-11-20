BEGIN;

CREATE TABLE IF NOT EXISTS articoli (
    id SERIAL PRIMARY KEY,
    codice TEXT UNIQUE,
    descrizione TEXT NOT NULL,
    quantita INTEGER DEFAULT 0,
    scorta_minima INTEGER DEFAULT 0,
    prezzo REAL DEFAULT 0,
    unita TEXT DEFAULT '',
    fornitore TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS commesse (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo_intervento TEXT,
    data_conferma TEXT,
    data_arrivo_materiali TEXT,
    data_inizio TEXT,
    ore_necessarie REAL,
    ore_eseguite REAL DEFAULT 0,
    ore_rimanenti REAL DEFAULT 0,
    marca_veicolo TEXT,
    modello_veicolo TEXT,
    dimensioni TEXT,
    data_consegna TEXT,
    foto TEXT,
    allegato TEXT,
    note_importanti TEXT
);

CREATE TABLE IF NOT EXISTS commessa_files (
    id SERIAL PRIMARY KEY,
    id_commessa INTEGER NOT NULL REFERENCES commesse(id),
    filename TEXT NOT NULL,
    original_name TEXT,
    upload_date TEXT
);

CREATE TABLE IF NOT EXISTS commesse_consegnate (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo_intervento TEXT,
    data_conferma TEXT,
    data_arrivo_materiali TEXT,
    data_inizio TEXT,
    ore_necessarie REAL,
    ore_eseguite REAL,
    ore_rimanenti REAL,
    marca_veicolo TEXT,
    modello_veicolo TEXT,
    dimensioni TEXT,
    data_consegna TEXT,
    saldata TEXT CHECK (saldata IN ('Si','No'))
);

CREATE TABLE IF NOT EXISTS consegnate (
    id SERIAL PRIMARY KEY,
    id_commessa INTEGER,
    nome TEXT,
    tipo_intervento TEXT,
    data_consegna TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS consegnati (
    id SERIAL PRIMARY KEY,
    nome_commessa TEXT,
    data_consegna TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS costo_orario (
    id SERIAL PRIMARY KEY,
    valore REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS magazzino (
    id SERIAL PRIMARY KEY,
    codice TEXT UNIQUE,
    descrizione TEXT NOT NULL,
    unita TEXT,
    quantita REAL DEFAULT 0,
    codice_barre TEXT,
    fornitore TEXT,
    scorta_minima REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS marche (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movimenti_magazzino (
    id SERIAL PRIMARY KEY,
    id_articolo INTEGER REFERENCES magazzino(id),
    tipo_movimento TEXT CHECK (tipo_movimento IN ('Carico','Scarico')),
    quantita REAL NOT NULL,
    data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_commessa INTEGER REFERENCES commesse(id),
    note TEXT
);

CREATE TABLE IF NOT EXISTS operatori (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ore_lavorate (
    id SERIAL PRIMARY KEY,
    id_operatore INTEGER,
    id_commessa INTEGER,
    ore REAL,
    data_imputazione TEXT
);

CREATE TABLE IF NOT EXISTS tipi_intervento (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS utenti (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    ruolo TEXT DEFAULT 'operatore'
);

-- DATI BASE
INSERT INTO costo_orario (valore) VALUES (0.0);

INSERT INTO utenti VALUES
('admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','amministratore'),
('fabrizio','c4ca4238a0b923820dcc509a6f75849b','amministratore'),
('stefano','c4ca4238a0b923820dcc509a6f75849b','operatore'),
('mauro','c4ca4238a0b923820dcc509a6f75849b','operatore'),
('valery','c4ca4238a0b923820dcc509a6f75849b','operatore'),
('andrea','c4ca4238a0b923820dcc509a6f75849b','operatore'),
('ilenia','c4ca4238a0b923820dcc509a6f75849b','operatore');

COMMIT;