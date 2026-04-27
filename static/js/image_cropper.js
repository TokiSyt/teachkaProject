(function () {
  const CARD_RATIO = 16 / 9;
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

  function wireCropper(wrap) {
    const inputId = wrap.dataset.inputId;
    const fileInput = document.getElementById(inputId);
    if (!fileInput) return;
    const form = fileInput.form;
    if (!form) return;
    const stage = wrap.querySelector("[data-crop-stage]");
    const full = wrap.querySelector("[data-crop-full]");
    const card = wrap.querySelector("[data-crop-card]");
    const dimT = wrap.querySelector('[data-crop-dim="top"]');
    const dimB = wrap.querySelector('[data-crop-dim="bottom"]');
    const dimL = wrap.querySelector('[data-crop-dim="left"]');
    const dimR = wrap.querySelector('[data-crop-dim="right"]');

    const state = { mode: "square", posX: 0, posY: 0, vw: 100, vh: 100, file: null, active: false };

    function paint() {
      for (const el of [dimT, dimB, dimL, dimR]) {
        el.style.width = el.style.height = "";
        el.style.display = "block";
      }
      if (state.mode === "wider") {
        dimL.style.width = state.posX + "%";
        dimR.style.width = (100 - state.posX - state.vw) + "%";
        dimT.style.display = dimB.style.display = "none";
        const maxLeft = 100 - state.vw;
        const px = maxLeft > 0 ? (state.posX / maxLeft) * 100 : 50;
        card.style.objectPosition = px + "% 50%";
        stage.style.cursor = "ew-resize";
      } else if (state.mode === "taller") {
        dimT.style.height = state.posY + "%";
        dimB.style.height = (100 - state.posY - state.vh) + "%";
        dimL.style.display = dimR.style.display = "none";
        const maxTop = 100 - state.vh;
        const py = maxTop > 0 ? (state.posY / maxTop) * 100 : 50;
        card.style.objectPosition = "50% " + py + "%";
        stage.style.cursor = "ns-resize";
      } else {
        for (const el of [dimT, dimB, dimL, dimR]) el.style.display = "none";
        card.style.objectPosition = "50% 50%";
        stage.style.cursor = "default";
      }
    }

    function init(focusX, focusY) {
      const r = full.naturalWidth / full.naturalHeight;
      if (r > CARD_RATIO) {
        state.mode = "wider";
        state.vw = (CARD_RATIO / r) * 100;
        state.vh = 100;
        const maxLeft = 100 - state.vw;
        state.posX = isFinite(focusX) ? clamp((focusX / 100) * maxLeft, 0, maxLeft) : maxLeft / 2;
        state.posY = 0;
      } else if (r < CARD_RATIO) {
        state.mode = "taller";
        state.vh = (r / CARD_RATIO) * 100;
        state.vw = 100;
        const maxTop = 100 - state.vh;
        state.posY = isFinite(focusY) ? clamp((focusY / 100) * maxTop, 0, maxTop) : maxTop / 2;
        state.posX = 0;
      } else {
        state.mode = "square";
        state.vw = 100; state.vh = 100;
        state.posX = 0; state.posY = 0;
      }
      paint();
    }

    let drag = null;
    stage.addEventListener("pointerdown", (e) => {
      if (state.mode === "square") return;
      drag = { x: e.clientX, y: e.clientY, posX: state.posX, posY: state.posY };
      stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const rect = stage.getBoundingClientRect();
      if (state.mode === "wider") {
        const dx = ((e.clientX - drag.x) / rect.width) * 100;
        state.posX = clamp(drag.posX + dx, 0, 100 - state.vw);
      } else {
        const dy = ((e.clientY - drag.y) / rect.height) * 100;
        state.posY = clamp(drag.posY + dy, 0, 100 - state.vh);
      }
      paint();
    });
    const endDrag = () => { drag = null; };
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);

    const removeBtn = form.querySelector(`[data-image-remove][data-input-id="${inputId}"]`);
    const focusXEl = form.querySelector(`input[data-image-focus="x"][data-input-id="${inputId}"]`);
    const focusYEl = form.querySelector(`input[data-image-focus="y"][data-input-id="${inputId}"]`);

    function showSrc(src, focusX, focusY) {
      full.onload = () => init(focusX, focusY);
      full.src = src;
      card.src = src;
      wrap.classList.remove("hidden");
      state.active = true;
      if (removeBtn) removeBtn.style.display = "inline-flex";
    }

    function showFile(file) {
      state.file = file;
      const fx = focusXEl ? parseFloat(focusXEl.value) : 50;
      const fy = focusYEl ? parseFloat(focusYEl.value) : 50;
      showSrc(URL.createObjectURL(file), fx, fy);
    }

    function clearFile() {
      state.file = null;
      state.mode = "square";
      state.active = false;
      fileInput.value = "";
      full.removeAttribute("src");
      card.removeAttribute("src");
      wrap.classList.add("hidden");
      if (removeBtn) removeBtn.style.display = "none";
    }

    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) { clearFile(); return; }
      showFile(file);
    });

    if (removeBtn) removeBtn.addEventListener("click", clearFile);

    const recutBtn = form.querySelector(`[data-image-recut][data-input-id="${inputId}"]`);
    if (recutBtn) {
      recutBtn.addEventListener("click", () => {
        const url = recutBtn.dataset.currentUrl;
        const fx = parseFloat(recutBtn.dataset.focusX);
        const fy = parseFloat(recutBtn.dataset.focusY);
        state.file = null; // re-cut existing image, no new upload
        showSrc(url, fx, fy);
      });
    }

    function computeFocus() {
      if (state.mode === "wider") {
        const maxLeft = 100 - state.vw;
        return [maxLeft > 0 ? Math.round((state.posX / maxLeft) * 100) : 50, 50];
      }
      if (state.mode === "taller") {
        const maxTop = 100 - state.vh;
        return [50, maxTop > 0 ? Math.round((state.posY / maxTop) * 100) : 50];
      }
      return [50, 50];
    }

    form.addEventListener("submit", () => {
      if (!state.active) return;
      const [fx, fy] = computeFocus();
      if (focusXEl) focusXEl.value = fx;
      if (focusYEl) focusYEl.value = fy;
    });
  }

  function initAll() {
    document.querySelectorAll("[data-image-cropper]").forEach((wrap) => {
      if (wrap.dataset.cropperWired === "1") return;
      wrap.dataset.cropperWired = "1";
      wireCropper(wrap);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
