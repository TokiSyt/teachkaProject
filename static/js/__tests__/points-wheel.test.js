import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// points.js is a plain script (no exports); run it and pull out the function.
const code = readFileSync(resolve(__dirname, '../points.js'), 'utf-8');
const fns = {};
new Function('window', 'document', '_out', code + '\n_out.disableNumberWheel = disableNumberWheel;')(
  globalThis,
  globalThis.document,
  fns,
);
const { disableNumberWheel } = fns;

function makeInput(type) {
  const input = document.createElement('input');
  input.type = type;
  document.body.appendChild(input);
  return input;
}

describe('disableNumberWheel', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('prevents wheel scroll from changing a focused number input', () => {
    const input = makeInput('number');
    disableNumberWheel(document.body);
    input.focus();
    const ev = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    input.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(true);
  });

  it('does not interfere when the number input is not focused', () => {
    const input = makeInput('number');
    disableNumberWheel(document.body);
    const ev = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    input.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(false);
  });

  it('leaves text inputs alone even when focused', () => {
    const input = makeInput('text');
    disableNumberWheel(document.body);
    input.focus();
    const ev = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    input.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(false);
  });

  it('only guards the focused number input, not an unfocused sibling', () => {
    const a = makeInput('number');
    const b = makeInput('number');
    disableNumberWheel(document.body);
    a.focus(); // b stays unfocused

    const onB = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    b.dispatchEvent(onB);
    expect(onB.defaultPrevented).toBe(false);

    const onA = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    a.dispatchEvent(onA);
    expect(onA.defaultPrevented).toBe(true);
  });

  it('does not guard a focused <select>', () => {
    const sel = document.createElement('select');
    document.body.appendChild(sel);
    disableNumberWheel(document.body);
    sel.focus();
    const ev = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    sel.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(false);
  });

  it('keeps guarding after the focus moves between number inputs', () => {
    const a = makeInput('number');
    const b = makeInput('number');
    disableNumberWheel(document.body);

    a.focus();
    b.focus(); // focus now on b
    const onB = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    b.dispatchEvent(onB);
    expect(onB.defaultPrevented).toBe(true);

    const onA = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 });
    a.dispatchEvent(onA);
    expect(onA.defaultPrevented).toBe(false);
  });
});
