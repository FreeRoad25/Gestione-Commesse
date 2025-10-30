from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime, date

app = Flask(__name__)

DB_NAME = "commesse.db"


# 🔹 Crea il database se non esiste
def crea_database():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Tabella principale
        c.execute('''CREATE TABLE commesse (
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
                        data_consegna TEXT
                    )''')

        # Tabella operatori (se non esiste)
        c.execute('''CREATE TABLE IF NOT EXISTS operatori (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL
                    )''')

        # Tabella ore lavorate (se non esiste)
        c.execute('''CREATE TABLE IF NOT EXISTS ore_lavorate (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_operatore INTEGER,
                        id_commessa INTEGER,
                        ore REAL,
                        data_imputazione TEXT
                    )''')

        # ✅ Nuova tabella per commesse consegnate
        c.execute('''CREATE TABLE IF NOT EXISTS commesse_consegnate (
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
                        saldata TEXT CHECK(saldata IN ('Si','No'))
                    )''')
        conn.commit()
        conn.close()



# 🔹 Home Page
@app.route('/')
def home():
    return render_template('index.html')


# 🔹 Elenco commesse
@app.route('/lista_commesse')
def lista_commesse():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM commesse")
    commesse = c.fetchall()
    conn.close()
    return render_template('commesse.html', commesse=commesse)

# 🔹 Elenco Soffietti — mostra solo le commesse con tipo_intervento contenente "soffietto"
@app.route("/elenco_soffietti")
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

# 🔹 Aggiungi nuova commessa
@app.route("/aggiungi_commessa", methods=["GET", "POST"])
def aggiungi_commessa():
    if request.method == "POST":
        nome = request.form.get("nome")

        # 🔹 Tipo intervento (gestisce anche l'opzione "Altro")
        tipo_intervento = request.form.get("tipo_intervento", "").strip()
        altro_input = request.form.get("altro_input", "").strip()

        # Se l'utente ha scelto “Altro”, usa il valore personalizzato
        if tipo_intervento.lower() == "altro" and altro_input:
            tipo_intervento = altro_input
        elif tipo_intervento.lower() == "altro" and not altro_input:
            tipo_intervento = "Non specificato"

        data_conferma = datetime.today().strftime("%Y-%m-%d")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        ore_necessarie = request.form.get("ore_necessarie")
        marca = request.form.get("marca_veicolo")
        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_consegna = request.form.get("data_consegna")

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO commesse 
            (nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio, 
             ore_necessarie, marca_veicolo, modello_veicolo, dimensioni, data_consegna)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
              ore_necessarie, marca, modello, dimensioni, data_consegna))
        conn.commit()
        conn.close()

        return redirect(url_for("lista_commesse"))

    return render_template("aggiungi_commessa.html")


