
class ProveedorDTO: # Objeto de Transferencia de Datos (DTO) para representar la información de un proveedor.
    def __init__(self, id, nombre, rut, contacto):
        self.id = id
        self.nombre = nombre
        self.rut = rut
        self.contacto = contacto