from dotenv import load_dotenv
import os
import uuid
import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for
import qrcode
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import send_file
from PIL import Image
import io


app = Flask(__name__)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer cadena de conexión desde variable de entorno
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT hour,
                           COUNT(*) AS total_vendidas,
                           COUNT(*) FILTER (WHERE attendance = TRUE) AS total_registradas
                    FROM info
                    GROUP BY hour
                    ORDER BY hour
                """)
                resumen = cur.fetchall()
    except Exception as e:
        return f"Error al obtener datos: {str(e)}", 500

    return render_template('index.html', resumen=resumen)

@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    hour = request.form.get('hour')

    if not name or not hour:
        return "Error: Nombre y hora son requeridos", 400

    uid = str(uuid.uuid4())

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO info (id, name, hour, attendance) VALUES (%s, %s, %s, %s)",
                    (uid, name, hour, False)
                )
    except Exception as e:
        return f"Error al insertar en la base de datos: {str(e)}", 500

    # Generar QR en memoria (base64)
    qr = qrcode.make(uid)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('result.html', uid=uid, qr_b64=qr_b64)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    record = None
    uid = request.form.get('uid', '').strip() if request.method == 'POST' else request.args.get('uid', '').strip()

    if uid:
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM info WHERE id = %s", (uid,))
                    record = cur.fetchone()
        except Exception as e:
            return f"Error al consultar la base de datos: {str(e)}", 500

    return render_template('verify.html', uid=uid, record=record)

@app.route('/mark/<uid>', methods=['POST'])
def mark(uid):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE info SET attendance = TRUE WHERE id = %s", (uid,))
        return redirect(url_for('verify', uid=uid))
    except Exception as e:
        return f"Error al actualizar asistencia: {str(e)}", 500
    
@app.route('/qr_image/<uid>')
def qr_image(uid):
    try:
        # Generar el QR
        qr = qrcode.make(uid)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)  # Asegúrate de posicionar el puntero al inicio del buffer

        # Retornar la imagen como respuesta
        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        return str(e)


@app.route('/descargar_entrada/<uid>')
def descargar_entrada_con_qr(uid):
    # Abrir la imagen base (la entrada visual)
    imagen_base = Image.open("static/entrada.png").convert("RGBA")

    # Crear el código QR con la URL de verificación, por ejemplo
    url_verificacion = f"/verify?uid={uid}"
    qr = qrcode.make(url_verificacion)
    qr = qr.resize((325, 325))  # Ajusta el tamaño si hace falta

    # Pegar el QR en la esquina superior derecha (con márgenes)
    margen = 10
    posicion = (imagen_base.width - qr.width - margen, margen)
    imagen_base.paste(qr, posicion)

    # Guardar la imagen final en un buffer para enviar
    buffer = io.BytesIO()
    imagen_base.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=f"entrada_qr_{uid}.png")

if __name__ == '__main__':
    app.run(debug=True)

