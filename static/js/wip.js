// "Coming soon" page (templates/wip.html): the Go Back button returns to the previous page,
// or home when there is no history (opened in a new tab).
document.querySelectorAll("[data-history-back]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    if (history.length > 1) history.back();
    else window.location.href = "/";
  });
});
