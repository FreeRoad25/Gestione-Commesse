from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chiave_segreta_casuale"

DB_NAME = "commesse.db"

# Cartella per i file allegati alle commesse
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "xls", "xlsx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# FUNZIONI DI SUPPORTO
# =========================================================
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================================================
# CREAZIONE DATABASE E TABELLE
# =========================================================
def crea_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # tabella commesse (con note_importanti)
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            note_importanti TEXT
        )
    """)

    # 🔹 Se la tabella esisteva già senza note_importanti, la aggiungo
    c.execute("PRAGMA table_info(commesse)")
    cols = [row[1] for row in c.fetchall()]
    if "note_importanti" not in cols:
        c.execute("ALTER TABLE commesse ADD COLUMN note_importanti TEXT")

    # tabella operatori
    c.execute("""
        CREATE TABLE IF NOT EXISTS operatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # tabella ore lavorate
    c.execute("""
        CREATE TABLE IF NOT EXISTS ore_lavorate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_operatore INTEGER,
            id_commessa INTEGER,
            ore REAL,
            data_imputazione TEXT
        )
    """)

    # tabella commesse consegnate
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse_consegnate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            saldata TEXT CHECK(saldata IN ('Si','No')) DEFAULT 'No'
        )
    """)

    # tabella magazzino
    c.execute("""
        CREATE TABLE IF NOT EXISTS magazzino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice TEXT UNIQUE,
            descrizione TEXT NOT NULL,
            unita TEXT,
            quantita REAL DEFAULT 0,
            codice_barre TEXT,
            fornitore TEXT,
            scorta_minima REAL DEFAULT 0
        )
    """)

    # tabella movimenti magazzino
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimenti_magazzino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_articolo INTEGER,
            tipo_movimento TEXT CHECK(tipo_movimento IN ('Carico', 'Scarico')),
            quantita REAL NOT NULL,
            data_movimento TEXT DEFAULT CURRENT_TIMESTAMP,
            id_commessa INTEGER,
            note TEXT,
            FOREIGN KEY (id_articolo) REFERENCES magazzino(id),
            FOREIGN KEY (id_commessa) REFERENCES commesse(id)
        )
    """)

    # tabella file allegati alle commesse
    c.execute("""
        CREATE TABLE IF NOT EXISTS commessa_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_commessa INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT,
            upload_date TEXT,
            FOREIGN KEY (id_commessa) REFERENCES commesse(id)
        )
    """)

    # tabella utenti per login con password cifrata
    c.execute("""
        CREATE TABLE IF NOT EXISTS utenti (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)

    # 🔹 utente admin di default con password 1234 se non esiste
    c.execute("SELECT COUNT(*) FROM utenti WHERE username = ?", ("admin",))
    if c.fetchone()[0] == 0:
        pwd_hash = generate_password_hash("1234")
        c.execute("INSERT INTO utenti (username, password_hash) VALUES (?, ?)", ("admin", pwd_hash))

    conn.commit()
    conn.close()


# =========================================================
# LOGIN / LOGOUT / CAMBIO PASSWORD
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM utenti WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="❌ Credenziali errate")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    return redirect(url_for("login"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/cambia_password", methods=["GET", "POST"])
@login_required
def cambia_password():
    if request.method == "POST":
        old_pwd = request.form.get("old_password", "")
        new_pwd = request.form.get("new_password", "")
        conf_pwd = request.form.get("confirm_password", "")

        if not new_pwd or new_pwd != conf_pwd:
            return render_template("cambia_password.html", error="Le nuove password non coincidono")

        username = session.get("username")
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM utenti WHERE username = ?", (username,))
        user = c.fetchone()

        if not user or not check_password_hash(user["password_hash"], old_pwd):
            conn.close()
            return render_template("cambia_password.html", error="Password attuale errata")

        new_hash = generate_password_hash(new_pwd)
        c.execute("UPDATE utenti SET password_hash = ? WHERE username = ?", (new_hash, username))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("cambia_password.html")


# =========================================================
# HOME
# =========================================================
@app.route("/home")
@login_required
def home():
    return render_template("index.html", current_year=datetime.now().year)


# =========================================================
# COMMESSE
# =========================================================
@app.route("/lista_commesse")
@login_required
def lista_commesse():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()
    conn.close()
    return render_template("commesse.html", commesse=commesse)


@app.route("/elenco_soffietti")
@login_required
def elenco_soffietti():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT *
        FROM commesse
        WHERE LOWER(tipo_intervento) LIKE '%soffietto%'
        ORDER BY date(data_conferma) DESC
    """)
    commesse = c.fetchall()
    conn.close()
    return render_template("elenco_soffietti.html", commesse=commesse)


