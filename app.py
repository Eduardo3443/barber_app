from flask import Flask, render_template_string, request, redirect, flash, send_file
import sqlite3
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Crear base de datos
def create_db():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            visits INTEGER DEFAULT 1,
            last_visit_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Página principal
@app.route('/')
def home():
    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>THE KRAKEN BARBER SHOP</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: Arial, sans-serif; }
                .container { margin-top: 50px; text-align: center; }
                h2 { color: #808080; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>THE KRAKEN BARBERSHOP</h2>
                <div class="mt-4">
                    <a href="/clientes" class="btn btn-primary btn-lg">Ver Clientes</a>
                    <a href="/registrar" class="btn btn-success btn-lg">Registrar Cliente</a>
                    <a href="/sumar_visita" class="btn btn-warning btn-lg">Sumar Visita</a>
                </div>
            </div>
        </body>
        </html>
    ''')

# Registrar cliente o sumar visita
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    errores = []
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()

        if not name or len(name) < 3:
            errores.append("El nombre debe tener al menos 3 caracteres.")
        if not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
            errores.append("El teléfono debe contener solo números y tener entre 10 y 15 dígitos.")

        if not errores:
            conn = sqlite3.connect('barber.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, visits, name FROM clients WHERE phone = ?", (phone,))
            cliente = cursor.fetchone()

            if cliente:
                cliente_id, visitas, existing_name = cliente
                cursor.execute('''
                    UPDATE clients
                    SET visits = ?, last_visit_date = DATE('now')
                    WHERE id = ?
                ''', (visitas + 1, cliente_id))
                conn.commit()
                conn.close()
                flash(f"Cliente ya registrado ({existing_name}). Se agregó una nueva visita.", "info")
                return redirect('/clientes')
            else:
                cursor.execute('''
                    INSERT INTO clients (name, phone, visits, last_visit_date)
                    VALUES (?, ?, 1, DATE('now'))
                ''', (name, phone))
                conn.commit()
                conn.close()
                flash(f"Cliente {name} registrado con su primera visita.", 'success')
                return redirect('/clientes')

    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Registrar Cliente</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: Arial, sans-serif; }
                .container { margin-top: 30px; max-width: 600px; }
                .form-control { margin-bottom: 15px; }
                .alert { margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Registrar Cliente</h2>

                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    {% for category, message in messages %}
                      <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                  {% endif %}
                {% endwith %}

                {% if errores %}
                  <div class="alert alert-danger">
                    <ul>{% for error in errores %}<li>{{ error }}</li>{% endfor %}</ul>
                  </div>
                {% endif %}

                <form method="POST">
                    <div class="mb-3">
                        <label for="name" class="form-label">Nombre</label>
                        <input type="text" class="form-control" id="name" name="name" required minlength="3">
                    </div>
                    <div class="mb-3">
                        <label for="phone" class="form-label">Teléfono</label>
                        <input type="text" class="form-control" id="phone" name="phone" required pattern="\\d{10,15}" title="Solo números entre 10 y 15 dígitos">
                    </div>
                    <button type="submit" class="btn btn-success">Registrar</button>
                </form>
                <a href="/" class="btn btn-link mt-3">Volver al Inicio</a>
            </div>
        </body>
        </html>
    ''', errores=errores)

