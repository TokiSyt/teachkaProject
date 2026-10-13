// Quiz round editor (apps/quizzmaker/templates/quizzmaker/round_editor.html): dialogs, drag to
// reorder rounds, inline answer editing (autosaved), the "accept all" row and the streak preview.
(function () {
  var csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
  var csrf = csrfInput ? csrfInput.value : "";

  // ── Dialogs ──
  // [data-dialog-open="id"] opens; [data-dialog-close] closes its own dialog;
  // [data-dialog-swap="id"] closes its own dialog and opens another (settings → delete quiz).
  function openDialog(id) { var d = document.getElementById(id); if (d && d.showModal) d.showModal(); }
  document.addEventListener("click", function (e) {
    var open = e.target.closest("[data-dialog-open]");
    if (open) { e.preventDefault(); openDialog(open.dataset.dialogOpen); return; }
    var close = e.target.closest("[data-dialog-close]");
    if (close) { var d = close.closest("dialog"); if (d) d.close(); return; }
    var swap = e.target.closest("[data-dialog-swap]");
    if (swap) { var own = swap.closest("dialog"); if (own) own.close(); openDialog(swap.dataset.dialogSwap); return; }
    // "Copy time to all rounds": carry this round's (possibly edited) time into the confirm dialog.
    var copy = e.target.closest("[data-copytime]");
    if (copy) {
      var pk = copy.dataset.copytime;
      var src = document.getElementById("round-time-" + pk), dst = document.getElementById("copytime-value-" + pk);
      if (src && dst) dst.value = src.value;
      openDialog("round-copytime-modal-" + pk);
    }
  });

  // ── Drag rounds to reorder (saved, then the page reloads with the new numbering) ──
  var list = document.getElementById("rounds-list");
  if (list) {
    var reorderUrl = list.dataset.reorderUrl, dragEl = null;
    list.addEventListener("dragstart", function (e) {
      var li = e.target.closest("li[data-round-pk]");
      if (!li) return;
      dragEl = li;
      li.classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    list.addEventListener("dragend", function () {
      if (dragEl) dragEl.classList.remove("is-dragging");
      dragEl = null;
    });
    list.addEventListener("dragover", function (e) {
      e.preventDefault();
      var target = e.target.closest("li[data-round-pk]");
      if (!target || !dragEl || target === dragEl) return;
      var rect = target.getBoundingClientRect();
      list.insertBefore(dragEl, (e.clientY - rect.top) > rect.height / 2 ? target.nextSibling : target);
    });
    list.addEventListener("drop", function (e) {
      e.preventDefault();
      var order = Array.prototype.map.call(list.querySelectorAll("li[data-round-pk]"), function (li) { return li.dataset.roundPk; });
      fetch(reorderUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ order: order }),
      }).then(function (r) { if (r.ok) location.reload(); });
    });
  }

  // ── Inline answer editing in the preview ──
  var grid = document.querySelector("[data-answer-update-base]");
  if (grid) {
    var baseUrl = grid.dataset.answerUpdateBase;
    var single = grid.hasAttribute("data-single"); // true_false: only one can be correct
    var createUrl = grid.dataset.answerCreateUrl; // type_input only
    var deleteBase = grid.dataset.answerDeleteBase; // type_input only
    var placeholder = grid.dataset.answerPlaceholder || "";
    var tiList = document.getElementById("ti-list");

    var urlFor = function (pk) { return baseUrl.replace(/\/0\/$/, "/" + pk + "/"); };
    var send = function (pk, body) {
      fetch(urlFor(pk), { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded", "X-CSRFToken": csrf }, body: body });
    };
    // The rail's correct-answer markers follow the edits.
    var setMarker = function (pk, on) {
      var dot = document.querySelector('[data-marker-answer="' + pk + '"]');
      if (dot) dot.classList.toggle("is-on", on);
    };
    var refreshTypeInputMarker = function () {
      if (!tiList) return;
      var any = Array.prototype.some.call(tiList.querySelectorAll("[data-answer-text]"), function (i) { return i.value.trim() !== ""; });
      var tick = document.querySelector("[data-marker-text]");
      if (tick) tick.classList.toggle("is-on", any);
    };
    var updateDelVisibility = function () {
      if (!tiList) return;
      var rows = tiList.querySelectorAll(".ti-row");
      rows.forEach(function (row) {
        var d = row.querySelector("[data-answer-del]");
        if (d) d.classList.toggle("hidden", rows.length <= 1); // the last accepted answer can't be removed
      });
    };

    var wireRow = function (card) {
      var pk = card.dataset.answerPk;
      var txt = card.querySelector("[data-answer-text]");
      var chk = card.querySelector("[data-answer-correct]");
      var refreshMarker = function () { if (!chk) refreshTypeInputMarker(); else setMarker(pk, chk.checked); };

      if (txt) { // true_false cards have no editable text, only the correct toggle
        var saveTimer;
        txt.addEventListener("input", function () {
          refreshMarker();
          clearTimeout(saveTimer);
          saveTimer = setTimeout(function () { send(pk, "text=" + encodeURIComponent(txt.value)); }, 400);
        });
        txt.addEventListener("blur", function () {
          clearTimeout(saveTimer);
          send(pk, "text=" + encodeURIComponent(txt.value));
        });
      }
      if (chk) {
        chk.addEventListener("change", function () {
          if (single && chk.checked) { // checking one clears the other
            grid.querySelectorAll("[data-answer-pk]").forEach(function (other) {
              if (other === card) return;
              var oc = other.querySelector("[data-answer-correct]");
              if (oc && oc.checked) {
                oc.checked = false;
                setMarker(other.dataset.answerPk, false);
                send(other.dataset.answerPk, "is_correct=0");
              }
            });
          }
          refreshMarker();
          send(pk, "is_correct=" + (chk.checked ? "1" : "0"));
        });
      }
      var del = card.querySelector("[data-answer-del]");
      if (del && deleteBase) {
        del.addEventListener("click", function () {
          if (tiList && tiList.querySelectorAll(".ti-row").length <= 1) return;
          fetch(deleteBase.replace("/0/delete/", "/" + pk + "/delete/"), { method: "POST", headers: { "X-CSRFToken": csrf } })
            .then(function (r) { if (r.ok) { card.remove(); updateDelVisibility(); refreshTypeInputMarker(); } });
        });
      }
    };

    grid.querySelectorAll("[data-answer-pk]").forEach(wireRow);
    updateDelVisibility();

    // Add an accepted answer (type_input): copy an existing row's markup, then clear it.
    var addBtn = document.getElementById("ti-add");
    if (addBtn && createUrl && tiList) {
      addBtn.addEventListener("click", function () {
        fetch(createUrl, { method: "POST", headers: { "X-CSRFToken": csrf } })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.ok) return;
            var row = document.createElement("div");
            row.className = "ti-row ap-answer";
            row.dataset.answerPk = data.pk;
            var icon = document.createElement("i");
            icon.setAttribute("data-lucide", "pencil-line");
            var input = document.createElement("input");
            input.type = "text";
            input.className = "ap-answer-input is-center";
            input.placeholder = placeholder;
            input.setAttribute("data-answer-text", "");
            var tmpl = tiList.querySelector("[data-answer-del]");
            var del = tmpl ? tmpl.cloneNode(true) : document.createElement("button");
            del.classList.remove("hidden");
            row.append(icon, input, del);
            tiList.appendChild(row);
            wireRow(row);
            updateDelVisibility();
            if (window.lucide) lucide.createIcons();
            input.focus();
          });
      });
    }
  }

  // ── "Accept all answers" only applies to "Write the answer" (type_input) ──
  document.querySelectorAll("[data-accept-all-row]").forEach(function (row) {
    var form = row.closest("form");
    var select = form && form.querySelector('select[name="question_type"]');
    if (!select) return;
    var sync = function () { row.classList.toggle("hidden", select.value !== "type_input"); };
    select.addEventListener("change", sync);
    sync();
  });

  // ── Streak bonus preview: a chip per consecutive correct answer until the cap ──
  var preview = document.getElementById("streak-preview");
  var rateEl = document.getElementById("id_streak_bonus_rate");
  var capEl = document.getElementById("id_streak_bonus_cap");
  if (preview && rateEl && capEl) {
    var MAX_LABEL = preview.dataset.maxLabel || "max";
    var OFF_LABEL = preview.dataset.offLabel || "Streak bonus off";
    var clamp = function (el) {
      var v = parseInt(el.value, 10);
      if (isNaN(v) || v < 0) v = 0;
      if (v > 100) v = 100;
      el.value = v;
      return v;
    };
    var chip = function (text, max) {
      var s = document.createElement("span");
      s.className = "ap-chip" + (max ? " is-ink" : "");
      s.textContent = text;
      return s;
    };
    var render = function () {
      var rate = clamp(rateEl), cap = clamp(capEl);
      preview.textContent = "";
      if (rate === 0 || cap === 0) {
        var off = document.createElement("span");
        off.className = "ap-help p-0";
        off.textContent = OFF_LABEL;
        preview.appendChild(off);
        return;
      }
      for (var streak = 2; streak <= 8; streak++) {
        var raw = rate * (streak - 1), atMax = raw >= cap;
        preview.appendChild(chip("×" + streak + " +" + Math.min(raw, cap) + "%" + (atMax ? " · " + MAX_LABEL : ""), atMax));
        if (atMax) break; // every later streak stays at the cap
      }
    };
    rateEl.addEventListener("input", render);
    capEl.addEventListener("input", render);
    render();
  }
})();
