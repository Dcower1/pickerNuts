
 # Objeto de Transferencia de Datos (DTO) para representar la información de un proveedor.
class ProveedorDTO: 
    def __init__(self, id_proveedor, nombre, rut, contacto, estado):
        self.id_proveedor = id_proveedor
        self.nombre = nombre
        self.rut = rut
        self.contacto = contacto
        self.estado = estado