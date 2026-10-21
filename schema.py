import sqlite3
import os

with sqlite3.connect('organic_trace.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    with open('schema.txt', 'w', encoding='utf-8') as f:
        for t in tables:
            f.write(f'Table: {t[0]}\n{t[1]}\n' + '-'*50 + '\n')
