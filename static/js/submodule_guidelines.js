(function () {
  const GROUP_KEY = "bundle_guidelines_open_group";

  function lucideRefresh() {
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
  }

  function openGroup(groupId) {
    document.querySelectorAll(".guidelineGroup").forEach(g => {
      const isTarget = g.dataset.group === groupId;
      const collapsed = g.querySelector(".groupCollapsedView");
      const openv = g.querySelector(".groupOpenView");
      const items = g.querySelector(".groupItems");

      if (!collapsed || !openv || !items) return;

      if (isTarget) {
        g.dataset.open = "1";
        g.classList.add("col-span-2");
        collapsed.classList.add("hidden");
        openv.classList.remove("hidden");
        openv.classList.add("flex");
        items.classList.remove("hidden");
      } else {
        g.dataset.open = "0";
        g.classList.remove("col-span-2");
        collapsed.classList.remove("hidden");
        openv.classList.add("hidden");
        openv.classList.remove("flex");
        items.classList.add("hidden");
      }
    });

    localStorage.setItem(GROUP_KEY, groupId || "");
    lucideRefresh();
  }

  function toggleGroup(groupId) {
    const g = document.querySelector(`.guidelineGroup[data-group="${groupId}"]`);
    if (!g) return;

    const isOpen = g.dataset.open === "1";
    if (isOpen) {
      // cerrar todos
      openGroup("");
      localStorage.removeItem(GROUP_KEY);
    } else {
      openGroup(groupId);
    }
  }

  function setActive(id) {
    // detail
    document.querySelectorAll(".guidelineDetail").forEach(el => el.classList.add("hidden"));
    const detail = document.getElementById(`detail-${id}`);
    if (detail) detail.classList.remove("hidden");

    // left buttons
    document.querySelectorAll(".guidelineBtn").forEach(btn => {
      const isActive = btn.dataset.guideline === id;
      btn.classList.toggle("bg-emerald-500/10", isActive);
      btn.classList.toggle("border-emerald-500/30", isActive);
      btn.classList.toggle("text-emerald-200", isActive);
      btn.classList.toggle("text-zinc-200", !isActive);
    });

    // abrir grupo del item seleccionado (solo 1 abierto)
    const btn = document.querySelector(`.guidelineBtn[data-guideline="${id}"]`);
    if (btn && btn.dataset.group) openGroup(btn.dataset.group);

    // sync mobile select
    const sel = document.getElementById("guidelinesSelect");
    if (sel && sel.value !== id) sel.value = id;

    if (location.hash !== `#${id}`) {
      history.replaceState(null, "", `#${id}`);
    }

    lucideRefresh();
  }

  function getInitialId() {
    const hash = (location.hash || "").replace("#", "").trim();
    if (hash) return hash;

    const firstDetail = document.querySelector(".guidelineDetail");
    if (firstDetail && firstDetail.id && firstDetail.id.startsWith("detail-")) {
      return firstDetail.id.replace("detail-", "");
    }
    return null;
  }

  document.addEventListener("DOMContentLoaded", () => {
    // grupos colapsados al inicio
    openGroup("");

    // toggles de grupo
    document.querySelectorAll(".groupToggle").forEach(btn => {
      btn.addEventListener("click", () => toggleGroup(btn.dataset.groupToggle));
    });

    // items
    document.querySelectorAll(".guidelineBtn").forEach(btn => {
      btn.addEventListener("click", () => setActive(btn.dataset.guideline));
    });

    // mobile select
    const sel = document.getElementById("guidelinesSelect");
    if (sel) sel.addEventListener("change", () => setActive(sel.value));

    // inicial: hash o primer item
    const initial = getInitialId();
    if (initial) setActive(initial);
  });
})();
