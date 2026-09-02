// Combat Duel page JavaScript - extracted from combat_duel.html

(function () {
  // Create and animate a clone of the image.
  function spawnClone() {
    const imgsSrc = "/static/picos/favpicos.png";
    const img = document.createElement("img");
    img.src = imgsSrc;
    img.style.position = "fixed";
    img.style.pointerEvents = "none";
    img.style.zIndex = "9999";

    // Random position within the viewport.
    const maxX = window.innerWidth - 50; // approximate image width
    const maxY = window.innerHeight - 50; // approximate image height
    const randomX = Math.random() * maxX;
    const randomY = Math.random() * maxY;
    img.style.left = `${randomX}px`;
    img.style.top = `${randomY}px`;

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

    // Apply the blink class and add the image to the document.
    img.classList.add("fast-blink");
    img.style.animation = `fastBlink ${duration}s infinite`;
    document.body.appendChild(img);

    // Remove the clone after the animation is complete.
    setTimeout(() => {
      img.remove();
    }, 8000);
  }

  // Example: spawn a clone every 300 ms while the duel is active.
  const intervalId = setInterval(spawnClone, 1000);
})();
