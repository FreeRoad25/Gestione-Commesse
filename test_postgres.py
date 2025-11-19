import os
import psycopg2
from flask import Flask

app = Flask(_name_)

# ====== LETTURA VARIABILI DI AMBIENTE ======
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ====== STRINGA DI CONNESSIONE ======
CONN_STRING = (
    f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' "
    f"host='{DB_HOST}' port='{DB_PORT}' sslmode='require'"
)

@app.route("/test_pg")
def test_pg():
    try:
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor()

        # Creiamo una tabella di test se non esiste
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_connessione (
                id SERIAL PRIMARY KEY,
                messaggio TEXT
            );
        """)

        # Inseriamo una riga di test
        cur.execute("INSERT INTO test_connessione (messaggio) VALUES ('OK - connessione riuscita');")
        conn.commit()

        # Recuperiamo l'ultima riga
        cur.execute("SELECT messaggio FROM test_connessione ORDER BY id DESC LIMIT 1;")
        riga = cur.fetchone()

        cur.close()
        conn.close()

        return f"Connessione Postgres FUNZIONA: {riga[0]}"

    except Exception as e:
        return f"ERRORE connessione Postgres: {str(e)}"


if _name_ == "_main_":
    app.run()