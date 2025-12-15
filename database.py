import sqlite3

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ======================
    # SEDES
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sedes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        logo TEXT,
        ciudad TEXT,
        direccion TEXT,
        telefono TEXT,
        activo INTEGER DEFAULT 1
    )
    """)

    # ======================
    # USUARIOS
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        usuario TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT DEFAULT 'usuario',
        sede_id INTEGER NOT NULL,
        FOREIGN KEY (sede_id) REFERENCES sedes(id)
    )
    """)

    # ======================
    # PERSONAL (doctores / enfermeros)
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,   -- doctor o enfermero
        cedula TEXT,
        firma TEXT,
        sede_id INTEGER NOT NULL,
        FOREIGN KEY (sede_id) REFERENCES sedes(id)
    )
    """)

    # ======================
    # PACIENTES
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cedula TEXT NOT NULL UNIQUE,
        tipo_documento TEXT,
        lugar_expedicion TEXT,
        fecha_nacimiento TEXT,
        firma TEXT
    )
    """)

    # ======================
    # ACUDIENTES
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS acudientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        nombre_acudiente TEXT NOT NULL,
        cedula_acudiente TEXT,
        lugar_expedicion_acudiente TEXT,
        parentesco_acudiente TEXT,
        firma_acudiente TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
    )
    """)

    # ======================
    # MENORES DE EDAD
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        nombre_menor TEXT NOT NULL,
        cedula_menor TEXT,
        lugar_expedicion_menor TEXT,
        fecha_nacimiento TEXT,
        firma_menor TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
    )
    """)

    # ======================
    # CONSENTIMIENTOS GENERADOS (HISTORIAL)
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consentimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        sede_id INTEGER NOT NULL,
        paciente_id INTEGER NOT NULL,
        doctor_id INTEGER,
        enfermero_id INTEGER,
        menor_id INTEGER,
        acudiente_id INTEGER,
        plantilla_usada TEXT,
        archivo_generado TEXT,
        FOREIGN KEY (sede_id) REFERENCES sedes(id),
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
        FOREIGN KEY (doctor_id) REFERENCES personal(id),
        FOREIGN KEY (enfermero_id) REFERENCES personal(id),
        FOREIGN KEY (menor_id) REFERENCES menores(id),
        FOREIGN KEY (acudiente_id) REFERENCES acudientes(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE consentimiento_secciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consentimiento_id INTEGER,
    tipo TEXT,               
    contenido TEXT,          
    orden INTEGER,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (consentimiento_id) REFERENCES consentimientos_definicion(id)
);
    """)
    
    cursor.execute("""
    CREATE TABLE consentimientos_definicion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paquete_id INTEGER,
    nombre TEXT NOT NULL,
    
    consentimiento_id INTEGER,
    tipo TEXT,               
    contenido TEXT,          
    orden INTEGER,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (consentimiento_id) REFERENCES consentimientos_definicion(id)
);
    """)
    cursor.execute("""
    CREATE TABLE consentimientos_definicion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paquete_id INTEGER,
    nombre TEXT NOT NULL,
    version TEXT NOT NULL,
    fecha_version TEXT NOT NULL,
    sede_id INTEGER,
    contenido TEXT NOT NULL,   -- TEXTO LARGO
    firma_paciente INTEGER DEFAULT 1,
    firma_medico INTEGER DEFAULT 0,
    firma_enfermero INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    created_at TEXT
);  
""")

        

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos creada.")