# Nueva ruta para sumar visita a cliente registrado
@app.route('/sumar_visita', methods=['GET', 'POST'])
def sumar_visita():
    mensaje = None
    error = None

    if request.method == 'POST':
        phone = request.form['phone'].strip()

        if not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
            error = "El teléfono debe tener entre 10 y 15 dígitos."
        else:
            conn = sqlite3.connect('barber.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, visits FROM clients WHERE phone = ?", (phone,))
            cliente = cursor.fetchone()

            if cliente:
                cliente_id, name, visitas = cliente
                cursor.execute('''
                    UPDATE clients
                    SET visits = ?, last_visit_date = DATE('now')
                    WHERE id = ?
                ''', (visitas + 1, cliente_id))
                conn.commit()
                mensaje = f"Visita registrada para {name}."
            else:
                error = "Cliente no encontrado."
            conn.close()

    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sumar Visita</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .container { margin-top: 40px; max-width: 500px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Sumar Visita</h2>

                {% if mensaje %}
                    <div class="alert alert-success">{{ mensaje }}</div>
                {% elif error %}
                    <div class="alert alert-danger">{{ error }}</div>
                {% endif %}

                <form method="POST">
                    <div class="mb-3">
                        <label for="phone" class="form-label">Teléfono del Cliente</label>
                        <input type="text" class="form-control" id="phone" name="phone" required pattern="\\d{10,15}">
                    </div>
                    <button type="submit" class="btn btn-warning">Sumar Visita</button>
                </form>

                <a href="/" class="btn btn-link mt-3">Volver al Inicio</a>
            </div>
        </body>
        </html>
    ''', mensaje=mensaje, error=error)

# Mostrar lista de clientes
@app.route('/clientes', methods=['GET'])
def clientes():
    filter_visits = request.args.get('filter_visits', default=None, type=int)
    search_query = request.args.get('search', default='', type=str)
    start_date = request.args.get('start_date', default='', type=str)
    end_date = request.args.get('end_date', default='', type=str)

    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()

    query = "SELECT id, name, phone, visits, last_visit_date FROM clients WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE ? OR phone LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if filter_visits:
        query += " AND visits = ?"
        params.append(filter_visits)

    if start_date:
        query += " AND last_visit_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND last_visit_date <= ?"
        params.append(end_date)

    cursor.execute(query, tuple(params))
    clientes = cursor.fetchall()
    conn.close()

    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Clientes Registrados</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: Arial, sans-serif; }
                .container { margin-top: 30px; }
                .search-form, .date-filter { margin-bottom: 20px; }
                .btn-sm { margin-right: 5px; }
                .filter-buttons { margin-bottom: 15px; }
                table { width: 100%; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Clientes Registrados</h2>

                <form method="GET" class="d-flex search-form">
                    <input type="text" name="search" class="form-control" placeholder="Buscar por nombre o teléfono" value="{{ request.args.get('search', '') }}">
                    <button type="submit" class="btn btn-primary ms-2">Buscar</button>
                </form>

                <div class="filter-buttons mb-2">
                    {% for i in range(1, 7) %}
                        <a href="/clientes?filter_visits={{ i }}" class="btn btn-outline-primary btn-sm">{{ i }} visitas</a>
                    {% endfor %}
                    <a href="/clientes" class="btn btn-outline-secondary btn-sm">Todos</a>
                </div>

                <form method="GET" class="d-flex date-filter">
                    <input type="date" name="start_date" class="form-control me-2" value="{{ request.args.get('start_date', '') }}">
                    <input type="date" name="end_date" class="form-control me-2" value="{{ request.args.get('end_date', '') }}">
                    <button type="submit" class="btn btn-outline-dark">Filtrar por Fecha</button>
                </form>

                <a href="/exportar" class="btn btn-outline-success mb-3">📥 Exportar CSV</a>

                <table class="table table-bordered table-striped">
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Teléfono</th>
                            <th>Visitas</th>
                            <th>Última Visita</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in clientes %}
                            <tr>
                                <td>{{ c[1] }}</td>
                                <td>{{ c[2] }}</td>
                                <td>{{ c[3] }}</td>
                                <td>{{ c[4] or 'Sin fecha' }}</td>
                                <td>
                                    <a href="/eliminar/{{ c[0] }}" class="btn btn-danger btn-sm" onclick="return confirm('¿Eliminar cliente?')">Eliminar</a>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <a href="/" class="btn btn-link">Volver al Inicio</a>
            </div>
        </body>
        </html>
    ''', clientes=clientes)

# Eliminar cliente
@app.route('/eliminar/<int:cliente_id>', methods=['GET'])
def eliminar(cliente_id):
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    flash("Cliente eliminado correctamente.", "success")
    return redirect('/clientes')

# Exportar CSV
@app.route('/exportar', methods=['GET'])
def exportar_csv():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, phone, visits, last_visit_date FROM clients")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nombre', 'Teléfono', 'Visitas', 'Última Visita'])
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

if __name__ == '__main__':
    create_db()
    import os

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


