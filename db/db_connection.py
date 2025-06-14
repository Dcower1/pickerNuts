import sqlite3

def obtener_conexion():
    return sqlite3.connect("sistema_nueces.db")
