import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Execute timer.js in a controlled scope to extract its functions.
// timer.js is a plain script (no exports), so we run it via new Function
// and pull out the functions we want to test.
const timerCode = readFileSync(resolve(__dirname, '../timer.js'), 'utf-8');
const fns = {};
new Function(
  'requestAnimationFrame', 'cancelAnimationFrame', 'window', '_out',
  timerCode + `
    _out.formatTime = formatTime;
    _out.showButtons = showButtons;
    _out.updateTimerDisplay = updateTimerDisplay;
  `
)(() => 1, () => {}, globalThis, fns);

const { formatTime, showButtons, updateTimerDisplay } = fns;

// ── formatTime ────────────────────────────────────────────────────────────────

describe('formatTime', () => {
  it('formats zero as 00:00', () => {
    const t = formatTime(0);
    expect(t.main).toBe('00:00');
    expect(t.cs).toBe('00');
  });

  it('formats sub-second centiseconds', () => {
    expect(formatTime(10).cs).toBe('01');
    expect(formatTime(500).cs).toBe('50');
    expect(formatTime(990).cs).toBe('99');
  });

  it('resets centiseconds at 1000ms', () => {
    expect(formatTime(1000).cs).toBe('00');
  });

  it('formats mm:ss without hours when < 1 hour', () => {
    expect(formatTime(65000).main).toBe('01:05');
    expect(formatTime(3599000).main).toBe('59:59');
  });

  it('includes hours when >= 1 hour', () => {
    expect(formatTime(3600000).main).toBe('01:00:00');
    expect(formatTime(3661000).main).toBe('01:01:01');
    expect(formatTime(7322000).main).toBe('02:02:02');
  });

  it('pads all segments with leading zeros', () => {
    expect(formatTime(61000).main).toBe('01:01');
    expect(formatTime(3601000).main).toBe('01:00:01');
  });
});

// ── showButtons ───────────────────────────────────────────────────────────────

describe('showButtons', () => {
  let btns;

  beforeEach(() => {
    btns = [0, 1, 2].map(() => document.createElement('button'));
  });

  it('hides all buttons when no visible argument given', () => {
    showButtons(btns);
    btns.forEach(b => expect(b.classList.contains('hidden')).toBe(true));
  });

  it('shows only the specified button', () => {
    showButtons(btns, btns[0]);
    expect(btns[0].classList.contains('hidden')).toBe(false);
    expect(btns[1].classList.contains('hidden')).toBe(true);
    expect(btns[2].classList.contains('hidden')).toBe(true);
  });

  it('shows multiple specified buttons', () => {
    showButtons(btns, btns[0], btns[2]);
    expect(btns[0].classList.contains('hidden')).toBe(false);
    expect(btns[1].classList.contains('hidden')).toBe(true);
    expect(btns[2].classList.contains('hidden')).toBe(false);
  });

  it('removes hidden from previously hidden buttons', () => {
    btns.forEach(b => b.classList.add('hidden'));
    showButtons(btns, btns[1]);
    expect(btns[1].classList.contains('hidden')).toBe(false);
  });

  it('idempotent: showing same button twice leaves it visible', () => {
    showButtons(btns, btns[0]);
    showButtons(btns, btns[0]);
    expect(btns[0].classList.contains('hidden')).toBe(false);
  });
});

// ── updateTimerDisplay ────────────────────────────────────────────────────────

describe('updateTimerDisplay', () => {
  let mainEl, msEl;

  beforeEach(() => {
    mainEl = document.createElement('span');
    mainEl.dataset.hours = '0';
    msEl = document.createElement('span');
  });

  it('writes formatted time to elements', () => {
    updateTimerDisplay(mainEl, msEl, 65000);
    expect(mainEl.textContent).toBe('01:05');
    expect(msEl.textContent).toBe('.00');
  });

  it('writes centiseconds to ms element', () => {
    updateTimerDisplay(mainEl, msEl, 1234);
    expect(msEl.textContent).toBe('.23');
  });

  it('sets data-hours=1 when time >= 1 hour', () => {
    updateTimerDisplay(mainEl, msEl, 3600000);
    expect(mainEl.dataset.hours).toBe('1');
  });

  it('sets data-hours=0 when time < 1 hour', () => {
    mainEl.dataset.hours = '1';
    updateTimerDisplay(mainEl, msEl, 59000);
    expect(mainEl.dataset.hours).toBe('0');
  });
});
