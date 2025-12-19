
document.addEventListener("DOMContentLoaded", () => {
  const paqueteSelect = document.getElementById("paquete_id");
  const lista = document.getElementById("listaConsentimientos");

  if (!paqueteSelect || !lista) return;

  console.log("📦 Consentimientos JS activo");

  paqueteSelect.addEventListener("change", () => {
    const paqueteId = paqueteSelect.value;

    if (!paqueteId) {
      lista.innerHTML = `<p class="text-gray-500">Seleccione un paquete…</p>`;
      return;
    }

    lista.innerHTML = `<p class="text-gray-400">Cargando consentimientos…</p>`;

    fetch(`/api/plantillas_por_paquete/${paqueteId}`)
      .then(res => res.json())
      .then(data => {
        if (!data.result || data.result.length === 0) {
          lista.innerHTML = `<p class="text-gray-500">No hay consentimientos.</p>`;
          return;
        }

        let html = "";
        data.result.forEach(c => {
          html += `
            <div
              class="border rounded p-4 shadow hover:bg-blue-50 cursor-pointer"
              data-id="${c.id}"
            >
              <h5 class="font-semibold">${c.titulo}</h5>
              <p class="text-sm text-gray-600">${c.nombre}</p>
              <p class="text-xs text-gray-400">Versión ${c.version}</p>
            </div>
          `;
        });

        lista.innerHTML = html;
      })
      .catch(err => {
        console.error("❌ Error cargando consentimientos", err);
        lista.innerHTML = `<p class="text-red-500">Error al cargar</p>`;
      });
  });
});


(function () {
  const canvas = document.getElementById('firmaCanvas');
  const contenedor = document.getElementById('contenedorCanvas');
  const inputHidden = document.getElementById('inputFirmaData');

  // 🚨 CLAVE: si no existe, NO hacemos nada
  if (!canvas || !contenedor || !inputHidden) {
    console.log("✋ Firma no presente en esta vista");
    return;
  }

  const ctx = canvas.getContext('2d');
  let dibujando = false;

  function inicializarCanvas() {
    const rect = contenedor.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#000';
  }

  const observer = new ResizeObserver(() => inicializarCanvas());
  observer.observe(contenedor);

  const obtenerPos = (e) => {
    const rect = canvas.getBoundingClientRect();
    const p = e.touches ? e.touches[0] : e;
    return { x: p.clientX - rect.left, y: p.clientY - rect.top };
  };

  canvas.addEventListener('mousedown', e => {
    dibujando = true;
    const pos = obtenerPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  });

  canvas.addEventListener('mousemove', e => {
    if (!dibujando) return;
    const pos = obtenerPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  });

  window.addEventListener('mouseup', () => {
    if (dibujando) {
      dibujando = false;
      ctx.closePath();
      inputHidden.value = canvas.toDataURL();
    }
  });

})();
function generarConsentimiento(plantillaId) {
  const pacienteId = document.getElementById("paciente_id")?.value;
  const doctorId = document.getElementById("doctor_id")?.value;
  const enfermeroId = document.getElementById("enfermero_id")?.value;
  const fecha = document.getElementById("fecha_consentimiento")?.value;

  if (!pacienteId) {
    alert("Seleccione un paciente");
    return;
  }

  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/generar";

  const campos = {
    paciente_id: pacienteId,
    doctor_id: doctorId,
    enfermero_id: enfermeroId,
    fecha: fecha,
    plantilla_id: plantillaId
  };

  for (const k in campos) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = k;
    input.value = campos[k] || "";
    form.appendChild(input);
  }

  document.body.appendChild(form);
  form.submit();
}
