import sqlite3

# Conectamos con la base de datos
conn = sqlite3.connect('barber.db')
cursor = conn.cursor()

# Agregar la columna de la última visita si no existe
cursor.execute('''
    ALTER TABLE clients
    ADD COLUMN last_visit_date TEXT
''')

conn.commit()  # Guardamos los cambios
conn.close()  # Cerramos la conexión

print("Columna 'last_visit_date' agregada correctamente.")
