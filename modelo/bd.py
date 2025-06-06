import sqlite3

def conectar():
    return sqlite3.connect("sistema_nueces.db")

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    # Tabla de proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            contacto TEXT
        )
    ''')

    # ✅ Agrega esta tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clasificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            clase TEXT,
            fecha TEXT,
            FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
        )
    ''')

    conn.commit()
    conn.close()