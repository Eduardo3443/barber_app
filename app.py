from flask import Flask, render_template, request, redirect, flash, send_file
import psycopg2
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Conexión a PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def create_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            visits INTEGER DEFAULT 1,
            last_visit_date DATE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    errores = []
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()

        if not name or len(name) < 3:
            errores.append("El nombre debe tener al menos 3 caracteres.")
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            errores.append("El teléfono debe contener solo números y tener entre 10 y 15 dígitos.")

        if not errores:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, visits, name FROM clients WHERE phone = %s", (phone,))
            cliente = cursor.fetchone()

            if cliente:
                cliente_id, visitas, existing_name = cliente
                visitas += 1
                if visitas > 6:
                    visitas = 1
                cursor.execute('''
                    UPDATE clients
                    SET visits = %s, last_visit_date = CURRENT_DATE
                    WHERE id = %s
                ''', (visitas, cliente_id))
                conn.commit()
                conn.close()
                flash(f"{existing_name} ya registrado. Se agregó una nueva visita.", "info")
                return redirect('/clientes')
            else:
                cursor.execute('''
                    INSERT INTO clients (name, phone, visits, last_visit_date)
                    VALUES (%s, %s, 1, CURRENT_DATE)
                ''', (name, phone))
                conn.commit()
                conn.close()
                flash(f"Cliente {name} registrado con su primera visita.", 'success')
                return redirect('/clientes')

    return render_template('registrar.html', errores=errores)

@app.route('/sumar_visita', methods=['GET', 'POST'])
def sumar_visita():
    mensaje = None
    error = None

    if request.method == 'POST':
        phone = request.form['phone'].strip()

        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            error = "El teléfono debe tener entre 10 y 15 dígitos."
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, visits FROM clients WHERE phone = %s", (phone,))
            cliente = cursor.fetchone()

            if cliente:
                cliente_id, name, visitas = cliente
                visitas += 1
                if visitas > 6:
                    visitas = 1

                mensaje = f"Visita registrada para {name}."
                if visitas == 5:
                    mensaje += " ¡Una más para descuento!"
                elif visitas == 6:
                    mensaje += " ¡Tiene un descuento!"

                cursor.execute('''
                    UPDATE clients
                    SET visits = %s, last_visit_date = CURRENT_DATE
                    WHERE id = %s
                ''', (visitas, cliente_id))
                conn.commit()
            else:
                error = "Cliente no encontrado."
            conn.close()

    return render_template('sumar_visita.html', mensaje=mensaje, error=error)

@app.route('/clientes')
def clientes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, visits, last_visit_date FROM clients")
    clientes = cursor.fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/eliminar/<int:cliente_id>')
def eliminar(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = %s", (cliente_id,))
    conn.commit()
    conn.close()
    flash("Cliente eliminado correctamente.", "success")
    return redirect('/clientes')

@app.route('/exportar')
def exportar_csv():
    conn = get_db_connection()
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
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
