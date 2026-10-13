// Logged-in home: tool bubbles float only while on screen; activity stats pop in
// and count up on scroll; accent colour swatches preview the sidebar colour on hover
// and save it on click.
(function () {
  // ── Tool bubbles: pause the idle float while the section is off screen ──
  const tools = document.querySelector('.hm-tools');
  if (tools && 'IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      tools.classList.toggle('is-paused', !entry.isIntersecting);
    }).observe(tools);
  }

  // ── Activity stats ──
  const stats = document.querySelectorAll('.hm-stat');
  if (stats.length && 'IntersectionObserver' in window) {
    document.documentElement.classList.add('hm-js');
    const ease = t => t < .5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    const countUp = el => {
      const target = +el.dataset.target;
      if (!target) return;
      const start = performance.now();
      const tick = now => {
        const p = Math.min((now - start) / 800, 1);
        el.textContent = Math.round(ease(p) * target);
        if (p < 1) requestAnimationFrame(tick); else el.textContent = target;
      };
      requestAnimationFrame(tick);
    };
    const obs = new IntersectionObserver(entries => {
      entries.forEach((entry, i) => {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        setTimeout(() => entry.target.classList.add('is-in'), i * 70);
        entry.target.querySelectorAll('[data-target]').forEach(countUp);
      });
    }, { threshold: 0.3 });
    stats.forEach(el => obs.observe(el));
  }

  // ── Accent colour ──
  const box = document.getElementById('accent-swatches');
  if (!box) return;
  const root = document.documentElement;
  let saved = null;

  function preview(hex) {
    if (saved === null) saved = getComputedStyle(root).getPropertyValue('--sidebar-hover-color').trim();
    root.style.setProperty('--sidebar-hover-color', hex);
    document.body.classList.add('ac-previewing');
  }
  function revert() {
    document.body.classList.remove('ac-previewing');
    if (saved !== null) root.style.setProperty('--sidebar-hover-color', saved);
  }
  function save(hex) {
    saved = hex;
    root.style.setProperty('--sidebar-hover-color', hex);
    fetch(box.dataset.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': box.dataset.csrf },
      body: 'icon_hover_color=' + encodeURIComponent(hex)
    });
    box.querySelectorAll('[data-color]').forEach(b => b.setAttribute('aria-pressed', b.dataset.color === hex ? 'true' : 'false'));
  }

  box.querySelectorAll('[data-color]').forEach(b => {
    b.addEventListener('mouseenter', () => preview(b.dataset.color));
    b.addEventListener('mouseleave', revert);
    b.addEventListener('click', () => save(b.dataset.color));
  });
})();