@app.route("/aggiungi_commessa", methods=["GET", "POST"])
@login_required
def aggiungi_commessa():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form.get("nome")
        tipo_intervento = request.form.get("tipo_intervento", "").strip()
        altro_input = request.form.get("altro_input", "").strip()
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        ore_necessarie = request.form.get("ore_necessarie")
        marca = request.form.get("marca_veicolo")
        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_consegna = request.form.get("data_consegna")
        note_importanti = request.form.get("note_importanti", "").strip()

        if tipo_intervento.lower() == "altro" and altro_input:
            tipo_intervento = altro_input
        elif tipo_intervento.lower() == "altro":
            tipo_intervento = "Non specificato"

        data_conferma = datetime.today().strftime("%Y-%m-%d")

        c.execute("""
            INSERT INTO commesse 
              (nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
               ore_necessarie, marca_veicolo, modello_veicolo, dimensioni, data_consegna, note_importanti)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
            ore_necessarie, marca, modello, dimensioni, data_consegna, note_importanti
        ))
        id_commessa = c.lastrowid

        # 🔹 Salvataggio eventuali file allegati
        files = request.files.getlist("file_commessa")
        for f in files:
            if f and allowed_file(f.filename):
                original_name = f.filename
                filename = secure_filename(f.filename)
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                final_name = f"{id_commessa}{ts}{filename}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
                f.save(path)
                c.execute("""
                    INSERT INTO commessa_files (id_commessa, filename, original_name, upload_date)
                    VALUES (?, ?, ?, ?)
                """, (id_commessa, final_name, original_name, datetime.now().isoformat(timespec="seconds")))

        conn.commit()
        conn.close()
        return redirect(url_for("lista_commesse"))

    # GET: leggo valori per tendine dinamiche
    c.execute("SELECT DISTINCT tipo_intervento FROM commesse WHERE tipo_intervento IS NOT NULL AND tipo_intervento != ''")
    tipi_intervento = [row["tipo_intervento"] for row in c.fetchall()]
    c.execute("SELECT DISTINCT marca_veicolo FROM commesse WHERE marca_veicolo IS NOT NULL AND marca_veicolo != ''")
    marche = [row["marca_veicolo"] for row in c.fetchall()]
    c.execute("SELECT DISTINCT modello_veicolo FROM commesse WHERE modello_veicolo IS NOT NULL AND modello_veicolo != ''")
    modelli = [row["modello_veicolo"] for row in c.fetchall()]
    conn.close()

    return render_template("aggiungi_commessa.html",
                           tipi_intervento=tipi_intervento,
                           marche=marche,
                           modelli=modelli)


@app.route("/modifica_commessa/<int:id>", methods=["GET", "POST"])
@login_required
def modifica_commessa(id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Preleva la commessa
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    if request.method == "POST":
        nome = request.form.get("nome")
        tipo_intervento = request.form.get("tipo_intervento", "").strip()
        altro_input = request.form.get("altro_input", "").strip()

        if tipo_intervento.lower() == "altro" and altro_input:
            tipo_intervento = altro_input
        elif tipo_intervento.lower() == "altro":
            tipo_intervento = "Non specificato"
        elif not tipo_intervento:
            tipo_intervento = commessa["tipo_intervento"]

        data_conferma = request.form.get("data_conferma")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        ore_necessarie = request.form.get("ore_necessarie")
        marca = request.form.get("marca_veicolo")
        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_consegna = request.form.get("data_consegna")
        note_importanti = request.form.get("note_importanti", "").strip()

        c.execute("""
            UPDATE commesse
               SET nome=?,
                   tipo_intervento=?,
                   data_conferma=?,
                   data_arrivo_materiali=?,
                   data_inizio=?,
                   ore_necessarie=?,
                   marca_veicolo=?,
                   modello_veicolo=?,
                   dimensioni=?,
                   data_consegna=?,
                   note_importanti=?
             WHERE id=?
        """, (
            nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
            ore_necessarie, marca, modello, dimensioni, data_consegna, note_importanti, id
        ))

        # Nuovi file allegati
        files = request.files.getlist("file_commessa")
        for f in files:
            if f and allowed_file(f.filename):
                original_name = f.filename
                filename = secure_filename(f.filename)
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                final_name = f"{id}{ts}{filename}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], final_name)
                f.save(path)
                c.execute("""
                    INSERT INTO commessa_files (id_commessa, filename, original_name, upload_date)
                    VALUES (?, ?, ?, ?)
                """, (id, final_name, original_name, datetime.now().isoformat(timespec="seconds")))

        conn.commit()
        conn.close()
        return redirect(url_for("lista_commesse"))

    # GET: valori unici per tendine + file allegati
    c.execute("SELECT DISTINCT tipo_intervento FROM commesse WHERE tipo_intervento IS NOT NULL AND tipo_intervento != ''")
    tipi_intervento = [row["tipo_intervento"] for row in c.fetchall()]
    c.execute("SELECT DISTINCT marca_veicolo FROM commesse WHERE marca_veicolo IS NOT NULL AND marca_veicolo != ''")
    marche = [row["marca_veicolo"] for row in c.fetchall()]
    c.execute("SELECT DISTINCT modello_veicolo FROM commesse WHERE modello_veicolo IS NOT NULL AND modello_veicolo != ''")
    modelli = [row["modello_veicolo"] for row in c.fetchall()]

    c.execute("SELECT * FROM commessa_files WHERE id_commessa = ? ORDER BY upload_date DESC", (id,))
    files = c.fetchall()
    conn.close()

    return render_template("modifica_commessa.html",
                           commessa=commessa,
                           files=files,
                           tipi_intervento=tipi_intervento,
                           marche=marche,
                           modelli=modelli)


@app.route("/elimina/<int:id>")
@login_required
def elimina_commessa(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM commesse WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("lista_commesse"))


# =========================================================
# FILE ALLEGATI COMMESSE
# =========================================================
@app.route("/commessa/<int:id>/files")
@login_required
def commessa_files_view(id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()
    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    c.execute("SELECT * FROM commessa_files WHERE id_commessa = ? ORDER BY upload_date DESC", (id,))
    files = c.fetchall()
    conn.close()
    return render_template("commessa_files.html", commessa=commessa, files=files)


@app.route("/commessa_file/<int:file_id>/download")
@login_required
def download_commessa_file(file_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commessa_files WHERE id = ?", (file_id,))
    file_row = c.fetchone()
    conn.close()

    if not file_row:
        return "File non trovato", 404

    filename = file_row["filename"]
    original_name = file_row["original_name"] or filename
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True, download_name=original_name)
# =========================================================
# OPERATORI
# =========================================================
@app.route("/operatori")
@login_required
def operatori():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM operatori ORDER BY nome ASC")
    operatori = c.fetchall()
    c.execute("SELECT id, nome FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()
    conn.close()
    return render_template("operatori.html", operatori=operatori, commesse=commesse)


@app.route("/aggiungi_operatore", methods=["GET", "POST"])
@login_required
def aggiungi_operatore():
    if request.method == "POST":
        nome = request.form.get("nome")
        if nome:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO operatori (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
        return redirect(url_for("operatori"))

    return render_template("aggiungi_operatore.html")


@app.route("/registra_ore", methods=["POST"])
@login_required
def registra_ore():
    id_operatore = request.form.get("operatore")
    id_commessa = request.form.get("commessa")
    ore = float(request.form.get("ore"))
    data_imputazione = date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO ore_lavorate (id_operatore, id_commessa, ore, data_imputazione)
        VALUES (?, ?, ?, ?)
    """, (id_operatore, id_commessa, ore, data_imputazione))

    c.execute("""
        UPDATE commesse
           SET ore_eseguite = COALESCE(ore_eseguite, 0) + ?,
               ore_rimanenti =
                 CASE
                    WHEN ore_necessarie IS NOT NULL
                    THEN ore_necessarie - (COALESCE(ore_eseguite, 0) + ?)
                    ELSE NULL
                 END
         WHERE id = ?
    """, (ore, ore, id_commessa))

    conn.commit()
    conn.close()
    return redirect(url_for("operatori"))


