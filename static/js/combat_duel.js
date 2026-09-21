// Only initialise on the combat duel page (safe to include in a bundle).
if (document.getElementById("lightning")) {
(function () {
  let liveClones = 0;
  let intervalId = null;

  // Create and animate a clone of the image.
  function spawnClone() {
    // Stop spawning once all hero digits have been destroyed.
    if (window.__digitsAlive === false) {
      if (intervalId) clearInterval(intervalId);
      return;
    }
    // Keep at most 3 pics on screen at once.
    if (liveClones >= 3) return;
    const imgsSrc = "/static/picos/favpicos.png";
    const box = document.createElement("div");
    box.style.position = "fixed";
    box.style.pointerEvents = "none";
    box.style.zIndex = "9999";
    box.style.display = "flex";
    box.style.flexDirection = "column";
    box.style.alignItems = "center";
    box.style.gap = "2px";

    // Random position within the viewport.
    const maxX = window.innerWidth - 50; // approximate image width
    const maxY = window.innerHeight - 50; // approximate image height
    const randomX = Math.random() * maxX;
    const randomY = Math.random() * maxY;
    box.style.left = `${randomX}px`;
    box.style.top = `${randomY}px`;

    // Random duration for the blink effect (0.1 s to 0.6 s).
    const duration = (Math.random() * (0.6 - 0.1) + 0.1).toFixed(2);

    // Ensure the fast‑blink CSS rule exists only once.
    if (!document.getElementById("fastBlinkStyle")) {
      const style = document.createElement("style");
      style.id = "fastBlinkStyle";
      style.textContent = `
          @keyframes fastBlink {
            0%   { opacity: 1; }
            50%  { opacity: 0; }
            100% { opacity: 1; }
          }
          .fast-blink {
            animation: fastBlink ${duration}s infinite;
          }
        `;
      document.head.appendChild(style);
    }

    // Apply the blink class, tag as a laser-visible navpico and add to the page.
    const img = document.createElement("img");
    img.src = imgsSrc;
    img.classList.add("navpico", "fast-blink");
    img.style.display = "block";
    img.style.width = "18px";
    img.style.height = "auto";
    img.style.imageRendering = "pixelated";
    img.style.animation = `fastBlink ${duration}s infinite`;

    // Small-caps code name under the image.
    const label = document.createElement("span");
    label.textContent = WORDS[Math.floor(Math.random() * WORDS.length)];
    label.style.font = "small-caps 10px 'Terminus', monospace";
    label.style.color = "#7ef29a";
    label.style.textShadow = "0 0 4px rgba(126,242,154,0.8)";
    label.style.background = "rgba(0,0,0,0.55)";
    label.style.padding = "0 3px";
    label.style.lineHeight = "1.2";

    box.appendChild(img);
    box.appendChild(label);
    document.body.appendChild(box);
    liveClones++;

    // Remove the clone after the animation is complete.
    setTimeout(() => {
      box.remove();
      liveClones = Math.max(0, liveClones - 1);
    }, 8000);
  }

  // Spawn a pic every 1000 ms while the duel is active.
  intervalId = setInterval(spawnClone, 1000);
})();
}
