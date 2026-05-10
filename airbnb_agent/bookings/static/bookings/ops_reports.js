document.addEventListener("DOMContentLoaded", () => {
  const search = document.getElementById("report-search");
  const cards = Array.from(document.querySelectorAll("[data-report-card]"));
  const metrics = Array.from(document.querySelectorAll(".ops-report-metric"));
  const chips = Array.from(document.querySelectorAll("[data-report-filter]"));
  const expandButton = document.querySelector("[data-report-expand]");
  const collapseButton = document.querySelector("[data-report-collapse]");
  const grid = document.getElementById("report-grid");
  let activeCategory = "all";

  if (!grid || !cards.length) return;

  const emptyState = document.createElement("div");
  emptyState.className = "ops-report-empty-state";
  emptyState.hidden = true;
  emptyState.textContent = "No report cards match this search/filter.";
  grid.appendChild(emptyState);

  function normalize(value) {
    return String(value || "").toLowerCase().trim();
  }

  function applyFilters() {
    const term = normalize(search ? search.value : "");
    let visibleCards = 0;

    cards.forEach((card) => {
      const category = card.dataset.reportCategory || "all";
      const text = normalize(card.dataset.reportText);
      const categoryMatches = activeCategory === "all" || category === activeCategory;
      const searchMatches = !term || text.includes(term);
      const visible = categoryMatches && searchMatches;
      card.hidden = !visible;
      if (visible) visibleCards += 1;
    });

    metrics.forEach((metric) => {
      const text = normalize(metric.dataset.reportText || metric.textContent);
      metric.hidden = Boolean(term && !text.includes(term));
    });

    emptyState.hidden = visibleCards !== 0;
  }

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      activeCategory = chip.dataset.reportFilter || "all";
      chips.forEach((item) => item.setAttribute("aria-pressed", item === chip ? "true" : "false"));
      applyFilters();
    });
  });

  if (search) {
    search.addEventListener("input", applyFilters);
  }

  cards.forEach((card) => {
    const toggle = card.querySelector(".ops-report-card__toggle");
    if (toggle) {
      toggle.addEventListener("click", () => {
        const collapsed = card.classList.toggle("is-collapsed");
        toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      });
    }

    card.querySelectorAll("[data-report-row]").forEach((row) => {
      row.addEventListener("click", () => {
        card.querySelectorAll("[data-report-row]").forEach((item) => item.classList.remove("is-active"));
        row.classList.add("is-active");
      });
    });
  });

  if (expandButton) {
    expandButton.addEventListener("click", () => {
      cards.forEach((card) => {
        card.classList.remove("is-collapsed");
        const toggle = card.querySelector(".ops-report-card__toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "true");
      });
    });
  }

  if (collapseButton) {
    collapseButton.addEventListener("click", () => {
      cards.forEach((card) => {
        card.classList.add("is-collapsed");
        const toggle = card.querySelector(".ops-report-card__toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
});
