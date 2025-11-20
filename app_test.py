import os
import psycopg2
import sqlite3

print("=== TEST SQLITE PATH ===")
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = "commesse.db"
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)
    print("BASE_DIR:", BASE_DIR)
    print("DB_PATH:", DB_PATH)

    conn_sqlite = sqlite3.connect(DB_PATH)
    conn_sqlite.close()
    print("SQLite OK ✓")
except Exception as e:
    print("ERRORE SQLITE:", e)


print("\n=== TEST POSTGRES ===")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME_PG = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("Variabili:")
print(" DB_HOST:", DB_HOST)
print(" DB_PORT:", DB_PORT)
print(" DB_NAME:", DB_NAME_PG)
print(" DB_USER:", DB_USER)
print(" DB_PASSWORD:", "(nascosta)")

try:
    conn_pg = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME_PG,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn_pg.close()
    print("Postgres OK ✓")
except Exception as e:
    print("ERRORE POSTGRES:", e)

# === TEST POSTGRES ===
print("\n=== TEST POSTGRES ===")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME_PG = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("Variabili:")
print(" DB_HOST:", DB_HOST)
print(" DB_PORT:", DB_PORT)
print(" DB_NAME:", DB_NAME_PG)
print(" DB_USER:", DB_USER)
print(" DB_PASSWORD:", "(nascosta)")

try:
    conn_pg = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME_PG,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn_pg.close()
    print("Postgres OK ✓")
except Exception as e:
    print("ERRORE POSTGRES:", e)