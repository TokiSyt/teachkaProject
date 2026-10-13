// Member dashboard (apps/point_system/templates/point_system/dashboard.html): member dialog,
// tabs with an unsaved-changes guard, live breakdown, and auto-save.
// Translated status labels come from data-t-* on #dash-autosave-toggle.
(function () {
  // ── Dialogs: [data-dialog-open] opens one, [data-dialog-close] closes its own ──
  document.querySelectorAll("[data-dialog-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var d = document.getElementById(btn.dataset.dialogOpen);
      if (d && d.showModal) d.showModal();
    });
  });
  document.querySelectorAll("[data-dialog-close]").forEach(function (btn) {
    btn.addEventListener("click", function () { var d = btn.closest("dialog"); if (d) d.close(); });
  });

  // ── Member colour: a palette swatch sets the custom colour input ──
  var colorInput = document.getElementById("color-input");
  var swatches = document.querySelectorAll("#color-form [data-color]");
  swatches.forEach(function (b) {
    b.addEventListener("click", function () {
      if (colorInput) colorInput.value = b.dataset.color;
      swatches.forEach(function (s) { s.setAttribute("aria-pressed", s === b ? "true" : "false"); });
    });
  });
  if (colorInput) colorInput.addEventListener("input", function () {
    swatches.forEach(function (s) { s.setAttribute("aria-pressed", "false"); });
  });

  var tablist = document.querySelector("[data-default-tab]");
  if (!tablist) return;
  var tabs = Array.prototype.slice.call(tablist.querySelectorAll("[data-tab]"));
  var panels = Array.prototype.slice.call(document.querySelectorAll("[data-tab-panel]"));
  var forms = Array.prototype.slice.call(document.querySelectorAll("form[data-dash-form]"));
  var toggle = document.getElementById("dash-autosave-toggle");
  var status = document.getElementById("dash-autosave-status");
  var modal = document.getElementById("tab-dirty-modal");
  var KEY = tablist.dataset.autosaveKey || "karma-dash-autosave";
  var DEBOUNCE_MS = 1500;
  var T = {
    enabled: toggle.dataset.tEnabled, pending: toggle.dataset.tPending, saving: toggle.dataset.tSaving,
    saved: toggle.dataset.tSaved, failed: toggle.dataset.tFailed,
  };

  function setStatus(t) { if (status) status.textContent = t ? "· " + t : ""; }
  function storageGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function storageSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  var dirty = new Map();
  var timer = null;
  var submitting = false;

  toggle.checked = storageGet(KEY) === "1";
  setStatus(toggle.checked ? T.enabled : "");
  toggle.addEventListener("change", function () {
    storageSet(KEY, toggle.checked ? "1" : "0");
    setStatus(toggle.checked ? T.enabled : "");
    if (toggle.checked && dirty.size) schedule();
  });

  forms.forEach(function (form) {
    form.addEventListener("input", function () {
      dirty.set(form.dataset.dashForm, form);
      recompute(form); // live-update bar / legend / totals without a reload
      if (toggle.checked) { setStatus(T.pending); schedule(); }
    });
    form.addEventListener("submit", function () { submitting = true; dirty.delete(form.dataset.dashForm); });
  });

  // ── Live breakdown (numeric tables only) ──
  var totals = {
    positive: parseInt((document.querySelector('[data-stat="positive"]') || {}).textContent, 10) || 0,
    negative: parseInt((document.querySelector('[data-stat="negative"]') || {}).textContent, 10) || 0,
  };
  function recompute(form) {
    var table = form.dataset.dashForm;
    var numbers = Array.prototype.slice.call(form.querySelectorAll('input[type="number"]'));
    if (!numbers.length) return; // notes form: nothing to recompute
    var panel = document.querySelector('[data-tab-panel="' + table + '"]');
    var marker = "_" + table + "_";
    var total = 0;
    var vals = numbers.map(function (inp) {
      var i = inp.name.indexOf(marker);
      var col = i >= 0 ? inp.name.slice(i + marker.length) : inp.name;
      var v = parseInt(inp.value, 10);
      if (isNaN(v) || v < 0) v = 0;
      total += v;
      return [col, v];
    });
    if (panel) {
      vals.forEach(function (pair) {
        var col = pair[0], v = pair[1];
        var pct = total ? Math.round(v / total * 100) : 0;
        panel.querySelectorAll("[data-seg-bar]").forEach(function (b) { if (b.dataset.segBar === col) b.style.setProperty("--w", pct + "%"); });
        panel.querySelectorAll("[data-seg-value]").forEach(function (s) { if (s.dataset.segValue === col) s.textContent = v; });
        panel.querySelectorAll("[data-seg-pct]").forEach(function (s) { if (s.dataset.segPct === col) s.textContent = pct + "%"; });
      });
      var tot = panel.querySelector("[data-bar-total]"); if (tot) tot.textContent = total;
      var hint = panel.querySelector("[data-empty-hint]"); if (hint) hint.classList.toggle("hidden", total > 0);
    }
    totals[table] = total;
    var stat = document.querySelector('[data-stat="' + table + '"]'); if (stat) stat.textContent = total;
    var net = (totals.positive || 0) - (totals.negative || 0);
    var netEl = document.querySelector('[data-stat="net"]');
    if (netEl) netEl.textContent = net;
    var netBubble = document.querySelector("[data-net-bubble]");
    if (netBubble) netBubble.classList.toggle("is-neg", net < 0);
  }

  function schedule() { clearTimeout(timer); timer = setTimeout(saveDirty, DEBOUNCE_MS); }

  async function saveDirty() {
    if (!dirty.size) return true;
    setStatus(T.saving);
    var failed = false;
    var entries = Array.from(dirty.entries());
    for (var i = 0; i < entries.length; i++) {
      var table = entries[i][0], form = entries[i][1];
      try {
        var fd = new FormData(form);
        fd.set(table + "_save", "1");
        var res = await fetch(window.location.pathname, {
          method: "POST", body: fd, headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin",
        });
        if (res.ok) dirty.delete(table); else failed = true;
      } catch (e) { failed = true; }
    }
    setStatus(failed ? T.failed : T.saved + " " + new Date().toLocaleTimeString());
    return !failed;
  }

  // ── Tabs + unsaved-changes guard; the last-viewed tab is remembered ──
  var pendingTab = null;
  var TAB_KEY = "karma-dash-tab-" + KEY;
  function activate(name) {
    storageSet(TAB_KEY, name);
    tabs.forEach(function (t) {
      var on = t.dataset.tab === name;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach(function (p) { p.classList.toggle("hidden", p.dataset.tabPanel !== name); });
  }
  var initialTab = tablist.dataset.defaultTab || "negative";
  var savedTab = storageGet(TAB_KEY);
  if (savedTab && tabs.some(function (t) { return t.dataset.tab === savedTab; })) initialTab = savedTab;
  activate(initialTab);
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function (e) {
      e.preventDefault();
      if (tab.classList.contains("is-active")) return;
      if (dirty.size) { pendingTab = tab.dataset.tab; modal.showModal(); }
      else activate(tab.dataset.tab);
    });
  });
  function go() { if (pendingTab) { activate(pendingTab); pendingTab = null; } }

  if (modal) {
    modal.querySelector('[data-dirty="save"]').addEventListener("click", async function () {
      var ok = await saveDirty();
      modal.close();
      if (ok) go(); else pendingTab = null;
    });
    modal.querySelector('[data-dirty="discard"]').addEventListener("click", function () {
      dirty.forEach(function (form) { form.reset(); });
      dirty.clear(); setStatus(""); modal.close(); go();
    });
    modal.querySelector('[data-dirty="cancel"]').addEventListener("click", function () {
      pendingTab = null; modal.close();
    });
  }

  window.addEventListener("beforeunload", function (e) {
    if (!submitting && dirty.size) { e.preventDefault(); e.returnValue = ""; }
  });
})();
