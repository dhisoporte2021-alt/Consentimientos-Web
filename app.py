from flask import Flask, render_template, request, send_file, redirect, url_for
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

    # Carga plantilla
    plantilla_path = os.path.join("plantillas", datos["plantilla"])
    doc = DocxTemplate(plantilla_path)

    # Lista EXACTA de variables que existen en tus plantillas
    firmas = [
        "firma_paciente",
        "firma_doctor",
        "firma_enfermero",
        "firma_menor",
        "firma_acudiente"
    ]

    # Crear carpeta donde guardar las imágenes
    os.makedirs("static/firmas", exist_ok=True)

    for campo in firmas:
        archivo = request.files.get(campo)

        if archivo and archivo.filename != "":
            # Guardar imagen
            nombre_img = f"{campo}_{datetime.now().strftime('%H%M%S')}.png"
            ruta_img = os.path.join("static/firmas", nombre_img)
            archivo.save(ruta_img)

            # Convertir a imagen insertable en Word
            datos[campo] = InlineImage(doc, ruta_img, width=Mm(40))
        else:
            # Si no se sube la firma → queda vacío
            datos[campo] = ""

    # Render de la plantilla
    doc.render(datos)

    # Guardar archivo final
    nombre_archivo = f"consentimiento_{datos['paciente']}_{datetime.now().strftime('%H%M%S')}.docx"
    salida = os.path.join("generated", nombre_archivo)

    os.makedirs("generated", exist_ok=True)
    doc.save(salida)

    return send_file(salida, as_attachment=True)

# LISTAR
@app.route("/personal")
def personal_lista():
    db = get_db()
    data = db.execute("SELECT * FROM personal").fetchall()
    db.close()
    return render_template("personal/lista.html", personal=data)

# AGREGAR
@app.route("/personal/agregar", methods=["GET", "POST"])
def personal_agregar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]

        db = get_db()
        db.execute("INSERT INTO personal (nombre, tipo) VALUES (?, ?)", (nombre, tipo))
        db.commit()
        db.close()
        return redirect(url_for("personal_lista"))

    return render_template("personal/agregar.html")

# EDITAR
@app.route("/personal/editar/<int:id>", methods=["GET", "POST"])
def personal_editar(id):
    db = get_db()
    if request.method == "POST":
        nombre = request.form["nombre"]
        tipo = request.form["tipo"]

        db.execute("UPDATE personal SET nombre=?, tipo=? WHERE id=?", (nombre, tipo, id))
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


if __name__ == "__main__":
    app.run(debug=True)
