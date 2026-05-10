(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function revealOnScroll() {
    const candidates = document.querySelectorAll(
      ".hero-content, .hero-photo, .section-heading, .listing-card, .review-card, .about-teaser > *, .booking-copy, .agent-panel, .booking-form, .deposit-form, .review-highlight-card, .rules-book, .mini-stay, .ops-card, .reservation-row"
    );
    candidates.forEach((element) => element.classList.add("ml-reveal"));

    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      candidates.forEach((element) => element.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    candidates.forEach((element, index) => {
      element.style.transitionDelay = `${Math.min(index % 6, 5) * 45}ms`;
      observer.observe(element);
    });
  }

  function enhanceGallery() {
    document.querySelectorAll(".gallery-grid").forEach((gallery) => {
      const figures = Array.from(gallery.querySelectorAll("figure"));
      if (figures.length < 2) return;

      const controls = document.createElement("div");
      controls.className = "ml-gallery-controls";
      controls.setAttribute("aria-label", "Gallery controls");

      figures.forEach((figure, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "ml-gallery-control";
        button.textContent = index === 0 ? "Featured" : `Photo ${index + 1}`;
        button.setAttribute("aria-pressed", index === 0 ? "true" : "false");
        button.addEventListener("click", () => activate(index, true));
        controls.appendChild(button);
        figure.addEventListener("click", () => activate(index, true));
      });

      gallery.insertAdjacentElement("afterend", controls);

      let activeIndex = 0;
      let timer = null;
      const buttons = Array.from(controls.querySelectorAll("button"));

      function activate(index, pause) {
        activeIndex = index;
        figures.forEach((figure, currentIndex) => {
          figure.classList.toggle("is-active-gallery-image", currentIndex === index);
          figure.classList.toggle("is-featured", currentIndex === index);
          figure.classList.toggle("ml-autoplay-pulse", currentIndex === index && !prefersReducedMotion);
        });
        buttons.forEach((button, currentIndex) => {
          button.setAttribute("aria-pressed", currentIndex === index ? "true" : "false");
        });
        if (pause && timer) {
          clearInterval(timer);
          timer = null;
        }
      }

      activate(0, false);

      if (!prefersReducedMotion && figures.length > 2) {
        timer = window.setInterval(() => {
          activate((activeIndex + 1) % figures.length, false);
        }, 5000);
      }
    });
  }

  function enhanceForms() {
    document.querySelectorAll("form").forEach((form) => {
      form.addEventListener("submit", () => {
        const submitter = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitter && submitter.tagName === "BUTTON") {
          submitter.classList.add("ml-button-loading");
          submitter.setAttribute("aria-busy", "true");
        }
      });
    });

    document.querySelectorAll("[data-auto-submit], .ml-auto-submit select, .ml-auto-submit input").forEach((control) => {
      const eventName = control.matches('input[type="text"], input[type="month"], input[type="date"], input[type="search"]') ? "change" : "change";
      control.addEventListener(eventName, () => submitClosestForm(control, "Updating..."));
    });

    document.querySelectorAll("[data-auto-navigate]").forEach((control) => {
      control.addEventListener("change", () => {
        const url = control.value || control.dataset.autoNavigateUrl;
        if (!url) return;
        showLoadingOverlay("Updating...");
        window.location.assign(url);
      });
    });

    document.querySelectorAll(".ml-autoload-link").forEach((link) => {
      link.addEventListener("click", () => showLoadingOverlay("Updating..."));
    });
  }

  function submitClosestForm(control, label) {
    const form = control.closest("form");
    if (!form) return;
    showLoadingOverlay(label || "Updating...");
    form.requestSubmit ? form.requestSubmit() : form.submit();
  }

  function showLoadingOverlay(label) {
    if (document.querySelector(".ml-loading-overlay")) return;
    const overlay = document.createElement("div");
    overlay.className = "ml-loading-overlay";
    overlay.innerHTML = `<div class="ml-loading-card"><span class="ml-spinner" aria-hidden="true"></span><span>${label}</span></div>`;
    document.body.appendChild(overlay);
  }

  function enhanceAgentPanel() {
    document.querySelectorAll(".agent-panel").forEach((panel) => {
      const form = panel.querySelector("form");
      const textarea = panel.querySelector("textarea");
      if (!form || !textarea || panel.querySelector(".ml-agent-suggestions")) return;

      const suggestions = [
        "How does the deposit work?",
        "Help me choose the right stay.",
        "What info do you need to book?",
      ];
      const wrap = document.createElement("div");
      wrap.className = "ml-agent-suggestions theme-row";
      wrap.setAttribute("aria-label", "Suggested questions");
      suggestions.forEach((text) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "ml-gallery-control";
        button.textContent = text;
        button.addEventListener("click", () => {
          textarea.value = text;
          textarea.focus();
        });
        wrap.appendChild(button);
      });
      form.insertAdjacentElement("beforebegin", wrap);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    revealOnScroll();
    enhanceGallery();
    enhanceForms();
    enhanceAgentPanel();
  });
})();
