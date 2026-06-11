(function () {
  const form = document.querySelector("[data-maintenance-form]");
  const modal = document.querySelector("[data-generate-modal]");
  if (!form || !modal) return;

  const fields = {
    title: form.querySelector("#id_title"),
    description: form.querySelector("#id_description"),
    nextAction: form.querySelector("#id_next_action"),
    status: form.querySelector("#id_status"),
    priority: form.querySelector("#id_priority"),
    item: form.querySelector("#id_item"),
    inquiry: form.querySelector("#id_inquiry"),
    dueDate: form.querySelector("#id_due_date")
  };

  const generated = {
    title: modal.querySelector("[data-generated-title]"),
    description: modal.querySelector("[data-generated-description]"),
    nextAction: modal.querySelector("[data-generated-next-action]")
  };

  let generationCount = 0;

  function selectedText(field, fallback) {
    if (!field) return fallback;
    const option = field.options ? field.options[field.selectedIndex] : null;
    const text = option ? option.textContent.trim() : field.value.trim();
    return text && text !== "---------" ? text : fallback;
  }

  function openModal() {
    modal.hidden = false;
    document.body.classList.add("ml-modal-open");
    generated.title.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove("ml-modal-open");
  }

  function buildDraft() {
    generationCount += 1;
    const listing = selectedText(fields.item, "selected listing");
    const reservation = selectedText(fields.inquiry, "selected reservation");
    const priority = selectedText(fields.priority, "Medium");
    const status = selectedText(fields.status, "Captured");
    const dueDate = fields.dueDate && fields.dueDate.value ? fields.dueDate.value : "not scheduled yet";
    const currentTitle = fields.title && fields.title.value.trim();
    const currentDescription = fields.description && fields.description.value.trim();
    const currentNextAction = fields.nextAction && fields.nextAction.value.trim();

    const titleOptions = [
      "Maintenance follow-up for " + listing,
      "Prepare maintenance record for " + listing,
      "Document work needed for " + listing
    ];
    const title = currentTitle || titleOptions[(generationCount - 1) % titleOptions.length];

    const description = currentDescription || [
      "Create a structured maintenance work item connected to " + listing + ".",
      "Reservation/request context: " + reservation + ".",
      "Priority: " + priority + ". Current status: " + status + ". Due date: " + dueDate + ".",
      "Capture the work performed, reason for the work, evidence/photos, cost details, and notes needed for a future report, bill, expense record, or tax-support packet."
    ].join("\n");

    const nextActionOptions = [
      "Confirm the work details, attach evidence/photos, and verify whether the item should generate a bill or report.",
      "Review the listing/reservation context, add cost/time evidence, and prepare the report-ready summary.",
      "Validate the maintenance scope, collect proof, and decide whether Finance should create an expense or invoice record."
    ];
    const nextAction = currentNextAction || nextActionOptions[(generationCount - 1) % nextActionOptions.length];

    generated.title.value = title;
    generated.description.value = description;
    generated.nextAction.value = nextAction;
  }

  function applyDraft() {
    if (fields.title) fields.title.value = generated.title.value.trim();
    if (fields.description) fields.description.value = generated.description.value.trim();
    if (fields.nextAction) fields.nextAction.value = generated.nextAction.value.trim();
    closeModal();
  }

  const openButton = form.querySelector("[data-open-generate-modal]");
  if (openButton) {
    openButton.addEventListener("click", function () {
      buildDraft();
      openModal();
    });
  }

  const againButton = modal.querySelector("[data-auto-generate-again]");
  if (againButton) againButton.addEventListener("click", buildDraft);

  const useButton = modal.querySelector("[data-use-generated-work-item]");
  if (useButton) useButton.addEventListener("click", applyDraft);

  modal.querySelectorAll("[data-close-generate-modal]").forEach(function (button) {
    button.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) closeModal();
  });
})();
