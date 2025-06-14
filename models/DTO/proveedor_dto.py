
 # Objeto de Transferencia de Datos (DTO) para representar la información de un proveedor.
class ProveedorDTO: 
    def __init__(self, id, nombre, rut, contacto, estado):
        self.id = id
        self.nombre = nombre
        self.rut = rut
        self.contacto = contacto
        self.estado = estado