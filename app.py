from flask import send_file
from reportlab.lib.styles import ParagraphStyle
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
# === Database path unico e corretto ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "commesse.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
from datetime import datetime, date
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
app = Flask(__name__)
# BYPASS LOGIN
from flask import session
@app.before_request
def bypass_login():
    session["ruolo"] = "amministratore"
# Inizializzazione LoginManager
login_manager = LoginManager()
# Login automatico di sicurezza
@login_manager.request_loader
def load_user_from_request(request):
    class FakeUser(UserMixin):
        id = 1
        ruolo = "amministratore"
    session["ruolo"] = "amministratore"
    return FakeUser()
login_manager.init_app(app)
login_manager.login_view = "login"  # nome della route di login
app.secret_key = os.environ.get("SECRET_KEY", "fallback123")
login_manager.session_protection = "strong"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 ora
# ===================== CONTROLLO RUOLO AMMINISTRATORE =====================


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
# ========================================================================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "commesse.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



# ====== CREAZIONE AUTOMATICA TABELLA UTENTI SU RENDER ======
def init_db_online():    
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                ruolo TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("Tabella 'utenti' verificata/creata.")
    except Exception as e:
        print("Errore creazione tabella utenti:", e)

init_db_online()
import crea_admin_online
crea_admin_online.crea_admin_se_manca()

# Creazione tabella tipi_intervento se non esiste
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS tipi_intervento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
)
""")

# Inserimento valori di default se la tabella è vuota
c.execute("SELECT COUNT(*) FROM tipi_intervento")
count = c.fetchone()[0]

if count == 0:
    c.executemany("INSERT INTO tipi_intervento (nome) VALUES (?)", [
        ("Montaggio Riscaldatore",),
        ("Tetto a Soffietto",),
        ("Coibentazione",),
        ("Allestimento Interno",),
        ("Impianto Elettrico",),
        ("Impianto Acqua",),
        ("Installazione Accessori",),
        ("Tagliando Camper",),
        ("Altro",)
    ])
    print("Tabella 'tipi_intervento' creata e popolata.")

conn.commit()
conn.close()
# ============================================================

# Cartella per i file allegati alle commesse
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx", "xls", "xlsx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================
# FUNZIONE DI CONNESSIONE AL DATABASE
# =========================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM utenti WHERE username = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        user = User(row["username"], row["ruolo"])
        return user
    return None
# =========================================================
# FUNZIONI DI SUPPORTO
# =========================================================
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================================================
# CREAZIONE DATABASE E TABELLE
# =========================================================
def crea_database():
    conn = sqlite3.connect(DB_PATH)
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
    # tabella articoli di magazzino
    c.execute("""
        CREATE TABLE IF NOT EXISTS articoli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice TEXT UNIQUE NOT NULL,
            descrizione TEXT NOT NULL,
            unita TEXT,
            quantita REAL DEFAULT 0,
            codice_barre TEXT,
            fornitore TEXT,
            scorta_minima REAL
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
    session["ruolo"] = "amministratore"
    return redirect(url_for("home"))
   


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
#@login_required
def cambia_password():
    if request.method == "POST":
        old_pwd = request.form.get("old_password", "")
        new_pwd = request.form.get("new_password", "")
        conf_pwd = request.form.get("confirm_password", "")

        if not new_pwd or new_pwd != conf_pwd:
            return render_template("cambia_password.html", error="Le nuove password non coincidono")

        username = session.get("username")
        conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()
    conn.close()
    return render_template("commesse.html", commesse=commesse)


@app.route("/elenco_soffietti")
#@login_required
def elenco_soffietti():
    conn = sqlite3.connect(DB_PATH)
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


from werkzeug.utils import secure_filename
import os
import sqlite3
from flask import request, redirect, url_for, render_template
from flask_login import login_required

# Percorso assoluto al database
DB_PATH = r"commesse.db"

