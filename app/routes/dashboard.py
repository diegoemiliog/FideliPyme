"""
Rutas del dashboard web de administración de FideliPyme.
Login, estadísticas, registro de ventas, gestión de premios y clientes.
"""
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify, flash,
)
from app.models.database import obtener_supabase
from app.services.cliente_service import buscar_cliente_por_telefono
from app.services.puntos_service import acumular_puntos
from app.config import NIVELES

dashboard_bp = Blueprint(
    'dashboard', __name__,
    url_prefix='/dashboard',
    template_folder='../templates/dashboard',
)

DASHBOARD_PASSWORD = 'fidelipyme2026'


# --- Decorador de autenticación ---

def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('dashboard_auth'):
            return redirect(url_for('dashboard.login'))
        return f(*args, **kwargs)
    return wrapper


# --- Vistas ---

@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == DASHBOARD_PASSWORD:
            session['dashboard_auth'] = True
            return redirect(url_for('dashboard.index'))
        flash('Contraseña incorrecta', 'error')
    return render_template('login.html')


@dashboard_bp.route('/logout')
def logout():
    session.pop('dashboard_auth', None)
    return redirect(url_for('dashboard.login'))


@dashboard_bp.route('/')
@login_requerido
def index():
    """Panel principal con estadísticas."""
    return render_template('index.html')


@dashboard_bp.route('/ventas')
@login_requerido
def ventas():
    """Página de registro de ventas."""
    return render_template('ventas.html')


@dashboard_bp.route('/clientes')
@login_requerido
def clientes():
    """Página de lista de clientes."""
    return render_template('clientes.html')


@dashboard_bp.route('/premios')
@login_requerido
def premios():
    """Página de gestión de premios."""
    return render_template('premios.html')


# --- API endpoints para AJAX ---

@dashboard_bp.route('/api/estadisticas')
@login_requerido
def api_estadisticas():
    """Retorna estadísticas generales del sistema."""
    db = obtener_supabase()

    clientes = db.table('clientes').select('*').execute().data
    transacciones = db.table('transacciones').select('*').execute().data
    premios = db.table('premios').select('*').eq('activo', True).execute().data

    total_clientes = len(clientes)
    puntos_circulacion = sum(c['puntos'] for c in clientes)

    canjes = [t for t in transacciones if t['tipo'] == 'canje']
    compras = [t for t in transacciones if t['tipo'] == 'compra']
    total_canjes = len(canjes)
    total_ventas = sum(t.get('monto', 0) or 0 for t in compras)

    # Distribución por nivel
    niveles = {'Bronce': 0, 'Plata': 0, 'Oro': 0, 'Platino': 0}
    for c in clientes:
        nivel = c.get('nivel', 'Bronce')
        if nivel in niveles:
            niveles[nivel] += 1

    # Top 5 clientes por puntos
    clientes_sorted = sorted(clientes, key=lambda c: c['puntos'], reverse=True)
    top_clientes = [
        {
            'nombre': c['nombre'],
            'puntos': c['puntos'],
            'nivel': c['nivel'],
            'telefono': c['telefono'],
        }
        for c in clientes_sorted[:5]
    ]

    return jsonify({
        'total_clientes': total_clientes,
        'puntos_circulacion': puntos_circulacion,
        'total_canjes': total_canjes,
        'total_ventas': round(total_ventas, 2),
        'niveles': niveles,
        'top_clientes': top_clientes,
        'total_premios': len(premios),
    })


@dashboard_bp.route('/api/buscar-cliente')
@login_requerido
def api_buscar_cliente():
    """Busca un cliente por teléfono."""
    telefono = request.args.get('telefono', '').strip()
    if not telefono:
        return jsonify({'error': 'Teléfono requerido'}), 400

    # Intentar buscar con y sin prefijo whatsapp:
    cliente = buscar_cliente_por_telefono(telefono)
    if not cliente and not telefono.startswith('whatsapp:'):
        cliente = buscar_cliente_por_telefono(f'whatsapp:{telefono}')

    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    config_nivel = NIVELES.get(cliente['nivel'], NIVELES['Bronce'])

    return jsonify({
        'id': cliente['id'],
        'nombre': cliente['nombre'],
        'telefono': cliente['telefono'],
        'puntos': cliente['puntos'],
        'nivel': cliente['nivel'],
        'multiplicador': config_nivel['multiplicador'],
    })


