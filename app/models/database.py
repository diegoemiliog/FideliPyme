"""
Módulo de conexión a Supabase.
Proporciona un cliente singleton para toda la aplicación.
"""
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY

# Cliente singleton de Supabase
_cliente_supabase: Client = None


def obtener_supabase() -> Client:
    """Obtiene la instancia del cliente de Supabase (singleton)."""
    global _cliente_supabase
    if _cliente_supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Faltan las variables SUPABASE_URL y/o SUPABASE_KEY. "
                "Revisa tu archivo .env"
            )
        _cliente_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _cliente_supabase
