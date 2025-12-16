from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify,session, abort, make_response
import sqlite3
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from docxtpl import DocxTemplate
import pandas as pd
import os
from datetime import datetime
from database import get_db
import json
import base64
from weasyprint import HTML


app = Flask(__name__)
app.secret_key = os.urandom(24)

PLANTILLAS_DIR = os.path.join(os.getcwd(), "plantillas")
def get_sede_actual():
    return session.get('sede_id')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND password=?", (usuario, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario"] = user["usuario"]
            session["rol"] = user["rol"]
            session["sede_id"] = user["sede_id"]
            return redirect("/")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


##INICIO CRUD DE USUARIOS
##crear usuarios en la base de datos
@app.route("/usuarios/crear", methods=["GET", "POST"])
def crear_usuario():
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        usuario = request.form["usuario"]
        password = request.form["password"]
        rol = request.form["rol"]

        # sede
       
        sede_id = request.form["sede_id"]
      

        cursor.execute("""
        INSERT INTO usuarios (nombre, email, usuario, password, rol, sede_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, email, usuario, password, rol, sede_id))

        conn.commit()
        conn.close()
        return redirect("/usuarios")

    # solo superadmin necesita lista de sedes
    cursor.execute("SELECT * FROM sedes")
    sedes = cursor.fetchall()
    conn.close()

    return render_template("/usuarios/usuarioscrear.html", sedes=sedes)


##LISTAR USUARIOS
@app.route("/usuarios")
def listar_usuarios():
    if "usuario" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    if session["rol"] == "superadmin":
        cursor.execute("""
        SELECT u.*, s.nombre AS sede
        FROM usuarios u
        JOIN sedes s ON u.sede_id = s.id
        """)
    else:
        cursor.execute("""
        SELECT * FROM usuarios
        WHERE sede_id = ?
        """, (session["sede_id"],))

    usuarios = cursor.fetchall()
    conn.close()

    return render_template("/usuarios/usuarioslista.html", usuarios=usuarios)


##EDITAR USUARIOS
@app.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        abort(404)

    # 🔐 Validar sede
    if usuario["sede_id"] != session["sede_id"]:
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        usuario_form = request.form["usuario"]
        rol = request.form["rol"]

        cursor.execute("""
            UPDATE usuarios
            SET nombre=?, email=?, usuario=?, rol=?
            WHERE id=?
        """, (nombre, email, usuario_form, rol, id))

        conn.commit()
        conn.close()
        return redirect("/usuarios")

    conn.close()
    return render_template("/usuarios/usuarioseditar.html", usuario=usuario)


##ELIMINAR USUARIOS
@app.route("/usuarios/eliminar/<int:id>")
def eliminar_usuario(id):
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        abort(404)

    if usuario["sede_id"] != session["sede_id"]:
        abort(403)

    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/usuarios")

##FIN CRUD DE USUARIOS

def cargar_personal():
    db = get_db()
    data = db.execute(
        "SELECT * FROM personal WHERE sede_id = ?",
        (session["sede_id"],)
    ).fetchall()
    db.close()

    medicos = [p for p in data if p["tipo"] == "doctor"]
    enfermeros = [p for p in data if p["tipo"] == "enfermero"]

    return medicos, enfermeros



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/consentimientos")
def consentimientos():
    return render_template("consentimientos/consentimientos.html")

@app.route("/formulario")
def formulario():
    medicos, enfermeros = cargar_personal()

    # Cargar plantillas
    plantillas = []
    if os.path.exists(PLANTILLAS_DIR):
        plantillas = [
            f for f in os.listdir(PLANTILLAS_DIR)
            if f.lower().endswith(".docx")
        ]

    return render_template(
        "formulario.html",
        medicos=medicos,
        enfermeros=enfermeros,
        plantillas=plantillas
    )


@app.route("/generar", methods=["POST"])
def generar():
    if "usuario" not in session:
        return redirect("/login")

    datos = request.form.to_dict()

    if not datos.get("fecha"):
        datos["fecha"] = datetime.now().strftime("%Y-%m-%d")

    plantilla_path = os.path.join("plantillas", datos["plantilla"])
    doc = DocxTemplate(plantilla_path)

    db = get_db()

    # ==============================
    # DOCTOR
    # ==============================
    doctor_id = datos.get("doctor_id")
    if doctor_id:
        doctor = db.execute("""
            SELECT * FROM personal
            WHERE id=? AND tipo='doctor' AND sede_id=?
        """, (doctor_id, session["sede_id"])).fetchone()

        if doctor:
            datos["doctor"] = doctor["nombre"]
            datos["cedula_doctor"] = doctor["cedula"]
        else:
            datos["doctor"] = ""
            datos["cedula_doctor"] = ""
    else:
        datos["doctor"] = ""
        datos["cedula_doctor"] = ""

    # ==============================
    # ENFERMERO
    # ==============================
    enfermero_id = datos.get("enfermero_id")
    if enfermero_id:
        enf = db.execute("""
            SELECT * FROM personal
            WHERE id=? AND tipo='enfermero' AND sede_id=?
        """, (enfermero_id, session["sede_id"])).fetchone()

        if enf:
            datos["enfermero"] = enf["nombre"]
            datos["cedula_enfermero"] = enf["cedula"]
        else:
            datos["enfermero"] = ""
            datos["cedula_enfermero"] = ""
    else:
        datos["enfermero"] = ""
        datos["cedula_enfermero"] = ""

    # ==============================
    # FIRMAS
    # ==============================
    firmas = [
        "firma_paciente",
        "firma_doctor",
        "firma_enfermero",
        "firma_menor",
        "firma_acudiente"
    ]

    os.makedirs("static/firmas", exist_ok=True)

    for campo in firmas:
        archivo = request.files.get(campo)
        if archivo and archivo.filename:
            nombre_img = f"{campo}_{datetime.now().strftime('%H%M%S')}.png"
            ruta_img = os.path.join("static/firmas", nombre_img)
            archivo.save(ruta_img)
            datos[campo] = InlineImage(doc, ruta_img, width=Mm(40))
        else:
            datos[campo] = ""
    print("PLANTILLA RECIBIDA:", datos["plantilla"])
    print("RUTA FINAL:", plantilla_path)
    print("EXISTE?:", os.path.exists(plantilla_path))

    # ==============================
    # GENERAR DOCX
    # ==============================
    doc.render(datos)

    os.makedirs("generated", exist_ok=True)
    nombre_archivo = f"consentimiento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    salida = os.path.join("generated", nombre_archivo)
    doc.save(salida)

    # ==============================
    # GUARDAR HISTORIAL EN BD
    # ==============================
    plantilla_id = datos.get("plantilla_id")
    db.execute("""
        INSERT INTO consentimientos (
            fecha,
            sede_id,
            paciente_id,
            doctor_id,
            enfermero_id,
            plantilla_usada,
            archivo_generado
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["fecha"],
        session["sede_id"],
        datos.get("paciente_id"),
        doctor_id if doctor_id else None,
        enfermero_id if enfermero_id else None,
        f"{plantilla_id} | {datos['plantilla']}",
        salida
    ))

    db.commit()
    db.close()

    return send_file(salida, as_attachment=True)



