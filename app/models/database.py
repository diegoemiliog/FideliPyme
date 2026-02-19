"""
Módulo de conexión a Supabase via REST API.
Usa requests en lugar de la librería supabase-py para compatibilidad con Python 3.14.
Proporciona un cliente singleton con interfaz fluida compatible.
"""
import requests as _requests
from app.config import SUPABASE_URL, SUPABASE_KEY


class _Response:
    """Respuesta que imita la interfaz de supabase-py."""
    __slots__ = ('data',)

    def __init__(self, data: list):
        self.data = data


class _QueryBuilder:
    """Constructor de queries con interfaz fluida compatible con supabase-py."""

    def __init__(self, base_url: str, headers: dict, table_name: str):
        self._url = f"{base_url}/rest/v1/{table_name}"
        self._headers = dict(headers)
        self._params: list[tuple[str, str]] = []
        self._operation: str | None = None
        self._body = None

    # --- Operaciones ---

    def select(self, columns: str = '*'):
        self._operation = 'select'
        self._params.append(('select', columns))
        return self

    def insert(self, data):
        self._operation = 'insert'
        self._body = data
        return self

    def update(self, data: dict):
        self._operation = 'update'
        self._body = data
        return self

    def delete(self):
        self._operation = 'delete'
        return self

    # --- Filtros ---

    def eq(self, column: str, value):
        if isinstance(value, bool):
            value = str(value).lower()
        self._params.append((column, f"eq.{value}"))
        return self

    def neq(self, column: str, value):
        if isinstance(value, bool):
            value = str(value).lower()
        self._params.append((column, f"neq.{value}"))
        return self

    def order(self, column: str, desc: bool = False):
        direction = "desc" if desc else "asc"
        self._params.append(('order', f"{column}.{direction}"))
        return self

    def limit(self, count: int):
        self._params.append(('limit', str(count)))
        return self

    # --- Ejecución ---

    def execute(self) -> _Response:
        headers = self._headers

        if self._operation == 'select':
            resp = _requests.get(self._url, headers=headers, params=self._params)

        elif self._operation == 'insert':
            headers['Prefer'] = 'return=representation'
            resp = _requests.post(
                self._url, headers=headers, json=self._body, params=self._params,
            )

        elif self._operation == 'update':
            headers['Prefer'] = 'return=representation'
            resp = _requests.patch(
                self._url, headers=headers, json=self._body, params=self._params,
            )

        elif self._operation == 'delete':
            headers['Prefer'] = 'return=representation'
            resp = _requests.delete(
                self._url, headers=headers, params=self._params,
            )
        else:
            raise ValueError(f"Operación no definida: llama select/insert/update/delete antes de execute")

        resp.raise_for_status()
        return _Response(resp.json())


class SupabaseREST:
    """Cliente ligero de Supabase usando la REST API (PostgREST)."""

    def __init__(self, url: str, key: str):
        self._url = url.rstrip('/')
        self._headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        }

    def table(self, table_name: str) -> _QueryBuilder:
        return _QueryBuilder(self._url, self._headers, table_name)


# --- Singleton ---
_cliente_supabase: SupabaseREST | None = None


def obtener_supabase() -> SupabaseREST:
    """Obtiene la instancia del cliente de Supabase (singleton)."""
    global _cliente_supabase
    if _cliente_supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Faltan las variables SUPABASE_URL y/o SUPABASE_KEY. "
                "Revisa tu archivo .env"
            )
        _cliente_supabase = SupabaseREST(SUPABASE_URL, SUPABASE_KEY)
    return _cliente_supabase
