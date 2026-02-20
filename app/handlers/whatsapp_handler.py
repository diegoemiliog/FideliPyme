"""
Handler principal de mensajes de WhatsApp.
Gestiona el flujo conversacional: registro, menú, consultas y canjes.
Acepta tanto números (1-6) como palabras clave.
Nunca se queda sin responder — siempre retorna texto válido.
"""
from app.services.cliente_service import (
    buscar_cliente_por_telefono,
    registrar_cliente,
    obtener_info_cliente,
)
from app.services.puntos_service import (
    acumular_puntos,
    obtener_historial,
    formatear_historial,
)
from app.services.premio_service import (
    obtener_catalogo,
    formatear_catalogo,
    canjear_premio,
)
from app.services.qr_service import generar_qr_cliente

# Estado temporal para flujos de conversación (registro y canje)
# Formato: { 'whatsapp:+521234567890': {'estado': 'esperando_nombre'} }
_estados_conversacion = {}

# Palabras clave reconocidas como comandos (no son nombres de persona)
_COMANDOS = {
    '1', '2', '3', '4', '5', '6',
    'puntos', 'saldo', 'ver puntos', 'mis puntos',
    'premios', 'catalogo', 'catálogo', 'ver premios',
    'canjear', 'canje', 'canjes',
    'historial', 'mi historial', 'movimientos',
    'qr', 'codigo qr', 'código qr', 'mi qr', 'mi código qr',
    'ayuda', 'help', 'info',
    'menu', 'menú', 'inicio', 'hola', 'hi', 'hello',
    'cancelar', 'salir', 'volver',
}


def obtener_menu() -> str:
    """Retorna el menú principal del bot."""
    return (
        "📱 *FideliPyme* - Programa de Lealtad\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Elige una opción:\n\n"
        "1️⃣ *Ver mis puntos* y nivel\n"
        "2️⃣ *Ver premios* disponibles\n"
        "3️⃣ *Canjear* un premio\n"
        "4️⃣ *Mi historial* de movimientos\n"
        "5️⃣ *Mi código QR*\n"
        "6️⃣ *Ayuda*\n\n"
        "Escribe el *número* o *nombre* de la opción."
    )


def obtener_ayuda() -> str:
    """Retorna el mensaje de ayuda."""
    return (
        "ℹ️ *Ayuda - FideliPyme*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *¿Cómo funciona?*\n"
        "Por cada $10 MXN de compra ganas puntos.\n"
        "Acumula puntos y canjéalos por premios.\n\n"
        "🔹 *Niveles:*\n"
        "🥉 Bronce (0-99 pts) - x1\n"
        "🥈 Plata (100-249 pts) - x1.25\n"
        "🥇 Oro (250-499 pts) - x1.5\n"
        "👑 Platino (500+ pts) - x2\n\n"
        "🔹 *Multiplicador:*\n"
        "Entre mayor sea tu nivel, más puntos\n"
        "ganas por cada compra.\n\n"
        "🔹 *Comandos:*\n"
        "Escribe *menu* para ver las opciones.\n"
        "Escribe *puntos* para ver tu saldo.\n"
        "Escribe *cancelar* para salir de cualquier flujo.\n\n"
        "¿Dudas? Pregunta en el negocio. 😊"
    )


def procesar_mensaje(telefono: str, mensaje: str) -> str:
    """
    Procesa un mensaje entrante de WhatsApp y retorna la respuesta.
    Nunca lanza excepciones — siempre retorna un texto válido.
    """
    try:
        return _procesar_mensaje_interno(telefono, mensaje)
    except Exception:
        # Limpiar cualquier estado corrupto
        _estados_conversacion.pop(telefono, None)
        return (
            "😅 Ocurrió un error inesperado. Intenta de nuevo.\n\n"
            + obtener_menu()
        )


def _procesar_mensaje_interno(telefono: str, mensaje: str) -> str:
    """Lógica principal del procesamiento de mensajes."""
    mensaje = mensaje.strip()
    mensaje_lower = mensaje.lower().strip()

    # Si no hay texto, mostrar menú
    if not mensaje:
        cliente = buscar_cliente_por_telefono(telefono)
        if cliente:
            return f"¡Hola, *{cliente['nombre']}*! 👋\n\n" + obtener_menu()
        _estados_conversacion[telefono] = {'estado': 'esperando_nombre'}
        return _mensaje_bienvenida()

    # Verificar si hay un flujo de conversación pendiente
    estado = _estados_conversacion.get(telefono)

    if estado:
        return _procesar_estado(telefono, mensaje, mensaje_lower, estado)

    # Buscar si el cliente está registrado
    cliente = buscar_cliente_por_telefono(telefono)

    if not cliente:
        # Cliente nuevo: iniciar flujo de registro
        _estados_conversacion[telefono] = {'estado': 'esperando_nombre'}
        return _mensaje_bienvenida()

    # Cliente registrado: procesar opción del menú
    return _procesar_opcion(telefono, mensaje_lower, cliente)


def _mensaje_bienvenida() -> str:
    """Mensaje de bienvenida para clientes nuevos."""
    return (
        "👋 *¡Bienvenido a FideliPyme!*\n\n"
        "Nuestro programa de lealtad te premia\n"
        "por cada compra que realices.\n\n"
        "Para registrarte, escríbenos tu *nombre completo*:"
    )


