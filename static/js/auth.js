// Visitor form pages: show/hide password buttons.
// <button data-password-toggle="<input id>"> containing an <i data-lucide="eye">.
document.querySelectorAll('[data-password-toggle]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var input = document.getElementById(btn.dataset.passwordToggle);
    var show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    btn.setAttribute('aria-pressed', show ? 'true' : 'false');
    btn.innerHTML = '<i data-lucide="' + (show ? 'eye-off' : 'eye') + '"></i>';
    lucide.createIcons();
  });
});
