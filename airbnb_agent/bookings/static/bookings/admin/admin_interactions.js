document.addEventListener("DOMContentLoaded", () => {
  const filterPanel = document.querySelector("#changelist-filter");
  if (!filterPanel) return;

  filterPanel.querySelectorAll("details[open]").forEach((details) => {
    details.open = false;
    details.classList.add("modern-admin-filter-details");
  });
  filterPanel.querySelectorAll("details").forEach((details) => {
    details.classList.add("modern-admin-filter-details");
  });

  filterPanel.querySelectorAll("h3").forEach((heading, index) => {
    const controlled = [];
    let node = heading.nextElementSibling;
    while (node && node.tagName !== "H3") {
      controlled.push(node);
      node = node.nextElementSibling;
    }

    if (!controlled.length) return;

    const setExpanded = (expanded) => {
      heading.setAttribute("aria-expanded", expanded ? "true" : "false");
      controlled.forEach((element) => {
        element.classList.toggle("is-collapsed", !expanded);
      });
    };

    heading.setAttribute("role", "button");
    heading.setAttribute("tabindex", "0");
    heading.classList.add("modern-admin-filter-toggle");
    setExpanded(index === 0 && filterPanel.classList.contains("keep-first-filter-open"));

    heading.addEventListener("click", () => {
      setExpanded(heading.getAttribute("aria-expanded") !== "true");
    });

    heading.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      heading.click();
    });
  });
});
