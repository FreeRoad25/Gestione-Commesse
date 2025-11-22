from flask import send_file
from reportlab.lib.styles import ParagraphStyle
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
from crea_tabelle_pg import create_tables

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
print("DB_HOST:", DB_HOST)
print("DB_NAME:", DB_NAME)
print("DB_USER:", DB_USER)

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

# ✅ Test connessione isolato (solo diagnostica, non interferisce con il flusso)
def test_pg_connection():
    try:
        conn = get_db_connection()
        conn.close()
        print(">>> POSTGRES: CONNESSIONE OK ✔")
    except Exception as e:
        print(">>> POSTGRES: ERRORE ❌")
        print(e)


from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
create_tables()

# =========================
# BYPASS LOGIN TEMPORANEO
# =========================
@app.before_request
def bypass_login():
    session["ruolo"] = "amministratore"

# =========================
# LOGIN MANAGER
# =========================
login_manager = LoginManager()

@login_manager.request_loader
def load_user_from_request(request):
    class FakeUser(UserMixin):
        id = 1
        ruolo = "amministratore"
    session["ruolo"] = "amministratore"
    return FakeUser()

login_manager.init_app(app)
login_manager.login_view = "login"

app.secret_key = os.environ.get("SECRET_KEY", "fallback123")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 ora

# =====================
# CONTROLLO RUOLO ADMIN
# =====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "ruolo" not in session:
            flash("Devi effettuare il login.")
            return redirect(url_for("login"))
        if session.get("ruolo") != "amministratore":
            flash("Accesso non autorizzato.")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


# ====== CREAZIONE AUTOMATICA TABELLE BASE SU POSTGRES ======

def init_db_online():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Tabella UTENTI (PostgreSQL)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                ruolo TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()
        print("Tabella 'utenti' verificata/creata su PostgreSQL.")

    except Exception as e:
        print("Errore creazione tabella utenti:", e)


init_db_online()

import crea_admin_online
crea_admin_online.crea_admin_se_manca()