@app.route("/modifica_commessa/<int:id>", methods=["GET", "POST"])
def modifica_commessa(id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Recupera la commessa da modificare
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()

    if not commessa:
        conn.close()
        return "Commessa non trovata", 404

    if request.method == "POST":
        nome = request.form.get("nome")

        # 🔹 Tipo intervento (gestisce anche l'opzione "Altro")
        tipo_intervento = request.form.get("tipo_intervento", "").strip()
        altro_input = request.form.get("altro_input", "").strip()

        if tipo_intervento.lower() == "altro" and altro_input:
            tipo_intervento = altro_input
        elif tipo_intervento.lower() == "altro" and not altro_input:
            tipo_intervento = "Non specificato"

        data_conferma = request.form.get("data_conferma")
        data_arrivo_materiali = request.form.get("data_arrivo_materiali")
        data_inizio = request.form.get("data_inizio")
        ore_necessarie = request.form.get("ore_necessarie")
        marca = request.form.get("marca_veicolo")
        modello = request.form.get("modello_veicolo")
        dimensioni = request.form.get("dimensioni")
        data_consegna = request.form.get("data_consegna")

        # 🔹 Aggiorna nel database
        c.execute("""
            UPDATE commesse 
            SET nome=?, tipo_intervento=?, data_conferma=?, data_arrivo_materiali=?, data_inizio=?, 
                ore_necessarie=?, marca_veicolo=?, modello_veicolo=?, dimensioni=?, data_consegna=? 
            WHERE id=?
        """, (nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
              ore_necessarie, marca, modello, dimensioni, data_consegna, id))
        conn.commit()
        conn.close()

        # 🔹 Torna alla lista dopo la modifica
        return redirect(url_for("lista_commesse"))

    # 🔹 Se non è POST, mostra il form con i dati esistenti
    conn.close()
    return render_template("modifica_commessa.html", commessa=commessa)


# 🔹 Elimina commessa
@app.route('/elimina/<int:id>')
def elimina_commessa(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM commesse WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lista_commesse'))


# 🔹 Pagina operatori
@app.route('/operatori', methods=['GET'])
def operatori():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM operatori")
    operatori = c.fetchall()
    c.execute("SELECT id, nome FROM commesse")
    commesse = c.fetchall()
    conn.close()
    return render_template('operatori.html', operatori=operatori, commesse=commesse)


# 🔹 Registra ore lavorate
@app.route("/registra_ore", methods=["POST"])
def registra_ore():
    id_operatore = request.form["operatore"]
    id_commessa = request.form["commessa"]
    ore = float(request.form["ore"])
    data_imputazione = date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Registra le ore lavorate
    c.execute("""
        INSERT INTO ore_lavorate (id_operatore, id_commessa, ore, data_imputazione)
        VALUES (?, ?, ?, ?)
    """, (id_operatore, id_commessa, ore, data_imputazione))

    # Aggiorna ore eseguite e ore rimanenti
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


# 🔹 Aggiungi nuovo operatore
@app.route("/aggiungi_operatore", methods=["GET", "POST"])
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

# 🔹 Pagina di ricerca commessa per consegna
@app.route("/consegna", methods=["GET", "POST"])
def consegna_veicolo():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Recupera tutte le commesse ancora attive
    c.execute("SELECT id, nome, tipo_intervento FROM commesse ORDER BY id DESC")
    commesse = c.fetchall()

    if request.method == "POST":
        id_commessa = request.form.get("id_commessa")
        if id_commessa:
            conn.close()
            return redirect(url_for("conferma_consegna", id=id_commessa))

    conn.close()
    return render_template("consegna_veicolo.html", commesse=commesse)




# 🔹 Pagina di conferma consegna
from datetime import date

@app.route("/conferma_consegna/<int:id>", methods=["GET", "POST"])
def conferma_consegna(id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Recupera la commessa selezionata
    c.execute("SELECT * FROM commesse WHERE id = ?", (id,))
    commessa = c.fetchone()

    if request.method == "POST":
        saldata = request.form.get("saldata")
        data_consegna = date.today().isoformat()  # ✅ Data odierna come data consegna

        # ✅ Crea la tabella commesse_consegnate se non esiste
        c.execute("""
            CREATE TABLE IF NOT EXISTS commesse_consegnate AS
            SELECT * FROM commesse WHERE 1=0;
        """)

        # ✅ Aggiungi la colonna 'saldata' se non esiste
        try:
            c.execute("ALTER TABLE commesse_consegnate ADD COLUMN saldata TEXT DEFAULT 'No'")
        except sqlite3.OperationalError:
            pass  # Colonna già presente

        # ✅ Copia la commessa in "commesse_consegnate" con la data attuale
        c.execute("""
            INSERT INTO commesse_consegnate 
            (id, nome, tipo_intervento, data_conferma, data_arrivo_materiali, data_inizio,
             ore_necessarie, ore_eseguite, ore_rimanenti, marca_veicolo, modello_veicolo,
             dimensioni, data_consegna, saldata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            commessa["id"], commessa["nome"], commessa["tipo_intervento"], commessa["data_conferma"],
            commessa["data_arrivo_materiali"], commessa["data_inizio"], commessa["ore_necessarie"],
            commessa["ore_eseguite"], commessa["ore_rimanenti"], commessa["marca_veicolo"],
            commessa["modello_veicolo"], commessa["dimensioni"], data_consegna, saldata
        ))

        # ✅ Elimina la commessa dalla tabella principale
        c.execute("DELETE FROM commesse WHERE id = ?", (id,))

        conn.commit()
        conn.close()
        return redirect(url_for("archivio_consegnati"))

    conn.close()
    return render_template("conferma_consegna.html", commessa=commessa)
@app.route("/archivio_consegnati")
def archivio_consegnati():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Crea la tabella se non esiste
    c.execute("""
        CREATE TABLE IF NOT EXISTS commesse_consegnate (
            id INTEGER PRIMARY KEY,
            nome TEXT,
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
            saldata TEXT DEFAULT 'No'
        )
    """)

    # ✅ Ordina mettendo prima le non saldate, poi le saldate
    c.execute("""
        SELECT * FROM commesse_consegnate
        ORDER BY 
            CASE saldata 
                WHEN 'No' THEN 0 
                WHEN 'NO' THEN 0
                WHEN 'no' THEN 0
                ELSE 1 
            END,
            data_consegna DESC
    """)
    commesse = c.fetchall()

    conn.close()
    return render_template("archivio_consegnati.html", commesse=commesse)

# 🔹 Aggiorna stato "Saldata" di una commessa consegnata

@app.route("/aggiorna_saldato/<int:id>", methods=["POST"])
def aggiorna_saldato(id):
    # Legge e normalizza il valore dal form
    nuova_saldato = request.form.get("saldata", "").strip().lower()

    # Normalizzazione per sicurezza (accetta anche "si", "sì", "SI", ecc.)
    if nuova_saldato in ("si", "sì", "yes", "y"):
        nuova_saldato = "Si"
    else:
        nuova_saldato = "No"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE commesse_consegnate SET saldata = ? WHERE id = ?", (nuova_saldato, id))
    conn.commit()
    conn.close()

    print(f"✅ Commessa {id} aggiornata correttamente a: {nuova_saldato}")
    return redirect(url_for("archivio_consegnati"))
# 🔹 Avvio dell’app
if __name__ == '__main__':
    crea_database()
    app.run(debug=True)
