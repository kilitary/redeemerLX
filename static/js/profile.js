(function () {
  const el = document.createElement("div");
  el.id = "profiler";
  el.setAttribute("aria-hidden", "true");
  document.body.appendChild(el);

  function render(profile) {
    if (!profile) return;
    const lines = [];
    lines.push(profile.method + " " + profile.path);
    (profile.steps || []).forEach((step) => {
      lines.push(step[0] + ": " + step[1].toFixed(2) + "ms");
    });
    el.innerHTML =
      lines.join("<br>") + " &middot; " + new Date().toLocaleTimeString();
    el.classList.add("visible");
  }

  window.renderProfile = render;

  function showLast() {
    if (window.__lastProfile) render(window.__lastProfile);
  }

  if (document.readyState === "complete") showLast();
  else window.addEventListener("DOMContentLoaded", showLast);
})();