# ✅ TABELLA TIPI_INTERVENTO
conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS tipi_intervento (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
)
""")

# Verifica se vuota
cur.execute("SELECT COUNT(*) AS count FROM tipi_intervento")
result = cur.fetchone()
count = result["count"]

if count == 0:
    valori_default = [
        "Montaggio Riscaldatore",
        "Tetto a Soffietto",
        "Coibentazione",
        "Allestimento Interno",
        "Impianto Elettrico",
        "Impianto Acqua",
        "Installazione Accessori",
        "Tagliando Camper",
        "Altro"
    ]

    for nome in valori_default:
        cur.execute(
            "INSERT INTO tipi_intervento (nome) VALUES (%s)",
            (nome,)
        )

    print("Tabella 'tipi_intervento' popolata con dati default.")

conn.commit()
conn.close()

# ===================== FILE ALLEGATI =====================
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "xls", "xlsx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- GESTIONE LOGIN E UTENTI ---

class User(UserMixin):
    def __init__(self, username=None, ruolo=None):
        self.id = username
        self.username = username
        self.ruolo = ruolo

    def get_id(self):
        return str(self.id)

    @staticmethod
    def from_row(row):
        return User(row["username"], row["ruolo"])


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, ruolo FROM utenti WHERE username = %s", (user_id,))
    row = cur.fetchone()

    conn.close()

    if row:
        return User(row["username"], row["ruolo"])

    return None
# =========================================================
# CREAZIONE STRUTTURA DATABASE POSTGRES (SAFE MODE)
# =========================================================

def crea_database():
    conn = get_db_connection()
    c = conn.cursor()

    # ===== COMMESSE =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo_intervento TEXT,
            data_conferma DATE,
            data_arrivo_materiali DATE,
            data_inizio DATE,
            ore_necessarie REAL,
            ore_eseguite REAL DEFAULT 0,
            ore_rimanenti REAL DEFAULT 0,
            marca_veicolo TEXT,
            modello_veicolo TEXT,
            dimensioni TEXT,
            data_consegna DATE,
            note_importanti TEXT
        )
    """)

    # ===== OPERATORI =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS operatori (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            costo_orario REAL DEFAULT 0
        )
    """)

    # ===== MARCHE =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS marche (
            id SERIAL PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        )
    """)

    # ===== ARTICOLI =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS articoli (
            id SERIAL PRIMARY KEY,
            codice TEXT UNIQUE NOT NULL,
            descrizione TEXT NOT NULL,
            unita TEXT,
            quantita REAL DEFAULT 0,
            codice_barre TEXT,
            fornitore TEXT,
            scorta_minima REAL DEFAULT 0,
            costo_netto REAL DEFAULT 0,
            data_modifica DATE
        )
    """)

    # ===== COMMESSE MATERIALI (ORA CORRETTO) =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse_materiali (
            id SERIAL PRIMARY KEY,
            id_commessa INTEGER REFERENCES commesse(id),
            id_articolo INTEGER REFERENCES articoli(id),
            quantita REAL NOT NULL
        )
    """)

    # ===== ORE LAVORATE =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS ore_lavorate (
            id SERIAL PRIMARY KEY,
            id_operatore INTEGER REFERENCES operatori(id),
            id_commessa INTEGER REFERENCES commesse(id),
            ore REAL,
            data_imputazione DATE
        )
    """)

    # ===== COMMESSE CONSEGNATE =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse_consegnate (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo_intervento TEXT,
            data_conferma DATE,
            data_arrivo_materiali DATE,
            data_inizio DATE,
            ore_necessarie REAL,
            ore_eseguite REAL,
            ore_rimanenti REAL,
            marca_veicolo TEXT,
            modello_veicolo TEXT,
            dimensioni TEXT,
            data_consegna DATE,
            saldata TEXT CHECK (saldata IN ('Si','No')) DEFAULT 'No'
        )
    """)

    # ===== MOVIMENTI MAGAZZINO =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS movimenti_magazzino (
            id SERIAL PRIMARY KEY,
            id_articolo INTEGER REFERENCES articoli(id),
            tipo_movimento TEXT CHECK (tipo_movimento IN ('Carico','Scarico')),
            quantita REAL NOT NULL,
            data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_commessa INTEGER REFERENCES commesse(id),
            note TEXT
        )
    """)

    # ===== FILE COMMESSE =====
    c.execute("""
        CREATE TABLE IF NOT EXISTS commessa_files (
            id SERIAL PRIMARY KEY,
            id_commessa INTEGER REFERENCES commesse(id),
            filename TEXT NOT NULL,
            original_name TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
  
    crea_database()

# =========================================================
# LOGIN / LOGOUT / CAMBIO PASSWORD (STABILE)
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    session["logged_in"] = True
    session["username"] = "admin"
    session["ruolo"] = "amministratore"
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/cambia_password", methods=["GET", "POST"])
def cambia_password():
    if request.method == "POST":
        old_pwd = request.form.get("old_password", "")
        new_pwd = request.form.get("new_password", "")
        conf_pwd = request.form.get("confirm_password", "")

        if not new_pwd or new_pwd != conf_pwd:
            return render_template("cambia_password.html", error="Le nuove password non coincidono")

        username = session.get("username")

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT password_hash FROM utenti WHERE username = %s", (username,))
        user = c.fetchone()

        if not user or not check_password_hash(user["password_hash"], old_pwd):
            conn.close()
            return render_template("cambia_password.html", error="Password attuale errata")

        new_hash = generate_password_hash(new_pwd)
        c.execute("UPDATE utenti SET password_hash = %s WHERE username = %s", (new_hash, username))

        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("cambia_password.html")


# =========================================================
# HOME
# =========================================================
@app.route("/home")
#@login_required
def home():
    username = session.get("username")
    ruolo = session.get("ruolo")
    print("Entrato nella funzione HOME")
    return render_template("index.html", username=username, ruolo=ruolo, current_year=datetime.now().year)


# =========================================================
# COMMESSE
# =========================================================
@app.route("/lista_commesse")
#@login_required
def lista_commesse():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()
    conn.close()
    return render_template("commesse.html", commesse=commesse)


@app.route("/elenco_soffietti")
#@login_required
def elenco_soffietti():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    SELECT *
    FROM commesse
    WHERE LOWER(tipo_intervento) LIKE '%soffietto%'
    ORDER BY data_conferma DESC
""")
    commesse = c.fetchall()
    conn.close()
    return render_template("elenco_soffietti.html", commesse=commesse)


from werkzeug.utils import secure_filename
import os
from flask import request, redirect, url_for, render_template
from flask_login import login_required

# Percorso assoluto al database


@app.route("/aggiungi_commessa", methods=["GET", "POST"])
def aggiungi_commessa():
    conn = get_db_connection()
    import psycopg2.extras
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        nome = request.form.get("nome")
        tipo_intervento = request.form.get("tipo_intervento")
        marca_veicolo = request.form.get("marca_veicolo")
        modello_veicolo = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_conferma = request.form.get("data_conferma")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        note_importanti = request.form.get("note_importanti")

        ore_necessarie = float(request.form.get("ore_necessarie") or 0)
        ore_eseguite = 0
        ore_rimanenti = ore_necessarie

        try:
           c.execute("""
             INSERT INTO commesse
             (nome, tipo_intervento, marca_veicolo, modello_veicolo, dimensioni,
             data_conferma, data_arrivo_materiali, data_inizio,
             ore_necessarie, ore_eseguite, ore_rimanenti, data_consegna,
             foto, allegato, note_importanti)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            nome,
            tipo_intervento,
            marca_veicolo,
            modello_veicolo,
            dimensioni,
            data_conferma,
           data_arrivo_materiali,
            data_inizio,
            ore_necessarie,
           ore_eseguite,
            ore_rimanenti,
            None,
           None,
           None,
           note_importanti
 )) 

           conn.commit()
           return redirect(url_for("lista_commesse"))

        except Exception as e:
            conn.rollback()
            print("ERRORE INSERT COMMESSA:", e)
            return f"Errore salvataggio commessa: {str(e)}", 500

        finally:
            conn.close()

    # GET
    c.execute("SELECT nome FROM tipi_intervento ORDER BY nome ASC")
    tipi_intervento = [row["nome"] for row in c.fetchall()]

    c.execute("SELECT id, nome FROM marche ORDER BY nome ASC")
    marche = c.fetchall()

    conn.close()

    return render_template(
        "aggiungi_commessa.html",
        tipi_intervento=tipi_intervento,
        marche=marche
    )


