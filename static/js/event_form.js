// Event form (apps/calendar/templates/calendar/event_form.html): separate date + 24h time
// fields that fill the hidden start/end datetime inputs, an all-day switch, and the
// "Repeat until" row that only shows when a recurrence is chosen.
(function () {
  var form = document.getElementById("event-form");
  if (!form) return;
  var sd = document.getElementById("start_d"), st = document.getElementById("start_t");
  var ed = document.getElementById("end_d"), et = document.getElementById("end_t");
  var startH = document.getElementById("id_start_datetime"), endH = document.getElementById("id_end_datetime");
  var allDay = document.getElementById("id_all_day");
  var recurrence = document.getElementById("id_recurrence");
  var recurrenceRow = document.getElementById("recurrence-end-row");

  function sync() {
    if (sd.value) startH.value = sd.value + "T" + (st.value || "00:00");
    if (ed.value) endH.value = ed.value + "T" + (et.value || "23:59");
  }

  function init(iso, dEl, tEl) {
    if (!iso) return;
    var parts = iso.replace(" ", "T").split("T");
    dEl.value = parts[0] || "";
    tEl.value = parts[1] ? parts[1].slice(0, 5) : "";
  }

  // 24h time dropdown: every half hour plus 23:59, filtered as you type.
  function buildTimePicker(inp, drop) {
    var presets = [];
    for (var h = 0; h < 24; h++) {
      presets.push(String(h).padStart(2, "0") + ":00");
      presets.push(String(h).padStart(2, "0") + ":30");
    }
    presets.push("23:59");

    presets.forEach(function (t) {
      var row = document.createElement("div");
      row.textContent = t;
      row.className = "ap-timedrop-item";
      row.addEventListener("mousedown", function (e) {
        e.preventDefault();
        inp.value = t;
        drop.classList.add("hidden");
        sync();
      });
      drop.appendChild(row);
    });

    function showDrop() {
      drop.classList.remove("hidden");
      var cur = Array.prototype.find.call(drop.children, function (r) { return r.textContent === inp.value; });
      if (cur) cur.scrollIntoView({ block: "nearest" });
      else drop.scrollTop = 0;
    }

    function filterDrop() {
      var q = inp.value.trim();
      Array.prototype.forEach.call(drop.children, function (r) {
        r.style.display = (!q || r.textContent.indexOf(q) === 0) ? "" : "none";
      });
      drop.classList.remove("hidden");
    }

    inp.addEventListener("focus", showDrop);
    inp.addEventListener("blur", function () { drop.classList.add("hidden"); });
    inp.addEventListener("input", function () {
      if (/^\d{2}$/.test(inp.value)) inp.value += ":";
      filterDrop();
    });
    inp.addEventListener("change", sync);
  }

  buildTimePicker(st, document.getElementById("start_t_drop"));
  buildTimePicker(et, document.getElementById("end_t_drop"));

  // All day: fix the times to 00:00 – 23:59 and lock the time fields. Times are only cleared
  // when the user switches All day off; on page load the event's own times are kept (clearing
  // them then made an edited 09:30 event save as 00:00).
  function toggleAllDay(fromUser) {
    var on = allDay.checked;
    if (on) { st.value = "00:00"; et.value = "23:59"; sync(); }
    else if (fromUser) { st.value = ""; et.value = ""; sync(); }
    st.disabled = on; et.disabled = on;
  }

  allDay.addEventListener("change", function () { toggleAllDay(true); });
  init(startH.value, sd, st);
  init(endH.value, ed, et);
  toggleAllDay(false);

  // Moving the start date drags the end date along while they were the same day.
  var prevDate = sd.value;
  sd.addEventListener("change", function () {
    if (!ed.value || ed.value === prevDate) { ed.value = sd.value; if (!et.value) et.value = "23:59"; }
    prevDate = sd.value;
    sync();
  });
  ed.addEventListener("change", sync);
  form.addEventListener("submit", sync);

  recurrence.addEventListener("change", function () {
    recurrenceRow.classList.toggle("hidden", !recurrence.value || recurrence.value === "none");
  });
})();
