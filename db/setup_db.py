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
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            rut TEXT NOT NULL UNIQUE,
            contrasena_hash TEXT NOT NULL,
            rol INTEGER NOT NULL CHECK(rol IN (1, 2)) -- 1: admin/supervisor, 2: usuario
        )
    ''')

    # Tabla Proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            contacto TEXT,
            estado INTEGER NOT NULL CHECK(estado IN (1, 2)) DEFAULT 1 -- 1 activo, 2 inactivo
        )
    ''')

    # Tabla Clasificación / Trazabilidad
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clasificaciones (
            id_clasificacion INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL,
            fecha TEXT NOT NULL, 
            total_nueces INTEGER NOT NULL,  
            FOREIGN KEY(proveedor_id) REFERENCES proveedores(id_proveedor)
        )
    ''')

        # Tabla de Métricas para conexión con TensorFlow
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detalle_clasificaciones (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            clasificacion_id INTEGER NOT NULL,
            clase TEXT NOT NULL CHECK(clase IN ('A', 'B', 'C', 'D')),   
            color TEXT,     
            forma TEXT,     
            tamano REAL,    
            FOREIGN KEY(clasificacion_id) REFERENCES clasificaciones(id_clasificacion)
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historial_metricas (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,  
            clasificacion_id INTEGER NOT NULL,
            proveedor_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            total_nueces INTEGER NOT NULL,
            cantidad_A INTEGER DEFAULT 0,
            cantidad_B INTEGER DEFAULT 0,
            cantidad_C INTEGER DEFAULT 0,
            cantidad_D INTEGER DEFAULT 0,
            promedio_tamaño REAL,
            distribucion_color TEXT,
            FOREIGN KEY(clasificacion_id) REFERENCES clasificaciones(id_clasificacion),
            FOREIGN KEY(proveedor_id) REFERENCES proveedores(id_proveedor)                                  
        )
    ''')

    conn.commit()
    conn.close()

    
    insertar_admin()
    insertar_usuario()


#Funciones para insertar el usuario y el admin, la contraseña esta hasheada 
# Función para insertar el admin/supervisor
def insertar_admin():
    conn = conectar()
    cursor = conn.cursor()

    nombre = "admin"
    rut = "215163725"  # RUT con guión, más estándar
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusuarios WHERE nombre = ?", (nombre,))
    existe = cursor.fetchone()[0]

    if not existe:
        cursor.execute(
            "INSERT INTO superusuarios (nombre, rut, contrasena_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, rut, password_hash, 1)  # 1 = admin/supervisor
        )
        print("✅ Administrador insertado correctamente.")
    else:
        print("ℹ️ El administrador ya existe en la base de datos.")

    conn.commit()
    conn.close()


# Función para insertar un usuario normal
def insertar_usuario():
    conn = conectar()
    cursor = conn.cursor()

    nombre = "usuario"
    rut = "123456789"
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusuarios WHERE nombre = ?", (nombre,))
    existe = cursor.fetchone()[0]

    if not existe:
        cursor.execute(
            "INSERT INTO superusuarios (nombre, rut, contrasena_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, rut, password_hash, 2)  # 2 = usuario
        )
        print("✅ Usuario insertado correctamente.")
    else:
        print("ℹ️ El usuario ya existe en la base de datos.")

    conn.commit()
    conn.close()