@app.route("/modifica_commessa/<int:id>", methods=["GET", "POST"])
def modifica_commessa(id):
    conn = get_db_connection()
    c = conn.cursor()

    # Preleva la commessa
    c.execute("SELECT * FROM commesse WHERE id = %s", (id,))
    commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    if request.method == "POST":

        # --- NOME ---
        nome = request.form.get("nome")

        # --- TIPO INTERVENTO ---
        tipo_intervento = (request.form.get("tipo_intervento") or "").strip()
        nuovo_intervento = (request.form.get("nuovo_intervento") or "").strip()

        # Se selezioni "Altro" e scrivi qualcosa → salva in tabella e usa quel valore
        if tipo_intervento == "Altro" and nuovo_intervento:
            c.execute(
                """
                INSERT INTO tipi_intervento (nome)
                VALUES (%s)
                ON CONFLICT (nome) DO NOTHING
                """,
                (nuovo_intervento,)
            )
            conn.commit()
            tipo_intervento = nuovo_intervento

        # Se la select è vuota ma hai scritto un nuovo intervento
        elif not tipo_intervento and nuovo_intervento:
            c.execute(
                """
                INSERT INTO tipi_intervento (nome)
                VALUES (%s)
                ON CONFLICT (nome) DO NOTHING
                """,
                (nuovo_intervento,)
            )
            conn.commit()
            tipo_intervento = nuovo_intervento

        # Se non cambi nulla → mantieni valore precedente
        elif not tipo_intervento:
            # commessa è un dict (RealDictCursor)
            tipo_intervento = commessa["tipo_intervento"]

        # --- MARCA ---
        marca_sel = request.form.get("marca_veicolo")
        nuova_marca = (request.form.get("nuova_marca") or "").strip()

        if marca_sel == "nuova" and nuova_marca:
            # salva nel DB solo se non esiste
            c.execute(
                """
                INSERT INTO marche (nome)
                VALUES (%s)
                ON CONFLICT (nome) DO NOTHING
                """,
                (nuova_marca,)
            )
            conn.commit()
            marca = nuova_marca
        else:
            marca = marca_sel

        # --- ALTRI CAMPI ---
        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_conferma = request.form.get("data_conferma")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        data_consegna = request.form.get("data_consegna")
        ore_necessarie = request.form.get("ore_necessarie") or 0
        note_importanti = (request.form.get("note_importanti") or "").strip()

        # --- UPDATE COMMESSA ---
        c.execute("""
            UPDATE commesse
               SET nome=%s,
                   tipo_intervento=%s,
                   data_conferma=%s,
                   data_arrivo_materiali=%s,
                   data_inizio=%s,
                   ore_necessarie=%s,
                   marca_veicolo=%s,
                   modello_veicolo=%s,
                   dimensioni=%s,
                   data_consegna=%s,
                   note_importanti=%s
             WHERE id=%s
        """, (
            nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
            ore_necessarie, marca, modello, dimensioni, data_consegna, note_importanti, id
        ))

        # --- FILE ALLEGATI ---
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
                    VALUES (%s, %s, %s, %s)
                """, (id, final_name, original_name, datetime.now().isoformat(timespec="seconds")))

        conn.commit()
        conn.close()
        return redirect(url_for("lista_commesse"))

    # --- GET: CARICO LE TENDINE ---

    # Tipi intervento dalla tabella
    c.execute("SELECT nome FROM tipi_intervento ORDER BY nome ASC")
    tipi_intervento = [row["nome"] for row in c.fetchall()]

    # Marche dalla tabella
    c.execute("SELECT id, nome FROM marche ORDER BY nome ASC")
    marche = c.fetchall()

    # Modelli (come prima)
    c.execute("""
        SELECT DISTINCT modello_veicolo
        FROM commesse
        WHERE modello_veicolo IS NOT NULL AND modello_veicolo != ''
    """)
    modelli = [row["modello_veicolo"] for row in c.fetchall()]

    # File allegati
    c.execute(
        "SELECT * FROM commessa_files WHERE id_commessa = %s ORDER BY upload_date DESC",
        (id,)
    )
    files = c.fetchall()

    conn.close()

    return render_template(
        "modifica_commessa.html",
        id_commessa=id,
        commessa=commessa,
        files=files,
        tipi_intervento=tipi_intervento,
        marche=marche,
        modelli=modelli
    )

@app.route("/stampa_commessa/<int:id>")
def stampa_commessa(id):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    import tempfile

    conn = get_db_connection()
    c = conn.cursor()

    # CERCA IN COMMESSE
    c.execute("SELECT * FROM commesse WHERE id = %s", (id,))
    commessa = c.fetchone()

    # SE NON TROVATA, CERCA IN ARCHIVIO
    if not commessa:
        c.execute("SELECT * FROM commesse_consegnate WHERE id = %s", (id,))
        commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata"

    # MATERIALI
    c.execute("""
        SELECT a.codice, a.descrizione, cm.quantita, a.costo_netto
        FROM commesse_materiali cm
        JOIN articoli a ON cm.id_articolo = a.id
        WHERE cm.id_commessa = %s
    """, (id,))
    materiali = c.fetchall()

    # ORE LAVORATE
    c.execute("""
        SELECT o.nome AS operatore, ol.ore, COALESCE(o.costo_orario, 0) AS costo_orario
        FROM ore_lavorate ol
        LEFT JOIN operatori o ON o.id = ol.id_operatore
        WHERE ol.id_commessa = %s
    """, (id,))
    ore_lavorate = c.fetchall()

    conn.close()

    # === CREAZIONE PDF TEMPORANEO ===
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filename = tmp.name

    pdf = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # INTESTAZIONE
    elements.append(Paragraph(f"<b>Commessa #{id} – {commessa['nome']}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # DATI COMMESSA
    tabella_commessa = [
        ["Tipo Intervento", commessa["tipo_intervento"]],
        ["Marca Veicolo", f"{commessa['marca_veicolo']} {commessa['modello_veicolo']}"],
        ["Data Conferma", commessa["data_conferma"] or "---"],
        ["Data Arrivo Materiali", commessa["data_arrivo_materiali"] or "---"],
        ["Data Inizio", commessa["data_inizio"] or "---"],
        ["Data Consegna", commessa["data_consegna"] or "---"],
        ["Ore Necessarie", commessa["ore_necessarie"] or 0],
        ["Ore Eseguite", commessa.get("ore_eseguite", 0)]
    ]

    t_info = Table(tabella_commessa, colWidths=[150, 350])
    t_info.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))

    # MATERIALI
    if materiali:
        data_materiali = [["Codice", "Descrizione", "Q.tà", "Costo €", "Totale €"]]
        for m in materiali:
            tot = (m["quantita"] or 0) * (m["costo_netto"] or 0)
            data_materiali.append([
                m["codice"], m["descrizione"], m["quantita"],
                f"{m['costo_netto']:.2f}", f"{tot:.2f}"
            ])

        t_mat = Table(data_materiali, colWidths=[70, 250, 60, 80, 80])
        t_mat.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.4, colors.black),
        ]))

        elements.append(Paragraph("Materiali Utilizzati", styles["Heading2"]))
        elements.append(t_mat)
        elements.append(Spacer(1, 12))

    # ORE LAVORATE
    if ore_lavorate:
        data_ore = [["Operatore", "Ore", "€/h", "Totale €"]]
        for r in ore_lavorate:
            tot = r["ore"] * r["costo_orario"]
            data_ore.append([r["operatore"], r["ore"], r["costo_orario"], f"{tot:.2f}"])

        t_ore = Table(data_ore, colWidths=[200, 80, 80, 80])
        t_ore.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.4, colors.black),
        ]))

        elements.append(Paragraph("Ore Lavorate", styles["Heading2"]))
        elements.append(t_ore)

    pdf.build(elements)

    return send_file(filename, as_attachment=False, mimetype="application/pdf")
  
@app.route("/stampa_commessa_archiviata/<int:id>")
def stampa_commessa_archiviata(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM commesse_consegnate WHERE id = %s", (id,))
    com = c.fetchone()
    conn.close()

    if not com:
        return "Commessa archiviata non trovata"

    return render_template("stampa_commessa.html", commessa=com)


@app.route("/elimina/<int:id>")
def elimina_commessa(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("DELETE FROM commesse WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("lista_commesse"))


@app.route("/test_db")
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        conn.close()

        return f"✅ CONNESSIONE OK – PostgreSQL risponde: {result['now'] if isinstance(result, dict) else result}"

    except Exception as e:
        return f"❌ ERRORE CONNESSIONE: {e}"


# =========================================================
# FILE ALLEGATI COMMESSE
# =========================================================
@app.route("/commessa/<int:id>/files")
def commessa_files_view(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM commesse WHERE id = %s", (id,))
    commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    c.execute("""
        SELECT * FROM commessa_files 
        WHERE id_commessa = %s 
        ORDER BY upload_date DESC
    """, (id,))

    files = c.fetchall()
    conn.close()

    return render_template("commessa_files.html", commessa=commessa, files=files)


@app.route("/commessa_file/<int:file_id>/download")
def download_commessa_file(file_id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM commessa_files WHERE id = %s", (file_id,))
    file_row = c.fetchone()
    conn.close()

    if not file_row:
        return "File non trovato", 404

    filename = file_row["filename"]
    original_name = file_row["original_name"] or filename
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True,
        download_name=original_name
    )


@app.route("/test_marche")
def test_marche():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT id, nome FROM marche ORDER BY nome ASC")
    marche = c.fetchall()
    conn.close()

    # PostgreSQL restituisce dict, quindi conversione sicura
    return {"marche_rilevate": [dict(r) for r in marche]}


# =========================================================
# OPERATORI
# =========================================================
@app.route("/operatori")
def operatori():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM operatori ORDER BY nome ASC")
    operatori = c.fetchall()

    c.execute("SELECT id, nome FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    conn.close()
    return render_template("operatori.html", operatori=operatori, commesse=commesse)


@app.route("/aggiungi_operatore", methods=["GET", "POST"])
def aggiungi_operatore():
    if request.method == "POST":
        nome = request.form.get("nome")
        if nome:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO operatori (nome) VALUES (%s)", (nome,))
            conn.commit()
            conn.close()
        return redirect(url_for("operatori"))

    return render_template("aggiungi_operatore.html")


@app.route("/registrazione_ore", methods=["POST"])
def registrazione_ore():
    id_operatore = request.form.get("id_operatore")
    id_commessa = request.form.get("id_commessa")
    ore = float(request.form.get("ore") or 0)
    data_imputazione = request.form.get("data_imputazione") or date.today()

    conn = get_db_connection()
    c = conn.cursor()

    # ✅ Inserimento ore
    c.execute("""
        INSERT INTO ore_lavorate (id_operatore, id_commessa, ore, data_imputazione)
        VALUES (%s, %s, %s, %s)
    """, (id_operatore, id_commessa, ore, data_imputazione))

    # ✅ Aggiornamento ore eseguite
    c.execute("""
        UPDATE commesse
        SET ore_eseguite = COALESCE(ore_eseguite, 0) + %s
        WHERE id = %s
    """, (ore, id_commessa))

    conn.commit()
    conn.close()
    return redirect(url_for("operatori"))


# =========================================================
# CONSEGNA VEICOLO / ARCHIVIO
# =========================================================
@app.route("/consegna", methods=["GET", "POST"])
def consegna_veicolo():
    conn = get_db_connection()
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
def conferma_consegna(id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM commesse WHERE id = %s", (id,))
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

        c.execute("DELETE FROM commesse WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("consegna_veicolo"))

    conn.close()
    return render_template("conferma_consegna.html", commessa=commessa)


@app.route("/archivio_consegnati")
def archivio_consegnati():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
        SELECT
            id,
            nome,
            tipo_intervento,
            data_consegna,
            saldata
        FROM commesse_consegnate
        ORDER BY
            CASE WHEN LOWER(saldata) = 'no' THEN 0 ELSE 1 END,
            id DESC
        """)

        commesse = c.fetchall()
        conn.close()

        return render_template("archivio_consegnati.html", commesse=commesse)

    except Exception as e:
        print("ERRORE ARCHIVIO CONSEGNATI:", e)
        return "Errore caricamento archivio", 500


