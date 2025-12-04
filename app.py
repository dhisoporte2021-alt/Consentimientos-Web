from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
import sqlite3
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from docxtpl import DocxTemplate
import pandas as pd
import os
from datetime import datetime
from database import get_db

app = Flask(__name__)

PLANTILLAS_DIR = os.path.join(os.getcwd(), "plantillas")

# print("Ruta de plantillas:", PLANTILLAS_DIR)
# if os.path.exists(PLANTILLAS_DIR):
#     print("Archivos encontrados:", os.listdir(PLANTILLAS_DIR))
# else:
#     print("La carpeta de plantillas NO existe")


# Cargar doctores y enfermeros desde Excel
def cargar_personal():
    db = get_db()
    data = db.execute("SELECT * FROM personal").fetchall()
    db.close()

    medicos = [p for p in data if p["tipo"] == "doctor"]
    enfermeros = [p for p in data if p["tipo"] == "enfermero"]

    return medicos, enfermeros


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/consentimientos")
def consentimientos():
    return render_template("consentimientos.html")

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
    datos = request.form.to_dict()

    # Fecha si está vacía
    if not datos.get("fecha"):
        datos["fecha"] = datetime.now().strftime("%Y-%m-%d")

    # ==============================
    # Cargar plantilla DOCX
    # ==============================
    plantilla_path = os.path.join("plantillas", datos["plantilla"])
    doc = DocxTemplate(plantilla_path)

    # ==============================
    # CARGAR DOCTOR DESDE DB
    # ==============================
    db = get_db()

    doctor_id = datos.get("doctor_id")
    if doctor_id and doctor_id != "":
        doctor = db.execute(
            "SELECT * FROM personal WHERE id=? AND tipo='doctor'",
            (doctor_id,)
        ).fetchone()

        if doctor:
            datos["doctor"] = doctor["nombre"]
            datos["cedula_doctor"] = doctor.get("cedula", "")
        else:
            datos["doctor"] = ""
            datos["cedula_doctor"] = ""
    else:
        datos["doctor"] = ""
        datos["cedula_doctor"] = ""

    # ==============================
    # CARGAR ENFERMERO DESDE DB
    # ==============================
    enfermero_id = datos.get("enfermero_id")
    if enfermero_id and enfermero_id != "":
        enf = db.execute(
            "SELECT * FROM personal WHERE id=? AND tipo='enfermero'",
            (enfermero_id,)
        ).fetchone()

        if enf:
            datos["enfermero"] = enf["nombre"]
            datos["cedula_enfermero"] = enf.get("cedula", "")
        else:
            datos["enfermero"] = ""
            datos["cedula_enfermero"] = ""
    else:
        datos["enfermero"] = ""
        datos["cedula_enfermero"] = ""

    db.close()

    # ==============================
    # PROCESAR FIRMAS SUBIDAS
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

        if archivo and archivo.filename != "":
            nombre_img = f"{campo}_{datetime.now().strftime('%H%M%S')}.png"
            ruta_img = os.path.join("static/firmas", nombre_img)
            archivo.save(ruta_img)

            datos[campo] = InlineImage(doc, ruta_img, width=Mm(40))
        else:
            datos[campo] = ""

    # ==============================
    # RENDERIZAR WORD
    # ==============================
    doc.render(datos)

    # ==============================
    # GUARDAR ARCHIVO
    # ==============================
    nombre_archivo = f"consentimiento_{datos.get('paciente', 'documento')}_{datetime.now().strftime('%H%M%S')}.docx"
    salida = os.path.join("generated", nombre_archivo)

    os.makedirs("generated", exist_ok=True)
    doc.save(salida)

    return send_file(salida, as_attachment=True)


# LISTAR
@app.route("/personal")
def personal_lista():
    db = get_db()
    data = db.execute("SELECT * FROM personal ORDER BY nombre").fetchall()
    db.close()
    return render_template("personal/lista.html", personal=data)


# AGREGAR PERSONAL
@app.route("/personal/agregar", methods=["GET", "POST"])
def personal_agregar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]
        cedula = request.form["cedula"]

        firma_archivo = request.files["firma"]
        nombre_firma = None

        if firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nombre_firma = f"firma_{tipo}_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nombre_firma))

        db = get_db()
        db.execute("""
            INSERT INTO personal (nombre, tipo, cedula, firma)
            VALUES (?, ?, ?, ?)
        """, (nombre, tipo, cedula, nombre_firma))
        db.commit()
        db.close()

        return redirect(url_for("personal_lista"))

    return render_template("personal/agregar.html")


