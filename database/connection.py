import sqlite3
import os

def databaseConfig():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'ecommerce.db')

    print("DB PATH:", db_path)   # 👈 ADD THIS LINE

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn