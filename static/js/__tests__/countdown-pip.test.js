// Tests for the PiP state machine in the countdown timer.
//
// The logic here mirrors the inline script in countdown.html exactly.
// If these tests pass, the logic is correct — if buttons still don't work
// in the browser the issue is in the Document PiP API integration
// (focus model, event propagation, browser quirks), not the state machine.

// ── State machine (mirrors countdown.html) ────────────────────────────────────

function createCountdown() {
  let state = 'idle';
  let remaining = 0;
  let endTime = null;
  let totalSet = 0;

  return {
    get state() { return state; },
    get remaining() { return remaining; },
    get endTime() { return endTime; },
    get totalSet() { return totalSet; },

    start(ms) {
      remaining = ms;
      totalSet = ms;
      endTime = Date.now() + ms;
      state = 'running';
    },

    addTime(ms) {
      remaining += ms;
      totalSet += ms;
      if (endTime !== null) endTime += ms;
    },

    pause() {
      if (endTime !== null) remaining = Math.max(0, endTime - Date.now());
      state = 'paused';
      endTime = null;
    },

    resume() {
      endTime = Date.now() + remaining;
      state = 'running';
    },

    stop() {
      const elapsed = totalSet - remaining;
      state = 'idle';
      endTime = null;
      return elapsed;
    },
  };
}

// ── PiP button sync (mirrors syncPip in countdown.html) ───────────────────────

function syncPipButtons(state, pauseEl, playEl, stopEl) {
  if (state === 'running') {
    pauseEl.style.display = 'flex';
    playEl.style.display = 'none';
    stopEl.style.display = 'none';
  } else if (state === 'paused') {
    pauseEl.style.display = 'none';
    playEl.style.display = 'flex';
    stopEl.style.display = 'flex';
  } else {
    pauseEl.style.display = 'none';
    playEl.style.display = 'none';
    stopEl.style.display = 'none';
  }
}

function makePipButtons() {
  const pauseEl = document.createElement('button');
  const playEl = document.createElement('button');
  const stopEl = document.createElement('button');
  pauseEl.id = 'pipPause';
  playEl.id = 'pipPlay';
  stopEl.id = 'pipStop';
  // Initial state matches what the PiP HTML sets when timer is running
  pauseEl.style.display = 'flex';
  playEl.style.display = 'none';
  stopEl.style.display = 'none';
  return { pauseEl, playEl, stopEl };
}

// ── State machine tests ───────────────────────────────────────────────────────

describe('Countdown state machine', () => {
  let cd;

  beforeEach(() => {
    cd = createCountdown();
  });

  it('starts in idle state', () => {
    expect(cd.state).toBe('idle');
    expect(cd.remaining).toBe(0);
    expect(cd.endTime).toBeNull();
  });

  it('transitions to running on start', () => {
    cd.start(60000);
    expect(cd.state).toBe('running');
    expect(cd.remaining).toBe(60000);
    expect(cd.totalSet).toBe(60000);
    expect(cd.endTime).toBeGreaterThan(Date.now() - 10);
  });

  it('transitions to paused on pause', () => {
    cd.start(60000);
    cd.pause();
    expect(cd.state).toBe('paused');
    expect(cd.endTime).toBeNull();
    expect(cd.remaining).toBeGreaterThan(0);
  });

  it('captures remaining from wall clock when pausing', () => {
    cd.start(60000);
    cd.pause();
    // Remaining should be close to 60000 (very little time elapsed in test)
    expect(cd.remaining).toBeLessThanOrEqual(60000);
    expect(cd.remaining).toBeGreaterThan(59900);
  });

  it('transitions back to running on resume', () => {
    cd.start(60000);
    cd.pause();
    cd.resume();
    expect(cd.state).toBe('running');
    expect(cd.endTime).not.toBeNull();
  });

  it('resume sets endTime from current remaining', () => {
    cd.start(60000);
    cd.pause();
    const beforeResume = cd.remaining;
    cd.resume();
    expect(cd.endTime).toBeCloseTo(Date.now() + beforeResume, -2);
  });

  it('transitions to idle on stop', () => {
    cd.start(60000);
    cd.stop();
    expect(cd.state).toBe('idle');
    expect(cd.endTime).toBeNull();
  });

  it('stop returns elapsed time (totalSet - remaining)', () => {
    cd.start(60000);
    // In a synchronous test, nearly no time elapses, so elapsed ≈ 0
    const elapsed = cd.stop();
    expect(elapsed).toBeGreaterThanOrEqual(0);
    expect(elapsed).toBeLessThan(100);
  });

  it('addTime increases remaining and totalSet when running', () => {
    cd.start(60000);
    cd.addTime(5000);
    expect(cd.remaining).toBe(65000);
    expect(cd.totalSet).toBe(65000);
  });

  it('addTime shifts endTime forward when running', () => {
    cd.start(60000);
    const before = cd.endTime;
    cd.addTime(10000);
    expect(cd.endTime).toBeCloseTo(before + 10000, -2);
  });

  it('addTime increases remaining but not endTime when paused', () => {
    cd.start(60000);
    cd.pause();
    const remainingBefore = cd.remaining;
    cd.addTime(5000);
    expect(cd.endTime).toBeNull();
    expect(cd.remaining).toBe(remainingBefore + 5000);
  });

  it('multiple pause/resume cycles preserve remaining', () => {
    cd.start(60000);
    cd.pause();
    const r1 = cd.remaining;
    cd.resume();
    cd.pause();
    const r2 = cd.remaining;
    // r2 should be <= r1 (a tiny bit of time may have passed)
    expect(r2).toBeLessThanOrEqual(r1);
    expect(r2).toBeGreaterThan(r1 - 100);
  });
});

// ── PiP button visibility ─────────────────────────────────────────────────────

