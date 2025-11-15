import sqlite3

conn = sqlite3.connect("commesse.db")
c = conn.cursor()

c.execute("PRAGMA table_info(commesse)")
for col in c.fetchall():
    print(col)

conn.close()