# =========================================================
# CONSEGNA VEICOLO / ARCHIVIO
# =========================================================
@app.route("/consegna", methods=["GET", "POST"])
@login_required
def consegna_veicolo():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, nome, tipo_intervento FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    if request.method == "POST":
        id_commessa = request.form.get("id_commessa")
        if id_commessa:
            conn.close()
            return redirect(url_for("conferma_consegna", id=int(id_commessa)))

    conn.close()
    return render_template("consegna_veicolo.html", commesse=commesse)


@app.route("/conferma_consegna/<int:id>", methods=["GET", "POST"])
@login_required
def conferma_consegna(id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    if request.method == "POST":
        saldata = request.form.get("saldata", "No")
        data_consegna = date.today().isoformat()

        c.execute("""
            INSERT INTO commesse_consegnate
              (nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
               ore_necessarie, ore_eseguite, ore_rimanenti, marca_veicolo, modello_veicolo,
               dimensioni, data_consegna, saldata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            commessa["nome"],
            commessa["tipo_intervento"],
            commessa["data_conferma"],
            commessa["data_arrivo_materiali"],
            commessa["data_inizio"],
            commessa["ore_necessarie"],
            commessa["ore_eseguite"],
            commessa["ore_rimanenti"],
            commessa["marca_veicolo"],
            commessa["modello_veicolo"],
            commessa["dimensioni"],
            data_consegna,
            saldata
        ))

        c.execute("DELETE FROM commesse WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("archivio_consegnati"))

    conn.close()
    return render_template("conferma_consegna.html", commessa=commessa)


@app.route("/archivio_consegnati")
@login_required
def archivio_consegnati():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT *
        FROM commesse_consegnate
        ORDER BY
            CASE
                WHEN saldata IN ('No','NO','no') THEN 0
                ELSE 1
            END,
            date(data_consegna) DESC
    """)
    commesse = c.fetchall()
    conn.close()
    return render_template("archivio_consegnati.html", commesse=commesse)


@app.route("/aggiorna_saldato/<int:id>", methods=["POST"])
@login_required
def aggiorna_saldato(id):
    nuova = request.form.get("saldata", "").strip().lower()
    nuova = "Si" if nuova in ("si", "sì", "yes", "y") else "No"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE commesse_consegnate SET saldata = ? WHERE id = ?", (nuova, id))
    conn.commit()
    conn.close()
    return redirect(url_for("archivio_consegnati"))
# =========================================================
# MAGAZZINO
# =========================================================
@app.route("/magazzino")
@login_required
def magazzino():
    # pagina di menu del magazzino
    return render_template("magazzino.html")


@app.route("/magazzino_articoli")
@login_required
def magazzino_articoli():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM magazzino ORDER BY descrizione ASC")
    articoli = c.fetchall()
    conn.close()
    return render_template("magazzino_articoli.html", articoli=articoli)


@app.route("/magazzino_sottoscorta")
@login_required
def magazzino_sottoscorta():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT * 
        FROM magazzino
        WHERE quantita < scorta_minima
        ORDER BY descrizione ASC
    """)
    articoli = c.fetchall()
    conn.close()
    return render_template("magazzino_sottoscorta.html", articoli=articoli)


@app.route("/aggiungi_articolo", methods=["POST"])
@login_required
def aggiungi_articolo():
    codice = request.form.get("codice")
    descrizione = request.form.get("descrizione")
    unita = request.form.get("unita")
    quantita = request.form.get("quantita") or 0
    codice_barre = request.form.get("codice_barre")
    fornitore = request.form.get("fornitore")
    scorta_minima = request.form.get("scorta_minima") or 0

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO magazzino
            (codice, descrizione, unita, quantita, codice_barre, fornitore, scorta_minima)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (codice, descrizione, unita, quantita, codice_barre, fornitore, scorta_minima))
    conn.commit()
    conn.close()
    return redirect(url_for("magazzino_articoli"))


@app.route("/scarico_magazzino", methods=["GET", "POST"])
@login_required
def scarico_magazzino():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM magazzino ORDER BY descrizione ASC")
    articoli = c.fetchall()
    c.execute("SELECT id, nome FROM commesse ORDER BY nome ASC")
    commesse = c.fetchall()

    if request.method == "POST":
        id_articolo = request.form.get("id_articolo")
        id_commessa = request.form.get("id_commessa")
        quantita = float(request.form.get("quantita"))
        note = request.form.get("note")

        c.execute("UPDATE magazzino SET quantita = quantita - ? WHERE id = ?", (quantita, id_articolo))

        c.execute("""
            INSERT INTO movimenti_magazzino
                (id_articolo, tipo_movimento, quantita, id_commessa, note)
            VALUES (?, 'Scarico', ?, ?, ?)
        """, (id_articolo, quantita, id_commessa, note))

        conn.commit()
        conn.close()
        return redirect(url_for("movimenti_magazzino"))

    conn.close()
    return render_template("scarico_magazzino.html", articoli=articoli, commesse=commesse)


@app.route("/carico_magazzino", methods=["GET", "POST"])
@login_required
def carico_magazzino():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM magazzino ORDER BY descrizione ASC")
    articoli = c.fetchall()

    if request.method == "POST":
        id_articolo = request.form.get("id_articolo")
        quantita = float(request.form.get("quantita"))
        note = request.form.get("note")

        c.execute("UPDATE magazzino SET quantita = quantita + ? WHERE id = ?", (quantita, id_articolo))
        c.execute("""
            INSERT INTO movimenti_magazzino (id_articolo, tipo_movimento, quantita, note)
            VALUES (?, 'Carico', ?, ?)
        """, (id_articolo, quantita, note))

        conn.commit()
        conn.close()
        # Resta sulla stessa pagina dopo il salvataggio
        return redirect(url_for("carico_magazzino"))

    conn.close()
    return render_template("carico_magazzino.html", articoli=articoli)


@app.route("/movimenti_magazzino", methods=["GET"])
@login_required
def movimenti_magazzino():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Parametri di ricerca
    ricerca = request.args.get("ricerca", "").strip()
    id_commessa = request.args.get("id_commessa", "")
    tipo = request.args.get("tipo", "")

    query = """
        SELECT m.*, 
               a.descrizione AS articolo, 
               a.codice_barre, 
               c.nome AS commessa
        FROM movimenti_magazzino m
        JOIN magazzino a ON m.id_articolo = a.id
        LEFT JOIN commesse c ON m.id_commessa = c.id
        WHERE 1=1
    """
    params = []

    if ricerca:
        query += " AND (a.descrizione LIKE ? OR a.codice_barre LIKE ?)"
        params.extend([f"%{ricerca}%", f"%{ricerca}%"])

    if id_commessa:
        query += " AND m.id_commessa = ?"
        params.append(id_commessa)

    if tipo:
        query += " AND m.tipo_movimento = ?"
        params.append(tipo)

    query += " ORDER BY m.data_movimento DESC"

    movimenti = []
    if ricerca or id_commessa or tipo:
        c.execute(query, params)
        movimenti = c.fetchall()

    c.execute("SELECT id, nome FROM commesse ORDER BY nome ASC")
    commesse = c.fetchall()

    conn.close()

    return render_template(
        "movimenti_magazzino.html",
        movimenti=movimenti,
        commesse=commesse,
        filtro_commessa=request.args.get("id_commessa")
    )


# ROOT
# =========================================================
@app.route("/")
def root():
    return redirect(url_for("login"))


# =========================================================
# AVVIO APP
# =========================================================
if __name__ == "__main__":
    crea_database()
    app.run(debug=True)