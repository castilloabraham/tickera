import os, json, uuid
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import qrcode

app = Flask(__name__)

DATA_FILE = 'data.json'
QR_FOLDER = os.path.join('static', 'qr_codes')
os.makedirs(QR_FOLDER, exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    hour = request.form['hour']
    uid = str(uuid.uuid4())
    record = {
        'id': uid,
        'name': name,
        'hour': hour,
        'attendance': False
    }
    data = load_data()
    data.append(record)
    save_data(data)

    # generar QR en memoria
    qr = qrcode.make(uid)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('result.html', uid=uid, qr_b64=qr_b64)

@app.route('/qr/<uid>')
def qr_image(uid):
    return send_from_directory(QR_FOLDER, f'{uid}.png')

@app.route('/verify', methods=['GET','POST'])
def verify():
    record = None
    # 1) obtener uid de POST o de GET
    if request.method == 'POST':
        uid = request.form.get('uid','').strip()
    else:
        uid = request.args.get('uid','').strip()

    # 2) si tenemos uid, buscar en data.json
    if uid:
        data = load_data()
        record = next((r for r in data if r['id'] == uid), None)

    # 3) renderizar plantilla pasando uid y record
    return render_template('verify.html', uid=uid, record=record)


@app.route('/mark/<uid>', methods=['POST'])
def mark(uid):
    data = load_data()
    for r in data:
        if r['id'] == uid:
            r['attendance'] = True
            break
    save_data(data)
    return redirect(url_for('verify') + f'?uid={uid}')

if __name__ == '__main__':
    app.run(debug=True)
