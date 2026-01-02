// static/js/submodules.js
(function () {
  const root = document.getElementById("submodulePage");
  if (!root) return;

  const oauthConnected = root.dataset.oauth === "1";
  const oauthUrl = root.dataset.oauthUrl || "/";

  const $ = (id) => document.getElementById(id);

  const selectedCard = $("selectedCard");
  const selectedMeta = $("selectedMeta");
  const selectedWarning = $("selectedWarning");
  const selectedWarningText = $("selectedWarningText");

  const deleteBtn = $("deleteBtn");
  const copyCdBtn = $("copyCdBtn");

  const reloadBtn = $("reloadBtn");
  const emptyState = $("emptyState");
  const subsTable = $("subsTable");
  const subsTbody = $("subsTbody");

  let selected = null;

  // ===========================
  // SWEETALERT THEME (Tailwind)
  // ===========================
  const SWAL_BASE_CLASS = {
popup: "rounded-3xl border-2 border-emerald-400 bg-zinc-950 text-zinc-100 shadow-2xl ring-4 ring-emerald-400/20 outline outline-2 outline-emerald-400/70 outline-offset-0",
  title: "text-xl md:text-2xl font-black text-white",
  htmlContainer: "text-sm text-zinc-300",
  confirmButton:
    "inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2 text-xs font-black text-slate-950 hover:bg-emerald-400",
  cancelButton:
    "inline-flex items-center justify-center rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-black text-zinc-100 hover:bg-slate-800",
  actions: "gap-2",
  icon: "border border-slate-700",
  input:
    "rounded-xl border border-slate-700 bg-slate-900 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/40",
};


  const swal = Swal.mixin({
  backdrop: "rgba(0,0,0,0.75)",
  buttonsStyling: false,
  customClass: SWAL_BASE_CLASS,
});


  const swalDanger = Swal.mixin({
  backdrop: "rgba(0,0,0,0.75)",
  buttonsStyling: false,
  customClass: {
    ...SWAL_BASE_CLASS,
    confirmButton:
      "inline-flex items-center justify-center rounded-xl bg-rose-500 px-4 py-2 text-xs font-black text-white hover:bg-rose-400",
  },
});



  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  async function apiGet(url) {
    const r = await fetch(url, { credentials: "same-origin" });
    return r.json();
  }

  async function apiPost(url, payload) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload || {}),
    });

    let data = {};
    try {
      data = await r.json();
    } catch (e) {
      if (!r.ok) throw new Error("Error de red / servidor reiniciando");
      return {};
    }
    if (!r.ok) throw new Error(data.error || "Error");
    return data;
  }

  function renderSelectedCard(sel) {
    selected = sel;

    if (!sel) {
      selectedCard.classList.add("hidden");
      selectedWarning.classList.add("hidden");
      return;
    }

    selectedCard.classList.remove("hidden");

    const repo = sel.repo_url
      ? `<a class="text-emerald-300 hover:underline" target="_blank" rel="noopener" href="${sel.repo_url}">
          ${sel.repo_url.replace("https://github.com/", "")}
        </a>`
      : `<span class="text-zinc-400">sin repo</span>`;

    selectedMeta.innerHTML = `
      <div class="mt-1 text-xs text-zinc-300">
        <div><b>Ruta local:</b> <code class="text-[11px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">${sel.local_path}</code></div>
        <div class="mt-1"><b>Domain/Subdomain:</b> <code class="text-[11px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">${sel.domain} / ${sel.subdomain}</code></div>
        <div class="mt-1"><b>Repo:</b> ${repo} <span class="ml-2 text-zinc-400">(branch: ${sel.repo_main_branch || "main"})</span></div>
      </div>
    `;

    if (sel.scaffold_warning) {
      selectedWarningText.textContent = sel.scaffold_warning;
      selectedWarning.classList.remove("hidden");
    } else {
      selectedWarning.classList.add("hidden");
    }
  }

  async function loadSelected() {
    const data = await apiGet("/api/workspace/selected");
    renderSelectedCard(data.selected || null);
  }

  function rowTemplate(s) {
    const repo = s.repo_url
      ? `<a class="text-emerald-300 hover:underline" target="_blank" rel="noopener" href="${s.repo_url}">
           ${s.repo_url.replace("https://github.com/", "")}
         </a>`
      : `<span class="text-zinc-500">Sin repo</span>`;

    const isSelectedRow =
      selected && selected.domain === s.domain && selected.subdomain === s.subdomain;

    let actionHtml = "";

    if (selected) {
      if (isSelectedRow) {
        actionHtml = `
          <button class="deleteRowBtn inline-flex items-center gap-2 rounded-xl border border-rose-500/50 bg-rose-500/10 px-3 py-2 text-xs font-black text-rose-200 hover:bg-rose-500/15"
                  data-domain="${s.domain}" data-subdomain="${s.subdomain}">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
            Eliminar
          </button>
        `;
      } else {
        actionHtml = `
          <button class="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-black text-zinc-400 cursor-not-allowed"
                  disabled>
            <i data-lucide="lock" class="w-4 h-4"></i>
            Bloqueado
          </button>
        `;
      }
    } else {
      actionHtml = `
        <button class="selectBtn inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-3 py-2 text-xs font-black text-slate-950 hover:bg-emerald-400"
                data-id="${s.id}">
          <i data-lucide="check" class="w-4 h-4"></i>
          Seleccionar
        </button>
      `;
    }

    return `
      <tr class="border-b border-slate-800 hover:bg-slate-900/60 align-top">
        <td class="py-3 pr-4">
          <div class="font-mono text-xs text-zinc-200">${s.domain} <span class="text-zinc-500">/</span> ${s.subdomain}</div>
        </td>
        <td class="py-3 pr-4">
          <div class="font-semibold text-zinc-50">${s.capability_name || "—"}</div>
        </td>
        <td class="py-3 pr-4 text-xs">${repo}</td>
        <td class="py-3 pr-4 whitespace-nowrap">${actionHtml}</td>
      </tr>
    `;
  }

  async function loadList() {
    subsTbody.innerHTML = "";
    subsTable.classList.add("hidden");
    emptyState.classList.remove("hidden");
    emptyState.textContent = "Cargando submódulos...";

    if (!oauthConnected) {
      emptyState.innerHTML = `
        <div class="flex items-start gap-3">
          <div class="mt-0.5">
            <i data-lucide="alert-triangle" class="w-5 h-5 text-amber-300"></i>
          </div>
          <div>
            <div class="font-black text-zinc-200">Conecta OAuth para ver tus submódulos</div>
            <div class="mt-1 text-xs text-zinc-400">Sin OAuth no podemos listar ni inicializar submódulos.</div>
            <a class="mt-3 inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-3 py-2 text-xs font-black text-slate-950 hover:bg-emerald-400"
               href="${oauthUrl}">
              <i data-lucide="log-in" class="w-4 h-4"></i> Conectar OAuth
            </a>
          </div>
        </div>
      `;
      if (window.lucide && typeof lucide.createIcons === "function") lucide.createIcons();
      return;
    }

    const data = await apiGet("/api/submodules/list");

    if (!data.ok) {
      emptyState.innerHTML = `❌ ${data.error || "No se pudo cargar la lista."}`;
      return;
    }

    const items = data.items || [];
    if (!items.length) {
      emptyState.textContent = "Aún no hay submódulos para mostrar.";
      return;
    }

    emptyState.classList.add("hidden");
    subsTable.classList.remove("hidden");
    subsTbody.innerHTML = items.map(rowTemplate).join("");

    if (window.lucide && typeof lucide.createIcons === "function") lucide.createIcons();

    // Seleccionar
    document.querySelectorAll(".selectBtn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (selected) {
          await swal.fire({
            icon: "warning",
            title: "Ya hay un submódulo seleccionado",
            html: `
              <div class="text-left">
                <div>Este bundle solo puede trabajar con <b>1 submódulo</b>.</div>
                <div class="mt-2">Primero elimina el workspace actual para elegir otro.</div>
              </div>
            `,
            confirmButtonText: "OK",
          });
          return;
        }

        const sid = btn.getAttribute("data-id");

        const res = await swal.fire({
          icon: "question",
          title: "Confirmar selección",
          html: `
            <div class="text-left">
              <div>Se creará el workspace para el submódulo <b>#${sid}</b>.</div>
              <div class="mt-2 text-xs text-zinc-400">
                Regla: <b class="text-zinc-200">1 submódulo por bundle</b> (se bloqueará el resto hasta eliminarlo).
              </div>
              <div class="mt-2 text-xs text-zinc-400">
                Esto genera carpetas dentro de
                <code class="text-[11px] bg-slate-900 px-1 rounded border border-slate-800">modules/</code>.
              </div>
            </div>
          `,
          showCancelButton: true,
          confirmButtonText: "Sí, crear workspace",
          cancelButtonText: "Cancelar",
        });

        if (!res.isConfirmed) return;

        // loading modal (oscuro + borde visible, sin azul)
        swal.fire({
          title: "Creando workspace…",
          html: `<div class="text-sm text-zinc-300">Generando carpetas y scaffold. No cierres esta pestaña.</div>`,
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => Swal.showLoading(),
        });

        try {
          const initData = await apiGet(`/api/submodules/${sid}/init`);
          if (!initData.ok) throw new Error(initData.error || "No se pudo obtener payload");

          const out = await apiPost("/api/workspace/init", initData.payload);

          await loadSelected();
          await loadList();

          await swal.fire({
            icon: "success",
            title: "Workspace creado",
            html: `<div class="text-sm text-zinc-300">Listo. Ya puedes abrir tu editor y empezar a trabajar.</div>`,
            confirmButtonText: "OK",
          });
        } catch (e) {
          // workaround simple: a veces fetch falla pero ya creó
          await sleep(1200);
          try {
            await loadSelected();
            if (selected) {
              await loadList();
              await swal.fire({
                icon: "success",
                title: "Workspace creado",
                html: `
                  <div class="text-left text-sm text-zinc-300">
                    <div>El servidor se reinició durante el proceso, pero el workspace <b>sí quedó creado</b>.</div>
                    <div class="mt-2">Ya quedó seleccionado y la lista se bloqueó como corresponde.</div>
                  </div>
                `,
                confirmButtonText: "OK",
              });
              return;
            }
          } catch (_) {}

          await swal.fire({
            icon: "error",
            title: "No se pudo crear",
            html: `<div class="text-sm text-zinc-300">${(e && e.message) ? e.message : "Error"}</div>`,
            confirmButtonText: "OK",
          });
        }
      });
    });

    // Eliminar desde fila (solo para el seleccionado)
    document.querySelectorAll(".deleteRowBtn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await triggerDelete();
      });
    });
  }

  async function triggerDelete() {
    if (!selected) return;

    const res = await swalDanger.fire({
      icon: "warning",
      title: "Eliminar workspace local",
      html: `
        <div class="text-left text-sm">
          <div>Se eliminará la carpeta:</div>
          <div class="mt-2">
            <code class="text-[11px] bg-slate-900 px-2 py-1 rounded border border-slate-800">${selected.local_path}</code>
          </div>
          <div class="mt-3 text-rose-300 font-black">Esto no se puede deshacer.</div>
          <div class="mt-2 text-xs text-zinc-400">Luego podrás seleccionar otro submódulo.</div>
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",

    });

    if (!res.isConfirmed) return;

    try {
      await apiPost("/api/workspace/delete", {});
      renderSelectedCard(null);
      await loadList();

      await swal.fire({
        icon: "success",
        title: "Eliminado",
        html: `<div class="text-sm text-zinc-300">Listo. Ya puedes seleccionar otro submódulo.</div>`,
        confirmButtonText: "OK",
      });
    } catch (e) {
      await swal.fire({
        icon: "error",
        title: "No se pudo eliminar",
        html: `<div class="text-sm text-zinc-300">${e.message}</div>`,
        confirmButtonText: "OK",
      });
    }
  }

  // Delete selected
  deleteBtn?.addEventListener("click", triggerDelete);

  // Reload
  reloadBtn?.addEventListener("click", async () => {
    await loadSelected();
    await loadList();
  });

  // Init
  (async function () {
    await loadSelected();
    await loadList();
    if (window.lucide && typeof lucide.createIcons === "function") lucide.createIcons();
  })();
})();
