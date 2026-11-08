// Reconstruct the address only after an explicit copy action.
document.addEventListener("click", async (event) => {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest(".copy-email");
  if (!button) return;
  const address = atob(button.dataset.user) + "@" + atob(button.dataset.domain);
  const status = button.parentElement.querySelector(".email-status");
  try {
    await navigator.clipboard.writeText(address);
    status.textContent = "Email copied.";
  } catch {
    status.textContent = address;
  }
});
