import random
from models.DAO.clasificacion_dao import ClasificacionDAO

def simular_clasificacion(proveedor_id):
    clase = random.choice(["A", "B", "C"])
    ClasificacionDAO.insertar_datos_simulados_si_no_existen(proveedor_id, clase)
    print(f"Simulación: Clasificación '{clase}' insertada para proveedor {proveedor_id}")