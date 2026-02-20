"""
Servicio de generación de códigos QR.
Genera QR en formato texto ASCII (sin dependencia de Pillow).
"""
import io
import os
import qrcode
from app.models.database import obtener_supabase


def generar_qr_cliente(cliente_id: str, telefono: str) -> str:
    """
    Genera un código QR en texto ASCII para el cliente.
    Guarda el resultado como archivo .txt.
    Retorna la ruta del archivo generado.
    """
    directorio_qr = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'static', 'qr_codes',
    )
    os.makedirs(directorio_qr, exist_ok=True)

    # Datos que contendrá el QR
    datos_qr = f"FIDELIPYME|{cliente_id}|{telefono}"

    # Generar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    qr.add_data(datos_qr)
    qr.make(fit=True)

    # Capturar la salida ASCII en un string
    buffer = io.StringIO()
    qr.print_ascii(out=buffer)
    contenido_ascii = buffer.getvalue()

    # Guardar como archivo de texto
    nombre_archivo = f"qr_{cliente_id}.txt"
    ruta_archivo = os.path.join(directorio_qr, nombre_archivo)
    with open(ruta_archivo, 'w') as f:
        f.write(contenido_ascii)

    # Guardar referencia en la base de datos
    db = obtener_supabase()
    db.table('clientes').update({
        'codigo_qr': nombre_archivo,
    }).eq('id', cliente_id).execute()

    return ruta_archivo


def obtener_ruta_qr(cliente_id: str) -> str | None:
    """Obtiene la ruta del QR de un cliente, generándolo si no existe."""
    directorio_qr = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'static', 'qr_codes',
    )
    ruta = os.path.join(directorio_qr, f"qr_{cliente_id}.txt")

    if os.path.exists(ruta):
        return ruta

    # Si no existe, obtener teléfono del cliente y generar
    db = obtener_supabase()
    cliente = (
        db.table('clientes')
        .select('telefono')
        .eq('id', cliente_id)
        .execute()
    )
    if cliente.data:
        return generar_qr_cliente(cliente_id, cliente.data[0]['telefono'])

    return None