def _procesar_estado(telefono: str, mensaje: str, mensaje_lower: str, estado: dict) -> str:
    """Procesa mensajes cuando hay un flujo activo (registro o canje)."""

    # "cancelar" siempre rompe cualquier flujo
    if mensaje_lower in ('cancelar', 'salir', 'volver', 'menu', 'menú'):
        del _estados_conversacion[telefono]
        cliente = buscar_cliente_por_telefono(telefono)
        if cliente:
            return f"👍 De acuerdo, *{cliente['nombre']}*.\n\n" + obtener_menu()
        # Si canceló el registro, volver a ofrecer registro
        _estados_conversacion[telefono] = {'estado': 'esperando_nombre'}
        return _mensaje_bienvenida()

    if estado['estado'] == 'esperando_nombre':
        return _procesar_registro_nombre(telefono, mensaje, mensaje_lower)

    if estado['estado'] == 'esperando_canje':
        return _procesar_canje_seleccion(telefono, mensaje, mensaje_lower)

    # Estado desconocido: limpiar y mostrar menú
    del _estados_conversacion[telefono]
    cliente = buscar_cliente_por_telefono(telefono)
    if cliente:
        return obtener_menu()
    _estados_conversacion[telefono] = {'estado': 'esperando_nombre'}
    return _mensaje_bienvenida()


def _procesar_registro_nombre(telefono: str, mensaje: str, mensaje_lower: str) -> str:
    """Procesa el nombre durante el flujo de registro."""

    # Si el usuario manda un comando conocido en vez de su nombre, re-pedir
    if mensaje_lower in _COMANDOS:
        return (
            "👋 Primero necesitamos registrarte.\n"
            "Escríbenos tu *nombre completo*:\n\n"
            "_(escribe *cancelar* para salir)_"
        )

    nombre = mensaje.strip()

    # Validar que el nombre sea razonable
    if len(nombre) < 2 or len(nombre) > 100:
        return "Por favor, escribe un nombre válido (entre 2 y 100 caracteres):"

    if nombre.isdigit():
        return "Eso parece un número, no un nombre. 😅\nEscríbenos tu *nombre completo*:"

    # Registrar al cliente
    cliente = registrar_cliente(nombre, telefono)
    del _estados_conversacion[telefono]

    # Generar su código QR
    generar_qr_cliente(cliente['id'], telefono)

    return (
        f"🎉 *¡Registro exitoso!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Nombre: *{cliente['nombre']}*\n"
        f"⭐ Puntos de bienvenida: *{cliente['puntos']}*\n"
        f"🏅 Nivel: *{cliente['nivel']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{obtener_menu()}"
    )


def _procesar_canje_seleccion(telefono: str, mensaje: str, mensaje_lower: str) -> str:
    """Procesa la selección de premio durante el flujo de canje."""
    cliente = buscar_cliente_por_telefono(telefono)
    del _estados_conversacion[telefono]

    if not cliente:
        return "Error: no se encontró tu cuenta. Escribe *hola* para empezar."

    # Si mandó un comando en vez de un número, ejecutar el comando
    if mensaje_lower in _COMANDOS and not mensaje.isdigit():
        return _procesar_opcion(telefono, mensaje_lower, cliente)

    try:
        indice = int(mensaje)
    except ValueError:
        return (
            "❌ Opción inválida. Escribe el *número* del premio.\n\n"
            + obtener_menu()
        )

    resultado = canjear_premio(cliente['id'], indice)
    return resultado['mensaje'] + "\n\n" + obtener_menu()


def _procesar_opcion(telefono: str, mensaje_lower: str, cliente: dict) -> str:
    """
    Procesa la opción seleccionada del menú.
    Acepta números (1-6) y palabras clave.
    Siempre retorna una respuesta — nunca se queda sin responder.
    """

    # Opción 1: Ver puntos
    if mensaje_lower in ('1', 'puntos', 'saldo', 'ver puntos', 'mis puntos'):
        return obtener_info_cliente(telefono)

    # Opción 2: Ver premios
    if mensaje_lower in ('2', 'premios', 'catalogo', 'catálogo', 'ver premios'):
        premios = obtener_catalogo()
        return formatear_catalogo(premios, cliente['puntos'])

    # Opción 3: Canjear premio
    if mensaje_lower in ('3', 'canjear', 'canje', 'canjes'):
        premios = obtener_catalogo()
        catalogo = formatear_catalogo(premios, cliente['puntos'])
        _estados_conversacion[telefono] = {'estado': 'esperando_canje'}
        return catalogo + "\n\n✏️ Escribe el *número* del premio que deseas canjear:"

    # Opción 4: Historial
    if mensaje_lower in ('4', 'historial', 'mi historial', 'movimientos'):
        transacciones = obtener_historial(cliente['id'])
        return formatear_historial(cliente['nombre'], transacciones)

    # Opción 5: Código QR
    if mensaje_lower in ('5', 'qr', 'codigo qr', 'código qr', 'mi qr', 'mi código qr'):
        return (
            "📱 *Tu Código QR de FideliPyme*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 {cliente['nombre']}\n"
            f"🆔 ID: {cliente['id'][:8]}...\n\n"
            "Muestra este código en el negocio para\n"
            "acumular puntos en tus compras.\n\n"
            "Tu QR ha sido generado. Solicítalo\n"
            "en el negocio para que lo escaneen. ✅"
        )

    # Opción 6: Ayuda
    if mensaje_lower in ('6', 'ayuda', 'help', 'info'):
        return obtener_ayuda()

    # Comando: menú / hola
    if mensaje_lower in ('menu', 'menú', 'inicio', 'hola', 'hi', 'hello'):
        return f"¡Hola, *{cliente['nombre']}*! 👋\n\n" + obtener_menu()

    # Cualquier mensaje no reconocido → SIEMPRE responder con menú
    return (
        f"No entendí tu mensaje, *{cliente['nombre']}*. 🤔\n\n"
        + obtener_menu()
    )
