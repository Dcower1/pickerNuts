import hashlib
import sqlite3


def connect():
    return sqlite3.connect("nuts_system.db")


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    # Table: Superusers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS superusers (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            rut TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role INTEGER NOT NULL CHECK(role IN (1, 2)) -- 1: admin/supervisor, 2: user
        )
    ''')

    # Table: Suppliers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            contact TEXT,
            created_by INTEGER NOT NULL,
            status INTEGER NOT NULL CHECK(status IN (1, 2)) DEFAULT 1 -- 1 active, 2 inactive
        )
    ''')

    # Table: Classifications / Traceability
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classifications (
            classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_nuts INTEGER NOT NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
        )
    ''')

    # Table: Classification Details (for TensorFlow metrics)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classification_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_id INTEGER NOT NULL,
            grade TEXT NOT NULL CHECK(grade IN ('A', 'B', 'C', 'D')),
            color TEXT,
            shape TEXT,
            size REAL,
            FOREIGN KEY(classification_id) REFERENCES classifications(classification_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS procesos_lote (
            proceso_id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor1_id INTEGER NOT NULL,
            proveedor2_id INTEGER NOT NULL,
            porcentaje1 REAL NOT NULL,
            porcentaje2 REAL NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY(proveedor1_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY(proveedor2_id) REFERENCES suppliers(supplier_id)
        )
    ''')


    # Table: Metrics History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_nuts INTEGER NOT NULL,
            count_A INTEGER DEFAULT 0,
            count_B INTEGER DEFAULT 0,
            count_C INTEGER DEFAULT 0,
            count_D INTEGER DEFAULT 0,
            avg_size REAL,
            color_distribution TEXT,
            FOREIGN KEY(classification_id) REFERENCES classifications(classification_id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
        )
    ''')

    conn.commit()
    conn.close()

    insertar_admin()
    insertar_user()


# --- Insert default users (admin & standard user) ---

def insertar_admin():
    conn = connect()
    cursor = conn.cursor()

    username = "admin"
    rut = "215163725"
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusers WHERE username = ?", (username,))
    exists = cursor.fetchone()[0]

    if not exists:
        cursor.execute(
            "INSERT INTO superusers (username, rut, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, rut, password_hash, 1)  # 1 = admin/supervisor
        )
        print("✅ Admin inserted successfully.")
    else:
        print("ℹ️ Admin already exists in the database.")

    conn.commit()
    conn.close()


def insertar_user():
    conn = connect()
    cursor = conn.cursor()

    username = "user"
    rut = "123456789"
    password = "qwerty"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT COUNT(*) FROM superusers WHERE username = ?", (username,))
    exists = cursor.fetchone()[0]

    if not exists:
        cursor.execute(
            "INSERT INTO superusers (username, rut, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, rut, password_hash, 2)  # 2 = regular user
        )
        print("✅ User inserted successfully.")
    else:
        print("ℹ️ User already exists in the database.")

    conn.commit()
    conn.close()
