// Group divider page (apps/group_divider/templates/group_divider/home.html):
// the group dropdown, and the size field following the "Split by" mode.
(function () {
  var dd = document.getElementById("groupDropdown");
  var hidden = document.getElementById("groupSelect");
  var label = document.getElementById("groupSelectLabel");

  // Pick a group: store its id in the hidden field, show its label, close the menu.
  document.querySelectorAll(".ap-menu-pick").forEach(function (btn) {
    btn.addEventListener("click", function () {
      hidden.value = btn.dataset.id;
      label.textContent = btn.dataset.label;
      dd.open = false;
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });

  // Close the menu on a click outside it.
  document.addEventListener("click", function (e) {
    if (dd && dd.open && !dd.contains(e.target)) dd.open = false;
  });

  // Mode change: swap the size field's label (translations live in data-size / data-teams) and icon.
  var sizeLabel = document.getElementById("sizeLabel");
  var iconWrap = document.getElementById("sizeIconWrap");
  document.querySelectorAll(".mode-radio").forEach(function (radio) {
    radio.addEventListener("change", function () {
      if (!radio.checked) return;
      var teams = radio.value === "teams";
      sizeLabel.textContent = teams ? sizeLabel.dataset.teams : sizeLabel.dataset.size;
      // Lucide replaced the <i> with an <svg>: put a fresh <i> back and re-render it.
      var old = iconWrap.querySelector("svg, i");
      var icon = document.createElement("i");
      icon.setAttribute("data-lucide", teams ? "layout-grid" : "hash");
      if (old) iconWrap.replaceChild(icon, old); else iconWrap.prepend(icon);
      if (window.lucide) lucide.createIcons();
    });
  });
})();
