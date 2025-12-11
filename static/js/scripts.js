let timer = null;

document.getElementById("buscarInput")?.addEventListener("input", function () {
    clearTimeout(timer);

    timer = setTimeout(() => {
        let q = this.value.trim();

        if (q.length === 0) {
            document.getElementById("resultados").innerHTML = "";
            document.getElementById("resultados").classList.add("hidden");
            return;
        }

        fetch(`/buscar_pacientes?q=${q}`)
            .then(res => res.json())
            .then(data => {
                let cont = document.getElementById("resultados");

                if (data.length === 0) {
                    cont.innerHTML = `<div class="p-3 text-gray-500">Sin resultados...</div>`;
                    cont.classList.remove("hidden");
                    return;
                }

                let html = "";
                data.forEach(p => {
                    html += `
                        <div class="p-3 border-b hover:bg-blue-50 cursor-pointer"
                             onclick="seleccionarPaciente(${p.id}, '${p.nombre}', '${p.tipo_documento}', '${p.cedula}', '${p.lugar_expedicion}')">
                            <strong>${p.nombre}</strong><br>
                            <span class="text-sm text-gray-600">${p.tipo_documento}: ${p.cedula}</span>
                        </div>
                    `;
                });

                cont.innerHTML = html;
                cont.classList.remove("hidden");
            });

    }, 300);
});

function seleccionarPaciente(id, nombre, tipoDoc, documento, ciudad) {
    console.log("PACIENTE SELECCIONADO → ID:", id);
    abrirModalPaciente(id, nombre, tipoDoc, documento, ciudad);
}
function abrirModalPaciente(id, nombre, tipo, documento, ciudad) {
  document.getElementById("pacienteNombre").textContent = nombre;
  document.getElementById("pacienteTipo").textContent = tipo;
  document.getElementById("pacienteDocumento").textContent = documento;
  document.getElementById("pacienteCiudad").textContent = ciudad;
  document.getElementById("modalPaciente").classList.remove("hidden");
}

function abrirModalFirma() {
  document.getElementById("modalPaciente").classList.add("hidden");
  document.getElementById("modalFirma").classList.remove("hidden");
}

function cerrarModal(id) {
  document.getElementById(id).classList.add("hidden");
}

// Firma con Canvas
let canvas = document.getElementById("canvasFirma");
let ctx = canvas.getContext("2d");
let firmando = false;

canvas.addEventListener("mousedown", () => firmando = true);
canvas.addEventListener("mouseup", () => firmando = false);
canvas.addEventListener("mousemove", dibujar);

function dibujar(e) {
  if (!firmando) return;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.strokeStyle = "black";
  ctx.lineTo(e.offsetX, e.offsetY);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(e.offsetX, e.offsetY);
}

function limpiarFirma() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
}

function guardarFirma() {
  let firma = canvas.toDataURL("image/png");
  console.log("Firma guardada en base64:", firma.substring(0, 50) + "...");
  cerrarModal("modalFirma");
}

document.getElementById("menor_checkbox").addEventListener("change", function() {
    let container = document.getElementById("menor_container");
    container.classList.toggle("hidden", !this.checked);
});

