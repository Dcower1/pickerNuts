import sqlite3 # Importa el módulo sqlite3 para trabajar con bases de datos SQLite.

def conectar(): # Establece y retorna una conexión a la base de datos "sistema_nueces.db".
    return sqlite3.connect("sistema_nueces.db")

def crear_tablas(): # Crea las tablas 'proveedores' y 'clasificaciones' en la base de datos si no existen.
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

    #  Tabla Trazabilidad
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