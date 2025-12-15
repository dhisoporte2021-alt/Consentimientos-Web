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

document.addEventListener('DOMContentLoaded', function() {
      const button = document.getElementById('user-menu-button');
      const menu = document.getElementById('user-menu');

        // Función para alternar la visibilidad
        function toggleMenu() {
            if (menu.style.display === 'none' || menu.style.display === '') {
                menu.style.display = 'block';
            } else {
                menu.style.display = 'none';
            }
        }

        // 1. Mostrar/Ocultar al hacer clic en el botón
        button.addEventListener('click', toggleMenu);

        // 2. Ocultar el menú al hacer clic fuera de él
        document.addEventListener('click', function(event) {
            const container = document.getElementById('user-menu-container');
            if (container && !container.contains(event.target) && menu.style.display === 'block') {
                menu.style.display = 'none';
            }
      });
  });
