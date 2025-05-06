import os
import uuid
import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for
import qrcode
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Leer cadena de conexión desde variable de entorno
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    hour = request.form['hour']
    uid = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO info (id, name, hour, attendance) VALUES (%s, %s, %s, %s)",
                (uid, name, hour, False)
            )

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
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM info WHERE id = %s", (uid,))
                record = cur.fetchone()

    return render_template('verify.html', uid=uid, record=record)

@app.route('/mark/<uid>', methods=['POST'])
def mark(uid):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE info SET attendance = TRUE WHERE id = %s", (uid,))
    return redirect(url_for('verify') + f'?uid={uid}')

if __name__ == '__main__':
    app.run(debug=True)
