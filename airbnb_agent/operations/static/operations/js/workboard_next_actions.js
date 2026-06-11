(function () {
  document.querySelectorAll("[data-next-action]").forEach(function (container) {
    const button = container.querySelector("[data-next-action-toggle]");
    if (!button) return;

    function syncButton() {
      const isCollapsed = container.classList.contains("is-collapsed");
      button.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
      button.textContent = isCollapsed ? "Show next action" : "Hide next action";
    }

    button.addEventListener("click", function () {
      container.classList.toggle("is-collapsed");
      syncButton();
    });

    syncButton();
  });
})();