# LISTAR
@app.route("/personal")
def personal_lista():
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()
    data = db.execute("""
        SELECT * FROM personal
        WHERE sede_id = ?
        ORDER BY nombre
    """, (session["sede_id"],)).fetchall()
    db.close()

    return render_template("personal/lista.html", personal=data)


# AGREGAR PERSONAL
@app.route("/personal/agregar", methods=["GET", "POST"])
def personal_agregar():
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]
        cedula = request.form["cedula"]

        firma_archivo = request.files["firma"]
        nombre_firma = None

        if firma_archivo and firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nombre_firma = f"firma_{tipo}_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nombre_firma))

        db = get_db()
        db.execute("""
            INSERT INTO personal (nombre, tipo, cedula, firma, sede_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            nombre,
            tipo,
            cedula,
            nombre_firma,
            session["sede_id"]
        ))
        db.commit()
        db.close()

        return redirect(url_for("personal_lista"))

    return render_template("personal/agregar.html")


# EDITAR PERSONAL
@app.route("/personal/editar/<int:id>", methods=["GET", "POST"])
def personal_editar(id):
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()
    persona = db.execute(
        "SELECT * FROM personal WHERE id=?",
        (id,)
    ).fetchone()

    if not persona:
        db.close()
        abort(404)

    if persona["sede_id"] != session["sede_id"]:
        db.close()
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]
        cedula = request.form["cedula"]

        firma_archivo = request.files["firma"]
        nueva_firma = persona["firma"]

        if firma_archivo and firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nueva_firma = f"firma_{tipo}_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nueva_firma))

        db.execute("""
            UPDATE personal
            SET nombre=?, tipo=?, cedula=?, firma=?
            WHERE id=?
        """, (nombre, tipo, cedula, nueva_firma, id))

        db.commit()
        db.close()
        return redirect(url_for("personal_lista"))

    db.close()
    return render_template("personal/editar.html", persona=persona)


# ELIMINAR
@app.route("/personal/eliminar/<int:id>")
def personal_eliminar(id):
   
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()
    persona = db.execute(
        "SELECT * FROM personal WHERE id=?",
        (id,)
    ).fetchone()

    if not persona:
        db.close()
        abort(404)

    if persona["sede_id"] != session["sede_id"]:
        db.close()
        abort(403)

    db.execute("DELETE FROM personal WHERE id=?", (id,))
    db.commit()
    db.close()

    return redirect(url_for("personal_lista"))
# ============================
#   PACIENTES
# ============================

@app.route("/pacientes")
def pacientes_lista():
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()
    data = db.execute("SELECT * FROM pacientes ORDER BY nombre").fetchall()
    db.close()
    return render_template("pacientes/lista.html", pacientes=data)


@app.route("/pacientes/agregar", methods=["GET", "POST"])
def pacientes_agregar():
    if "usuario" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        lugar = request.form["lugar_expedicion"]
        tipo = request.form["tipo_documento"]
        fecha_nac = request.form["fecha_nacimiento"]

        # Procesar firma
        firma_archivo = request.files["firma"]
        nombre_firma = None
        if firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nombre_firma = f"firma_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nombre_firma))

        db = get_db()
        db.execute("""
            INSERT INTO pacientes (nombre, cedula, lugar_expedicion, firma, fecha_nacimiento, tipo_documento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, cedula, lugar, nombre_firma, tipo, fecha_nac))
        db.commit()
        db.close()

        return redirect(url_for("pacientes_lista"))

    return render_template("pacientes/agregar.html")


