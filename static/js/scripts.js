console.log("scripts.js de niuevo");

let timer = null;

document.getElementById("buscarInput")?.addEventListener("input", function () {
  clearTimeout(timer);

  timer = setTimeout(() => {
    let q = this.value.trim();
    let cont = document.getElementById("resultados");

    if (q.length === 0) {
      cont.innerHTML = "";
      cont.classList.add("hidden");
      return;
    }

    fetch(`/api/buscar_paciente?query=${q}`)
      .then((res) => res.json())
      .then((data) => {
        let pacientes = data.result;

        if (!pacientes || pacientes.length === 0) {
          cont.innerHTML = `<div class="p-3 text-gray-500">Sin resultados...</div>`;
          cont.classList.remove("hidden");
          return;
        }

        let html = "";
        pacientes.forEach((p) => {
          html += `
            <div class="p-3 border-b hover:bg-blue-50 cursor-pointer"
                 onclick="seleccionarPaciente(${p.id}, '${p.nombre}', '${p.cedula}', '${p.ciudad}')">
              <strong>${p.nombre}</strong><br>
              <span class="text-sm text-gray-600">CC: ${p.cedula}</span>
            </div>
          `;
        });

        cont.innerHTML = html;
        cont.classList.remove("hidden");
      });
  }, 300);
});

function seleccionarPaciente(id, nombre, tipoDoc, documento, ciudad) {
  document.getElementById("paciente_id").value = id;

  document.getElementById("pacienteNombre").textContent = nombre;
  document.getElementById("pacienteDocumento").textContent = documento;
  document.getElementById("pacienteCiudad").textContent = ciudad;

  document.getElementById("modalPaciente").classList.remove("hidden");
  document.getElementById("resultados").classList.add("hidden");
}

function abrirModalPaciente(id, nombre, documento, ciudad) {
  document.getElementById("pacienteNombre").textContent = nombre;
  document.getElementById("pacienteDocumento").textContent = documento;
  document.getElementById("pacienteCiudad").textContent = ciudad;

  // 🔥 CLAVE PARA GUARDAR CONSENTIMIENTO
  document.getElementById("paciente_id").value = id;

  document.getElementById("modalPaciente").classList.remove("hidden");
}

document.addEventListener('DOMContentLoaded', function () {
  const button = document.getElementById('user-menu-button');
  const menu = document.getElementById('user-menu');
  const container = document.getElementById('user-menu-container');

  // 🔒 Si no existe en esta vista, salimos sin romper nada
  if (!button || !menu || !container) return;

  function toggleMenu() {
    menu.style.display =
      menu.style.display === 'block' ? 'none' : 'block';
  }

  // Mostrar / ocultar
  button.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  // Ocultar al hacer click fuera
  document.addEventListener('click', function (event) {
    if (!container.contains(event.target)) {
      menu.style.display = 'none';
    }
  });
});


   document.addEventListener('DOMContentLoaded', function () {
  const button = document.getElementById('user-menu-button');
  const menu = document.getElementById('user-menu');
  const container = document.getElementById('user-menu-container');

  // 🔒 Si no existe en esta vista, salimos sin romper nada
  if (!button || !menu || !container) return;

  function toggleMenu() {
    menu.style.display =
      menu.style.display === 'block' ? 'none' : 'block';
  }

  // Mostrar / ocultar
  button.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  // Ocultar al hacer click fuera
  document.addEventListener('click', function (event) {
    if (!container.contains(event.target)) {
      menu.style.display = 'none';
    }
  });
});


  function seleccionarPaciente(id, nombre, cedula, ciudad) {
  document.getElementById("p_nombre").innerText = nombre;
  document.getElementById("p_cedula").innerText = cedula;
  document.getElementById("p_ciudad").innerText = ciudad;

  document.getElementById("paciente_id").value = id;

  document.getElementById("resultados").classList.add("hidden");
  document.getElementById("buscarInput").value = nombre;

  document.getElementById("bloquePaciente").classList.remove("hidden");
}
const canvas = document.getElementById("firmaCanvas");
const ctx = canvas.getContext("2d");
let dibujando = false;

canvas.addEventListener("mousedown", () => dibujando = true);
canvas.addEventListener("mouseup", () => dibujando = false);
canvas.addEventListener("mousemove", dibujar);

function dibujar(e) {
  if (!dibujando) return;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#000";
  ctx.lineTo(e.offsetX, e.offsetY);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(e.offsetX, e.offsetY);
}

function limpiarFirma() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// document.getElementById("paquete_id").addEventListener("change", function () {
//   let paqueteId = this.value;
//   let cont = document.getElementById("listaConsentimientos");

