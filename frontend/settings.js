const dialog = document.getElementById("settings-dialog");
const menu = document.getElementById("settings-open");
const themeOptions = dialog.querySelectorAll('input[name="theme"]');

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  for (const option of themeOptions) option.checked = option.value === theme;
  document.dispatchEvent(new Event("theme-change"));
}

applyTheme(document.documentElement.dataset.theme ?? "light");

menu.addEventListener("click", () => dialog.showModal());
dialog.addEventListener("close", () => menu.focus({ preventScroll: true }));
dialog.addEventListener("click", (event) => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});

for (const option of themeOptions) {
  option.addEventListener("change", () => {
    if (!option.checked) return;
    applyTheme(option.value);
    try {
      localStorage.setItem("theme", option.value);
    } catch {
      // The theme still works when browser storage is unavailable.
    }
  });
}

window.addEventListener("storage", (event) => {
  if (event.key === "theme" || event.key === null) {
    applyTheme(event.newValue === "dark" ? "dark" : "light");
  }
});