@app.route("/pacientes/editar/<int:id>", methods=["GET", "POST"])
def pacientes_editar(id):
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        lugar = request.form["lugar_expedicion"]
        tipo = request.form["tipo_documento"]
        fecha_nac = request.form["fecha_nacimiento"]

        firma_archivo = request.files["firma"]
        nombre_firma = None

        if firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nombre_firma = f"firma_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nombre_firma))

        if nombre_firma:
            db.execute("""
                UPDATE pacientes SET nombre=?, cedula=?, lugar_expedicion=?,  fecha_nacimiento=?, tipo_documento=?, firma=?
                WHERE id=?
            """, (nombre, cedula, lugar, fecha_nac, tipo, nombre_firma, id))
        else:
            db.execute("""
                UPDATE pacientes SET nombre=?, cedula=?, lugar_expedicion=?, fecha_nacimiento=?, tipo_documento=?
                WHERE id=?
            """, (nombre, cedula, lugar,  fecha_nac, tipo, id))

        db.commit()
        db.close()
        return redirect(url_for("pacientes_lista"))

    paciente = db.execute("SELECT * FROM pacientes WHERE id=?", (id,)).fetchone()
    db.close()

    return render_template("pacientes/editar.html", paciente=paciente)


@app.route("/pacientes/eliminar/<int:id>")
def pacientes_eliminar(id):
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")
    db = get_db()
    db.execute("DELETE FROM pacientes WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect(url_for("pacientes_lista"))


@app.route("/api/buscar_paciente")
def api_buscar_paciente():
    if "usuario" not in session:
        return redirect("/login")
    query = request.args.get("query", "").strip()

    if not query:
        return {"result": []}

    db = get_db()
    data = db.execute("""
        SELECT id, nombre, cedula, lugar_expedicion
        FROM pacientes
        WHERE nombre LIKE ? OR cedula LIKE ?
        ORDER BY nombre LIMIT 10
    """, (f"%{query}%", f"%{query}%")).fetchall()
    db.close()

    # Convertir a lista normal
    pacientes = [
        {
            "id": p["id"],
            "nombre": p["nombre"],
            "cedula": p["cedula"],
            "ciudad": p["lugar_expedicion"]
        }
        for p in data
    ]

    return {"result": pacientes}

@app.route("/api/plantillas_por_paquete/<int:paquete_id>")
def plantillas_por_paquete(paquete_id):
    if "usuario" not in session:
        return {"error": "unauthorized"}, 401

    db = get_db()
    plantillas = db.execute("""
        SELECT id, nombre, titulo, version
        FROM plantillas_consentimiento
        WHERE paquete_id = ?
        ORDER BY nombre
    """, (paquete_id,)).fetchall()
    db.close()

    return {
        "result": [
            {
                "id": p["id"],
                "nombre": p["nombre"],
                "titulo": p["titulo"],
                "version": p["version"]
            } for p in plantillas
        ]
    }

@app.route("/consentimientos/generar_pdf")
def generar_consentimiento_pdf():
    if "usuario" not in session:
        return redirect("/login")

    plantilla_id = request.args.get("plantilla_id")
    paciente_id = request.args.get("paciente_id")
    doctor_id = request.args.get("doctor_id")
    enfermero_id = request.args.get("enfermero_id")
    fecha = request.args.get("fecha")

    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")

    db = get_db()

    plantilla = db.execute("""
        SELECT * FROM plantillas_consentimiento WHERE id=?
    """, (plantilla_id,)).fetchone()

    paciente = db.execute("""
        SELECT * FROM pacientes WHERE id=?
    """, (paciente_id,)).fetchone()

    doctor = db.execute("""
        SELECT * FROM personal WHERE id=?
    """, (doctor_id,)).fetchone() if doctor_id else None

    enfermero = db.execute("""
        SELECT * FROM personal WHERE id=?
    """, (enfermero_id,)).fetchone() if enfermero_id else None

    sede = db.execute("""
        SELECT * FROM sedes WHERE id=?
    """, (session["sede_id"],)).fetchone()

    db.close()

    html = render_template(
        "consentimientos/pdf.html",
        plantilla=plantilla,
        paciente=paciente,
        doctor=doctor,
        enfermero=enfermero,
        sede=sede,
        fecha=fecha
    )

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=Consentimiento_{paciente['nombre']}.pdf"
    )

    return response
