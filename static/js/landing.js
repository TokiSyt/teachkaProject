// Landing page (templates/landing.html): scroll reveal for the below-the-fold rows,
// and pausing the idle float of bubble clusters and stages while they are off screen.
(function () {
  var root = document.querySelector('.lp');
  if (!root || !('IntersectionObserver' in window)) return;

  var floaters = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { e.target.classList.toggle('is-paused', !e.isIntersecting); });
  });
  root.querySelectorAll('.lp-cluster, .lp-stage').forEach(function (el) { floaters.observe(el); });

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