//   if (!paqueteId) {
//     cont.innerHTML = `<p class="text-gray-500">Seleccione un paquete…</p>`;
//     return;
//   }

//   fetch(`/api/plantillas_por_paquete/${paqueteId}`)
//     .then(res => res.json())
//     .then(data => {
//       if (!data.result || data.result.length === 0) {
//         cont.innerHTML = `<p class="text-gray-500">No hay consentimientos.</p>`;
//         return;
//       }

//       let html = "";
//       data.result.forEach(c => {
//         html += `
//           <div class="border rounded p-4 hover:bg-blue-50 cursor-pointer"
//                onclick="generarConsentimiento(${c.id})">
//             <h5 class="font-semibold">${c.titulo}</h5>
//             <p class="text-sm text-gray-600">${c.nombre}</p>
//             <p class="text-xs text-gray-400">Versión ${c.version}</p>
//           </div>
//         `;
//       });

//       cont.innerHTML = html;
//     });
// });


// document.querySelector('select[name="paquete_id"]')
//   addEventListener("change", function () {

//     const paqueteId = this.value;
//     const contenedor = document.getElementById("opcionesConsentimientos");
//     const lista = document.getElementById("listaConsentimientos");

//     lista.innerHTML = "";
//     contenedor.classList.add("hidden");

//     if (!paqueteId) return;

//     fetch(`/api/plantillas_por_paquete/${paqueteId}`)
//       .then(res => res.json())
//       .then(data => {

//         if (!data.plantillas.length) {
//           lista.innerHTML = `
//             <div class="text-gray-500">
//               No hay consentimientos para este paquete
//             </div>
//           `;
//         } else {
//           data.plantillas.forEach(p => {
//             lista.innerHTML += `
//               <button
//                 onclick="generarConsentimiento(${p.id})"
//                 class="border rounded p-4 hover:bg-blue-50 text-left"
//               >
//                 <h3 class="font-semibold">${p.titulo}</h3>
//                 <p class="text-sm text-gray-600">${p.nombre}</p>
//               </button>
//             `;
//           });
//         }

//         contenedor.classList.remove("hidden");
//       });
// });

function generarConsentimiento(plantillaId) {
  const form = document.querySelector("form");

  const input = document.createElement("input");
  input.type = "hidden";
  input.name = "plantilla_id";
  input.value = plantillaId;

  form.appendChild(input);
  form.action = "/generar";
  form.submit();
}
// document.addEventListener("DOMContentLoaded", function () {
//   const paqueteSelect = document.getElementById("paquete_id");
//   const cont = document.getElementById("listaConsentimientos");

//   if (!paqueteSelect || !cont) return;

//   paqueteSelect.addEventListener("change", function () {
//     const paqueteId = this.value;

//     if (!paqueteId) {
//       cont.innerHTML = `<p class="text-gray-500">Seleccione un paquete…</p>`;
//       return;
//     }

//     fetch(`/api/plantillas_por_paquete/${paqueteId}`)
//       .then(res => res.json())
//       .then(data => {
//         if (!data.result || data.result.length === 0) {
//           cont.innerHTML = `<p class="text-gray-500">No hay consentimientos.</p>`;
//           return;
//         }

//         let html = "";
//         data.result.forEach(c => {
//           html += `
//             <div class="border rounded p-4 hover:bg-blue-50 cursor-pointer"
//                  onclick="generarConsentimiento(${c.id})">
//               <h5 class="font-semibold">${c.titulo}</h5>
//               <p class="text-sm text-gray-600">${c.nombre}</p>
//               <p class="text-xs text-gray-400">Versión ${c.version}</p>
//             </div>
//           `;
//         });

//         cont.innerHTML = html;
//       });
//   });
// });
document.addEventListener('DOMContentLoaded', function () {

  // ===== MENU USUARIO =====
  const button = document.getElementById('user-menu-button');
  const menu = document.getElementById('user-menu');
  const container = document.getElementById('user-menu-container');

  if (button && menu) {
    button.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', function (event) {
      if (container && !container.contains(event.target)) {
        menu.style.display = 'none';
      }
    });
  }

  // ===== FLATPICKR =====
  if (document.getElementById("fecha_nacimiento_flatpickr")) {
    flatpickr("#fecha_nacimiento_flatpickr", {
      dateFormat: "Y-m-d",
    });
  }

  // ===== FIRMA =====
  const canvas = document.getElementById("firmaCanvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    let dibujando = false;

    canvas.addEventListener("mousedown", () => dibujando = true);
    canvas.addEventListener("mouseup", () => dibujando = false);
    canvas.addEventListener("mousemove", function (e) {
      if (!dibujando) return;
      ctx.lineTo(e.offsetX, e.offsetY);
      ctx.stroke();
    });
  }

});
