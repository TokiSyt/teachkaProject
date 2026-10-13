// Quiz list (apps/quizzmaker/templates/quizzmaker/home.html): switch scope, search and paginate
// by swapping in the ?partial=1 region without a full page load; GIF covers stay still until hover.
(function () {
  var region = document.getElementById("quiz-region");
  if (!region) return;

  // Show a still frame of each GIF cover and play it while its card is hovered.
  function setupGifHover(root) {
    root.querySelectorAll('img[data-gif="1"]:not([data-gif-init])').forEach(function (img) {
      img.dataset.gifInit = "1";
      var gifUrl = img.getAttribute("src");
      var tmp = new Image();
      tmp.crossOrigin = "anonymous";
      tmp.onload = function () {
        var c = document.createElement("canvas");
        c.width = tmp.naturalWidth;
        c.height = tmp.naturalHeight;
        try {
          c.getContext("2d").drawImage(tmp, 0, 0);
          var poster = c.toDataURL("image/png");
          img.src = poster;
          var host = img.closest(".ap-quiz") || img.parentElement;
          host.addEventListener("mouseenter", function () { img.src = gifUrl; });
          host.addEventListener("mouseleave", function () { img.src = poster; });
        } catch (e) { /* CORS-tainted canvas: leave the GIF playing */ }
      };
      tmp.src = gifUrl;
    });
  }

  async function load(url, push) {
    var res = await fetch(url + (url.indexOf("?") !== -1 ? "&" : "?") + "partial=1", {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (!res.ok) return;
    region.innerHTML = await res.text(); // server-rendered template, same origin
    if (window.lucide) lucide.createIcons();
    setupGifHover(region);
    if (push) history.pushState({}, "", url);
  }

  setupGifHover(region);

  region.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-quiz-toggle]");
    if (!a) return;
    e.preventDefault();
    load(a.getAttribute("href"), true);
  });

  region.addEventListener("submit", function (e) {
    var f = e.target.closest("form[data-quiz-search]");
    if (!f) return;
    e.preventDefault();
    load("?" + new URLSearchParams(new FormData(f)).toString(), true);
  });

  window.addEventListener("popstate", function () { load(location.search || "?", false); });
})();