#MENOR DE EDAD 

@app.route("/menores")
def menores_lista():
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()
    data = db.execute("""
        SELECT m.*, p.nombre AS nombre_paciente
        FROM menores m
        JOIN pacientes p ON m.paciente_id = p.id
    """).fetchall()
    db.close()
    return render_template("menores/lista.html", menores=data)

@app.route("/menores/nuevo", methods=["GET", "POST"])
def menores_nuevo():
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()

    # Obtener lista de pacientes
    pacientes = db.execute("SELECT id, nombre FROM pacientes").fetchall()

    if request.method == "POST":
        paciente_id = request.form["paciente_id"]
        nombre_menor = request.form["nombre_menor"]
        cedula_menor = request.form["cedula_menor"]
        lugar_exp = request.form["lugar_expedicion_menor"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        firma_menor = request.form["firma_menor"]  # texto o ruta de archivo

        db.execute("""
            INSERT INTO menores (paciente_id, nombre_menor, cedula_menor, lugar_expedicion_menor, fecha_nacimiento, firma_menor)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (paciente_id, nombre_menor, cedula_menor, lugar_exp, fecha_nacimiento, firma_menor))

        db.commit()
        db.close()
        return redirect("/menores")

    db.close()
    return render_template("menores/nuevo.html", pacientes=pacientes)

@app.route("/acudientes")
def acudientes_lista():
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()
    data = db.execute("""
        SELECT a.*, p.nombre AS nombre_paciente
        FROM acudientes a
        JOIN pacientes p ON a.paciente_id = p.id
    """).fetchall()
    db.close()
    return render_template("acudientes/lista.html", acudientes=data)

@app.route("/acudientes/nuevo", methods=["GET", "POST"])
def acudientes_nuevo():
    if "usuario" not in session:
        return redirect("/login")
    db = get_db()

    # lista de pacientes
    pacientes = db.execute("SELECT id, nombre FROM pacientes").fetchall()

    if request.method == "POST":
        paciente_id = request.form["paciente_id"]
        nombre = request.form["nombre_acudiente"]
        cedula = request.form["cedula_acudiente"]
        lugar_exp = request.form["lugar_expedicion_acudiente"]
        parentesco = request.form["parentesco_acudiente"]
        firma = request.form["firma_acudiente"]

        db.execute("""
            INSERT INTO acudientes (paciente_id, nombre_acudiente, cedula_acudiente,
            lugar_expedicion_acudiente, parentesco_acudiente, firma_acudiente)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (paciente_id, nombre, cedula, lugar_exp, parentesco, firma))

        db.commit()
        db.close()
        return redirect("/acudientes")

    db.close()
    return render_template("acudientes/nuevo.html", pacientes=pacientes)

@app.route("/admin")
def admin():
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")
    return render_template("admin.html")

## LISTAR CONSENTIMIENTOS
@app.route("/consentimientos/lista")
def listar_consentimientos():
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()
    data = db.execute("""
        SELECT 
            c.id,
            c.fecha,
            c.plantilla_usada,
            c.archivo_generado,
            p.nombre AS paciente,
            d.nombre AS doctor
        FROM consentimientos c
        LEFT JOIN pacientes p ON c.paciente_id = p.id
        LEFT JOIN personal d ON c.doctor_id = d.id
        WHERE c.sede_id = ?
        ORDER BY c.fecha DESC
    """, (session["sede_id"],)).fetchall()
    db.close()

    return render_template("consentimientos/lista.html", consentimientos=data)

@app.route("/consentimientos/nuevo")
def nuevo_consentimiento():
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()

    doctores = db.execute("""
        SELECT * FROM personal
        WHERE tipo='doctor' AND sede_id=?
    """, (session["sede_id"],)).fetchall()

    enfermeros = db.execute("""
        SELECT * FROM personal
        WHERE tipo='enfermero' AND sede_id=?
    """, (session["sede_id"],)).fetchall()

    db.close()

    return render_template(
        "consentimientos/nuevo.html",
        doctores=doctores,
        enfermeros=enfermeros
    )
## crud PLANTILLAS DE CONSENTIMIENTOS
@app.route("/plantillas_consentimiento/nuevo", methods=["GET", "POST"])
def nueva_plantilla():
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()

    # Obtener los paquetes y sedes
    paquetes = db.execute("SELECT * FROM paquetes").fetchall()
    sedes = db.execute("SELECT * FROM sedes").fetchall()

    if request.method == "POST":
        # Recibir los datos del formulario
        nombre = request.form.get("nombre")
        version = request.form.get("version")
        fecha_version = request.form.get("fecha_version")
        contenido = request.form.get("contenido")
        paquete_id = request.form.get("paquete_id")
        sede_id = request.form.get("sede_id")
        titulo = request.form.get("titulo")


        # Insertar la nueva plantilla
        db.execute("""
            INSERT INTO plantillas_consentimiento (
                nombre, version, fecha_version, contenido, paquete_id, sede_id, created_at, titulo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, version, fecha_version, contenido, paquete_id, sede_id, datetime.now().strftime("%Y-%m-%d"), titulo))

        db.commit()
        db.close()
        if nombre == "":
            print("Plantilla no fue creada:", nombre)
        # return redirect("/plantillas_consentimiento/lista.html")

    db.close()

    return render_template(
        "/plantillas_consentimiento/nueva.html",
        paquetes=paquetes,
        sedes=sedes
    )
    ##LISTA DE PLANTILLAS DE CONSENTIMIENTOS
@app.route("/plantillas_consentimiento")
def listar_plantillas():
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()

    plantillas = db.execute("""
        SELECT 
            pc.id,
            pc.nombre,
            pc.titulo,
            pc.version,
            pc.fecha_version,
            pc.activo,
            p.nombre AS paquete,
            s.nombre AS sede
        FROM plantillas_consentimiento pc
        LEFT JOIN paquetes p ON pc.paquete_id = p.id
        LEFT JOIN sedes s ON pc.sede_id = s.id
        ORDER BY pc.created_at DESC
    """).fetchall()

    db.close()

    return render_template(
        "plantillas_consentimiento/lista.html",
        plantillas=plantillas
    )
    
    ## DESACTIVAR PLANTILLA
@app.route("/plantillas_consentimiento/desactivar/<int:id>")
def desactivar_plantilla(id):
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()
    db.execute("UPDATE plantillas_consentimiento SET activo=0 WHERE id=?", (id,))
    db.commit()
    db.close()

    return redirect("/plantillas_consentimiento")
## ACTIVAR PLANTILLA
@app.route("/plantillas_consentimiento/activar/<int:id>")
def activar_plantilla(id):
    
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/login")

    db = get_db()
    db.execute("UPDATE plantillas_consentimiento SET activo=1 WHERE id=?", (id,))
    db.commit()
    db.close()

    return redirect("/plantillas_consentimiento")

@app.route("/consentimientos/crear", methods=["POST"])
def crear_consentimiento():
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()

    # =========================
    # DATOS BÁSICOS
    # =========================
    paciente_id = request.form.get("paciente_id")
    doctor_id = request.form.get("doctor_id") or None
    enfermero_id = request.form.get("enfermero_id") or None
    tipo = request.form.get("tipo", "general")
    fecha = request.form.get("fecha") or datetime.now().strftime("%Y-%m-%d")

    # =========================
    # DATOS DEL FORMULARIO (JSON)
    # =========================
    datos = request.form.to_dict()
    datos.pop("firma_paciente", None)
    datos.pop("firma_doctor", None)
    datos.pop("firma_enfermero", None)
    datos.pop("firma_acudiente", None)

    datos_json = json.dumps(datos, ensure_ascii=False)

    fecha = request.form.get("fecha")

    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    # =========================
    # GUARDAR FIRMAS (base64)
    # =========================
    def guardar_firma(base64_data, nombre):
        if not base64_data:
            return None

        os.makedirs("static/firmas", exist_ok=True)

        contenido = base64_data.split(",")[1]
        binario = base64.b64decode(contenido)

        ruta = f"static/firmas/{nombre}_{datetime.now().strftime('%H%M%S')}.png"
        with open(ruta, "wb") as f:
            f.write(binario)

        return ruta

    firma_paciente = guardar_firma(
        request.form.get("firma_paciente"), "paciente"
    )
    firma_doctor = guardar_firma(
        request.form.get("firma_doctor"), "doctor"
    )
    firma_enfermero = guardar_firma(
        request.form.get("firma_enfermero"), "enfermero"
    )
    firma_acudiente = guardar_firma(
        request.form.get("firma_acudiente"), "acudiente"
    )

    # =========================
    # INSERTAR EN BD
    # =========================
    db.execute("""
        INSERT INTO consentimientos (
            fecha, sede_id, paciente_id,
            doctor_id, enfermero_id,
            tipo, datos,
            firma_paciente, firma_doctor,
            firma_enfermero, firma_acudiente
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fecha,
        session["sede_id"],
        paciente_id,
        doctor_id,
        enfermero_id,
        tipo,
        datos_json,
        firma_paciente,
        firma_doctor,
        firma_enfermero,
        firma_acudiente
    ))

    db.commit()
    db.close()

    return redirect("/consentimientos")


@app.route("/descargar/<int:id>")
def descargar_consentimiento(id):
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()
    consentimiento = db.execute("""
        SELECT * FROM consentimientos
        WHERE id=? AND sede_id=?
    """, (id, session["sede_id"])).fetchone()
    db.close()

    if not consentimiento:
        abort(403)

    return send_file(consentimiento["archivo_generado"], as_attachment=True)
## CRUD PAQUETES
@app.route("/   ")
def paquetes_lista():
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()
    paquetes = db.execute("""
        SELECT * FROM paquetes
        WHERE sede_id = ?
    """, (session["sede_id"],)).fetchall()
    db.close()

    return render_template("paquetes/lista.html", paquetes=paquetes)

@app.route("/paquetes/crear", methods=["GET", "POST"])
def paquetes_crear():
    
    if "usuario" not in session:
        return redirect("/login")

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]

        db = get_db()
        db.execute("""
            INSERT INTO paquetes (nombre, descripcion, sede_id)
            VALUES (?, ?, ?)
        """, (nombre, descripcion, session["sede_id"]))
        db.commit()
        db.close()

        return redirect("/paquetes")

    return render_template("paquetes/crear.html")
