from flask import Flask, render_template_string, request, redirect, flash, send_file
import psycopg2
import csv
import io
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'sup3rs3cretk3y'

# Configuración para PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            visits INTEGER DEFAULT 1,
            last_visit_date TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_table()

TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Barber App</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f4; margin: 20px; }
        h1 { color: #444; }
        form, table { margin-bottom: 20px; }
        table { width: 100%%; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #333; color: white; }
        td { background-color: white; }
        input, button { padding: 6px; }
        .msg { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>📋 Registro de Clientes - Barber App</h1>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class="msg">
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}

    <form action="/" method="POST">
        <input type="text" name="name" placeholder="Nombre" required>
        <input type="text" name="phone" placeholder="Teléfono" required>
        <button type="submit">Agregar Cliente</button>
    </form>

    <form action="/export" method="GET">
        <button type="submit">📤 Exportar a CSV</button>
    </form>

    <table>
        <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Teléfono</th>
            <th>Visitas</th>
            <th>Última Visita</th>
            <th>Acciones</th>
        </tr>
        {% for client in clients %}
        <tr>
            <td>{{ client[0] }}</td>
            <td>{{ client[1] }}</td>
            <td>{{ client[2] }}</td>
            <td>{{ client[3] }}</td>
            <td>{{ client[4] }}</td>
            <td>
                <form action="/visit/{{ client[0] }}" method="POST" style="display:inline;">
                    <button type="submit">➕ Visita</button>
                </form>
                <form action="/delete/{{ client[0] }}" method="POST" style="display:inline;" onsubmit="return confirm('¿Eliminar cliente?');">
                    <button type="submit">🗑️ Borrar</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute('INSERT INTO clients (name, phone, last_visit_date) VALUES (%s, %s, %s)',
                           (name, phone, now))
            flash('Cliente agregado con éxito.')
        except psycopg2.errors.UniqueViolation:
            flash('Ese teléfono ya está registrado.')
            conn.rollback()
        conn.commit()

    cursor.execute('SELECT * FROM clients ORDER BY id')
    clients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template_string(TEMPLATE, clients=clients)

@app.route('/visit/<int:client_id>', methods=['POST'])
def add_visit(client_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT name, visits FROM clients WHERE id = %s', (client_id,))
    result = cursor.fetchone()
    if not result:
        flash('Cliente no encontrado.')
        return redirect('/')
    name, current_visits = result

    # Lógica de visitas y mensajes
    if current_visits == 6:
        new_visits = 1
        flash(f'{name} ya tiene un descuento por su 6ta visita 🥳')
    else:
        new_visits = current_visits + 1
        if new_visits == 5:
            flash(f'{name} está a una visita de obtener un descuento 🎉')

    cursor.execute('''
        UPDATE clients SET visits = %s, last_visit_date = %s WHERE id = %s
    ''', (new_visits, now, client_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('¡Visita registrada!')
    return redirect('/')

@app.route('/delete/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clients WHERE id = %s', (client_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Cliente eliminado.')
    return redirect('/')

@app.route('/export', methods=['GET'])
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients ORDER BY id')
    clients = cursor.fetchall()
    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Teléfono', 'Visitas', 'Última Visita'])
    for c in clients:
        writer.writerow(c)

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='clientes.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

