// Admin dashboard: tabs, message filters, confirm dialogs, and keeping the
// tab + scroll position across the POST/redirect of reply and force-quit forms.
(function () {
  const btns = document.querySelectorAll("[data-tab-btn]");
  const panels = document.querySelectorAll("[data-tab-panel]");
  const TAB_KEY = "admin_tab", SCROLL_KEY = "admin_scroll";

  function showTab(name) {
    panels.forEach(p => { p.hidden = p.dataset.tabPanel !== name; });
    btns.forEach(b => b.setAttribute("aria-selected", b.dataset.tabBtn === name ? "true" : "false"));
    try { sessionStorage.setItem(TAB_KEY, name); } catch (e) {}
  }
  btns.forEach(b => b.addEventListener("click", () => showTab(b.dataset.tabBtn)));

  // Restore the tab we were on before a POST/redirect (default: overview).
  let startTab = "overview";
  try { startTab = sessionStorage.getItem(TAB_KEY) || "overview"; } catch (e) {}
  if (![...panels].some(p => p.dataset.tabPanel === startTab)) startTab = "overview";
  showTab(startTab);

  // "Mark as answered/open" submits the reply form with an empty body (toggles the flag).
  document.querySelectorAll("[data-clear-reply]").forEach(b => b.addEventListener("click", () => {
    const reply = b.closest("form").querySelector("[name=reply]");
    if (reply) reply.value = "";
  }));

  // Forms with data-confirm ask first (e.g. force-quit a live session).
  document.querySelectorAll("form[data-confirm]").forEach(f => f.addEventListener("submit", e => {
    if (!confirm(f.dataset.confirm)) e.preventDefault();
  }));

  // Preserve scroll position across form submits (force-quit / reply).
  document.addEventListener("submit", e => {
    if (e.defaultPrevented) return;
    try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (err) {}
  });

  // Contact filters: kind + open-only.
  const rows = document.querySelectorAll(".contact-row");
  const emptyMsg = document.getElementById("contact-empty");
  const kindBtns = document.querySelectorAll("[data-kind-filter]");
  const openOnly = document.getElementById("unhandled-only");
  let curKind = "all";
  function matches(row, kind, openFilter) {
    return (kind === "all" || row.dataset.kind === kind) && (!openFilter || row.dataset.handled === "0");
  }
  function applyFilters() {
    const openFilter = openOnly && openOnly.checked;
    let visible = 0;
    rows.forEach(r => {
      const show = matches(r, curKind, openFilter);
      r.hidden = !show;
      if (show) visible++;
    });
    if (emptyMsg) emptyMsg.hidden = visible !== 0;
    // Recompute each filter count against the current open-only state.
    kindBtns.forEach(b => {
      const kind = b.dataset.kindFilter;
      let n = 0;
      rows.forEach(r => { if (matches(r, kind, openFilter)) n++; });
      const count = b.querySelector(".ad-count");
      if (count) count.textContent = n;
      b.setAttribute("aria-selected", kind === curKind ? "true" : "false");
    });
  }
  kindBtns.forEach(b => b.addEventListener("click", () => { curKind = b.dataset.kindFilter; applyFilters(); }));
  if (openOnly) openOnly.addEventListener("change", applyFilters);
  if (kindBtns.length) applyFilters();

  if (window.lucide) lucide.createIcons();

  // Restore scroll after layout settles (tab + filters already applied).
  try {
    const y = sessionStorage.getItem(SCROLL_KEY);
    if (y !== null) {
      sessionStorage.removeItem(SCROLL_KEY);
      requestAnimationFrame(() => window.scrollTo(0, parseInt(y, 10) || 0));
    }
  } catch (e) {}
})();
