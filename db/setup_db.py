import hashlib
import sqlite3 # Importa el módulo sqlite3 para trabajar con bases de datos SQLite.


def conectar():
    return sqlite3.connect("sistema_nueces.db")


def crear_tablas(): # Crea las tablas 'proveedores' y 'clasificaciones' en la base de datos si no existen.
    conn = conectar()
    cursor = conn.cursor()

        # Tabla SuperUsuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS superusuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            contrasena_hash TEXT NOT NULL,
            rol INTEGER NOT NULL CHECK(rol IN (1, 2)) -- 1: admin, 2: usuario
        )
    ''')

    # Tabla Proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            contacto TEXT,
            estado INTEGER NOT NULL CHECK(estado IN (1, 2)) DEFAULT 1 -- 1 activo, 2 inactivo
        )
    ''')

    # Tabla Clasificación / Trazabilidad
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clasificacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL,
            total REAL NOT NULL,
            fecha TEXT NOT NULL,
            clase TEXT NOT NULL,
            FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
        )
    ''')

        # Tabla de Métricas para conexión con TensorFlow
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metricas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clasificacion_id INTEGER NOT NULL,
            tamaño REAL,
            color TEXT,
            forma TEXT,
            peso REAL,
            FOREIGN KEY(clasificacion_id) REFERENCES clasificacion(id)
        )
    ''')
    conn.commit()
    conn.close()

    # 🔁 Insertar el admin por defecto DESPUÉS de crear la tabla
    insertar_admin_por_defecto()

def insertar_admin_por_defecto():
    conn = conectar()
    cursor = conn.cursor()

    nombre = "admintrador"
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusuarios WHERE nombre = ?", (nombre,))
    existe = cursor.fetchone()[0]

    if not existe:
        cursor.execute("INSERT INTO superusuarios (nombre, contrasena_hash, rol) VALUES (?, ?, ?)",
                       (nombre, password_hash, 1))  # 1 para admin
        print("✅ Administrador insertado correctamente.")
    else:
        print("ℹ️ El administrador ya existe en la base de datos.")

    conn.commit()
    conn.close()