@dashboard_bp.route('/api/registrar-venta', methods=['POST'])
@login_requerido
def api_registrar_venta():
    """Registra una venta y acumula puntos."""
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos requeridos'}), 400

    cliente_id = datos.get('cliente_id')
    monto = datos.get('monto')

    if not cliente_id or not monto:
        return jsonify({'error': 'cliente_id y monto son requeridos'}), 400

    try:
        monto = float(monto)
    except (ValueError, TypeError):
        return jsonify({'error': 'Monto inválido'}), 400

    if monto <= 0:
        return jsonify({'error': 'El monto debe ser mayor a 0'}), 400

    # Obtener cliente
    db = obtener_supabase()
    resultado = db.table('clientes').select('*').eq('id', cliente_id).execute()
    if not resultado.data:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    cliente = resultado.data[0]
    resultado_puntos = acumular_puntos(cliente['id'], monto, cliente['nivel'])

    return jsonify({
        'exito': True,
        'cliente': cliente['nombre'],
        'monto': monto,
        'puntos_otorgados': resultado_puntos['puntos_otorgados'],
        'multiplicador': resultado_puntos['multiplicador'],
        'nuevo_total': resultado_puntos['nuevo_total'],
        'nivel': resultado_puntos['nuevo_nivel'],
        'subio_nivel': resultado_puntos['subio_nivel'],
    })


@dashboard_bp.route('/api/clientes')
@login_requerido
def api_clientes():
    """Lista de clientes con búsqueda opcional."""
    db = obtener_supabase()
    busqueda = request.args.get('q', '').strip()

    query = db.table('clientes').select('*')

    if busqueda:
        # Buscar por nombre o teléfono
        query = query.ilike('nombre', f'%{busqueda}%')

    clientes = query.order('fecha_registro', desc=True).execute().data

    # Si buscó y no encontró por nombre, intentar por teléfono
    if busqueda and not clientes:
        clientes = (
            db.table('clientes').select('*')
            .ilike('telefono', f'%{busqueda}%')
            .order('fecha_registro', desc=True)
            .execute().data
        )

    return jsonify([
        {
            'id': c['id'],
            'nombre': c['nombre'],
            'telefono': c['telefono'],
            'puntos': c['puntos'],
            'nivel': c['nivel'],
            'fecha_registro': c['fecha_registro'][:10] if c.get('fecha_registro') else '',
        }
        for c in clientes
    ])


@dashboard_bp.route('/api/premios')
@login_requerido
def api_premios():
    """Lista todos los premios (activos e inactivos)."""
    db = obtener_supabase()
    premios = (
        db.table('premios').select('*')
        .order('costo_puntos', desc=False)
        .execute().data
    )
    return jsonify(premios)


@dashboard_bp.route('/api/premios', methods=['POST'])
@login_requerido
def api_crear_premio():
    """Crea un nuevo premio."""
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos requeridos'}), 400

    nombre = datos.get('nombre', '').strip()
    costo = datos.get('costo_puntos')
    descripcion = datos.get('descripcion', '').strip()

    if not nombre or not costo:
        return jsonify({'error': 'nombre y costo_puntos son requeridos'}), 400

    try:
        costo = int(costo)
    except (ValueError, TypeError):
        return jsonify({'error': 'Costo debe ser un número entero'}), 400

    if costo <= 0:
        return jsonify({'error': 'El costo debe ser mayor a 0'}), 400

    db = obtener_supabase()
    resultado = db.table('premios').insert({
        'nombre': nombre,
        'costo_puntos': costo,
        'descripcion': descripcion,
        'activo': True,
    }).execute()

    return jsonify(resultado.data[0]), 201


@dashboard_bp.route('/api/premios/<premio_id>', methods=['PUT'])
@login_requerido
def api_editar_premio(premio_id):
    """Edita un premio existente."""
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'Datos requeridos'}), 400

    campos = {}
    if 'nombre' in datos:
        campos['nombre'] = datos['nombre'].strip()
    if 'costo_puntos' in datos:
        try:
            campos['costo_puntos'] = int(datos['costo_puntos'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Costo inválido'}), 400
    if 'descripcion' in datos:
        campos['descripcion'] = datos['descripcion'].strip()
    if 'activo' in datos:
        campos['activo'] = bool(datos['activo'])

    if not campos:
        return jsonify({'error': 'Nada que actualizar'}), 400

    db = obtener_supabase()
    resultado = (
        db.table('premios')
        .update(campos)
        .eq('id', premio_id)
        .execute()
    )

    if not resultado.data:
        return jsonify({'error': 'Premio no encontrado'}), 404

    return jsonify(resultado.data[0])


@dashboard_bp.route('/api/premios/<premio_id>', methods=['DELETE'])
@login_requerido
def api_eliminar_premio(premio_id):
    """Elimina (desactiva) un premio."""
    db = obtener_supabase()
    resultado = (
        db.table('premios')
        .update({'activo': False})
        .eq('id', premio_id)
        .execute()
    )

    if not resultado.data:
        return jsonify({'error': 'Premio no encontrado'}), 404

    return jsonify({'exito': True, 'mensaje': 'Premio desactivado'})
