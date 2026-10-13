// Countdown page (apps/timer/templates/timer/countdown.html), with a Document
// Picture-in-Picture mini window. Uses the shared helpers in timer.js
// (formatTime, updateTimerDisplay, showButtons, initPicker, getPickerValue, track).
//
// Timing: the remaining time always comes from the wall clock (endTime). The main
// tab's requestAnimationFrame only paints; a 250 ms interval also checks for the
// end, so the countdown still finishes while the tab is in the background (which
// is exactly when the PiP window is in use, and when browsers pause rAF).
(function () {
  var main = document.getElementById("timerMain"),
      ms = document.getElementById("timerMs"),
      setup = document.getElementById("setupCard"),
      timer = document.getElementById("timerCard"),
      clock = document.getElementById("clock"),
      btns = ["playBtn", "pauseBtn", "stopBtn"].map(function (id) { return document.getElementById(id); }),
      play = btns[0], pause = btns[1], stop = btns[2],
      scrollH = document.getElementById("scrollH"),
      scrollM = document.getElementById("scrollM"),
      scrollS = document.getElementById("scrollS"),
      ring = document.getElementById("progressRing"),
      totalLabel = document.getElementById("totalLabel"),
      CIRC = 565.49,
      // idle → running ⇄ paused; running → done at zero; stop → idle (setup again).
      state = "idle", remaining = 0, endTime = null, afId = null, watchdog = null,
      totalSet = 0;
  if (!main) return;

  ring.style.strokeDasharray = CIRC;
  ring.style.strokeDashoffset = 0;

  initPicker(scrollH, 99, 0);
  initPicker(scrollM, 59, 5);
  initPicker(scrollS, 59, 0);

  // Ring colour by progress: the CSS default (primary), then warning below half, error in the
  // last fifth. Written as var(...) rather than a resolved colour, so a theme change while
  // paused repaints the ring in the new theme's colours. Mixed with 20% text colour (like the
  // primary fill in apps.css) so pale theme colours, e.g. lemonade's warning, stay visible.
  function ringColor(progress) {
    if (progress > 0.5) return "";
    var c = progress > 0.2 ? "--color-warning" : "--color-error";
    return "color-mix(in oklab, var(" + c + ") 80%, var(--color-base-content))";
  }

  function updateRing() {
    var progress = totalSet > 0 ? remaining / totalSet : 1;
    ring.style.strokeDashoffset = CIRC * (1 - progress);
    ring.style.stroke = ringColor(progress);
    totalLabel.textContent = formatTime(totalSet).main;
  }

  function readRemaining() {
    if (state === "running" && endTime !== null) remaining = Math.max(0, endTime - Date.now());
  }

  // Reaching zero: record the full run once, stop the clock, leave a stop (reset) button.
  function finish() {
    remaining = 0; endTime = null; state = "done";
    if (afId) cancelAnimationFrame(afId);
    stopWatchdog();
    updateTimerDisplay(main, ms, 0); updateRing();
    clock.classList.remove("is-running");
    track("stop", totalSet);
    showButtons(btns, stop);
  }

  function tick() {
    if (state !== "running") return;
    readRemaining();
    if (remaining <= 0) { finish(); return; }
    updateTimerDisplay(main, ms, remaining);
    updateRing();
    afId = requestAnimationFrame(tick);
  }

  function startWatchdog() {
    stopWatchdog();
    watchdog = setInterval(function () {
      if (state !== "running") return;
      readRemaining();
      if (remaining <= 0) finish();
    }, 250);
  }
  function stopWatchdog() { if (watchdog) { clearInterval(watchdog); watchdog = null; } }

  function run() {
    endTime = Date.now() + remaining;
    state = "running";
    afId = requestAnimationFrame(tick);
    startWatchdog();
    clock.classList.add("is-running");
    showButtons(btns, pause);
  }

  document.getElementById("startBtn").addEventListener("click", function () {
    remaining = (getPickerValue(scrollH, 99) * 3600 + getPickerValue(scrollM, 59) * 60 + getPickerValue(scrollS, 59)) * 1000;
    if (remaining <= 0) return;
    totalSet = remaining;
    setup.classList.add("hidden"); timer.classList.remove("hidden");
    updateTimerDisplay(main, ms, remaining);
    updateRing();
    run();
    track("start");
  });

  document.querySelectorAll(".add-time-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var extra = parseInt(btn.dataset.seconds, 10) * 1000;
      if (state === "done") { remaining = 0; totalSet = 0; }
      remaining += extra;
      totalSet += extra;
      if (endTime !== null) endTime += extra;
      updateTimerDisplay(main, ms, remaining);
      updateRing();
      if (state === "done") run(); // adding time after the end starts it again
    });
  });

  function doPlay() { if (remaining > 0) run(); }

  function doPause() {
    readRemaining();
    state = "paused"; endTime = null;
    if (afId) cancelAnimationFrame(afId);
    stopWatchdog();
    clock.classList.remove("is-running");
    showButtons(btns, play, stop);
  }

  function doStop() {
    if (state !== "done") {
      var elapsed = totalSet - remaining;
      if (elapsed > 0) track("stop", elapsed);
    }
    state = "idle"; endTime = null;
    if (afId) cancelAnimationFrame(afId);
    stopWatchdog();
    clock.classList.remove("is-running");
    main.dataset.hours = "0";
    timer.classList.add("hidden"); setup.classList.remove("hidden");
  }

  play.addEventListener("click", doPlay);
  pause.addEventListener("click", doPause);
  stop.addEventListener("click", doStop);

  // ── Picture-in-Picture ──
  var pipBtn = document.getElementById("pipBtn");
  var pipWindow = null;

  if (!("documentPictureInPicture" in window)) pipBtn.classList.add("hidden");

  pipBtn.addEventListener("click", async function () {
    if (pipWindow) { pipWindow.close(); pipWindow = null; return; }

    try {
      pipWindow = await documentPictureInPicture.requestWindow({ width: 420, height: 340 });
    } catch (err) {
      console.error("Picture-in-Picture could not open:", err);
      pipWindow = null;
      return;
    }
    var pipDoc = pipWindow.document;

    // The PiP window has its own document, so it can't read the page's theme variables.
    // Copy the theme colours onto its root as --p, --bg, ... (daisyUI v5 stores them as full
    // oklch(...) values) and refresh them whenever the page's theme changes.
    function applyPipTheme() {
      var cs = getComputedStyle(document.documentElement), root = pipDoc.documentElement.style;
      [["--p", "--color-primary"], ["--bg", "--color-base-100"], ["--tx", "--color-base-content"],
       ["--warn", "--color-warning"], ["--err", "--color-error"]].forEach(function (pair) {
        root.setProperty(pair[0], cs.getPropertyValue(pair[1]).trim());
      });
    }
    applyPipTheme();
    var themeWatch = new MutationObserver(applyPipTheme);
    themeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });

    pipDoc.head.innerHTML = '<style>' +
      'body{margin:0;display:flex;align-items:center;justify-content:center;height:100vh;background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden}' +
      '.wrap{text-align:center}' +
      '.pip-ring{width:220px;height:220px;pointer-events:none;display:block}' +
      '.ring-bg{stroke:color-mix(in oklab,var(--tx) 12%,var(--bg))}' +
      '.ring-fill{stroke:color-mix(in oklab,var(--p) 85%,var(--tx));transition:stroke-dashoffset 0.1s linear}' +
      '.time{font-variant-numeric:tabular-nums;font-weight:bold;font-size:40px;color:var(--tx)}' +
      '.time-ms{font-size:20px;color:color-mix(in srgb,var(--tx) 40%,transparent)}' +
      '.total{font-size:14px;color:color-mix(in srgb,var(--tx) 40%,transparent);font-variant-numeric:tabular-nums;margin-top:4px}' +
      '.face{margin-top:-165px;position:relative}' +
      '.controls{margin-top:12px;display:flex;gap:10px;justify-content:center;min-height:44px}' +
      '.pip-btn{width:44px;height:44px;border:none;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#fff}' +
      '.pip-primary{background:var(--p)}' +
      '.pip-stop{background:var(--err)}' +
      '</style>';

    pipDoc.body.innerHTML =
      '<div class="wrap">' +
        '<svg class="pip-ring" viewBox="0 0 200 200">' +
          '<g transform="rotate(-90 100 100)">' +
            '<circle cx="100" cy="100" r="90" fill="none" stroke-width="8" class="ring-bg"/>' +
            '<circle id="pipRing" cx="100" cy="100" r="90" fill="none" stroke-width="8" stroke-linecap="round" class="ring-fill" style="stroke-dasharray:565.49;stroke-dashoffset:0"/>' +
          '</g>' +
        '</svg>' +
        '<div class="face">' +
          '<div><span id="pipMain" class="time">00:00</span><span id="pipMs" class="time-ms">.00</span></div>' +
          '<div id="pipTotal" class="total"></div>' +
        '</div>' +
        '<div class="controls">' +
          '<button id="pipPause" class="pip-btn pip-primary" style="display:flex" autofocus><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="3" width="4" height="18" rx="1"/><rect x="15" y="3" width="4" height="18" rx="1"/></svg></button>' +
          '<button id="pipPlay" class="pip-btn pip-primary" style="display:none"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg></button>' +
          '<button id="pipStop" class="pip-btn pip-stop" style="display:none"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="2"/></svg></button>' +
        '</div>' +
      '</div>';

    var pipRing = pipDoc.getElementById("pipRing"),
        pipMain = pipDoc.getElementById("pipMain"),
        pipMs = pipDoc.getElementById("pipMs"),
        pipTotal = pipDoc.getElementById("pipTotal"),
        pipPause = pipDoc.getElementById("pipPause"),
        pipPlay = pipDoc.getElementById("pipPlay"),
        pipStop = pipDoc.getElementById("pipStop");

    function syncPip() {
      if (!pipWindow) return;
      readRemaining();
      if (state === "running" && remaining <= 0) finish();
      var t = formatTime(remaining);
      pipMain.textContent = t.main;
      pipMs.textContent = "." + t.cs;
      pipTotal.textContent = formatTime(totalSet).main;
      var progress = totalSet > 0 ? remaining / totalSet : 1;
      pipRing.style.strokeDashoffset = CIRC * (1 - progress);
      pipRing.style.stroke = progress > 0.5 ? "" : "color-mix(in oklab, var(" + (progress > 0.2 ? "--warn" : "--err") + ") 80%, var(--tx))";

      // running: pause · paused: play + stop · done: stop (reset) · idle: nothing
      pipPause.style.display = state === "running" ? "flex" : "none";
      pipPlay.style.display = state === "paused" ? "flex" : "none";
      pipStop.style.display = state === "paused" || state === "done" ? "flex" : "none";
    }

    pipPause.addEventListener("click", function () { doPause(); syncPip(); });
    pipPlay.addEventListener("click", function () { doPlay(); syncPip(); });
    pipStop.addEventListener("click", function () { doStop(); if (pipWindow) { pipWindow.close(); pipWindow = null; } });

    // The PiP window's own rAF keeps painting while the main tab is backgrounded.
    var win = pipWindow, pipAf = null;
    function pipTick() {
      if (!pipWindow) return;
      syncPip();
      pipAf = win.requestAnimationFrame(pipTick);
    }
    pipTick();

    win.addEventListener("pagehide", function () {
      if (pipAf) win.cancelAnimationFrame(pipAf);
      themeWatch.disconnect();
      pipWindow = null;
    });
  });
})();
