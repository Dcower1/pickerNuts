# models/usuario.py
class Usuario:
    def __init__(self, id_user, nombre, rol):
        self.id_user = id_user
        self.nombre = nombre
        self.rol = rol

    @property
    def es_admin(self):
        return self.rol == 1