document.addEventListener("DOMContentLoaded", () => {
  setupFilterPanel();
  setupLogoPreview();
});

function setupFilterPanel() {
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
}

function setupLogoPreview() {
  const input = document.querySelector('input[type="file"][name="logo"]');
  if (!input) return;

  const previewRow = document.querySelector(".field-logo_preview")
    || document.querySelector(".form-row:has(.modern-admin-logo-preview)");
  if (!previewRow) return;

  const readonlyValue = previewRow.querySelector(".readonly")
    || previewRow.querySelector("div:last-child")
    || previewRow;

  let livePreview = previewRow.querySelector(".modern-admin-logo-live-preview");
  if (!livePreview) {
    livePreview = document.createElement("div");
    livePreview.className = "modern-admin-logo-live-preview";
    readonlyValue.appendChild(livePreview);
  }

  let objectUrl = "";

  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    livePreview.innerHTML = "";

    if (!file || !file.type.startsWith("image/")) {
      livePreview.hidden = true;
      return;
    }

    objectUrl = URL.createObjectURL(file);
    const image = document.createElement("img");
    image.src = objectUrl;
    image.alt = "Selected logo preview";
    const label = document.createElement("span");
    label.textContent = "Preview before save";
    livePreview.append(image, label);
    livePreview.hidden = false;
  });
}
