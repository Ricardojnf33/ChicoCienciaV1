import sqlite3
import os

db_path = "/home/r33/repos/ChicoCienciaV1/runs.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, stage, status FROM NodeRow ORDER BY rowid DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("Database not found.")