@app.route("/toggle_saldata/<int:id>", methods=["POST"])
def toggle_saldata(id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Leggo il valore attuale
        c.execute("SELECT saldata FROM commesse_consegnate WHERE id = %s", (id,))
        row = c.fetchone()

        if not row:
            conn.close()
            print(f"ERRORE TOGGLE SALDATA: Nessuna commessa trovata con id {id}")
            return "Errore: commessa non trovata", 404

        attuale = row["saldata"]

        # Calcolo il nuovo valore
        nuovo = "Si" if str(attuale).lower() in ("no", "n", "0") else "No"

        # Aggiorno
        c.execute(
            "UPDATE commesse_consegnate SET saldata = %s WHERE id = %s",
            (nuovo, id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("archivio_consegnati"))

    except Exception as e:
        print("ERRORE TOGGLE SALDATA:", e)
        return "Errore durante aggiornamento stato pagamento", 500


# =========================================================
# MAGAZZINO
# =========================================================
@app.route("/magazzino")
#@login_required
def magazzino():
    # Reindirizza direttamente alla pagina articoli
    return redirect(url_for("magazzino_articoli"))


@app.route("/modifica_articolo/<int:id>", methods=["GET", "POST"])
def modifica_articolo(id):
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == "POST":
        descrizione = request.form.get("descrizione")
        unita = request.form.get("unita")
        quantita = float(request.form.get("quantita") or 0)
        scorta_minima = float(request.form.get("scorta_minima") or 0)
        fornitore = request.form.get("fornitore")
        codice_barre = request.form.get("codice_barre")
        costo_netto = float(request.form.get("costo_netto") or 0)

        # Legge il costo precedente
        c.execute("SELECT costo_netto FROM articoli WHERE id = %s", (id,))
        row = c.fetchone()
        prezzo_vecchio = row["costo_netto"] if row else 0

        # Se cambia il prezzo aggiorna anche la data
        if costo_netto != prezzo_vecchio:
            c.execute("""
                UPDATE articoli SET
                    descrizione = %s,
                    unita = %s,
                    quantita = %s,
                    scorta_minima = %s,
                    fornitore = %s,
                    codice_barre = %s,
                    costo_netto = %s,
                    data_modifica = CURRENT_DATE
                WHERE id = %s
            """, (
                descrizione,
                unita,
                quantita,
                scorta_minima,
                fornitore,
                codice_barre,
                costo_netto,
                id
            ))
        else:
            c.execute("""
                UPDATE articoli SET
                    descrizione = %s,
                    unita = %s,
                    quantita = %s,
                    scorta_minima = %s,
                    fornitore = %s,
                    codice_barre = %s,
                    costo_netto = %s
                WHERE id = %s
            """, (
                descrizione,
                unita,
                quantita,
                scorta_minima,
                fornitore,
                codice_barre,
                costo_netto,
                id
            ))

        conn.commit()

    # Ricarica articolo aggiornato
    c.execute("SELECT * FROM articoli WHERE id = %s", (id,))
    articolo = c.fetchone()
    conn.close()

    return render_template("modifica_articolo.html", articolo=articolo)


@app.route('/pagina_aggiungi_articolo')
#@login_required
def pagina_aggiungi_articolo():
    return render_template('pagina_aggiungi_articolo.html')


@app.route("/magazzino_articoli")
def magazzino_articoli():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    conn.close()
    return render_template("magazzino_articoli.html", articoli=articoli)


@app.route("/magazzino_sottoscorta")
def magazzino_sottoscorta():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
            SELECT codice, descrizione, unita, quantita, scorta_minima
            FROM articoli
            WHERE COALESCE(quantita, 0) < COALESCE(scorta_minima, 0)
            ORDER BY descrizione ASC
        """)

        articoli_sottoscorta = c.fetchall()
        conn.close()

        return render_template(
            "magazzino_sottoscorta.html",
            articoli=articoli_sottoscorta
        )

    except Exception as e:
        print("ERRORE MAGAZZINO SOTTOSCORTA:", e)
        return "Errore caricamento sottoscorta", 500


# ===============================
# 🗑 ELIMINA ARTICOLO
# ===============================
@app.route('/elimina_articolo/<codice>', methods=['POST'])
def elimina_articolo(codice):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("DELETE FROM articoli WHERE codice = %s", (codice,))
    conn.commit()
    conn.close()

    flash("Articolo eliminato con successo!", "success")
    return redirect(url_for("magazzino_articoli"))


@app.route("/aggiungi_articolo", methods=["GET", "POST"])
def aggiungi_articolo():
    if request.method == "POST":
        codice = request.form.get("codice", "").strip()
        descrizione = request.form.get("descrizione", "").strip()
        unita = request.form.get("unita", "").strip()
        quantita = request.form.get("quantita", "").strip()
        codice_barre = request.form.get("codice_barre", "").strip()
        fornitore = request.form.get("fornitore", "").strip()
        scorta_minima = request.form.get("scorta_minima", "").strip()
        costo_netto = request.form.get("costo_netto", "").strip()

        try:
            quantita = float(quantita) if quantita else 0.0
            scorta_minima = float(scorta_minima) if scorta_minima else 0.0
            costo_netto = float(costo_netto) if costo_netto else 0.0
        except ValueError:
            quantita = 0.0
            scorta_minima = 0.0
            costo_netto = 0.0

        data_modifica = datetime.now().date()

        try:
            conn = get_db_connection()
            c = conn.cursor()

            c.execute("""
                INSERT INTO articoli
                (codice, descrizione, unita, quantita, codice_barre, fornitore, scorta_minima, costo_netto, data_modifica)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                codice, descrizione, unita, quantita,
                codice_barre, fornitore, scorta_minima,
                costo_netto, data_modifica
            ))

            conn.commit()
            conn.close()
            return redirect(url_for("magazzino_articoli"))

        except Exception as e:
            print(f"ERRORE salvataggio articolo: {e}")
            return "Errore durante il salvataggio dell'articolo."

    return render_template("pagina_aggiungi_articolo.html")

