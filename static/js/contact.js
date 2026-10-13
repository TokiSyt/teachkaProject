// Contact page: record the page the visitor came from, and count message characters.
(function () {
  var pageUrl = document.getElementById('page_url_input');
  if (pageUrl) pageUrl.value = document.referrer || '';

  var body = document.getElementById('id_body');
  var counter = document.getElementById('body-counter');
  if (!body || !counter) return;
  function update() { counter.textContent = body.value.length + ' / 5000'; }
  body.addEventListener('input', update);
  update();
})();
