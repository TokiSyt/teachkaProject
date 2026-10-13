// Settings page: apply the theme as soon as it is picked, and preview the accent colour.
(function () {
  var theme = document.getElementById('settings-theme-select');
  if (theme) theme.addEventListener('change', function () { setTheme(theme.value); });

  var color = document.getElementById('settings-accent-input');
  var label = document.getElementById('settings-accent-label');
  var bubble = document.querySelector('.au-accent-bub');
  if (!color) return;
  color.addEventListener('input', function () {
    if (label) label.textContent = color.value.toUpperCase();
    if (bubble) bubble.style.setProperty('--c', color.value);
  });
})();
