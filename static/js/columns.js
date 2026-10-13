// Point system column pages (new / edit / delete column).
(function () {
  // New column: repeatable name + type rows cloned from a <template>; the last row can't be removed.
  var rows = document.getElementById("column-rows");
  var tpl = document.getElementById("column-row-template");
  var addBtn = document.getElementById("add-row");
  if (rows && tpl && addBtn) {
    var refreshRemoveState = function () {
      var all = rows.querySelectorAll(".column-row");
      all.forEach(function (row) {
        var btn = row.querySelector(".remove-row");
        if (btn) btn.disabled = all.length <= 1;
      });
    };
    var addRow = function (focus) {
      rows.appendChild(tpl.content.cloneNode(true));
      var row = rows.lastElementChild;
      row.querySelector(".remove-row").addEventListener("click", function () {
        row.remove();
        refreshRemoveState();
      });
      if (window.lucide) lucide.createIcons();
      refreshRemoveState();
      if (focus) row.querySelector('input[name="name"]').focus();
    };
    addBtn.addEventListener("click", function () { addRow(true); });
    addRow(true); // start with one row
  }

  // Edit / delete column: show the chosen column's type. The select names the display element
  // (data-column-type-for); its translated labels live in data-int / data-str.
  document.querySelectorAll("[data-column-type-for]").forEach(function (select) {
    var display = document.getElementById(select.dataset.columnTypeFor);
    if (!display) return;
    select.addEventListener("change", function () {
      var opt = select.options[select.selectedIndex];
      var type = opt && opt.dataset.type;
      display.textContent = (type && display.dataset[type]) || "-";
    });
  });
})();
