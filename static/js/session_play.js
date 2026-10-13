// Live quiz player screen (apps/quizzmaker/templates/quizzmaker/session_play.html).
// Connects to the quiz WebSocket and renders each phase into #app: lobby, answering (options or
// typed answer), waiting, reveal (own result), leaderboard and final result. Code / URLs come from
// #app's data-*, labels from the #play-i18n JSON. Everything shown from the server goes through esc().
(function () {
  var root = document.getElementById("app");
  if (!root) return;
  var CODE = root.dataset.code;
  var HOME = root.dataset.home;
  var T = JSON.parse(document.getElementById("play-i18n").textContent);
  var LETTERS = ["A", "B", "C", "D"];
  var FLAME = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4"/></svg>';
  var BTN_PRIMARY = "btn btn-primary rounded-full w-full max-w-md";

  var ws = null, state = null, curRound = -1, closing = false;
  var selected = new Set(), typed = "", locked = false, answered = false;

  function streakBadge(n) { return n > 1 ? '<span class="qz-flame">' + FLAME + n + "</span>" : ""; }
  function el(html) { var d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; }
  function clear() { root.innerHTML = ""; }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  function icon(name, warn) { return '<div class="qz-icon' + (warn ? " is-warn" : "") + '"><i data-lucide="' + name + '"></i></div>'; }

  // ── Leave dialog ──
  document.addEventListener("click", function (e) {
    var open = e.target.closest("[data-dialog-open]");
    if (open) { var d = document.getElementById(open.dataset.dialogOpen); if (d) d.showModal(); return; }
    var close = e.target.closest("[data-dialog-close]");
    if (close) { var dlg = close.closest("dialog"); if (dlg) dlg.close(); }
  });

  // ── WebSocket ──
  function connect() {
    var scheme = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(scheme + "://" + location.host + "/ws/quiz/" + CODE + "/");
    ws.onmessage = function (e) { handle(JSON.parse(e.data)); };
    ws.onclose = function (e) {
      if (closing) return;
      // 4004 = game gone, 4003 = not allowed: stop looping, leave.
      if (e.code === 4003 || e.code === 4004) { closing = true; window.location.href = HOME; return; }
      // 4500 = live store unreachable: stop looping, show error.
      if (e.code === 4500) {
        closing = true;
        root.innerHTML = '<p class="text-error text-center">' + esc(T.unavailable) + "</p>";
        return;
      }
      setTimeout(connect, 1500);
    };
  }
  function send(obj) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj)); }

  function handle(msg) {
    if (msg.type === "state") onState(msg); // host back / any update clears the notice
    else if (msg.type === "host_left") renderHostLeft();
    else if (msg.type === "closed") { closing = true; window.location.href = HOME; }
    // "error": transient; ignore
  }

  function renderHostLeft() {
    clear();
    root.appendChild(el('<div class="qz-stage">' + icon("plug-zap", true) + '<p class="qz-title lp-soft">' + esc(T.host_left) + "</p></div>"));
    if (window.lucide) lucide.createIcons();
  }

  function onState(s) {
    // New question: reset local answer state.
    if (s.phase === "question" && s.current_round !== curRound) {
      curRound = s.current_round;
      selected = new Set();
      typed = "";
      locked = false;
      answered = false;
      if (s.my_answer) { // reconnected after already answering: show the waiting screen
        if (Array.isArray(s.my_answer)) s.my_answer.forEach(function (id) { selected.add(id); });
        else typed = s.my_answer;
        answered = true;
      }
    }
    if (s.phase !== "question") locked = true;
    state = s;
    render();
  }

  function render() {
    clear();
    if (!state) return;
    if (state.phase === "lobby") renderLobby();
    else if (state.phase === "question") renderQuestion();
    else if (state.phase === "reveal") renderReveal();
    else if (state.phase === "leaderboard") renderLeaderboard();
    else if (state.phase === "ended") renderEnded();
    if (window.lucide) lucide.createIcons();
  }

  function renderLobby() {
    root.appendChild(el('<div class="qz-stage">' + icon("gamepad-2") +
      '<h2 class="qz-title lp-soft">' + esc(state.quiz_title || "") + "</h2>" +
      "<p>" + esc(T.waiting) + "</p>" +
      '<p class="qz-label">' + esc(T.lobby_hint) + "</p></div>"));
  }

  function modeBadge(single) {
    return el('<span class="ap-chip gap-1.5"><i data-lucide="' + (single ? "circle-dot" : "list-checks") + '" class="w-3.5 h-3.5"></i>' + esc(single ? T.pick_one : T.pick_all) + "</span>");
  }

  function renderQuestion() {
    clear();
    var r = state.round || {};
    if (answered || locked) { renderWaiting(); return; } // no inputs once answered / locked

    var wrap = el('<div class="qz-stage"></div>');
    if (state.show_question && r.question) wrap.appendChild(el('<h2 class="qz-question is-small lp-soft">' + esc(r.question) + "</h2>"));
    wrap.appendChild(timerBar(r)); // between the question and the image
    if (r.image_url) {
      wrap.appendChild(el('<figure class="qz-img"><img src="' + esc(r.image_url) + '" alt="" style="--fx: ' + (r.focus_x ?? 50) + "%; --fy: " + (r.focus_y ?? 50) + '%"></figure>'));
    }

    if (r.question_type === "type_input") {
      var box = el('<form class="qz-form"><input type="text" inputmode="text" autocomplete="off" class="input" aria-label="' + esc(T.type_answer) + '">' +
        '<button type="submit" class="' + BTN_PRIMARY + '">' + esc(T.submit) + "</button></form>");
      var input = box.querySelector("input");
      input.placeholder = T.type_answer;
      input.value = typed;
      input.addEventListener("input", function () { typed = input.value; });
      box.addEventListener("submit", function (e) {
        e.preventDefault();
        typed = input.value.trim();
        if (!typed) return;
        submitAnswer(typed);
      });
      wrap.appendChild(box);
    } else {
      // select_correct / true_false: pick option(s), then Submit.
      var tf = r.question_type === "true_false";
      var single = !!r.single_select;
      if (!tf) wrap.appendChild(modeBadge(single));
      var grid = el('<div class="qz-opts"></div>');
      (r.answers || []).forEach(function (a, i) {
        var on = selected.has(a.id);
        // true_false: always localized True/False; select_correct hides text unless the host shares the question.
        var label = tf ? (i === 0 ? T.true : T.false) : (state.show_question ? a.text : "");
        var btn = el('<button type="button" class="qz-opt' + (tf ? " is-tf" : "") + (on ? " is-on" : "") + '" aria-pressed="' + on + '">' +
          (tf ? "" : '<span class="qz-opt-letter">' + LETTERS[i % 4] + "</span>") +
          '<span class="qz-opt-text">' + esc(label) + "</span>" + (on ? '<span aria-hidden="true">✓</span>' : "") + "</button>");
        btn.addEventListener("click", function () {
          if (single) { // radio behaviour: only one option may be selected
            if (selected.has(a.id)) selected.clear();
            else { selected.clear(); selected.add(a.id); }
          } else if (selected.has(a.id)) selected.delete(a.id);
          else selected.add(a.id);
          renderQuestion();
        });
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);
      var submit = el('<button type="button" class="' + BTN_PRIMARY + '">' + esc(T.submit) + "</button>");
      submit.disabled = !selected.size;
      submit.addEventListener("click", function () { if (selected.size) submitAnswer(Array.from(selected)); });
      wrap.appendChild(submit);
    }
    root.appendChild(wrap);
  }

  function submitAnswer(value) {
    send({ action: "answer", round_idx: curRound, value: value });
    answered = true;
    renderQuestion();
  }

  function renderWaiting() {
    clear();
    root.appendChild(el('<div class="qz-stage">' + icon("check") + '<p class="qz-title lp-soft">' + esc(T.waiting_others) + "</p></div>"));
    if (window.lucide) lucide.createIcons();
  }

  function timerBar(r) {
    var track = el('<div class="qz-timer"></div>');
    if (!r.time_limit || !state.round_started_at) { track.classList.add("hidden"); return track; }
    var fill = document.createElement("span");
    track.appendChild(fill);
    (function tick() {
      var frac = Math.max(0, Math.min(1, 1 - (Date.now() / 1000 - state.round_started_at) / r.time_limit));
      fill.style.width = (frac * 100) + "%";
      if (frac > 0 && !locked) setTimeout(tick, 250);
    })();
    return track;
  }

  function renderReveal() {
    var rev = state.reveal || {};
    var me = rev.me || { points: 0, full: false, earned: false, score: 0, streak: 0, rank: null };
    var acceptAll = !!rev.accept_all;
    var label = T.missed, cls = "is-miss";
    if (acceptAll) { label = T.submitted; cls = "is-good"; }
    else if (me.full) { label = T.correct; cls = "is-good"; }
    else if (me.earned) { label = T.partial; cls = "is-part"; }
    var yourAnswer = (acceptAll && me.your_answer)
      ? '<div class="qz-ans max-w-md w-full"><p>' + esc(T.your_answer) + "</p><p>" + esc(me.your_answer) + "</p></div>"
      : "";
    root.appendChild(el('<div class="qz-stage">' +
      '<h2 class="qz-result lp-soft ' + cls + '">' + esc(label) + "</h2>" + yourAnswer +
      '<p class="qz-points">+' + me.points + "</p>" +
      '<div class="qz-stats">' +
        '<span class="ap-chip">' + esc(T.rank) + ": <b class=\"ml-1\">#" + (me.rank ?? "?") + "</b></span>" +
        '<span class="ap-chip">' + esc(T.score) + ': <b class="ml-1">' + me.score + "</b></span>" +
        '<span class="ap-chip">' + esc(T.streak) + ': <b class="ml-1">' + me.streak + "</b></span>" +
      "</div></div>"));
  }

  function leaderboardEl(limit) {
    var mine = state.me || null;
    var rows = (state.leaderboard || []).slice(0, limit).map(function (row) {
      var me = mine && row.nickname === mine.nickname;
      return '<li class="' + (me ? "is-lead" : "") + '"><span><span class="qz-rank">#' + row.rank + "</span>" + esc(row.nickname) + streakBadge(row.streak) +
        '</span><span class="qz-score">' + row.score + "</span></li>";
    }).join("");
    return '<ul class="qz-lb">' + rows + "</ul>";
  }

  function renderLeaderboard() {
    var mine = state.me || null;
    root.appendChild(el('<div class="qz-stage"><h2 class="qz-title lp-soft">' + esc(T.leaderboard) + "</h2>" +
      (mine ? '<p class="qz-muted">' + esc(T.rank) + " <b>#" + mine.rank + "</b> · " + mine.score + " " + esc(T.score) + "</p>" : "") +
      leaderboardEl(8) + "</div>"));
  }

  function renderEnded() {
    var mine = state.me || null;
    root.appendChild(el('<div class="qz-stage">' + icon("trophy") + '<h2 class="qz-title lp-soft">' + esc(T.final) + "</h2>" +
      (mine ? '<p class="text-lg">' + esc(T.rank) + " <b>#" + mine.rank + "</b> · " + mine.score + " " + esc(T.score) + "</p>" : "") +
      leaderboardEl(5) + '<p class="qz-muted">' + esc(T.thanks) + "</p></div>"));
  }

  connect();
})();
