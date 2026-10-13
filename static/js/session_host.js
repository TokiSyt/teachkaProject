// Live quiz host screen (apps/quizzmaker/templates/quizzmaker/session_host.html).
// Connects to the quiz WebSocket and renders each phase (lobby, question, reveal, leaderboard,
// ended + per-question review) into #app. Game code / URLs come from #app's data-*, labels from
// the #host-i18n JSON. Everything shown from the server goes through esc().
(function () {
  var root = document.getElementById("app");
  if (!root) return;
  var CODE = root.dataset.code;
  var HOME = root.dataset.home;
  var JOIN = root.dataset.join;
  var T = JSON.parse(document.getElementById("host-i18n").textContent);
  var LETTERS = ["A", "B", "C", "D"];
  var FLAME = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4"/></svg>';
  var BTN = "btn rounded-full";
  var BTN_PRIMARY = BTN + " btn-primary px-8";
  var BTN_GHOST = BTN + " btn-ghost border border-base-300 font-medium text-base-content/75";

  var ws = null, state = null, reviewIdx = null, reviewData = null, closing = false;

  function streakBadge(n) { return n > 1 ? '<span class="qz-flame">' + FLAME + n + "</span>" : ""; }
  function el(html) { var d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; }
  function clear() { root.innerHTML = ""; }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  // true_false: localized True/False by index; other types: the stored option text.
  function optText(qtype, text, i) { return qtype === "true_false" ? (i === 0 ? T.true : T.false) : esc(text); }

  // ── Dialogs (close room, player) ──
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
      if (e.code === 4003 || e.code === 4004) { closing = true; window.location.href = HOME; return; }
      if (e.code === 4500) {
        closing = true;
        root.innerHTML = '<p class="text-error text-center my-auto">' + esc(T.unavailable) + "</p>";
        return;
      }
      setTimeout(connect, 1500);
    };
  }
  function send(obj) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj)); }

  function handle(msg) {
    if (msg.type === "state") { state = msg; if (state.phase !== "ended") { reviewIdx = null; reviewData = null; } render(); }
    else if (msg.type === "review") { reviewData = msg; renderReview(); }
    else if (msg.type === "closed") { closing = true; window.location.href = HOME; }
    else if (msg.type === "error") { window.alert(msg.message); }
  }

  document.getElementById("close-confirm").addEventListener("click", function () {
    send({ action: "close" });
    document.getElementById("close-modal").close();
  });

  // ── Player dialog: rename / kick ──
  var editingPlayer = null;
  function openPlayerModal(nick) {
    editingPlayer = nick;
    document.getElementById("player-modal-name").textContent = nick;
    document.getElementById("player-name-input").value = nick;
    document.getElementById("player-edit-row").classList.add("hidden"); // hidden until edit is clicked
    document.getElementById("player-modal").showModal();
  }
  document.getElementById("player-edit-toggle").addEventListener("click", function () {
    document.getElementById("player-edit-row").classList.remove("hidden");
    document.getElementById("player-name-input").focus();
  });
  document.getElementById("player-save").addEventListener("click", function () {
    var v = document.getElementById("player-name-input").value.trim();
    if (v && editingPlayer) send({ action: "rename", nickname: editingPlayer, new_name: v });
    document.getElementById("player-modal").close();
  });
  document.getElementById("player-kick").addEventListener("click", function () {
    if (editingPlayer) send({ action: "kick", nickname: editingPlayer });
    document.getElementById("player-modal").close();
  });

  // ── Rendering ──
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

  function button(cls, html, onClick) {
    var b = el('<button type="button" class="' + cls + '">' + html + "</button>");
    if (onClick) b.addEventListener("click", onClick);
    return b;
  }

  function renderLobby() {
    var players = state.players || [];
    var joinBase = location.host + JOIN;
    var chips = players.length
      ? players.map(function (n, i) {
          return '<button type="button" data-pi="' + i + '" class="' + BTN_GHOST + ' btn-sm">' + esc(n) + "</button>";
        }).join("")
      : '<p class="qz-muted">' + esc(T.no_players) + "</p>";
    var node = el(
      '<div class="qz-stage">' +
        '<h1 class="qz-title lp-soft">' + esc(state.quiz_title || "") + "</h1>" +
        "<div>" +
          '<p class="qz-label">' + esc(T.join_at) + "</p>" +
          '<p class="qz-joinurl">' + esc(joinBase) + "<b>" + esc(state.code) + "</b>/</p>" +
          '<p class="qz-label mt-3 mb-2">' + esc(T.or_enter) + "</p>" +
          '<div class="qz-code lp-soft">' + esc(state.code) + "</div>" +
        "</div>" +
        '<label class="ap-switch"><input type="checkbox" id="show-q" class="toggle toggle-primary toggle-sm" ' + (state.show_question ? "checked" : "") + ">" + esc(T.show_q) + "</label>" +
        '<div class="qz-players">' + chips + "</div>" +
      "</div>");
    var start = button(BTN_PRIMARY, '<i data-lucide="play" class="w-4 h-4"></i>' + esc(T.start) + " (" + players.length + ")", function () { send({ action: "start" }); });
    start.disabled = !players.length;
    node.appendChild(start);
    node.querySelector("#show-q").addEventListener("change", function (e) { send({ action: "set_show_question", value: e.target.checked }); });
    node.querySelectorAll("[data-pi]").forEach(function (b) {
      b.addEventListener("click", function () { openPlayerModal(players[+b.dataset.pi]); });
    });
    root.appendChild(node);
  }

  function questionHeader() {
    return '<div class="qz-head"><span>' + esc(T.round) + " " + (state.current_round + 1) + " " + esc(T.of) + " " + state.num_rounds + '</span><span id="timer"></span></div>';
  }

  function imageEl(r) {
    return el('<figure class="qz-img"><img src="' + esc(r.image_url) + '" alt="" style="--fx: ' + (r.focus_x ?? 50) + "%; --fy: " + (r.focus_y ?? 50) + '%"></figure>');
  }

  function modeBadge(single) {
    return el('<span class="ap-chip gap-1.5"><i data-lucide="' + (single ? "circle-dot" : "list-checks") + '" class="w-3.5 h-3.5"></i>' + esc(single ? T.pick_one : T.pick_all) + "</span>");
  }

  function renderQuestion() {
    var r = state.round || {};
    var node = el('<div class="qz-stage">' + questionHeader() + "</div>");
    node.appendChild(el('<h1 class="qz-question lp-soft">' + esc(r.question || "") + "</h1>"));
    if (r.time_limit && state.round_started_at) {
      node.appendChild(el('<div class="qz-timer"><span id="timer-fill"></span></div>')); // between question and image
    }
    if (r.image_url) node.appendChild(imageEl(r));
    if (r.question_type === "type_input") {
      node.appendChild(el('<p class="qz-muted text-lg">' + esc(T.players_type) + "</p>"));
    } else {
      var tf = r.question_type === "true_false";
      if (!tf) node.appendChild(modeBadge(!!r.single_select));
      var grid = el('<div class="qz-opts"></div>');
      (r.answers || []).forEach(function (a, i) {
        grid.appendChild(el('<div class="qz-opt' + (tf ? " is-tf" : "") + '">' +
          (tf ? "" : '<span class="qz-opt-letter">' + LETTERS[i % 4] + "</span>") +
          '<span class="qz-opt-text">' + optText(r.question_type, a.text, i) + "</span></div>"));
      });
      node.appendChild(grid);
    }
    node.appendChild(button(BTN_PRIMARY, esc(T.reveal), function () { send({ action: "reveal" }); }));
    root.appendChild(node);
    startTimer(r);
  }

  function startTimer(r) {
    var fill = document.getElementById("timer-fill");
    if (!fill || !r.time_limit || !state.round_started_at) return;
    (function tick() {
      if (!state || state.phase !== "question") return;
      var frac = Math.max(0, Math.min(1, 1 - (Date.now() / 1000 - state.round_started_at) / r.time_limit));
      fill.style.width = (frac * 100) + "%";
      if (frac > 0) setTimeout(tick, 250);
    })();
  }

  // Shows/hides a block behind a pair of toggle buttons.
  function toggleBlock(showLabel, buildExpanded) {
    var holder = el('<div class="flex flex-col items-center gap-3 w-full"></div>');
    function collapsed() {
      holder.innerHTML = "";
      holder.appendChild(button(BTN_GHOST + " btn-sm", esc(showLabel), expanded));
    }
    function expanded() {
      holder.innerHTML = "";
      holder.appendChild(buildExpanded());
      holder.appendChild(button(BTN_GHOST + " btn-sm", esc(T.hide_answers), collapsed));
    }
    collapsed();
    return holder;
  }

  function renderReveal() {
    var r = state.round || {};
    var rev = state.reveal || {};
    var node = el('<div class="qz-stage">' + questionHeader() + "</div>");
    node.appendChild(el('<h1 class="qz-question is-small lp-soft">' + esc(r.question || "") + "</h1>"));

    if (r.question_type === "type_input" && rev.accept_all) {
      node.appendChild(answersListEl(rev.answers_list || []));
    } else if (r.question_type === "type_input") {
      var d = rev.distribution || { right: 0, wrong: 0 };
      var texts = rev.correct_texts || [];
      // The first accepted answer + the right/wrong tally; more on demand.
      var block = el('<div class="flex flex-col items-center gap-2 w-full">' +
        '<p class="qz-label">' + esc(T.correct) + "</p>" +
        '<p class="qz-big-answer lp-soft">' + esc(texts[0] || "") + "</p>" +
        '<p class="qz-muted">' + d.right + " " + esc(T.right) + " · " + d.wrong + " " + esc(T.wrong) + "</p></div>");
      if (texts.length > 1) {
        block.appendChild(toggleBlock(T.show_accepted, function () {
          var list = el('<div class="flex flex-wrap gap-2 justify-center"></div>');
          texts.forEach(function (t) { list.appendChild(el('<span class="ap-chip">' + esc(t) + "</span>")); });
          return list;
        }));
      }
      var submissions = (rev.answers_list || []).filter(function (a) { return a.text && a.text.trim(); });
      if (submissions.length) {
        block.appendChild(toggleBlock(T.show_all_answers, function () { return answersListEl(rev.answers_list, rev.correct_texts); }));
      }
      node.appendChild(block);
    } else {
      var tf = r.question_type === "true_false";
      var counts = (rev.distribution && rev.distribution.counts) || {};
      var correct = new Set(rev.correct_ids || []);
      var grid = el('<div class="qz-opts"></div>');
      (r.answers || []).forEach(function (a, i) {
        var isC = correct.has(a.id);
        grid.appendChild(el('<div class="qz-opt' + (tf ? " is-tf" : "") + (isC ? " is-correct" : " is-dim") + '">' +
          (tf ? "" : '<span class="qz-opt-letter">' + LETTERS[i % 4] + "</span>") +
          '<span class="qz-opt-text">' + optText(r.question_type, a.text, i) + (isC ? " ✓" : "") + "</span>" +
          '<span class="qz-opt-count">' + (counts[a.id] || 0) + "</span></div>"));
      });
      node.appendChild(grid);
    }
    node.appendChild(button(BTN_PRIMARY, esc(T.next) + " →", function () { send({ action: "next" }); }));
    root.appendChild(node);
  }

  // Every participant's submitted answer; ticks the ones matching an accepted answer (optional).
  function answersListEl(list, correctTexts) {
    var correct = correctTexts ? new Set(correctTexts) : null;
    var items = (list || []).filter(function (a) { return a.text && a.text.trim(); });
    var cards = items.length
      ? items.map(function (a) {
          var ok = correct && correct.has(a.text.trim().toLowerCase());
          return '<div class="qz-ans' + (ok ? " is-ok" : "") + '"><p>' + esc(a.nickname) + "</p><p>" + esc(a.text) +
            (ok ? ' <span class="qz-ans-ok">✓</span>' : "") + "</p></div>";
        }).join("")
      : '<p class="qz-muted col-span-full text-center">' + esc(T.no_answers) + "</p>";
    return el('<div class="flex flex-col items-center gap-3 w-full"><p class="qz-label">' + esc(T.all_answers) + '</p><div class="qz-answers">' + cards + "</div></div>");
  }

  function leaderboardEl(limit, leadFirst) {
    var rows = (state.leaderboard || []).slice(0, limit).map(function (row) {
      var lead = leadFirst && row.rank === 1;
      return '<li class="' + (lead ? "is-lead" : "") + '"><span><span class="qz-rank">#' + row.rank + "</span>" + esc(row.nickname) + streakBadge(row.streak) +
        '</span><span class="qz-score">' + row.score + "</span></li>";
    }).join("");
    return el('<ul class="qz-lb">' + rows + "</ul>");
  }

  function renderLeaderboard() {
    var node = el('<div class="qz-stage"><h2 class="qz-title lp-soft">' + esc(T.standings) + "</h2></div>");
    node.appendChild(leaderboardEl(10, true));
    node.appendChild(button(BTN_PRIMARY, esc(T.next) + " →", function () { send({ action: "next" }); }));
    root.appendChild(node);
  }

  function renderEnded() {
    var node = el('<div class="qz-stage"><h1 class="qz-title lp-soft">' + esc(T.final) + "</h1></div>");
    node.appendChild(leaderboardEl(10, true));

    // Per-question review (ephemeral): one pill per round.
    node.appendChild(el('<p class="qz-label mt-2">' + esc(T.review) + "</p>"));
    var buttons = el('<div class="flex flex-wrap gap-2 justify-center"></div>');
    for (var i = 0; i < state.num_rounds; i++) {
      (function (idx) {
        buttons.appendChild(button((reviewIdx === idx ? BTN + " btn-primary" : BTN_GHOST) + " btn-sm btn-circle", String(idx + 1), function () {
          reviewIdx = idx;
          send({ action: "review", round_idx: idx });
          renderEnded.refresh();
        }));
      })(i);
    }
    node.appendChild(buttons);
    node.appendChild(el('<div id="review-panel" class="w-full flex justify-center"></div>'));

    // "Done" closes the room for everyone, so players are sent home.
    node.appendChild(button(BTN_GHOST, esc(T.done), function () { send({ action: "close" }); }));
    root.appendChild(node);
    if (reviewData && reviewIdx === reviewData.round_idx) renderReview();
  }
  renderEnded.refresh = function () { render(); };

  function renderReview() {
    var panel = document.getElementById("review-panel");
    if (!panel || !reviewData) return;
    var d = reviewData;
    var body = "";
    if (d.question_type === "type_input" && d.accept_all) {
      var items = (d.answers_list || []).filter(function (a) { return a.text && a.text.trim(); });
      body = items.length
        ? items.map(function (a) { return '<div class="qz-review-row"><span>' + esc(a.nickname) + '</span><span class="font-medium text-base-content">' + esc(a.text) + "</span><span></span></div>"; }).join("")
        : '<p class="qz-muted">' + esc(T.no_answers) + "</p>";
    } else if (d.question_type === "type_input") {
      var dist = d.distribution || {};
      body = '<p class="qz-big-answer lp-soft text-xl">' + esc((d.correct_texts || []).join("   ·   ")) + "</p>" +
             '<p class="qz-muted">' + (dist.right || 0) + " " + esc(T.right) + " · " + (dist.wrong || 0) + " " + esc(T.wrong) + "</p>";
    } else {
      var counts = (d.distribution && d.distribution.counts) || {};
      var correct = new Set(d.correct_ids || []);
      var tf = d.question_type === "true_false";
      body = (d.answers || []).map(function (a, i) {
        var isC = correct.has(a.id);
        return '<div class="qz-review-row' + (isC ? " is-correct" : "") + '">' + (tf ? "" : '<span class="w-5">' + LETTERS[i % 4] + "</span>") +
          "<span>" + optText(d.question_type, a.text, i) + (isC ? " ✓" : "") + "</span><span>" + (counts[a.id] || 0) + "</span></div>";
      }).join("");
    }
    panel.innerHTML = '<div class="qz-review"><p class="font-medium mb-2">' + esc(d.question) + "</p>" + body + "</div>";
  }

  connect();
})();