@app.route("/aggiungi_commessa", methods=["GET", "POST"])
def aggiungi_commessa():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form.get("nome")
        tipo_intervento = request.form.get("tipo_intervento")
        nuovo_intervento = request.form.get("nuovo_intervento")
        marca_veicolo = request.form.get("marca_veicolo")
        modello_veicolo = request.form.get("modello_veicolo")
        data_conferma = request.form.get("data_conferma")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        ore_necessarie = request.form.get("ore_necessarie") or 0
        data_inizio_prevista = request.form.get("data_inizio_prevista")
        note = request.form.get("note")

        if tipo_intervento == "altro" and nuovo_intervento:
            tipo_intervento = nuovo_intervento

        c.execute("""
            INSERT INTO commesse 
            (nome, tipo_intervento, marca_veicolo, modello_veicolo, data_conferma,
             data_arrivo_materiali, ore_necessarie, data_inizio_prevista, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, tipo_intervento, marca_veicolo, modello_veicolo, data_conferma,
            data_arrivo_materiali, ore_necessarie, data_inizio_prevista, note
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    # GET → preparo la pagina
    c.execute("SELECT DISTINCT tipo_intervento FROM commesse")
    tipi_intervento = c.fetchall()

    c.execute("SELECT DISTINCT marca_veicolo FROM commesse")
    marche = c.fetchall()

    conn.close()

    return render_template(
        "aggiungi_commessa.html",
        tipi_intervento=tipi_intervento,
        marche=marche
    )


@app.route("/modifica_commessa/<int:id>", methods=["GET", "POST"])
#@login_required
def modifica_commessa(id):
    conn = sqlite3.connect(DB_PATH)
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

       # 🔹 Marca scelta o nuova marca
        marca_sel = request.form.get("marca_veicolo")
        marca = request.form.get("nuova_marca") if marca_sel == "nuova" else marca_sel

        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_consegna = request.form.get("data_consegna")
        note_importanti = request.form.get("note_importanti", "").strip()

        # 🔹 Gestione nuovo tipo intervento
        if tipo_intervento.lower() == "altro" and altro_input:
            c.execute("INSERT OR IGNORE INTO tipi_intervento (nome) VALUES (?)", (altro_input,))
            conn.commit()
            tipo_intervento = altro_input

        # 🔹 Aggiorna la commessa
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

        # 🔹 Gestione nuovi file allegati
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

    # 🔹 GET: Caricamento dati per tendine
    c.execute("SELECT DISTINCT tipo_intervento FROM commesse WHERE tipo_intervento IS NOT NULL AND tipo_intervento != ''")
    tipi_intervento = [row["tipo_intervento"] for row in c.fetchall()]

    # 🔹 Marche derivate direttamente dalle commesse (nessuna tabella aggiuntiva)
    c.execute("SELECT DISTINCT marca_veicolo FROM commesse WHERE marca_veicolo IS NOT NULL AND marca_veicolo != '' ORDER BY marca_veicolo ASC")
    marche = [row["marca_veicolo"] for row in c.fetchall()]

    c.execute("SELECT DISTINCT modello_veicolo FROM commesse WHERE modello_veicolo IS NOT NULL AND modello_veicolo != ''")
    modelli = [row["modello_veicolo"] for row in c.fetchall()]

    c.execute("SELECT * FROM commessa_files WHERE id_commessa = ? ORDER BY upload_date DESC", (id,))
    files = c.fetchall()
    conn.close()

    return render_template("modifica_commessa.html",
                           id_commessa=id,
                           commessa=commessa,
                           files=files,
                           tipi_intervento=tipi_intervento,
                           marche=marche,
                           modelli=modelli)
@app.route("/stampa_commessa/<int:id>")
#@login_required
def stampa_commessa(id):
    import os
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    import sqlite3

    # --- Connessione DB ---
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1) CERCA NELLA TABELLA COMMESSE
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()

    # 2) SE NON TROVA → CERCA NELLA TABELLA COMMESSE_CONSEGNATE
    if not commessa:
        c.execute("SELECT * FROM commesse_consegnate WHERE id = ?", (id,))
        commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata"

    # MATERIALI
    c.execute("""
        SELECT a.codice, a.descrizione, cm.quantita, a.costo_netto
        FROM commesse_materiali cm
        JOIN articoli a ON cm.id_articolo = a.id
        WHERE cm.id_commessa = ?
    """, (id,))
    materiali = c.fetchall()

    # ORE LAVORATE
    c.execute("""
        SELECT o.nome AS operatore, ol.ore, COALESCE(o.costo_orario, 0) AS costo_orario
        FROM ore_lavorate ol
        LEFT JOIN operatori o ON o.id = ol.id_operatore
        WHERE ol.id_commessa = ?
    """, (id,))
    ore_lavorate = c.fetchall()

    conn.close()

    # --- GENERAZIONE PDF ---
    filename = f"C:\\Users\\fabrizio\\Documents\\GestioneCommesse\\commessa_{id}_tabellare.pdf"
    pdf = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # INTESTAZIONE
    elements.append(Paragraph(f"<b>🛠 Commessa #{id} – {commessa['nome']}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # TAB DATI COMMESSA
    tabella_commessa = [
        ["Tipo Intervento", commessa["tipo_intervento"]],
        ["Marca Veicolo", f"{commessa['marca_veicolo']} {commessa['modello_veicolo']}"],
        ["Data Conferma", commessa["data_conferma"] or "---"],
        ["Data Arrivo Materiali", commessa["data_arrivo_materiali"] or "---"],
        ["Data Inizio", commessa["data_inizio"] or "---"],
        ["Data Consegna", commessa["data_consegna"] or "---"],
        ["Ore Necessarie", commessa["ore_necessarie"] or 0],
        ["Ore Eseguite", commessa["ore_eseguite"] or 0]
    ]

    t_info = Table(tabella_commessa, colWidths=[150, 350])
    t_info.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))

    # MATERIALI
    if materiali:
        data_materiali = [["Codice", "Descrizione", "Q.tà", "Costo", "Totale €"]]
        for m in materiali:
            tot = (m["quantita"] or 0) * (m["costo_netto"] or 0)
            data_materiali.append([
                m["codice"], m["descrizione"], m["quantita"],
                f"{m['costo_netto']:.2f}", f"{tot:.2f}"
            ])

        t_mat = Table(data_materiali, colWidths=[70, 230, 60, 80, 80])
        t_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ]))

        elements.append(Paragraph("📦 Materiali Utilizzati", styles["Heading2"]))
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
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ]))

        elements.append(Paragraph("👷 Ore Lavorate", styles["Heading2"]))
        elements.append(t_ore)

    # CREA PDF
    pdf.build(elements)

    # APRI PDF
    os.startfile(filename)

    # CHIUDI LA FINESTRA DEL BROWSER
    return "<script>window.close();</script>"   
@app.route("/stampa_commessa_archiviata/<int:id>")
#@login_required
def stampa_commessa_archiviata(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM commesse_consegnate WHERE id = ?", (id,))
    com = c.fetchone()
    conn.close()

    if not com:
        return "Commessa archiviata non trovata"

    return render_template("stampa_commessa.html", commessa=com)

@app.route("/elimina/<int:id>")
#@login_required
def elimina_commessa(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM commesse WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("lista_commesse"))


# =========================================================
# FILE ALLEGATI COMMESSE
# =========================================================
@app.route("/commessa/<int:id>/files")
#@login_required
def commessa_files_view(id):
    conn = sqlite3.connect(DB_PATH)
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
#@login_required
def download_commessa_file(file_id):
    conn = sqlite3.connect(DB_PATH)
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
def operatori():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Prende la lista operatori
    c.execute("SELECT * FROM operatori ORDER BY nome ASC")
    operatori = c.fetchall()

    # Prende le commesse
    c.execute("SELECT id, nome FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    conn.close()

    return render_template(
        "operatori.html",
        operatori=operatori,
        commesse=commesse
    )


@app.route("/aggiungi_operatore", methods=["GET", "POST"])
#@login_required
def aggiungi_operatore():
    if request.method == "POST":
        nome = request.form.get("nome")
        if nome:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO operatori (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
        return redirect(url_for("operatori"))

    return render_template("aggiungi_operatore.html")


@app.route("/registrazione_ore", methods=["POST"])
#@login_required
def registrazione_ore():
    id_operatore = request.form.get("id_operatore")
    id_commessa = request.form.get("id_commessa")
    ore = float(request.form.get("ore") or 0)
    data_imputazione = request.form.get("data_imputazione") or date.today()

    # Connessione al database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ✅ 1. Inserisci la riga in "ore_lavorate"
    c.execute("""
        INSERT INTO ore_lavorate (id_operatore, id_commessa, ore, data_imputazione)
        VALUES (?, ?, ?, ?)
    """, (id_operatore, id_commessa, ore, data_imputazione))

    # ✅ 2. Aggiorna il totale delle ore nella tabella commesse
    c.execute("""
        UPDATE commesse
        SET ore_eseguite = COALESCE(ore_eseguite, 0) + ?
        WHERE id = ?
    """, (ore, id_commessa))

    conn.commit()
    conn.close()

    return redirect(url_for("operatori"))


# =========================================================
# CONSEGNA VEICOLO / ARCHIVIO
# =========================================================
@app.route("/consegna", methods=["GET", "POST"])
#@login_required
def consegna_veicolo():
    conn = sqlite3.connect(DB_PATH)
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
#@login_required
def conferma_consegna(id):
    conn = sqlite3.connect(DB_PATH)
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
#@login_required
def archivio_consegnati():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
        SELECT
            id,
           nome,
           tipo_intervento,
           data_conferma,
           data_arrivo_materiali,
           data_consegna,
           ore_necessarie AS ore_previste,
           ore_eseguite AS ore_lavorate,
           saldata
         FROM commesse_consegnate
         ORDER BY
            CASE WHEN saldata IN ('No', 'NO', 'no') THEN 0 ELSE 1 END,
          id DESC
    """)

        commesse = c.fetchall()
        conn.close()

        return render_template("archivio_consegnati.html", commesse=commesse)

    except Exception as e:
        print("ERRORE ARCHIVIO CONSEGNATI:", e)
        return "Errore nell'archivio consegnati", 500


