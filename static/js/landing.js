// Scroll reveal for the landing page's below-the-fold rows (templates/landing.html).
(function () {
  var root = document.querySelector('.lp');
  if (!root || !('IntersectionObserver' in window)) return;
  root.classList.add('lp-js');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  root.querySelectorAll('.lp-reveal').forEach(function (el) { io.observe(el); });
})();
