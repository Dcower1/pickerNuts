from ..base_proveedor_view import BaseProveedorView

class ProveedorView(BaseProveedorView):
    def __init__(self, root, usuario_activo=None):
        super().__init__(root, "Panel de Proveedores", usuario_activo)