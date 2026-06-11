(function () {
  document.querySelectorAll("[data-stay-card]").forEach(function (card) {
    const button = card.querySelector("[data-stay-image-toggle]");
    if (!button) return;

    function syncButton() {
      const isCollapsed = card.classList.contains("is-image-collapsed");
      button.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
      button.textContent = isCollapsed ? "Show image" : "Hide image";
    }

    button.addEventListener("click", function () {
      card.classList.toggle("is-image-collapsed");
      syncButton();
    });

    syncButton();
  });
})();
