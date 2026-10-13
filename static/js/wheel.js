// Name wheel (apps/wheel/templates/wheel/home.html): group picker, canvas wheel with an idle
// spin, spin-to-result via the view's JSON endpoint, "already chosen" list and the result dialog.
// Members per group come from the json_script blocks; translated text from data-t-* on the form.
(function () {
  var form = document.getElementById("wheelForm");
  var canvas = document.getElementById("wheelCanvas");
  if (!form || !canvas) return;

  var T = form.dataset;
  var groupSelect = document.getElementById("groupSelect");
  var groupLabel = document.getElementById("groupSelectLabel");
  var dropdown = document.getElementById("groupDropdown");
  var resetBtn = document.getElementById("resetBtn");
  var spinBtn = document.getElementById("spinBtn");
  var spinLabel = spinBtn.querySelector("span");
  var shuffleBtn = document.getElementById("shuffleBtn");
  var wheelSection = document.getElementById("wheelSection");
  var pointer = document.getElementById("wheelPointer");
  var membersChosenInput = document.getElementById("membersChosen");
  var alreadyChosenSection = document.getElementById("alreadyChosenSection");
  var clearSessionInput = document.getElementById("clearSession");
  var popup = document.getElementById("chosenPopup");
  var popupTitle = document.getElementById("popupTitle");
  var popupNames = document.getElementById("popupNames");
  var resetBase = form.dataset.url + "?reset=1";

  function readJSON(id, fallback) {
    var el = document.getElementById(id);
    try { return el ? JSON.parse(el.textContent) : fallback; } catch (e) { return fallback; }
  }
  var groupsData = readJSON("wheel-groups", {});
  var initialChosen = readJSON("wheel-already-chosen", []);
  var alreadyChosenByGroup = {};
  if (groupSelect.value && Array.isArray(initialChosen)) alreadyChosenByGroup[groupSelect.value] = initialChosen;

  var ctx = canvas.getContext("2d");
  var members = [];
  var currentRotation = 0, isSpinning = false, idleAnimationId = null;
  var cachedWheel = null, cachedSize = 0;

  // ── Group picker ──
  document.querySelectorAll(".ap-menu-pick").forEach(function (btn) {
    btn.addEventListener("click", function () {
      groupSelect.value = btn.dataset.id;
      groupLabel.textContent = btn.dataset.label;
      dropdown.open = false;
      groupSelect.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
  document.addEventListener("click", function (e) {
    if (dropdown.open && !dropdown.contains(e.target)) dropdown.open = false;
  });

  // ── Canvas drawing ──
  function getCanvasSize() {
    var box = canvas.parentElement;
    return Math.min(box.offsetWidth, box.offsetHeight) || 400;
  }
  function resizeCanvas() {
    var size = getCanvasSize(), dpr = window.devicePixelRatio || 1, px = Math.round(size * dpr);
    if (canvas.width !== px) {
      canvas.width = px; canvas.height = px;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }
  function hexToRgba(hex, alpha) {
    var r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
    return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
  }

  // The static wheel is drawn once to an offscreen canvas, then rotated each frame.
  function buildWheelCache() {
    var size = getCanvasSize();
    if (!size || !members.length) { cachedWheel = null; return; }
    cachedSize = size;
    var dpr = window.devicePixelRatio || 1;
    var off = document.createElement("canvas");
    off.width = Math.round(size * dpr); off.height = Math.round(size * dpr);
    var c = off.getContext("2d");
    c.setTransform(dpr, 0, 0, dpr, 0, 0);

    var center = size / 2, borderWidth = 4, borderGap = 4;
    var radius = center - borderWidth - borderGap - 2;
    var slice = (2 * Math.PI) / members.length;
    var fontSize = Math.max(10, Math.min(radius / 13, slice * radius * 0.6));
    c.font = "bold " + fontSize + "px sans-serif";

    var names = members.map(function (m) {
      var maxW = radius * 0.65, name = m.name;
      if (c.measureText(name).width > maxW) {
        while (name.length > 1 && c.measureText(name + "…").width > maxW) name = name.slice(0, -1);
        name += "…";
      }
      return name;
    });

    members.forEach(function (m, i) {
      var start = i * slice, end = start + slice;
      c.beginPath(); c.moveTo(center, center); c.arc(center, center, radius, start, end); c.closePath();
      c.fillStyle = m.color; c.fill();
      c.strokeStyle = "#fff"; c.lineWidth = 2; c.stroke();

      c.beginPath(); c.arc(center, center, radius + borderGap + borderWidth / 2, start, end);
      c.strokeStyle = hexToRgba(m.color, 0.5); c.lineWidth = borderWidth; c.stroke();

      c.save();
      c.translate(center, center); c.rotate(start + slice / 2);
      c.textAlign = "right"; c.font = "bold " + fontSize + "px sans-serif";
      c.lineWidth = 3; c.strokeStyle = "rgba(0,0,0,0.4)"; c.strokeText(names[i], radius - 15, fontSize / 3);
      c.fillStyle = "#fff"; c.fillText(names[i], radius - 15, fontSize / 3);
      c.restore();
    });

    // Hub: click it to spin.
    c.beginPath(); c.arc(center, center, radius * 0.15, 0, 2 * Math.PI);
    c.fillStyle = "#1f2937"; c.fill();
    c.strokeStyle = "#fff"; c.lineWidth = 3; c.stroke();
    cachedWheel = off;
  }

  function segmentAtArrow(rotation) {
    var slice = (2 * Math.PI) / members.length;
    var a = -Math.PI / 2 - rotation;
    a = ((a % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
    return Math.floor(a / slice);
  }

  function drawWheel(rotation) {
    resizeCanvas();
    var size = getCanvasSize();
    if (!members.length) { ctx.clearRect(0, 0, size, size); return; }
    if (!cachedWheel || cachedSize !== size) buildWheelCache();
    if (!cachedWheel) return;
    var center = size / 2;
    ctx.clearRect(0, 0, size, size);
    ctx.save(); ctx.translate(center, center); ctx.rotate(rotation);
    ctx.drawImage(cachedWheel, -center, -center, size, size);
    ctx.restore();
    var under = members[segmentAtArrow(rotation)];
    if (under) pointer.style.setProperty("--c", under.color); // the pointer takes the colour under it
  }

  function idleSpin() {
    if (isSpinning) return;
    currentRotation += 0.005;
    drawWheel(currentRotation);
    idleAnimationId = requestAnimationFrame(idleSpin);
  }
  function stopIdleSpin() {
    if (idleAnimationId) { cancelAnimationFrame(idleAnimationId); idleAnimationId = null; }
  }

  // Spin (eased, 5–7 turns) so the target slice ends under the pointer; the pointer ticks per slice.
  function spinWheelToTarget(targetIndex, callback) {
    isSpinning = true;
    stopIdleSpin();
    var duration = 3500, startRotation = currentRotation;
    var slice = (2 * Math.PI) / members.length;
    var target = -Math.PI / 2 - (targetIndex * slice + slice / 2);
    var fullSpins = (Math.floor(Math.random() * 3) + 5) * Math.PI * 2;
    while (target < startRotation) target += Math.PI * 2;
    target += fullSpins;
    var total = target - startRotation, startTime = performance.now(), lastSeg = -1;

    function tick() {
      pointer.classList.remove("is-tick");
      void pointer.offsetWidth; // restart the CSS tick animation
      pointer.classList.add("is-tick");
    }
    function animate(now) {
      var p = Math.min((now - startTime) / duration, 1);
      currentRotation = startRotation + total * (1 - Math.pow(1 - p, 5));
      drawWheel(currentRotation);
      var seg = segmentAtArrow(currentRotation);
      if (lastSeg !== -1 && seg !== lastSeg) tick();
      lastSeg = seg;
      if (p < 1) requestAnimationFrame(animate);
      else { isSpinning = false; if (callback) callback(); }
    }
    requestAnimationFrame(animate);
  }

  // ── "Already chosen" pills (text nodes: names are never parsed as HTML) ──
  function updateAlreadyChosenList(ids, groupId) {
    var list = document.getElementById("alreadyChosenList");
    var title = document.getElementById("alreadyChosenTitle");
    if (!ids.length) { alreadyChosenSection.classList.add("hidden"); return; }
    title.textContent = T.tAlready + " (" + ids.length + ")";
    var all = groupsData[groupId] || [];
    list.textContent = "";
    ids.forEach(function (id) {
      var m = all.find(function (x) { return x.id === id; });
      if (!m) return;
      var pill = document.createElement("span");
      pill.className = "ap-member";
      pill.style.setProperty("--c", m.color);
      pill.textContent = m.name;
      list.appendChild(pill);
    });
    alreadyChosenSection.classList.remove("hidden");
  }

  // ── Result dialog ──
  function openPopup(title, build) {
    popupTitle.textContent = title;
    popupNames.textContent = "";
    popupNames.className = "ap-picked";
    build();
    popup.showModal();
  }
  function showPopup(names) {
    openPopup(T.tSelected + " (" + names.length + ")", function () {
      popupNames.classList.toggle("is-many", names.length > 1);
      names.forEach(function (name) {
        var el = document.createElement("span");
        el.className = "ap-picked-name lp-soft";
        el.textContent = name;
        popupNames.appendChild(el);
      });
    });
  }
  function showMessage(text) {
    openPopup(T.tNotice, function () {
      var p = document.createElement("p");
      p.className = "ap-help";
      p.textContent = text;
      popupNames.appendChild(p);
    });
  }

  function updateWheel(groupId) {
    cachedWheel = null;
    stopIdleSpin();
    if (!groupId || !groupsData[groupId]) { wheelSection.classList.add("hidden"); return; }
    var chosen = alreadyChosenByGroup[groupId] || [];
    members = groupsData[groupId].filter(function (m) { return chosen.indexOf(m.id) === -1; });
    if (!members.length) { wheelSection.classList.add("hidden"); return; }
    wheelSection.classList.remove("hidden");
    resizeCanvas();
    drawWheel(currentRotation);
    idleSpin();
  }

  function updateResetLink() {
    resetBtn.href = groupSelect.value ? resetBase + "&group_id=" + groupSelect.value : resetBase;
  }

  groupSelect.addEventListener("change", function () {
    var id = groupSelect.value;
    updateResetLink();
    updateWheel(id);
    membersChosenInput.value = 1;
    membersChosenInput.max = (groupsData[id] || []).length || 99;
    alreadyChosenSection.classList.add("hidden");
    clearSessionInput.value = "1";
    window.history.pushState({ groupId: id }, "", window.location.pathname + "?group_id=" + id);
  });

  window.addEventListener("resize", function () {
    if (!wheelSection.classList.contains("hidden")) { cachedWheel = null; drawWheel(currentRotation); }
  });

  function setSpinning(on) {
    spinBtn.disabled = on;
    spinLabel.textContent = on ? T.tSpinning : T.tSpin;
  }

  function handleSpin() {
    var groupId = groupSelect.value;
    if (!groupId) { showMessage(T.tSelectGroup); return; }
    if (isSpinning) return;
    if (!members.length && groupsData[groupId]) {
      var chosen = alreadyChosenByGroup[groupId] || [];
      members = groupsData[groupId].filter(function (m) { return chosen.indexOf(m.id) === -1; });
    }
    if (!members.length) { showMessage(T.tAllChosen); return; }

    stopIdleSpin();
    setSpinning(true);
    wheelSection.classList.remove("hidden");
    var fd = new FormData(form);

    fetch(form.dataset.url, {
      method: "POST",
      body: fd,
      headers: { "X-CSRFToken": fd.get("csrfmiddlewaretoken"), "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          showMessage(data.all_chosen ? T.tAllChosen : data.error);
          setSpinning(false);
          if (data.all_chosen) wheelSection.classList.add("hidden");
          idleSpin();
          return;
        }
        var targetIndex = members.findIndex(function (m) { return m.id === data.chosen_ids[0]; });
        if (targetIndex === -1) { setSpinning(false); idleSpin(); return; }

        setTimeout(function () {
          resizeCanvas();
          drawWheel(currentRotation);
          clearSessionInput.value = "0";
          spinWheelToTarget(targetIndex, function () {
            var removeAfterSpin = document.getElementById("removeAfterSpin").checked;
            if (removeAfterSpin) {
              alreadyChosenByGroup[groupId] = data.already_chosen_ids;
              members = members.filter(function (m) { return data.chosen_ids.indexOf(m.id) === -1; });
              updateAlreadyChosenList(data.already_chosen_ids, groupId);
              updateWheel(groupId);
            }
            showPopup(data.chosen_members);
            setSpinning(false);
            if (!removeAfterSpin || members.length) idleSpin();
          });
        }, 100);
      })
      .catch(function () { setSpinning(false); idleSpin(); });
  }

  spinBtn.addEventListener("click", handleSpin);

  // Clicking the hub spins too.
  function isInCenter(e) {
    var rect = canvas.getBoundingClientRect();
    var x = e.clientX - rect.left, y = e.clientY - rect.top, center = rect.width / 2;
    return Math.sqrt(Math.pow(x - center, 2) + Math.pow(y - center, 2)) <= (center - 10) * 0.15;
  }
  canvas.addEventListener("click", function (e) { if (isInCenter(e)) handleSpin(); });
  canvas.addEventListener("mousemove", function (e) { canvas.style.cursor = isInCenter(e) ? "pointer" : "default"; });

  shuffleBtn.addEventListener("click", function () {
    if (!groupSelect.value || isSpinning || !members.length) return;
    for (var i = members.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = members[i]; members[i] = members[j]; members[j] = t;
    }
    cachedWheel = null;
    drawWheel(currentRotation);
  });

  updateResetLink();
  updateWheel(groupSelect.value);
})();
