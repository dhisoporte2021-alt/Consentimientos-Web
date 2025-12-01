import sqlite3

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Personal (doctores / enfermeros)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cedula TEXT,
            firma TEXT
        )
    """)

    # Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE,
            lugar_expedicion TEXT,
            fecha_nacimiento TEXT,
            firma TEXT
        )
    """)

    # Acudientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acudientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE,
            parentesco TEXT,
            lugar_expedicion TEXT,
            firma TEXT
        )
    """)

    # Menores de edad
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE,
            lugar_expedicion TEXT,
            firma TEXT,
            fecha_nacimiento TEXT,
            acudiente_id INTEGER,
            FOREIGN KEY(acudiente_id) REFERENCES acudientes(id)
        )
    """)

    # Historial de consentimientos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consentimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            paciente_id INTEGER,
            doctor_id INTEGER,
            enfermero_id INTEGER,
            menor_id INTEGER,
            acudiente_id INTEGER,
            plantilla_usada TEXT,
            archivo_generado TEXT,
            FOREIGN KEY(paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY(doctor_id) REFERENCES personal(id),
            FOREIGN KEY(enfermero_id) REFERENCES personal(id),
            FOREIGN KEY(menor_id) REFERENCES menores(id),
            FOREIGN KEY(acudiente_id) REFERENCES acudientes(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos creada.")
