import sqlite3

def conectar():
    return sqlite3.connect("sistema_nueces.db")

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            contacto TEXT
        )
    ''')
    conn.commit()
    conn.close()