@app.route("/scarico_magazzino", methods=["GET", "POST"])
def scarico_magazzino():

    id_articolo = request.args.get("id_articolo")
    print("SCARICO – ID articolo selezionato:", id_articolo)

    conn = get_db_connection()
    c = conn.cursor()

    # Elenco articoli
    c.execute("SELECT id, descrizione FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    # Elenco commesse
    c.execute("SELECT id, nome FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    if request.method == "POST":
        id_articolo_form = request.form.get("id_articolo")
        id_commessa = request.form.get("id_commessa") or None
        quantita = float(request.form.get("quantita") or 0)
        note = request.form.get("note")

        # Scarico quantità dal magazzino
        c.execute("""
            UPDATE articoli
            SET quantita = COALESCE(quantita, 0) - %s
            WHERE id = %s
        """, (quantita, id_articolo_form))

        # Registra movimento
        c.execute("""
            INSERT INTO movimenti_magazzino
            (id_articolo, tipo_movimento, quantita, note, id_commessa)
            VALUES (%s, %s, %s, %s, %s)
        """, (id_articolo_form, 'Scarico', quantita, note, id_commessa))

        conn.commit()
        conn.close()
        return redirect(url_for("magazzino_articoli"))

    conn.close()
    return render_template(
        "scarico_magazzino.html",
        articoli=articoli,
        commesse=commesse,
        id_articolo=id_articolo
    )


@app.route("/carico_magazzino", methods=["GET", "POST"])
def carico_magazzino():

    id_articolo = request.args.get("id_articolo")
    print("CARICO – ID articolo selezionato:", id_articolo)

    conn = get_db_connection()
    c = conn.cursor()

    # Elenco articoli
    c.execute("SELECT id, descrizione FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    # Articolo selezionato
    articolo = None
    for a in articoli:
     if str(a["id"]) == str(id_articolo):
        articolo = a
        break

    if request.method == "POST":
        id_articolo_form = request.form.get("id_articolo")
        quantita = float(request.form.get("quantita") or 0)
        note = request.form.get("note")

        # ✅ Aggiorna quantità (carico)
        c.execute("""
            UPDATE articoli
            SET quantita = COALESCE(quantita, 0) + %s
            WHERE id = %s
        """, (quantita, id_articolo_form))

        # ✅ Registra movimento
        c.execute("""
            INSERT INTO movimenti_magazzino
            (id_articolo, tipo_movimento, quantita, note)
            VALUES (%s, %s, %s, %s)
        """, (id_articolo_form, 'Carico', quantita, note))

        conn.commit()
        conn.close()
        return redirect(url_for("magazzino_articoli"))

    conn.close()
    return render_template(
        "carico_magazzino.html",
        articolo=articolo,
        articoli=articoli,
        id_articolo=id_articolo
    )


@app.route("/movimenti_magazzino")
def movimenti_magazzino():
    conn = get_db_connection()
    c = conn.cursor()

    q = request.args.get("q", "")
    tipo = request.args.get("tipo", "")

    query = """
        SELECT 
            m.id,
            a.codice,
            a.descrizione,
            m.tipo_movimento,
            m.quantita,
            m.data_movimento
        FROM movimenti_magazzino m
        LEFT JOIN articoli a ON m.id_articolo = a.id
        WHERE 1=1
    """

    params = []

    if q:
        query += " AND (a.codice ILIKE %s OR a.descrizione ILIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    if tipo:
        query += " AND m.tipo_movimento = %s"
        params.append(tipo)

    query += " ORDER BY m.data_movimento DESC"

    c.execute(query, params)
    movimenti = c.fetchall()
    conn.close()

    return render_template("movimenti_magazzino.html", movimenti=movimenti)




@app.route("/aggiorna_costo_orario", methods=["POST"])
#@login_required
def aggiorna_costo_orario():
    nuovo_costo = request.form.get("nuovo_costo_orario")

    if nuovo_costo:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute(
            "UPDATE operatori SET costo_orario = %s",
            (nuovo_costo,)
        )

        conn.commit()
        conn.close()

    return redirect(url_for("operatori"))

@app.route("/stampa_magazzino")
#@login_required
def stampa_magazzino():
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import tempfile

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT codice, descrizione, unita, quantita, scorta_minima, fornitore, costo_netto FROM articoli ORDER BY descrizione")
    articoli = cur.fetchall()
    conn.close()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filename = tmp.name

    pdf = SimpleDocTemplate(filename, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("📦 INVENTARIO MAGAZZINO", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Codice", "Descrizione", "Unità", "Q.tà", "Scorta Min.", "Fornitore", "Prezzo Netto €", "Valore Totale €"]]

    totale_generale = 0

    for art in articoli:
        codice, descrizione, unita, qta, scorta_minima, fornitore, prezzo = art
        qta = qta or 0
        prezzo = prezzo or 0
        valore = qta * prezzo
        totale_generale += valore

        data.append([
            codice,
            descrizione,
            unita,
            f"{qta:.2f}",
            f"{scorta_minima:.2f}",
            fornitore,
            f"{prezzo:.2f}",
            f"{valore:.2f}"
        ])

    data.append(["", "", "", "", "", "", "Totale", f"{totale_generale:.2f} €"])

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (3,1), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (-2,-1), (-1,-1), colors.beige),
    ]))

    elements.append(t)
    pdf.build(elements)

    from flask import send_file
    return send_file(filename, as_attachment=False, mimetype="application/pdf")
# ROOT
# =========================================================
@app.route("/")
def root():
    return redirect(url_for("login"))


# ===================== IMPORTA DATABASE (DISATTIVATA PER SICUREZZA) =====================
@app.route("/importa_db")
@login_required
def importa_db():
    return "IMPORT DATABASE DISABILITATO PER SICUREZZA – Postgres attivo"


# =========================================================
# AVVIO APP SICURO
# =========================================================
if __name__ == "__main__":
    app.run(debug=False)