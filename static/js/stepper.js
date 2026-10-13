// Number steppers (.ap-step): round − / + buttons around a number input, used on the points
// tables, the member dashboard and the name wheel. Steps by 1 (kept within the input's min / max)
// and fires "input" so totals and auto-save react exactly as when typing.
document.addEventListener("click", function (e) {
  var btn = e.target.closest(".ap-step [data-step]");
  if (!btn) return;
  var input = btn.parentElement.querySelector('input[type="number"]');
  if (!input) return;
  var current = parseInt(input.value, 10);
  if (isNaN(current)) current = 0;
  var min = input.min === "" ? -Infinity : parseInt(input.min, 10);
  var max = input.max === "" ? Infinity : parseInt(input.max, 10);
  input.value = Math.min(max, Math.max(min, current + parseInt(btn.dataset.step, 10)));
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
