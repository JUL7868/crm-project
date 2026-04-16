# create_tables.py (or inside app.py at startup)

from db import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prospects (
        id SERIAL PRIMARY KEY,
        name TEXT,
        business TEXT,
        status TEXT,
        last_contact DATE,
        notes TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()