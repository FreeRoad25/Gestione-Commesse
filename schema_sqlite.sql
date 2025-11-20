BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "articoli" (
	"id"	INTEGER,
	"codice"	TEXT UNIQUE,
	"descrizione"	TEXT NOT NULL,
	"quantita"	INTEGER DEFAULT 0,
	"scorta_minima"	INTEGER DEFAULT 0,
	"prezzo"	REAL DEFAULT 0,
	"unita"	TEXT DEFAULT '',
	"fornitore"	TEXT DEFAULT '',
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "commessa_files" (
	"id"	INTEGER,
	"id_commessa"	INTEGER NOT NULL,
	"filename"	TEXT NOT NULL,
	"original_name"	TEXT,
	"upload_date"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_commessa") REFERENCES "commesse"("id")
);
CREATE TABLE IF NOT EXISTS "commesse" (
	"id"	INTEGER,
	"nome"	TEXT NOT NULL,
	"tipo_intervento"	TEXT,
	"data_conferma"	TEXT,
	"data_arrivo_materiali"	TEXT,
	"data_inizio"	TEXT,
	"ore_necessarie"	REAL,
	"ore_eseguite"	REAL DEFAULT 0,
	"ore_rimanenti"	REAL DEFAULT 0,
	"marca_veicolo"	TEXT,
	"modello_veicolo"	TEXT,
	"dimensioni"	TEXT,
	"data_consegna"	TEXT,
	"foto"	TEXT,
	"allegato"	TEXT,
	"note_importanti"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "commesse_consegnate" (
	"id"	INTEGER,
	"nome"	TEXT NOT NULL,
	"tipo_intervento"	TEXT,
	"data_conferma"	TEXT,
	"data_arrivo_materiali"	TEXT,
	"data_inizio"	TEXT,
	"ore_necessarie"	REAL,
	"ore_eseguite"	REAL,
	"ore_rimanenti"	REAL,
	"marca_veicolo"	TEXT,
	"modello_veicolo"	TEXT,
	"dimensioni"	TEXT,
	"data_consegna"	TEXT,
	"saldata"	TEXT CHECK("saldata" IN ('Si', 'No')),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "consegnate" (
	"id"	INTEGER,
	"id_commessa"	INTEGER,
	"nome"	TEXT,
	"tipo_intervento"	TEXT,
	"data_consegna"	TEXT,
	"note"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "consegnati" (
	"id"	INTEGER,
	"nome_commessa"	TEXT,
	"data_consegna"	TEXT,
	"note"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "costo_orario" (
	"id"	INTEGER,
	"valore"	REAL NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "magazzino" (
	"id"	INTEGER,
	"codice"	TEXT UNIQUE,
	"descrizione"	TEXT NOT NULL,
	"unita"	TEXT,
	"quantita"	REAL DEFAULT 0,
	"codice_barre"	TEXT,
	"fornitore"	TEXT,
	"scorta_minima"	REAL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "marche" (
	"id"	INTEGER,
	"nome"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "movimenti_magazzino" (
	"id"	INTEGER,
	"id_articolo"	INTEGER,
	"tipo_movimento"	TEXT CHECK("tipo_movimento" IN ('Carico', 'Scarico')),
	"quantita"	REAL NOT NULL,
	"data_movimento"	TEXT DEFAULT CURRENT_TIMESTAMP,
	"id_commessa"	INTEGER,
	"note"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_articolo") REFERENCES "magazzino"("id"),
	FOREIGN KEY("id_commessa") REFERENCES "commesse"("id")
);
CREATE TABLE IF NOT EXISTS "operatori" (
	"id"	INTEGER,
	"nome"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "ore_lavorate" (
	"id"	INTEGER,
	"id_operatore"	INTEGER,
	"id_commessa"	INTEGER,
	"ore"	REAL,
	"data_imputazione"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "tipi_intervento" (
	"id"	INTEGER,
	"nome"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "utenti" (
	"username"	TEXT,
	"password_hash"	TEXT NOT NULL,
	"ruolo"	TEXT DEFAULT 'operatore',
	PRIMARY KEY("username")
);
INSERT INTO "costo_orario" VALUES (1,0.0);
INSERT INTO "magazzino" VALUES (1,'A','A','P',8.0,'SSS','SSS',8.0);
INSERT INTO "magazzino" VALUES (2,'B','B','PZ',2.0,'44545454545','B',5.0);
INSERT INTO "magazzino" VALUES (3,'C','HAH','LT',3.0,'5','C',2.0);
INSERT INTO "magazzino" VALUES (4,'primo','uno','pz',53.0,'X0013C4SD7♪','vecam',3.0);
INSERT INTO "magazzino" VALUES (5,'proca3','uno solo','pz',0.0,'0006184544♪','nesshuno',5.0);
INSERT INTO "marche" VALUES (28,'Fiat');
INSERT INTO "marche" VALUES (29,'Volkswagen');
INSERT INTO "marche" VALUES (30,'Mercedes');
INSERT INTO "marche" VALUES (31,'Renault');
INSERT INTO "marche" VALUES (32,'Peugeot');
INSERT INTO "marche" VALUES (33,'Citroen');
INSERT INTO "marche" VALUES (34,'Ford');
INSERT INTO "marche" VALUES (35,'Opel');
INSERT INTO "marche" VALUES (36,'Iveco');
INSERT INTO "marche" VALUES (37,'Nissan');
INSERT INTO "marche" VALUES (38,'Toyota');
INSERT INTO "marche" VALUES (39,'Altra Marca');
INSERT INTO "operatori" VALUES (1,'Stefano');
INSERT INTO "operatori" VALUES (2,'Mauro');
INSERT INTO "operatori" VALUES (3,'Valery');
INSERT INTO "operatori" VALUES (4,'Andrea');
INSERT INTO "tipi_intervento" VALUES (1,'Montaggio Riscaldatore');
INSERT INTO "tipi_intervento" VALUES (2,'Tetto a Soffietto');
INSERT INTO "tipi_intervento" VALUES (3,'Coibentazione');
INSERT INTO "tipi_intervento" VALUES (4,'Allestimento Interno');
INSERT INTO "tipi_intervento" VALUES (5,'Impianto Elettrico');
INSERT INTO "tipi_intervento" VALUES (6,'Impianto Acqua');
INSERT INTO "tipi_intervento" VALUES (7,'Installazione Accessori');
INSERT INTO "tipi_intervento" VALUES (8,'Tagliando Camper');
INSERT INTO "tipi_intervento" VALUES (9,'Altro');
INSERT INTO "utenti" VALUES ('fabrizio','c4ca4238a0b923820dcc509a6f75849b','amministratore');
INSERT INTO "utenti" VALUES ('stefano','c4ca4238a0b923820dcc509a6f75849b','operatore');
INSERT INTO "utenti" VALUES ('mauro','c4ca4238a0b923820dcc509a6f75849b','operatore');
INSERT INTO "utenti" VALUES ('ilenia','c4ca4238a0b923820dcc509a6f75849b','operatore');
INSERT INTO "utenti" VALUES ('andrea','c4ca4238a0b923820dcc509a6f75849b','operatore');
INSERT INTO "utenti" VALUES ('valery','c4ca4238a0b923820dcc509a6f75849b','operatore');
INSERT INTO "utenti" VALUES ('admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','amministratore');
INSERT INTO "utenti" VALUES ('herald','c4ca4238a0b923820dcc509a6f75849b','amministratore');
COMMIT;
