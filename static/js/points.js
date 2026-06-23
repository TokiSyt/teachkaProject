/**
 * Point system page behaviours.
 *
 * disableNumberWheel: stop the mouse wheel from changing the value of a focused
 * <input type="number">. Scrolling over a focused number field otherwise nudges
 * its value, which silently corrupts point totals while the user scrolls the page.
 */
function disableNumberWheel(root) {
  root.addEventListener(
    'wheel',
    function (e) {
      const t = e.target;
      if (
        t instanceof HTMLInputElement &&
        t.type === 'number' &&
        t === t.ownerDocument.activeElement
      ) {
        e.preventDefault();
      }
    },
    { passive: false },
  );
}

if (typeof document !== 'undefined' && document.addEventListener) {
  document.addEventListener('DOMContentLoaded', function () {
    disableNumberWheel(document);
  });
}
