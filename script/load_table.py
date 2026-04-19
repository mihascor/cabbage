import sqlite3


DB_PATH = r"C:\cabbage\data\cabbagedb.db"


def load_open_interest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            name,
            private_long,
            private_shorts,
            legal_long,
            legal_shorts
        FROM open_interest_record
    """)
    rows = cursor.fetchall()

    columns = [description[0] for description in cursor.description]

    conn.close()

    return columns, rows