@app.route("/paquetes/editar/<int:id>", methods=["GET", "POST"])
def paquetes_editar(id):
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()

    paquete = db.execute("""
        SELECT * FROM paquetes
        WHERE id = ? AND sede_id = ?
    """, (id, session["sede_id"])).fetchone()

    if not paquete:
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        activo = 1 if request.form.get("activo") else 0

        db.execute("""
            UPDATE paquetes
            SET nombre=?, descripcion=?, activo=?
            WHERE id=?
        """, (nombre, descripcion, activo, id))
        db.commit()
        db.close()

        return redirect("/paquetes")

    db.close()
    return render_template("paquetes/editar.html", paquete=paquete)

##CRUD PLANTILLAS 
@app.route("/plantillas/<int:paquete_id>")
def plantillas_lista(paquete_id):
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()

    paquete = db.execute("""
        SELECT * FROM paquetes
        WHERE id=? AND sede_id=?
    """, (paquete_id, session["sede_id"])).fetchone()

    if not paquete:
        abort(403)

    plantillas = db.execute("""
        SELECT * FROM plantillas
        WHERE paquete_id=?
    """, (paquete_id,)).fetchall()

    db.close()

    return render_template(
        "plantillas/lista.html",
        paquete=paquete,
        plantillas=plantillas
    )
    
