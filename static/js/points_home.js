// Point system home (apps/point_system/templates/point_system/home.html): group picker,
// keyboard navigation, live totals, auto-save, column drag-to-reorder, show/hide tables,
// and the clear-column / delete-all confirm dialogs. Translated labels come from data-t-* attributes.
(function () {
  var csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
  var csrf = csrfInput ? csrfInput.value : "";

  function postForm(url, fields) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest" },
      body: new URLSearchParams(fields).toString(),
      credentials: "same-origin",
    });
  }

  // ── Group picker: picking a group loads it ──
  var dd = document.getElementById("groupDropdown");
  var groupInput = document.getElementById("groupSelect");
  var groupLabel = document.getElementById("groupSelectLabel");
  document.querySelectorAll(".ap-menu-pick").forEach(function (btn) {
    btn.addEventListener("click", function () {
      groupInput.value = btn.dataset.id;
      groupLabel.textContent = btn.dataset.label;
      dd.open = false;
      document.getElementById("group-form").submit();
    });
  });
  document.addEventListener("click", function (e) {
    if (dd && dd.open && !dd.contains(e.target)) dd.open = false;
  });

  var form = document.getElementById("points-form");
  if (!form) return; // no group selected yet

  // ── Enter moves to the same column in the next row; text cells keep their value as tooltip ──
  form.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var t = e.target;
    if (!(t instanceof HTMLInputElement) || t.type === "submit" || t.type === "button") return;
    e.preventDefault();
    var td = t.closest("td"), tr = td && td.closest("tr");
    if (!tr || !tr.nextElementSibling) return;
    var idx = Array.prototype.indexOf.call(tr.children, td);
    var nextCell = tr.nextElementSibling.children[idx];
    var nextInput = nextCell && nextCell.querySelector("input");
    if (nextInput) { nextInput.focus(); if (nextInput.select) nextInput.select(); }
  });
  form.addEventListener("input", function (e) {
    if (e.target.matches('input[type="text"].ap-cell')) e.target.title = e.target.value;
  });
  // (The − / + stepper buttons on number cells live in static/js/stepper.js.)

  // ── Live row total: sum the row's number cells, tint the bubble ──
  function updateRowTotal(input, isPositive) {
    var tr = input.closest("tr");
    if (!tr) return;
    var total = 0;
    tr.querySelectorAll('input[type="number"]').forEach(function (i) {
      var v = parseInt(i.value, 10);
      if (!isNaN(v)) total += v;
    });
    var bubble = tr.querySelector(".ap-total");
    if (!bubble) return;
    bubble.textContent = total;
    var level = total >= 10 ? "high" : total >= 5 ? "mid" : "";
    bubble.className = "ap-total" + (level ? " is-" + (isPositive ? "pos" : "neg") + "-" + level : "");
  }

  // ── Auto-save (remembered per group in localStorage) ──
  var toggle = document.getElementById("autosave-toggle");
  var status = document.getElementById("autosave-status");
  var T = toggle ? {
    enabled: toggle.dataset.tEnabled, pending: toggle.dataset.tPending, saving: toggle.dataset.tSaving,
    saved: toggle.dataset.tSaved, failed: toggle.dataset.tFailed, failedRefresh: toggle.dataset.tFailedRefresh,
  } : {};
  var groupField = form.querySelector("[name=group_id]");
  var STORAGE_KEY = "points-autosave-" + (groupField ? groupField.value : "x");
  var DEBOUNCE_MS = 2000, MIN_INTERVAL_MS = 5000;
  var dirty = { negative: false, positive: false };
  var timer = null, lastSaveAt = 0, saving = false;
  var submitting = false; // manual Save submits the form: intentional navigation, no warning

  function setStatus(text) { if (status) status.textContent = text ? "· " + text : ""; }
  function storageGet() { try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; } }
  function storageSet(v) { try { localStorage.setItem(STORAGE_KEY, v); } catch (e) {} }

  if (toggle) {
    toggle.checked = storageGet() === "1";
    toggle.addEventListener("change", function () {
      storageSet(toggle.checked ? "1" : "0");
      setStatus(toggle.checked ? T.enabled : "");
    });
    setStatus(toggle.checked ? T.enabled : "");
  }

  form.addEventListener("submit", function () { submitting = true; });

  form.addEventListener("input", function (e) {
    var name = e.target.name || "";
    var isNeg = name.indexOf("_negative_") !== -1, isPos = name.indexOf("_positive_") !== -1;
    if (!isNeg && !isPos) return;
    updateRowTotal(e.target, isPos);
    if (!toggle || !toggle.checked) return;
    if (isNeg) dirty.negative = true; else dirty.positive = true;
    schedule();
  });

  function schedule() {
    clearTimeout(timer);
    var wait = Math.max(DEBOUNCE_MS, MIN_INTERVAL_MS - (Date.now() - lastSaveAt));
    setStatus(T.pending);
    timer = setTimeout(run, wait);
  }

  async function run() {
    if (saving || (!dirty.negative && !dirty.positive)) return;
    saving = true;
    var flags = [];
    if (dirty.negative) flags.push("negative_save");
    if (dirty.positive) flags.push("positive_save");
    dirty = { negative: false, positive: false };
    lastSaveAt = Date.now();
    setStatus(T.saving);
    var failed = false;
    try {
      for (var i = 0; i < flags.length; i++) {
        var fd = new FormData(form);
        fd.set(flags[i], "1");
        var res = await fetch(window.location.pathname + window.location.search, {
          method: "POST", body: fd, headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin",
        });
        if (res.type === "opaqueredirect" || !res.ok) {
          failed = true;
          console.warn("[autosave] failed for", flags[i], res.status);
        }
      }
      if (failed) setStatus(T.failedRefresh); else setStatus(T.saved + " " + new Date().toLocaleTimeString());
    } catch (err) {
      console.error("[autosave] error", err);
      failed = true;
      setStatus(T.failed);
    } finally {
      if (failed) {
        if (flags.indexOf("negative_save") !== -1) dirty.negative = true;
        if (flags.indexOf("positive_save") !== -1) dirty.positive = true;
      }
      saving = false;
      if (dirty.negative || dirty.positive) schedule();
    }
  }

  window.addEventListener("beforeunload", function (e) {
    if (!submitting && toggle && toggle.checked && (dirty.negative || dirty.positive)) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  // ── Drag a column header to reorder the column (saved right away) ──
  document.querySelectorAll("table[data-reorderable-table]").forEach(function (table) {
    var definition = table.dataset.reorderableTable, url = table.dataset.reorderUrl;
    var headerRow = table.querySelector("thead tr"), tbody = table.querySelector("tbody");
    if (!headerRow || !tbody || !url) return;
    var dragTh = null;

    function colIndex(th) { return Array.prototype.indexOf.call(headerRow.children, th); }
    function moveCells(fromIdx, toIdx) {
      if (fromIdx === toIdx) return;
      tbody.querySelectorAll("tr").forEach(function (tr) {
        var moving = tr.children[fromIdx];
        if (!moving) return;
        var ref = tr.children[toIdx];
        tr.insertBefore(moving, toIdx > fromIdx ? (ref ? ref.nextSibling : null) : ref);
      });
    }

    headerRow.addEventListener("dragstart", function (e) {
      var th = e.target.closest("th[data-field-pk]");
      if (!th) return;
      dragTh = th;
      th.querySelector(".ap-th-drag").classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    headerRow.addEventListener("dragend", function () {
      if (dragTh) dragTh.querySelector(".ap-th-drag").classList.remove("is-dragging");
      dragTh = null;
    });
    headerRow.addEventListener("dragover", function (e) {
      e.preventDefault();
      if (!dragTh) return;
      var target = e.target.closest("th[data-field-pk]");
      if (!target || target === dragTh) return;
      var rect = target.getBoundingClientRect();
      var after = (e.clientX - rect.left) > rect.width / 2;
      var fromIdx = colIndex(dragTh);
      headerRow.insertBefore(dragTh, after ? target.nextSibling : target);
      moveCells(fromIdx, colIndex(dragTh));
    });
    headerRow.addEventListener("drop", function (e) {
      e.preventDefault();
      var order = Array.prototype.map.call(headerRow.querySelectorAll("th[data-field-pk]"), function (th) {
        return parseInt(th.dataset.fieldPk, 10);
      });
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ definition: definition, order: order }),
        credentials: "same-origin",
      }).then(function (r) { if (!r.ok) console.warn("[reorder] failed", r.status); });
    });
  });

  // ── Show / hide a table (remembered per group on the server) ──
  document.querySelectorAll("[data-toggle-table]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var wrap = document.getElementById(btn.dataset.target);
      if (!wrap) return;
      var nowHidden = wrap.classList.toggle("hidden");
      var label = btn.querySelector("span");
      if (label) label.textContent = nowHidden ? btn.dataset.tShow : btn.dataset.tHide;
      // Lucide replaced the <i> with an <svg>: swap in a fresh <i> and re-render it.
      var old = btn.querySelector("svg, i");
      var icon = document.createElement("i");
      icon.setAttribute("data-lucide", nowHidden ? "eye-off" : "eye");
      icon.className = "w-4 h-4";
      if (old) btn.replaceChild(icon, old);
      if (window.lucide) lucide.createIcons();
      btn.setAttribute("aria-pressed", nowHidden ? "false" : "true");
      postForm(btn.dataset.toggleUrl, { definition: btn.dataset.toggleTable, visible: nowHidden ? "0" : "1" });
    });
  });

  // ── Confirm dialogs: clear one column / delete all columns ──
  var pending = null;
  var clearModal = document.getElementById("clear-column-modal");
  var deleteAllModal = document.getElementById("delete-all-modal");

  function runPending(e) {
    if (!pending) return;
    var p = pending;
    pending = null;
    var dlg = e.target.closest("dialog");
    if (dlg) dlg.close();
    postForm(p.url, p.fields).then(function () { window.location.reload(); });
  }

  document.querySelectorAll("[data-clear-field]").forEach(function (btn) {
    btn.addEventListener("mousedown", function (e) { e.stopPropagation(); }); // don't start a column drag
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (!clearModal) return;
      pending = { url: btn.dataset.clearUrl, fields: { field_name: btn.dataset.clearField, definition: btn.dataset.definition } };
      var nameEl = clearModal.querySelector("[data-col-name]");
      if (nameEl) nameEl.textContent = btn.dataset.clearField;
      clearModal.showModal();
    });
  });
  if (clearModal) clearModal.querySelector("[data-confirm]").addEventListener("click", runPending);

  document.querySelectorAll("[data-delete-all]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (!deleteAllModal) return;
      pending = { url: btn.dataset.deleteAllUrl, fields: { definition: btn.dataset.definition } };
      deleteAllModal.showModal();
    });
  });
  if (deleteAllModal) deleteAllModal.querySelector("[data-confirm]").addEventListener("click", runPending);
})();
