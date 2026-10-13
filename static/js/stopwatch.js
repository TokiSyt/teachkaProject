// Stopwatch page (apps/timer/templates/timer/stopwatch.html). Uses the shared helpers in
// timer.js (formatTime, updateTimerDisplay, showButtons, track).
(function () {
  var main = document.getElementById("timerMain"),
      ms = document.getElementById("timerMs"),
      clock = document.getElementById("clock"),
      btns = ["playBtn", "pauseBtn", "flagBtn", "stopBtn"].map(function (id) { return document.getElementById(id); }),
      play = btns[0], pause = btns[1], flag = btns[2], stop = btns[3],
      flagsEl = document.getElementById("flagsSection"),
      listEl = document.getElementById("flagsList"),
      state = "idle", elapsed = 0, lastTick = null, afId = null,
      flags = [], lastFlagTime = 0;
  if (!main) return;

  function setRunning(on) { clock.classList.toggle("is-running", on); }

  function tick(ts) {
    if (state !== "running") return;
    if (lastTick !== null) elapsed += ts - lastTick;
    lastTick = ts;
    updateTimerDisplay(main, ms, elapsed);
    afId = requestAnimationFrame(tick);
  }

  play.addEventListener("click", function () {
    if (state === "idle") track("start");
    state = "running"; lastTick = null;
    afId = requestAnimationFrame(tick);
    setRunning(true);
    showButtons(btns, pause, flag);
  });

  pause.addEventListener("click", function () {
    state = "paused"; lastTick = null;
    if (afId) cancelAnimationFrame(afId);
    setRunning(false);
    showButtons(btns, play, stop);
  });

  stop.addEventListener("click", function () {
    if (elapsed > 0) track("stop", elapsed);
    state = "idle"; lastTick = null;
    if (afId) cancelAnimationFrame(afId);
    elapsed = 0; flags = []; lastFlagTime = 0;
    listEl.innerHTML = "";
    flagsEl.classList.add("hidden");
    setRunning(false);
    updateTimerDisplay(main, ms, 0);
    showButtons(btns, play);
  });

  flag.addEventListener("click", function () {
    track("flag");
    var lap = elapsed - lastFlagTime;
    flags.push(elapsed); lastFlagTime = elapsed;
    flagsEl.classList.remove("hidden");
    var t = formatTime(elapsed), l = formatTime(lap), row = document.createElement("div");
    row.className = "ap-row";
    row.innerHTML =
      '<span class="ap-row-main"><span class="ap-row-num">' + flags.length + '</span>' +
      '<span>' + t.main + '<span class="ap-row-dim">.' + t.cs + '</span></span></span>' +
      '<span class="ap-row-side">+' + l.main + '.' + l.cs + '</span>';
    listEl.prepend(row);
  });
})();