# EDITAR PERSONAL
@app.route("/personal/editar/<int:id>", methods=["GET", "POST"])
def personal_editar(id):
    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]
        cedula = request.form["cedula"]

        firma_archivo = request.files["firma"]
        nueva_firma = None

        if firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nueva_firma = f"firma_{tipo}_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nueva_firma))

        if nueva_firma:
            db.execute("""
                UPDATE personal SET nombre=?, tipo=?, cedula=?, firma=? WHERE id=?
            """, (nombre, tipo, cedula, nueva_firma, id))
        else:
            db.execute("""
                UPDATE personal SET nombre=?, tipo=?, cedula=? WHERE id=?
            """, (nombre, tipo, cedula, id))

        db.commit()
        db.close()

        return redirect(url_for("personal_lista"))

    persona = db.execute("SELECT * FROM personal WHERE id=?", (id,)).fetchone()
    db.close()

    return render_template("personal/editar.html", persona=persona)


# ELIMINAR
@app.route("/personal/eliminar/<int:id>")
def personal_eliminar(id):
    db = get_db()
    db.execute("DELETE FROM personal WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect(url_for("personal_lista"))


# ============================
#   PACIENTES
# ============================

@app.route("/pacientes")
def pacientes_lista():
    db = get_db()
    data = db.execute("SELECT * FROM pacientes ORDER BY nombre").fetchall()
    db.close()
    return render_template("pacientes/lista.html", pacientes=data)


@app.route("/pacientes/agregar", methods=["GET", "POST"])
def pacientes_agregar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        lugar = request.form["lugar_expedicion"]
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
            INSERT INTO pacientes (nombre, cedula, lugar_expedicion, firma, fecha_nacimiento)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, cedula, lugar, nombre_firma, fecha_nac))
        db.commit()
        db.close()

        return redirect(url_for("pacientes_lista"))

    return render_template("pacientes/agregar.html")


@app.route("/pacientes/editar/<int:id>", methods=["GET", "POST"])
def pacientes_editar(id):
    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        lugar = request.form["lugar_expedicion"]
        fecha_nac = request.form["fecha_nacimiento"]

        firma_archivo = request.files["firma"]
        nombre_firma = None

        if firma_archivo.filename:
            os.makedirs("firmas", exist_ok=True)
            nombre_firma = f"firma_{cedula}.png"
            firma_archivo.save(os.path.join("firmas", nombre_firma))

        if nombre_firma:
            db.execute("""
                UPDATE pacientes SET nombre=?, cedula=?, lugar_expedicion=?, fecha_nacimiento=?, firma=?
                WHERE id=?
            """, (nombre, cedula, lugar, fecha_nac, nombre_firma, id))
        else:
            db.execute("""
                UPDATE pacientes SET nombre=?, cedula=?, lugar_expedicion=?, fecha_nacimiento=?
                WHERE id=?
            """, (nombre, cedula, lugar, fecha_nac, id))

        db.commit()
        db.close()
        return redirect(url_for("pacientes_lista"))

    paciente = db.execute("SELECT * FROM pacientes WHERE id=?", (id,)).fetchone()
    db.close()

    return render_template("pacientes/editar.html", paciente=paciente)


@app.route("/pacientes/eliminar/<int:id>")
def pacientes_eliminar(id):
    db = get_db()
    db.execute("DELETE FROM pacientes WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect(url_for("pacientes_lista"))

@app.route("/buscar_pacientes")
def buscar_pacientes():
    termino = request.args.get("q", "").strip()

    # Si no escriben nada → no devuelve nada para evitar recargar todo
    if termino == "":
        return jsonify([])

    conn = sqlite3.connect("mi_base.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre, tipo_documento, documento, ciudad_expedicion
        FROM pacientes
        WHERE documento LIKE ? OR nombre LIKE ?
        ORDER BY nombre ASC
        LIMIT 20
    """, (f"%{termino}%", f"%{termino}%"))

    resultados = [dict(row) for row in cur.fetchall()]

    return jsonify(resultados)

#MENOR DE EDAD 

@app.route("/menores")
def menores_lista():
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
    return render_template("admin.html")


if __name__ == "__main__":
    app.run(debug=True)