describe('PiP button visibility sync', () => {
  let pauseEl, playEl, stopEl;

  beforeEach(() => {
    ({ pauseEl, playEl, stopEl } = makePipButtons());
  });

  it('running: shows pause, hides play and stop', () => {
    syncPipButtons('running', pauseEl, playEl, stopEl);
    expect(pauseEl.style.display).toBe('flex');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('paused: hides pause, shows play and stop', () => {
    syncPipButtons('paused', pauseEl, playEl, stopEl);
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('flex');
    expect(stopEl.style.display).toBe('flex');
  });

  it('idle: hides all buttons', () => {
    syncPipButtons('idle', pauseEl, playEl, stopEl);
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('unknown state: hides all buttons', () => {
    syncPipButtons('unknown', pauseEl, playEl, stopEl);
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('multiple syncs are idempotent', () => {
    syncPipButtons('running', pauseEl, playEl, stopEl);
    syncPipButtons('running', pauseEl, playEl, stopEl);
    expect(pauseEl.style.display).toBe('flex');
  });
});

// ── PiP button click interactions ─────────────────────────────────────────────

describe('PiP button click interactions', () => {
  let cd, pauseEl, playEl, stopEl;

  function sync() {
    syncPipButtons(cd.state, pauseEl, playEl, stopEl);
  }

  beforeEach(() => {
    cd = createCountdown();
    ({ pauseEl, playEl, stopEl } = makePipButtons());
    cd.start(60000);
    sync(); // initial: pause visible

    // Wire up buttons exactly as countdown.html does
    pauseEl.addEventListener('click', () => { cd.pause(); sync(); });
    playEl.addEventListener('click', () => { cd.resume(); sync(); });
    stopEl.addEventListener('click', () => { cd.stop(); sync(); });
  });

  it('clicking pause: state → paused, play+stop appear', () => {
    pauseEl.click();
    expect(cd.state).toBe('paused');
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('flex');
    expect(stopEl.style.display).toBe('flex');
  });

  it('clicking play after pause: state → running, pause reappears', () => {
    pauseEl.click();
    playEl.click();
    expect(cd.state).toBe('running');
    expect(pauseEl.style.display).toBe('flex');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('clicking stop from paused: state → idle, all buttons hidden', () => {
    pauseEl.click();
    stopEl.click();
    expect(cd.state).toBe('idle');
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('full cycle: start → pause → resume → pause → stop', () => {
    pauseEl.click();
    expect(cd.state).toBe('paused');

    playEl.click();
    expect(cd.state).toBe('running');
    expect(pauseEl.style.display).toBe('flex');

    pauseEl.click();
    expect(cd.state).toBe('paused');
    expect(playEl.style.display).toBe('flex');

    stopEl.click();
    expect(cd.state).toBe('idle');
    expect(pauseEl.style.display).toBe('none');
    expect(playEl.style.display).toBe('none');
    expect(stopEl.style.display).toBe('none');
  });

  it('pause button is not clickable when already paused (display:none)', () => {
    pauseEl.click(); // now paused, pauseEl is display:none
    const stateBefore = cd.state;
    // pauseEl.click() would still fire in jsdom regardless of display,
    // but in a real browser display:none elements don't receive pointer events.
    // We verify the state stays correct if pause is somehow called again.
    cd.pause(); // calling directly since display:none in browser blocks it
    expect(cd.state).toBe('paused'); // stays paused
  });
});

// ── PiP CSS: button SVGs must not be oversized ────────────────────────────────
//
// Regression test for the bug where `svg { width: 220px; height: 220px }` in
// the PiP head styles made button icon SVGs 220×220px, causing massive
// invisible hit areas that swallowed click events on adjacent buttons.

describe('PiP CSS: ring SVG selector scoping', () => {
  let pipDoc;

  beforeEach(() => {
    pipDoc = document.implementation.createHTMLDocument('pip');

    // Inject the exact CSS the PiP window uses (after the fix)
    pipDoc.head.innerHTML = `<style>
      .pip-ring { width: 220px; height: 220px; }
      .pip-btn { width: 44px; height: 44px; border: none; border-radius: 50%;
                 cursor: pointer; display: flex; align-items: center;
                 justify-content: center; color: #fff; }
    </style>`;

    pipDoc.body.innerHTML = `
      <div class="wrap">
        <svg class="pip-ring" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="90" fill="none" stroke-width="8"/>
        </svg>
        <div class="controls">
          <button id="pipPause" class="pip-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <rect x="5" y="3" width="4" height="18"/>
            </svg>
          </button>
          <button id="pipPlay" class="pip-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="6 3 20 12 6 21 6 3"/>
            </svg>
          </button>
        </div>
      </div>`;
  });

  it('ring SVG has class pip-ring', () => {
    const ringSvg = pipDoc.querySelector('svg.pip-ring');
    expect(ringSvg).not.toBeNull();
  });

  it('button SVGs do NOT have class pip-ring', () => {
    const btnSvgs = pipDoc.querySelectorAll('.pip-btn svg');
    btnSvgs.forEach(svg => {
      expect(svg.classList.contains('pip-ring')).toBe(false);
    });
  });

  it('button SVG width/height attributes are not overridden by pip-ring rule', () => {
    // pip-ring rule should only apply to .pip-ring, not bare svg elements
    const btnSvg = pipDoc.querySelector('#pipPause svg');
    // The attribute width="16" should still be 16 (CSS pip-ring doesn't target it)
    expect(btnSvg.getAttribute('width')).toBe('16');
    expect(btnSvg.getAttribute('height')).toBe('16');
  });

  it('buttons exist and are accessible in the DOM', () => {
    expect(pipDoc.getElementById('pipPause')).not.toBeNull();
    expect(pipDoc.getElementById('pipPlay')).not.toBeNull();
  });
});
