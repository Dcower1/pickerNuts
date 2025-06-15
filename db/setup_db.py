import hashlib
import sqlite3 


def conectar():
    return sqlite3.connect("sistema_nueces.db")


def crear_tablas(): 
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
        CREATE TABLE IF NOT EXISTS clasificaciones (
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

    
    insertar_admin()
    insertar_usuario()


#Funciones para insertar el usuario y el admin, la contraseña esta hasheada 
def insertar_admin():
    conn = conectar()
    cursor = conn.cursor()

    nombre = "admin"
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

def insertar_usuario():
    conn = conectar()
    cursor = conn.cursor()

    nombre = "usuario"
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusuarios WHERE nombre = ?", (nombre,))
    existe = cursor.fetchone()[0]

    if not existe:
        cursor.execute("INSERT INTO superusuarios (nombre, contrasena_hash, rol) VALUES (?, ?, ?)",
                       (nombre, password_hash, 2))  # 2 para usuario
        print("✅ Usuario insertado correctamente.")
    else:
        print("ℹ️ El Usuario ya existe en la base de datos.")

    conn.commit()
    conn.close()