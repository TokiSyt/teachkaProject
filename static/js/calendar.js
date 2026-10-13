// Calendar pages: buttons with data-dialog-open="<dialog id>" open that dialog
// (the holiday help note in calendar/_help_dialog.html).
document.querySelectorAll("[data-dialog-open]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var dialog = document.getElementById(btn.dataset.dialogOpen);
    if (dialog && dialog.showModal) dialog.showModal();
  });
});