@app.route("/toggle_saldata/<int:id>", methods=["POST"])
#@login_required
def toggle_saldata(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Leggo il valore attuale
        c.execute("SELECT saldata FROM commesse_consegnate WHERE id = ?", (id,))
        row = c.fetchone()

        if not row:
            conn.close()
            print(f"ERRORE TOGGLE SALDATA: Nessuna commessa trovata con id {id}")
            return "Errore: commessa non trovata", 404

        attuale = row["saldata"]

        # Calcolo il nuovo valore
        nuovo = "Si" if attuale.lower() in ("no", "n", "0") else "No"

        # Aggiorno
        c.execute("UPDATE commesse_consegnate SET saldata = ? WHERE id = ?", (nuovo, id))
        conn.commit()
        conn.close()

        return redirect(url_for('archivio_consegnati'))

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
#@login_required
def modifica_articolo(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        descrizione = request.form.get("descrizione")
        unita = request.form.get("unita")
        quantita = float(request.form.get("quantita") or 0)
        scorta_minima = float(request.form.get("scorta_minima") or 0)
        fornitore = request.form.get("fornitore")
        codice_barre = request.form.get("codice_barre")
        costo_netto = float(request.form.get("costo_netto") or 0)

        # --- Controlla il prezzo precedente ---
        c.execute("SELECT costo_netto FROM articoli WHERE id = ?", (id,))
        row = c.fetchone()
        prezzo_vecchio = row["costo_netto"] if row else 0

        # --- Aggiorna la data solo se cambia il prezzo ---
        if costo_netto != prezzo_vecchio:
            c.execute("""
                UPDATE articoli
                SET descrizione=?, unita=?, quantita=?, scorta_minima=?, 
                    fornitore=?, codice_barre=?, costo_netto=?, data_modifica=date('now')
                WHERE id=?
            """, (descrizione, unita, quantita, scorta_minima, fornitore, codice_barre, costo_netto, id))
        else:
            c.execute("""
                UPDATE articoli
                SET descrizione=?, unita=?, quantita=?, scorta_minima=?, 
                    fornitore=?, codice_barre=?, costo_netto=?
                WHERE id=?
            """, (descrizione, unita, quantita, scorta_minima, fornitore, codice_barre, costo_netto, id))

        conn.commit()
        conn.close()
        return redirect(url_for("magazzino_articoli"))

    # --- Se è una richiesta GET: carica i dati ---
    c.execute("SELECT * FROM articoli WHERE id = ?", (id,))
    articolo = c.fetchone()
    conn.close()
    return render_template("modifica_articolo.html", articolo=articolo)

@app.route('/pagina_aggiungi_articolo')
#@login_required
def pagina_aggiungi_articolo():
    return render_template('pagina_aggiungi_articolo.html')



@app.route("/magazzino_articoli")
#@login_required
def magazzino_articoli():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ATTENZIONE: leggiamo dalla tabella "articoli"
    c.execute("SELECT * FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    conn.close()
    return render_template("magazzino_articoli.html", articoli=articoli)

@app.route("/magazzino_sottoscorta")
#@login_required
def magazzino_sottoscorta():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT codice, descrizione, unita, quantita, scorta_minima, fornitore
            FROM articoli
            WHERE IFNULL(CAST(quantita AS REAL), 0) < IFNULL(CAST(scorta_minima AS REAL), 0)
            ORDER BY descrizione ASC
        """)

        articoli_sottoscorta = c.fetchall()
        conn.close()

        return render_template("magazzino_sottoscorta.html", articoli=articoli_sottoscorta)

    except Exception as e:
        return f"Errore nel caricamento sottoscorta: {e}"




# ===============================
# 🗑 ELIMINA ARTICOLO
# ===============================
@app.route('/elimina_articolo/<codice>', methods=['POST'])
def elimina_articolo(codice):
    conn = get_db_connection()
    c = conn.cursor()

    # 🔹 Elimina l'articolo dal magazzino
    c.execute("DELETE FROM magazzino WHERE codice = ?", (codice,))
    conn.commit()
    conn.close()

    flash("Articolo eliminato con successo!", "success")
    return redirect(url_for('magazzino_articoli'))

@app.route("/aggiungi_articolo", methods=["GET", "POST"])
#@login_required
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

        # numerici sicuri
        try:
            quantita = float(quantita) if quantita else 0.0
            scorta_minima = float(scorta_minima) if scorta_minima else 0.0
            costo_netto = float(costo_netto) if costo_netto else 0.0
        except ValueError:
            quantita = 0.0
            scorta_minima = 0.0
            costo_netto = 0.0

        # nuova colonna
        data_modifica = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                INSERT INTO articoli
                    (codice, descrizione, unita, quantita, codice_barre, fornitore, scorta_minima, costo_netto, data_modifica)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (codice, descrizione, unita, quantita, codice_barre, fornitore, scorta_minima, costo_netto, data_modifica))

            conn.commit()
            conn.close()
            return redirect(url_for("magazzino_articoli"))

        except sqlite3.IntegrityError:
            return "Errore: codice articolo già esistente."
        except Exception as e:
            print(f"Errore salvataggio articolo: {e}")
            return "Errore durante il salvataggio dell'articolo."
    else:
        # se GET, mostra la pagina con il form
        return render_template("pagina_aggiungi_articolo.html")

@app.route("/scarico_magazzino", methods=["GET", "POST"])
#@login_required
def scarico_magazzino():
    # ID articolo selezionato dalla pagina principale
    id_articolo = request.args.get("id_articolo")
    print("🔴 SCARICO – ID articolo selezionato:", id_articolo)

    # Connessione al database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Elenco articoli per la tendina
    c.execute("SELECT * FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    # Elenco commesse per la selezione
    c.execute("SELECT id, nome FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    # Se il form viene inviato
    if request.method == "POST":
        id_articolo_form = request.form.get("id_articolo")
        id_commessa = request.form.get("id_commessa") or None
        quantita = float(request.form.get("quantita") or 0)
        note = request.form.get("note")

        # Aggiorna la quantità nel magazzino (scarico)
        c.execute("""
            UPDATE articoli
            SET quantita = IFNULL(quantita, 0) - ?
            WHERE codice = (
                SELECT codice FROM articoli WHERE id = ?
            )
        """, (quantita, id_articolo_form))

        # Registra il movimento (con commessa)
        c.execute("""
            INSERT INTO movimenti_magazzino (id_articolo, tipo_movimento, quantita, note, id_commessa)
            VALUES (?, ?, ?, ?, ?)
        """, (id_articolo_form, 'Scarico', quantita, note, id_commessa))

        conn.commit()
        conn.close()
        return redirect(url_for("magazzino_articoli"))

    # Se GET → mostra la pagina
    conn.close()
    return render_template("scarico_magazzino.html", articoli=articoli, commesse=commesse, id_articolo=id_articolo)


@app.route("/carico_magazzino", methods=["GET", "POST"])
#@login_required
def carico_magazzino():
    # ID articolo selezionato dalla pagina magazzino
    id_articolo = request.args.get("id_articolo")
    print("🟢 CARICO – ID articolo selezionato:", id_articolo)

    # Connessione al database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Elenco articoli per il menu a tendina (usato per trovare quello selezionato)
    c.execute("SELECT * FROM articoli ORDER BY descrizione ASC")
    articoli = c.fetchall()

    # Trova l'articolo selezionato
    articolo = None
    for a in articoli:
        if str(a["id"]) == str(id_articolo):
            articolo = a
            break

    # Se il form è stato inviato
    if request.method == "POST":
        id_articolo_form = request.form.get("id_articolo")
        quantita = float(request.form.get("quantita") or 0)
        note = request.form.get("note")

        # ✅ Aggiorna la quantità nel magazzino in base al codice articolo
        c.execute("""
            UPDATE articoli
            SET quantita = IFNULL(quantita, 0) + ?
            WHERE codice = (
                SELECT codice FROM articoli WHERE id = ?
            )
        """, (quantita, id_articolo_form))

        # ✅ Registra il movimento nel registro
        c.execute("""
            INSERT INTO movimenti_magazzino (id_articolo, tipo_movimento, quantita, note)
            VALUES (?, ?, ?, ?)
        """, (id_articolo_form, 'Carico', quantita, note))

        conn.commit()
        conn.close()
        return redirect(url_for("magazzino_articoli"))

    # Se GET → mostra la pagina
    conn.close()
    return render_template("carico_magazzino.html", articolo=articolo, articoli=articoli, id_articolo=id_articolo)


@app.route("/movimenti_magazzino")
def movimenti_magazzino():
    conn = get_db_connection()
    cursor = conn.cursor()

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
        query += " AND (a.codice LIKE ? OR a.descrizione LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])

    if tipo:
        query += " AND m.tipo_movimento = ?"
        params.append(tipo)

    query += " ORDER BY m.data_movimento DESC"

    cursor.execute(query, params)
    movimenti = cursor.fetchall()
    conn.close()

    return render_template("movimenti_magazzino.html", movimenti=movimenti)


@app.route("/aggiungi_operatore", methods=["GET", "POST"])
#@login_required
def pagina_aggiungi_operatore():
    if request.method == "POST":
        nome = request.form.get("nome")
        costo_orario = float(request.form.get("costo_orario") or 0)
        conn = sqlite3.connect("commesse.db")
        c = conn.cursor()
        c.execute("INSERT INTO operatori (nome, costo_orario) VALUES (?, ?)", (nome, costo_orario))
        conn.commit()
        conn.close()
        return redirect(url_for("operatori"))
    return render_template("aggiungi_operatore.html")

@app.route("/aggiorna_costo_orario", methods=["POST"])
#@login_required
def aggiorna_costo_orario():
    nuovo_costo = request.form.get("nuovo_costo_orario")
    if nuovo_costo:
        conn = sqlite3.connect(PATH_DB)
        c = conn.cursor()
        c.execute("UPDATE operatori SET costo_orario = ?", (nuovo_costo,))
        conn.commit()
        conn.close()
    return redirect(url_for("operatori"))

@app.route("/stampa_magazzino")
#@login_required
def stampa_magazzino():
    from reportlab.lib.pagesizes import landscape,A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import tempfile

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM articoli ORDER BY descrizione")
    articoli = c.fetchall()
    conn.close()

    # Percorso temporaneo PDF
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filename = tmp.name

    pdf = SimpleDocTemplate(filename, pagesize= landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("📦 INVENTARIO MAGAZZINO", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Tabella dati
    data = [["Codice", "Descrizione", "Unità", "Q.tà", "Scorta Min.", "Fornitore", "Prezzo Netto €", "Valore Totale €"]]

    totale_generale = 0
    for art in articoli:
        prezzo = art["prezzo"] or 0
        qta = art["quantita"] or 0
        valore = qta * prezzo
        totale_generale += valore

        data.append([
            art["codice"],
            art["descrizione"],
            art["unita"],
            f"{qta:.2f}",
            f"{art['scorta_minima']:.2f}",
            art["fornitore"],
            f"{prezzo:.2f}",
            f"{valore:.2f}"
        ])

    # Riga totale
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


# =========================================================
# AVVIO APP
# =========================================================
if __name__ == "__main__":
    crea_database()
    app.run(debug=True)