@app.route("/plantillas/crear/<int:paquete_id>", methods=["GET", "POST"])
def plantillas_crear(paquete_id):
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()

    paquete = db.execute("""
        SELECT * FROM paquetes
        WHERE id=? AND sede_id=?
    """, (paquete_id, session["sede_id"])).fetchone()

    if not paquete:
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        version = request.form["version"]
        tipo = request.form["tipo"]

        archivo = request.files["archivo"]
        if not archivo.filename.endswith(".docx"):
            return "Archivo inválido", 400

        os.makedirs("plantillas", exist_ok=True)
        nombre_archivo = f"{paquete_id}_{archivo.filename}"
        ruta = os.path.join("plantillas", nombre_archivo)
        archivo.save(ruta)

        db.execute("""
            INSERT INTO plantillas
            (nombre, archivo_docx, version, tipo, paquete_id)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, nombre_archivo, version, tipo, paquete_id))

        db.commit()
        db.close()

        return redirect(f"/plantillas/{paquete_id}")

    db.close()
    return render_template("plantillas/crear.html", paquete=paquete)

@app.route("/plantillas/editar/<int:id>", methods=["GET", "POST"])
def plantillas_editar(id):
    
    if "usuario" not in session:
        return redirect("/login")

    db = get_db()

    plantilla = db.execute("""
        SELECT p.*, pa.sede_id
        FROM plantillas p
        JOIN paquetes pa ON p.paquete_id = pa.id
        WHERE p.id=?
    """, (id,)).fetchone()

    if not plantilla or plantilla["sede_id"] != session["sede_id"]:
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        version = request.form["version"]
        tipo = request.form["tipo"]
        activo = 1 if request.form.get("activo") else 0

        db.execute("""
            UPDATE plantillas
            SET nombre=?, version=?, tipo=?, activo=?
            WHERE id=?
        """, (nombre, version, tipo, activo, id))
        db.commit()
        db.close()

        return redirect(f"/plantillas/{plantilla['paquete_id']}")

    db.close()
    return render_template("plantillas/editar.html", plantilla=plantilla)


if __name__ == "__main__":
    app.run(debug=True)
