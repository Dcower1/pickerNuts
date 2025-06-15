# models/usuario.py
class Usuario:
    def __init__(self, id, nombre, rol):
        self.id = id
        self.nombre = nombre
        self.rol = rol

    @property
    def es_admin(self):
        return self.rol == 1