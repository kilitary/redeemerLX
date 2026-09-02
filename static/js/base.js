let WORDS = [
  "alpha",
  "beta",
  "gamma",
  "delta",
  "epsilon",
  "zeta",
  "eta",
  "theta",
  "iota",
  "kappa",
  "lambda",
  "mu",
  "nu",
  "xi",
  "omicron",
  "pi",
  "rho",
  "sigma",
  "tau",
  "upsilon",
  "phi",
  "chi",
  "psi",
  "omega",
  "arcane",
  "eldritch",
  "runic",
  "sphinx",
  "nebula",
  "celestial",
  "aurora",
  "eclipse",
  "lunar",
  "solstice",
  "ice",
  "drice"
];

(function () {
  const canvas = document.getElementById("nato");
  const ctx = canvas.getContext("2d");
  let w, h;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  var drawSymbol = [
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y - s);
      c.lineTo(x + s, y + s);
      c.moveTo(x - s, y + s);
      c.lineTo(x + s, y - s);
      c.moveTo(x, y - s * 1.2);
      c.lineTo(x, y + s * 1.2);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.ellipse(x, y, s, s * 0.6, 0, 0, Math.PI * 2);
      c.stroke();
      c.beginPath();
      c.moveTo(x - s * 0.7, y);
      c.lineTo(x + s * 1.2, y);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.arc(x, y, s * 0.6, 0, Math.PI * 2);
      c.stroke();
      c.beginPath();
      c.arc(x, y, s * 0.25, 0, Math.PI * 2);
      c.fill();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y + s * 0.7);
      c.lineTo(x + s, y - s * 0.7);
      c.stroke();
      c.beginPath();
      c.moveTo(x - s * 0.5, y + s);
      c.lineTo(x - s, y + s * 0.7);
      c.moveTo(x + s * 0.5, y - s);
      c.lineTo(x + s, y - s * 0.7);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x, y - s);
      c.lineTo(x + s * 0.9, y + s * 0.7);
      c.moveTo(x, y - s);
      c.lineTo(x - s * 0.9, y + s * 0.7);
      c.moveTo(x - s * 0.6, y + s * 0.3);
      c.lineTo(x + s * 0.6, y + s * 0.3);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x, y - s);
      c.lineTo(x, y + s);
      c.moveTo(x - s, y);
      c.lineTo(x + s, y);
      c.arc(x, y, s * 1.2, 0, Math.PI * 2);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x, y - s);
      c.lineTo(x + s * 0.5, y - s * 0.3);
      c.lineTo(x, y);
      c.lineTo(x + s * 0.5, y + s * 0.3);
      c.lineTo(x, y + s);
      c.stroke();
      c.beginPath();
      c.arc(x + s * 0.25, y, s * 0.15, 0, Math.PI * 2);
      c.fill();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y - s * 0.5);
      c.lineTo(x, y);
      c.lineTo(x - s, y + s * 0.5);
      c.stroke();
      c.beginPath();
      c.moveTo(x + s * 0.3, y - s);
      c.lineTo(x + s * 0.3, y + s);
      c.stroke();
      c.beginPath();
      c.arc(x + s * 0.3, y - s * 0.4, s * 0.12, 0, Math.PI * 2);
      c.fill();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y + s * 0.5);
      c.lineTo(x - s * 0.5, y - s * 0.5);
      c.lineTo(x + s * 0.5, y - s * 0.5);
      c.lineTo(x + s, y + s * 0.5);
      c.closePath();
      c.stroke();
      c.beginPath();
      c.moveTo(x, y - s * 0.5);
      c.lineTo(x, y + s * 0.5);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y);
      c.quadraticCurveTo(x - s * 0.5, y - s * 0.8, x, y - s * 0.5);
      c.quadraticCurveTo(x + s * 0.5, y - s * 0.8, x + s, y);
      c.quadraticCurveTo(x + s * 0.5, y + s * 0.8, x, y + s * 0.5);
      c.quadraticCurveTo(x - s * 0.5, y + s * 0.8, x - s, y);
      c.closePath();
      c.stroke();
      c.beginPath();
      c.moveTo(x, y - s * 0.3);
      c.lineTo(x, y + s * 0.3);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.moveTo(x - s, y + s * 0.3);
      c.lineTo(x + s, y + s * 0.3);
      c.moveTo(x - s, y - s * 0.3);
      c.lineTo(x + s, y - s * 0.3);
      c.moveTo(x - s, y - s * 0.3);
      c.lineTo(x - s, y + s * 0.3);
      c.moveTo(x + s, y - s * 0.3);
      c.lineTo(x + s, y + s * 0.3);
      c.stroke();
      c.beginPath();
      c.moveTo(x, y - s);
      c.lineTo(x, y + s);
      c.stroke();
    },
    function (c, x, y, s) {
      c.beginPath();
      c.arc(x, y, s * 0.7, 0, Math.PI, false);
      c.stroke();
      c.beginPath();
      c.moveTo(x - s * 0.7, y);
      c.lineTo(x - s * 0.3, y - s * 0.5);
      c.moveTo(x + s * 0.7, y);
      c.lineTo(x + s * 0.3, y - s * 0.5);
      c.stroke();
    },
  ];

  var acts = [];
  window.natoActs = acts;
  // Expose acts for laser targeting
  window.natoActs = acts;
  function spawn() {
    if (acts.length > 40) return;
    var fnIdx = Math.floor(Math.random() * drawSymbol.length);
    var x = Math.random() * w;
    var y = Math.random() * h;
    if (Math.random() < 0.4) {
      fnIdx = drawSymbol.length - 1;
      x = w - 90 + Math.random() * 60;
      y = h / 2 + (Math.random() - 0.5) * 200;
    }
    var size = 5 + Math.random() * 20;
    var rot = (Math.random() - 0.1) * 0.9;
    var life = 16000 + Math.random() * 14000;
    var hue = 15 + Math.floor(Math.random() * 55);
    var color = "hsl(" + hue + ", 100%, 60%)";
    acts.push({
      fnIdx: fnIdx,
      x: x,
      y: y,
      size: size,
      rot: rot,
      born: performance.now(),
      life: life,
      color: color,
      // Crawl movement: a target is picked, the unit crawls 3px toward it
      // every 250ms, then picks another target once it arrives.
      tx: x,
      ty: y,
      lastCrawl: 0,
    });
  }

  function draw(now) {
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 1;
    ctx.lineJoin = "round";
    ctx.shadowBlur = 10;
    for (var i = acts.length - 1; i >= 0; i--) {
      var a = acts[i];
      // In draw loop, handle shrinking of destroyed units
      if (a.dying) {
        const dieElapsed = now - a.dieStart;
        const prog = Math.min(1, dieElapsed / a.dieDuration);
        a.size = a.origSize * (1 - prog);
        if (prog >= 1) {
          acts.splice(i, 1);
          continue;
        }
      }
      var age = now - a.born;
      if (age > a.life) {
        acts.splice(i, 1);
        continue;
      }
      // Crawl movement: every 250ms step 3px toward the current target; once
      // the unit arrives, pick a new random target within 50px of its position.
      if (a.lastFrame === 0) a.lastFrame = now;
      if (now - a.lastCrawl >= 150) {
        a.lastCrawl = now;
        a.lastFrame = now;
        var mdx = a.tx - a.x;
        var mdy = a.ty - a.y;
        var mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist <= 3) {
          // Arrived - select a new random position within 50px.
          a.x = a.tx;
          a.y = a.ty;
          a.tx = a.x + (Math.random() - 0.5) * 100;
          a.ty = a.y + (Math.random() - 0.5) * 100;
          a.tx = Math.max(0, Math.min(w, a.tx));
          a.ty = Math.max(0, Math.min(h, a.ty));
        } else {
          // Crawl 3px toward the target.
          a.x += (mdx / mdist) * 3;
          a.y += (mdy / mdist) * 3;
        }
      }
      ctx.save();
      var fade = Math.min(1, (a.life - age) / 1500);
      fade = Math.max(0.3, fade * 0.85);
      ctx.globalAlpha = fade;
      ctx.translate(a.x, a.y);
      ctx.rotate(a.rot);
      ctx.strokeStyle = a.color;
      ctx.shadowColor = a.color;
      drawSymbol[a.fnIdx](ctx, 0, 0, a.size);
      ctx.restore();
    }
  }

  function schedule() {
    spawn();
    setTimeout(schedule, 400 + Math.random() * 1200);
  }
  setTimeout(schedule, 300);

  function loop(t) {
    if (document.hidden) return;
    draw(t);
    requestAnimationFrame(loop);
  }
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) requestAnimationFrame(loop);
  });
  requestAnimationFrame(loop);
})();

(function () {
  const hero = document.getElementById("hero");
  if (!hero) return;
  const pre = document.createElement("pre");
  pre.className = "ascii";
  const HEX = "0123456789ABCDEF";
  const FS = 13;

  // Sum counters: left = all non-red digits, right = all red (hex-hit) digits
  const leftSum = document.createElement("div");
  leftSum.className = "hero-sum hero-sum-left";
  leftSum.title = "Sum of non-red hex digits";
  const leftVal = document.createElement("span");
  leftVal.className = "hero-sum-val";
  leftSum.append(leftVal);
  const rightSum = document.createElement("div");
  rightSum.className = "hero-sum hero-sum-right";
  rightSum.title = "Sum of red hex digits";
  const rightVal = document.createElement("span");
  rightVal.className = "hero-sum-val";
  rightSum.append(rightVal);
  const heroSums = document.createElement("div");
  heroSums.className = "hero-sums";
  heroSums.append(leftSum, rightSum);

  function hexValue(ch) {
    const v = parseInt(ch, 16);
    return Number.isFinite(v) ? v : 0;
  }

  function updateSums() {
    let other = 0;
    let red = 0;
    pre.querySelectorAll("span").forEach((span) => {
      const v = hexValue(span.textContent);
      if (span.classList.contains("hex-hit")) red += v;
      else if (span.classList.contains("hex-hot")) other += v;
    });
    leftVal.textContent = other;
    rightVal.textContent = red;
    // When one side is >=15% larger than the other, blink only the smaller
    // sum with a hard on/off (no fade).
    const big = other >= red ? other : red;
    const small = other >= red ? red : other;
    const lopsided = small > 0 && big >= small * 1.15;
    const smallIsLeft = other < red;
    leftSum.classList.toggle("blinking", lopsided && smallIsLeft);
    rightSum.classList.toggle("blinking", lopsided && !smallIsLeft);
    // When the red sum outweighs the green, convert a random batch of reds back to greens.
    if (red > other && !converting && Math.random() < 0.4) {
      converting = true;
      const hits = Array.from(pre.querySelectorAll("span.hex-hit"));
      const count = Math.min(hits.length, 5 + Math.floor(Math.random() * 11));
      for (let i = 0; i < count; i++) {
        const s = hits[Math.floor(Math.random() * hits.length)];
        if (s) s.className = "hex-hot";
      }
      setTimeout(() => {
        converting = false;
      }, 50);
      return;
    }
    if (other === 0 && red === 0 && !navigated) {
      navigated = true;
      runMasher();
    }
  }

  let navigated = false;
  let converting = false;

  function runMasher() {
    if (!heroSums.isConnected) return;
    const bar = document.createElement("div");
    bar.className = "masher";
    hero.appendChild(bar);
    const heroRect = hero.getBoundingClientRect();
    const endY = pre.getBoundingClientRect().bottom - heroRect.top;
    const duration = 6000;
    const start = performance.now();
    const GHOSTS = ["ghost-green", "ghost-red", "ghost-blue"];
    let opacity = 100;
    let cracked = false;
    let done = false;
    let lastGhost = 0;

    function spawnGhost(y) {
      const span = document.createElement("span");
      span.className =
        "ghost " + GHOSTS[Math.floor(Math.random() * GHOSTS.length)];
      span.textContent = HEX[Math.floor(Math.random() * HEX.length)];
      span.style.left = Math.floor(Math.random() * 90) + 5 + "%";
      span.style.top = y + "px";
      span.addEventListener("animationend", () => span.remove(), {
        once: true,
      });
      hero.appendChild(span);
    }

    function frame(now) {
      if (done) return;
      const p = Math.min(1, (now - start) / duration);
      const y = Math.floor(p * endY);
      bar.style.transform = "translateY(" + y + "px)";
      // Spawn shadowed colored digits that appear and vanish within 1s.
      if (now - lastGhost > 60) {
        lastGhost = now;
        spawnGhost(y);
        spawnGhost(y);
      }
      // Red sum goes transparent 100 -> 10, -10 percents every render epoch (frame).
      if (opacity > 10) {
        opacity = Math.max(10, opacity - 10);
        rightSum.style.opacity = (opacity / 100).toFixed(2);
      }
      // When the masher reaches the sum counters, crack them.
      if (
        !cracked &&
        p * endY >=
          heroSums.getBoundingClientRect().top -
            heroRect.top +
            heroSums.offsetHeight / 2
      ) {
        cracked = true;
        heroSums.classList.add("cracked");
      }
      if (p < 1) {
        requestAnimationFrame(frame);
      } else {
        done = true;
        bar.remove();
        setTimeout(restartDigits, 300);
      }
    }
    requestAnimationFrame(frame);
  }

  function restartDigits() {
    heroSums.classList.remove("cracked");
    rightSum.style.opacity = "1";
    navigated = false;
    converting = false;
    fill();
  }

  function fill() {
    const cols = 110;
    const rows = 6;
    const frag = document.createDocumentFragment();
    for (let r = 0; r < rows; r++) {
      const line = document.createElement("div");
      for (let c = 0; c < cols; c++) {
        if (Math.random() < 0.12) {
          line.appendChild(document.createTextNode(" "));
          continue;
        }
        const d = HEX[Math.floor(Math.random() * HEX.length)];
        const span = document.createElement("span");
        span.className = Math.random() < 0.15 ? "hex-hot" : "hex-dim";
        span.textContent = d;
        line.appendChild(span);
      }
      frag.appendChild(line);
    }
    pre.replaceChildren(frag);
  }

  // Immediate element siblings that are actual digit spans (skips space text
  // nodes so only truly adjacent digits are considered neighbors).
  function adjacentSpans(span) {
    const out = [];
    let s = span.previousSibling;
    if (s && s.nodeType === 1 && s.tagName === "SPAN") out.push(s);
    s = span.nextSibling;
    if (s && s.nodeType === 1 && s.tagName === "SPAN") out.push(s);
    return out;
  }

  // When a red (hex-hit) digit is directly adjacent to a green (hex-hot) digit,
  // remove BOTH with a 25% chance per such pair.
  function coagulate() {
    const reds = Array.from(pre.querySelectorAll("span.hex-hit"));
    let changed = false;
    for (let k = 0; k < reds.length; k++) {
      const red = reds[k];
      if (!red.isConnected) continue;
      const nbs = adjacentSpans(red);
      for (let m = 0; m < nbs.length; m++) {
        if (nbs[m].classList.contains("hex-hot") && Math.random() < 0.25) {
          deleteDigit(nbs[m]);
          if (red.isConnected) deleteDigit(red);
          changed = true;
          break;
        }
      }
    }
    if (changed) updateSums();
  }

  // On lightning: mark a random 4-10 unmarked (dim) digits red and delete a
  // random 4-10 green digits, then recount.
  function recolorOnLightning() {
    const dims = Array.from(pre.querySelectorAll("span.hex-dim"));
    const mark = 4 + Math.floor(Math.random() * 7);
    for (let i = 0; i < mark && dims.length; i++) {
      const idx = Math.floor(Math.random() * dims.length);
      dims.splice(idx, 1)[0].classList.add("hex-hit");
    }
    const greens = Array.from(pre.querySelectorAll("span.hex-hot"));
    const del = 4 + Math.floor(Math.random() * 7);
    for (let i = 0; i < del && greens.length; i++) {
      const idx = Math.floor(Math.random() * greens.length);
      deleteDigit(greens.splice(idx, 1)[0]);
    }
    updateSums();
  }

  // Red (hex-hit) digits are deleted after a random 150-1500ms. scheduleFades is
  // invoked on every hero change and ensures each red digit gets a delete timer.
  const fades = new Map();
  function scheduleFades() {
    const reds = pre.querySelectorAll("span.hex-hit");
    for (let k = 0; k < reds.length; k++) {
      const s = reds[k];
      if (fades.has(s)) continue;
      const delay = 150 + Math.random() * 1350;
      fades.set(
        s,
        setTimeout(() => {
          fades.delete(s);
          if (s.isConnected) deleteDigit(s);
        }, delay),
      );
    }
    for (const key of fades.keys()) {
      if (!key.classList.contains("hex-hit")) {
        clearTimeout(fades.get(key));
        fades.delete(key);
      }
    }
  }

  // Remove a digit: 90% delete it outright so the row collapses and the table
  // shrinks toward the center; 10% of the time leave a random gap of spaces
  // between digits instead.
  function deleteDigit(s) {
    if (fades.has(s)) {
      clearTimeout(fades.get(s));
      fades.delete(s);
    }
    if (Math.random() < 0.1) {
      const n = 1 + Math.floor(Math.random() * 3);
      s.replaceWith(document.createTextNode(" ".repeat(n)));
    } else {
      s.remove();
    }
  }

  // Delete a digit after a random delay.
  function scheduleDelete(s, minMs, maxMs) {
    setTimeout(
      () => {
        if (s.isConnected) deleteDigit(s);
      },
      minMs + Math.random() * (maxMs - minMs),
    );
  }

  // Each 250ms step: mark a random 3-7 nongreen/nonred (dim) digits red and
  // delete them after a random 600-1700ms; delete a random 2-5 green digits.
  function step() {
    const dims = Array.from(pre.querySelectorAll("span.hex-dim"));
    const mark = 3 + Math.floor(Math.random() * 5);
    for (let i = 0; i < mark && dims.length; i++) {
      const idx = Math.floor(Math.random() * dims.length);
      const s = dims.splice(idx, 1)[0];
      s.classList.add("hex-hit");
      scheduleDelete(s, 600, 1700);
    }
    const greens = Array.from(pre.querySelectorAll("span.hex-hot"));
    const del = 2 + Math.floor(Math.random() * 4);
    for (let i = 0; i < del && greens.length; i++) {
      const idx = Math.floor(Math.random() * greens.length);
      deleteDigit(greens.splice(idx, 1)[0]);
    }
    updateSums();
  }
  const stepTimer = setInterval(() => {
    if (pre.isConnected) step();
    else clearInterval(stepTimer);
  }, 250);

  // Explosion effect for NATO targets hit by laser
  function createExplosion(cx, cy, isShip) {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute(
      "viewBox",
      "0 0 " + window.innerWidth + " " + window.innerHeight,
    );
    svg.setAttribute(
      "style",
      "position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:6;",
    );
    document.body.appendChild(svg);

    // Longer, dramatic explosion – disappear after 1.5 seconds
    const particleCount = isShip ? 30 : 18;
    const maxRadius = isShip ? 80 : 50;
    const duration = 1500; // 1.5 seconds for all elements to fade out

    // Flash – fast expanding ring
    const flash = document.createElementNS(SVG_NS, "circle");
    flash.setAttribute("cx", cx);
    flash.setAttribute("cy", cy);
    flash.setAttribute("r", "2");
    flash.setAttribute("fill", "none");
    flash.setAttribute("stroke", "rgba(255,200,50,0.9)");
    flash.setAttribute("stroke-width", "3");
    svg.appendChild(flash);

    // Core blast – bright hotspot
    const core = document.createElementNS(SVG_NS, "circle");
    core.setAttribute("cx", cx);
    core.setAttribute("cy", cy);
    core.setAttribute("r", "4");
    core.setAttribute("fill", "rgba(255,255,200,1)");
    core.style.filter =
      "drop-shadow(0 0 8px rgba(255,200,50,1)) drop-shadow(0 0 20px rgba(255,100,20,0.8))";
    svg.appendChild(core);

    // Shockwave – secondary ring
    const shockwave = document.createElementNS(SVG_NS, "circle");
    shockwave.setAttribute("cx", cx);
    shockwave.setAttribute("cy", cy);
    shockwave.setAttribute("r", "6");
    shockwave.setAttribute("fill", "none");
    shockwave.setAttribute("stroke", "rgba(255,150,30,0.8)");
    shockwave.setAttribute("stroke-width", "2");
    svg.appendChild(shockwave);

    // **Real explosion shape** – random polygon vertices radiating outward
    const poly = document.createElementNS(SVG_NS, "polygon");
    const vertexCount = 10 + Math.floor(Math.random() * 5);
    let points = "";
    for (let i = 0; i < vertexCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * maxRadius;
      const px = cx + Math.cos(angle) * radius;
      const py = cy + Math.sin(angle) * radius;
      points += `${px},${py} `;
    }
    poly.setAttribute("points", points.trim());
    poly.setAttribute("fill", "rgba(255,150,0,0.4)");
    poly.setAttribute("stroke", "rgba(255,80,0,0.7)");
    poly.setAttribute("stroke-width", "1");
    svg.appendChild(poly);

    // Particles (debris, sparks)
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      const angle = (Math.PI * 2 * i) / particleCount + Math.random() * 0.5;
      const speed = 0.5 + Math.random() * 1.5;
      const size = 2 + Math.random() * (isShip ? 6 : 4);
      const life = duration * (0.4 + Math.random() * 0.6);
      const hue = isShip ? 15 + Math.random() * 30 : 0 + Math.random() * 25; // orange/red for ship, red for other

      const p = document.createElementNS(SVG_NS, "circle");
      p.setAttribute("cx", cx);
      p.setAttribute("cy", cy);
      p.setAttribute("r", size);
      p.setAttribute("fill", "hsl(" + hue + ", 100%, 60%)");
      p.style.filter =
        "drop-shadow(0 0 " + size * 1.5 + "px hsl(" + hue + ", 100%, 60%))";
      svg.appendChild(p);

      particles.push({
        el: p,
        x: cx,
        y: cy,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: size,
        life: life,
        maxLife: life,
        startTime: performance.now(),
      });
    }

    // Smoke particles – disperse in random directions
    const smokeCount = isShip ? 15 : 8;
    const smoke = [];
    for (let i = 0; i < smokeCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.2 + Math.random() * 0.6;
      const size = 8 + Math.random() * (isShip ? 20 : 12);
      const life = duration * (0.8 + Math.random() * 0.8);
      const opacity = 0.15 + Math.random() * 0.25;

      const s = document.createElementNS(SVG_NS, "circle");
      s.setAttribute("cx", cx);
      s.setAttribute("cy", cy);
      s.setAttribute("r", size);
      s.setAttribute("fill", "rgba(60,50,40," + opacity + ")");
      s.style.filter = "blur(4px)";
      svg.appendChild(s);

      smoke.push({
        el: s,
        x: cx,
        y: cy,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 0.1, // slight upward drift
        size: size,
        life: life,
        maxLife: life,
        opacity: opacity,
        startTime: performance.now(),
        nextShrink: 100,
      });
    }

    const startTime = performance.now();
    function animateExplosion(now) {
      const elapsed = now - startTime;
      if (elapsed > duration) {
        svg.remove();
        return;
      }
      const progress = elapsed / duration;
      const easeOut = 1 - Math.pow(1 - progress, 3);

      // Animate flash ring
      const flashR = 6 + maxRadius * 0.5 * easeOut;
      const flashOpacity = 1 - progress;
      flash.setAttribute("r", flashR);
      flash.setAttribute(
        "stroke",
        "rgba(255,200,50," + 0.9 * flashOpacity + ")",
      );
      flash.setAttribute("stroke-width", (3 * (1 - progress * 0.5)).toFixed(1));

      // Animate core
      const coreR = 4 * (1 - progress * 0.3);
      core.setAttribute("r", coreR);
      core.setAttribute("fill", "rgba(255,255,200," + (1 - progress) + ")");

      // Animate shockwave
      const swR = 6 + maxRadius * easeOut;
      const swOpacity = (1 - progress) * 0.8;
      shockwave.setAttribute("r", swR);
      shockwave.setAttribute("stroke", "rgba(255,150,30," + swOpacity + ")");
      shockwave.setAttribute("stroke-width", (2 * (1 - progress)).toFixed(1));

      // Animate particles
      particles.forEach((p) => {
        const pProgress = Math.min(1, elapsed / p.maxLife);
        const pEase = 1 - Math.pow(1 - pProgress, 2);
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.02; // gravity
        p.vx *= 0.995; // air resistance
        p.vy *= 0.995;
        const pSize = p.size * (1 - pProgress * 0.5);
        p.el.setAttribute("cx", p.x);
        p.el.setAttribute("cy", p.y);
        p.el.setAttribute("r", Math.max(0.5, pSize));
        p.el.setAttribute(
          "fill",
          "hsl(" + 10 + ", 100%, " + (60 - 40 * pProgress) + "%)",
        );
        p.el.style.opacity = 1 - pProgress;
      });

      // Animate smoke
      smoke.forEach((s) => {
        const sProgress = Math.min(1, elapsed / s.maxLife);
        s.x += s.vx;
        s.y += s.vy;
        s.vx *= 0.99;
        s.vy *= 0.99;
        // Shrink every 100ms by 10%
        if (elapsed >= s.nextShrink) {
          s.size *= 0.9;
          s.nextShrink += 100;
        }
        if (s.size <= 0) {
          s.el.remove();
          return; // skip property setting for this frame
        }
        s.el.setAttribute("cx", s.x);
        s.el.setAttribute("cy", s.y);
        s.el.setAttribute("r", s.size);
        s.el.setAttribute(
          "fill",
          "rgba(60,50,40," + s.opacity * (1 - sProgress) + ")",
        );
      });

      requestAnimationFrame(animateExplosion);
    }
    requestAnimationFrame(animateExplosion);
  }

  // Each 400ms: fire a laser beam from a random top navigation link to a random
  // unmarked digit. When digits are exhausted, target NATO icons (prefer ships on the right).
  // When NATO exhausted, target navpico images in nav links.
  let activeBeams = 0;
  function fireLaser() {
    if (activeBeams >= 2) return;
    const links = Array.from(document.querySelectorAll(".app-bar a"));
    if (!links.length) return;

    // Get available targets: digits first, then NATO icons, then navpicos
    const digits = Array.from(
      pre.querySelectorAll("span.hex-dim, span.hex-hot"),
    );
    const natoActs = window.natoActs || [];

    // Find ships (omega symbol, fnIdx 17) on the right side
    const ships = natoActs.filter((a) => a.fnIdx === 17);
    // Other NATO icons
    const otherNato = natoActs.filter((a) => a.fnIdx !== 17);
    // Navpico images in nav links
    const navpicos = Array.from(document.querySelectorAll(".navpico"));

    let target = null;
    let targetType = null; // 'digit', 'ship', 'nato', 'navpico'

    if (digits.length > 0) {
      // Target digits first
      target = digits[Math.floor(Math.random() * digits.length)];
      targetType = "digit";
    } else if (ships.length > 0) {
      // No digits left, target ships
      target = ships[Math.floor(Math.random() * ships.length)];
      targetType = "ship";
    } else if (otherNato.length > 0) {
      // No digits or ships, target other NATO icons
      target = otherNato[Math.floor(Math.random() * otherNato.length)];
      targetType = "nato";
    } else if (navpicos.length > 0) {
      // No digits or NATO, target navpicos
      target = navpicos[Math.floor(Math.random() * navpicos.length)];
      targetType = "navpico";
    } else {
      return; // No targets available
    }

    const link = links[Math.floor(Math.random() * links.length)];
    link.classList.add("laser-source");
    setTimeout(() => link.classList.remove("laser-source"), 220);
    // Random short delay so beams start slightly offset instead of all in sync.
    const delay = 2 + Math.random() * 18;
    setTimeout(() => {
      const lr = link.getBoundingClientRect();
      const x1 = lr.left + lr.width / 2;
      const y1 = lr.top + lr.height / 2;
      let x2, y2;

      if (targetType === "digit") {
        const dr = target.getBoundingClientRect();
        x2 = dr.left + dr.width / 2;
        y2 = dr.top + dr.height / 2;
      } else if (targetType === "navpico") {
        // navpico is a DOM element
        const nr = target.getBoundingClientRect();
        x2 = nr.left + nr.width / 2;
        y2 = nr.top + nr.height / 2;
      } else {
        // NATO icon - use canvas coordinates directly
        x2 = target.x;
        y2 = target.y;
      }

      const SVG_NS = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(SVG_NS, "svg");
      svg.classList.add("laser");
      svg.setAttribute(
        "viewBox",
        "0 0 " + window.innerWidth + " " + window.innerHeight,
      );
      svg.setAttribute(
        "style",
        "position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:5;",
      );
      // Vary beam thickness, intensity and lifetime so no two look identical.
      const coreW = 1 + Math.random() * 2;
      const glowW = coreW * 2.2;
      const coreA = 0.85 + Math.random() * 0.15;
      const glowA = 0.25 + Math.random() * 0.3;
      const life = 130 + Math.random() * 170;
      // Wide soft glow.
      const glow = document.createElementNS(SVG_NS, "line");
      glow.setAttribute("x1", x1);
      glow.setAttribute("y1", y1);
      glow.setAttribute("x2", x2);
      glow.setAttribute("y2", y2);
      glow.setAttribute("stroke", "rgba(255,60,60," + glowA.toFixed(2) + ")");
      glow.setAttribute("stroke-width", glowW.toFixed(1));
      glow.setAttribute("stroke-linecap", "round");
      glow.classList.add("laser-glow");
      // Bright hot core.
      const core = document.createElementNS(SVG_NS, "line");
      core.setAttribute("x1", x1);
      core.setAttribute("y1", y1);
      core.setAttribute("x2", x2);
      core.setAttribute("y2", y2);
      core.setAttribute("stroke", "rgba(255,40,40," + coreA.toFixed(2) + ")");
      core.setAttribute("stroke-width", coreW.toFixed(1));
      core.setAttribute("stroke-linecap", "round");
      core.classList.add("laser-core");
      core.style.filter =
        "drop-shadow(0 0 5px rgba(255,60,60,0.9)) drop-shadow(0 0 12px rgba(255,60,60,0.6))";
      // Blue destination point at the target, sized with the beam.
      const dot = document.createElementNS(SVG_NS, "circle");
      dot.setAttribute("cx", x2);
      dot.setAttribute("cy", y2);
      dot.setAttribute("r", String(2 + Math.random() * 2));
      dot.setAttribute("fill", "rgba(80,140,255,1)");
      dot.style.filter =
        "drop-shadow(0 0 5px rgba(80,140,255,0.9)) drop-shadow(0 0 10px rgba(80,140,255,0.7))";
      svg.appendChild(glow);
      svg.appendChild(core);
      svg.appendChild(dot);
      document.body.appendChild(svg);
      activeBeams++;
      setTimeout(() => {
        svg.remove();
        activeBeams--;
      }, life);

      // Explosion effect for NATO targets
      if (targetType === "ship" || targetType === "nato") {
        createExplosion(x2, y2, targetType === "ship");
      }

      if (targetType === "digit") {
        if (Math.random() < 0.5) target.classList.add("hex-hit");
        else target.classList.add("hex-hot");
      } else if (targetType === "ship") {
        // Mark ship as hit - change its color to red/orange temporarily
        target.color = "hsl(15, 100%, 60%)";
        // Start shrinking animation before removal
        target.origSize = target.size;
        target.dieStart = performance.now();
        target.dieDuration = 1000; // 1 second shrink
        target.dying = true;
        // Optional: reset color after short time (visual cue)
        setTimeout(() => {
          target.color = "hsl(35, 100%, 60%)";
        }, 2000);
        // No immediate splice; draw loop will remove after shrinking
      } else if (targetType === "navpico") {
        // Navpico hit - randomly rotate and shrink by 15%
        const currentRotation =
          target.style.transform.match(/rotate\(([^)]+)\)/);
        const currentDeg = currentRotation ? parseFloat(currentRotation[1]) : 0;
        const randomRotation = currentDeg + (Math.random() - 0.5) * 90; // ±45 degrees

        const currentScale = target.style.transform.match(/scale\(([^)]+)\)/);
        const currentScaleVal = currentScale ? parseFloat(currentScale[1]) : 1;
        const newScale = currentScaleVal * 0.85; // shrink by 15%

        target.style.transform = `rotate(${randomRotation}deg) scale(${newScale})`;

        // Flash effect
        target.style.filter =
          "brightness(2) drop-shadow(0 0 8px rgba(255,60,60,0.8))";
        setTimeout(() => {
          target.style.filter = "";
        }, 200);
      } else {
        // Other NATO icon - flash red and shrink
        target.color = "hsl(0, 100%, 60%)";
        target.origSize = target.size;
        target.dieStart = performance.now();
        target.dieDuration = 1000;
        target.dying = true;
        setTimeout(() => {
          target.color = "hsl(35, 100%, 60%)";
        }, 1500);
        // No immediate splice; will be removed by draw loop
      }
    }, delay);
  }
  fill();
  updateSums();

  let processing = false;
  // Recompute whenever spans change: coagulate red clusters first, then recount.
  // The `processing` guard prevents re-entrancy from the class changes coagulate
  // triggers on neighbors.
  function onHeroChange() {
    if (processing) return;
    processing = true;
    try {
      coagulate();
      updateSums();
      scheduleFades();
    } finally {
      processing = false;
    }
  }
  new MutationObserver(onHeroChange).observe(pre, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class"],
  });

  // Mark the digit nearest to a viewport point red or green with a 30% chance.
  // The MutationObserver above triggers onHeroChange() -> coagulate + recount.
  // Used by the matrix rain so a falling line "hits" a hero digit as it passes.
  window.__heroHit = function (x, y) {
    const spans = pre.querySelectorAll("span.hex-dim, span.hex-hot");
    let best = null;
    let bestDist = Infinity;
    for (let k = 0; k < spans.length; k++) {
      const r = spans[k].getBoundingClientRect();
      const dx = r.left + r.width / 2 - x;
      const dy = r.top + r.height / 2 - y;
      const d = dx * dx + dy * dy;
      if (d < bestDist) {
        bestDist = d;
        best = spans[k];
      }
    }
    if (best && bestDist < 3600 && Math.random() < 0.8) {
      best.classList.add(Math.random() < 0.5 ? "hex-hit" : "hex-hot");
      return true;
    }
    return false;
  };

  // Exposed for the lightning module to recolor the hero on each strike.
  window.__heroLightning = recolorOnLightning;

  // Remove a random 10-20 red (hex-hit) digits on each lightning strike.
  window.__heroRemoveReds = function () {
    const reds = Array.from(pre.querySelectorAll("span.hex-hit"));
    const n = 10 + Math.floor(Math.random() * 11);
    let removed = 0;
    for (let i = 0; i < n && reds.length; i++) {
      const idx = Math.floor(Math.random() * reds.length);
      deleteDigit(reds.splice(idx, 1)[0]);
      removed++;
    }
    updateSums();
    return removed;
  };

  if (document.readyState === "complete") {
    hero.replaceChildren(pre, heroSums);
    startLaserTimer();
  } else {
    window.addEventListener("DOMContentLoaded", () => {
      hero.replaceChildren(pre, heroSums);
      startLaserTimer();
    });
  }
  window.addEventListener("resize", fill);

  function startLaserTimer() {
    const laserTimer = setInterval(() => {
      if (pre.isConnected) fireLaser();
      else clearInterval(laserTimer);
    }, 35);
  }
})();

(function () {
  const el = document.getElementById("greek");
  if (!el) return;

  el.textContent = WORDS[Math.floor(Math.random() * WORDS.length)];
})();

(function () {
  const IDLE_MS = 115000;
  let lastActivity = Date.now();
  let reloadPending = null;
  let idleCheck = null;

  const EVENTS = [
    "mousemove",
    "mousedown",
    "keydown",
    "scroll",
    "touchstart",
    "click",
    "wheel",
  ];
  EVENTS.forEach((ev) =>
    window.addEventListener(ev, onActivity, { passive: true }),
  );

  function onActivity() {
    lastActivity = Date.now();
    if (reloadPending) {
      clearTimeout(reloadPending);
      reloadPending = null;
      scheduleNext();
    }
  }

  function scheduleNext() {
    clearTimeout(idleCheck);
    idleCheck = setTimeout(
      scheduleReload,
      Math.max(500, IDLE_MS - (Date.now() - lastActivity)),
    );
  }

  function scheduleReload() {
    const idle = Date.now() - lastActivity;
    if (idle >= IDLE_MS) {
    } else {
      scheduleNext();
    }
  }

  scheduleNext();
})();

(function () {
  const overlay = document.getElementById("reveal");
  const tv = document.getElementById("tv");
  const COLOR_KEY = "page-color";
  const TV_CHANCE = 0.5;

  function pickColor() {
    return "hsl(" + Math.floor(Math.random() * 360) + ", 70%, 45%)";
  }

  function spawnTv() {
    const el = tv.cloneNode(true);
    el.removeAttribute("id");
    const size = 180 + Math.random() * 260;
    const x = 8 + Math.random() * 84;
    const y = 10 + Math.random() * 70;
    const rot = (Math.random() - 0.5) * 30;
    const bars = 7;
    const stops = [];
    for (let i = 0; i < bars; i++) {
      const hue = Math.floor(Math.random() * 360);
      stops.push(
        "hsl(" +
          hue +
          ", 80%, 55%) " +
          (i * 100) / bars +
          "% " +
          ((i + 1) * 100) / bars +
          "%",
      );
    }
    el.querySelector(".tv-screen").style.background =
      "linear-gradient(90deg, " + stops.join(", ") + ")";
    el.querySelector(".tv-label").textContent = String(
      Math.floor(Math.random() * 10000),
    ).padStart(4, "0");
    el.style.width = size + "px";
    el.style.height = size * 0.75 + "px";
    el.style.left = x + "%";
    el.style.top = y + "%";
    el.style.transform = "translate(-50%, -50%) rotate(" + rot + "deg)";
    el.style.opacity = (0.8 + Math.random() * 0.2).toFixed(2);
    el.style.display = "block";
    document.body.appendChild(el);
    setTimeout(
      function () {
        el.remove();
      },
      700 + Math.random() * 300,
    );
  }

  function flashTv(onDone) {
    const counts = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
    const count = counts[Math.floor(Math.random() * counts.length)];
    for (let i = 0; i < count; i++) {
      setTimeout(spawnTv, Math.random() * 200);
    }
    if (onDone) setTimeout(onDone, 900);
  }

  function reveal() {
    const color = sessionStorage.getItem(COLOR_KEY);
    sessionStorage.removeItem(COLOR_KEY);
    if (color) {
      overlay.style.transition = "none";
      overlay.style.background = color;
      overlay.style.opacity = "1";
      void overlay.offsetWidth;
      overlay.style.transition = "opacity 800ms ease-out";
      overlay.style.opacity = "0";
    }
    if (Math.random() < TV_CHANCE) flashTv();
  }

  function cover(next) {
    if (Math.random() < TV_CHANCE) {
      flashTv(next);
      return;
    }
    const color = pickColor();
    sessionStorage.setItem(COLOR_KEY, color);
    overlay.style.transition = "none";
    overlay.style.background = color;
    overlay.style.opacity = "0";
    void overlay.offsetWidth;
    overlay.style.transition = "opacity 350ms ease-in";
    overlay.style.opacity = "1";
    setTimeout(next, 400);
  }

  document.addEventListener("click", (e) => {
    if (
      e.defaultPrevented ||
      e.button !== 0 ||
      e.metaKey ||
      e.ctrlKey ||
      e.shiftKey ||
      e.altKey
    )
      return;
    const a = e.target.closest("a[href]");
    if (!a) return;
    if (a.target && a.target !== "_self") return; // keep new-tab / parent / top links untouched
    if (a.hasAttribute("download")) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || url.protocol === "javascript:")
      return;
    e.preventDefault();
    cover(() => {
      location.href = url.href;
    });
  });

  document.addEventListener("submit", (e) => {
    if (e.defaultPrevented) return;
    const form = e.target;
    if (form.dataset.ajax === "true") return;
    const url = new URL(form.action || location.href, location.href);
    if (url.origin !== location.origin) return;
    e.preventDefault();
    // e.defaultPrevented is read‑only; already prevented
    cover(() => {
      form.submit();
    });
  });

  window.addEventListener("pageshow", (e) => {
    if (e.persisted) {
      overlay.style.transition = "none";
      overlay.style.opacity = "0";
      tv.style.display = "none";
    }
  });

  reveal();
})();

(function () {
  const host = document.getElementById("lightning");
  if (!host) return;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const COLORS = [
    { stroke: "rgba(214,255,214,0.95)", glow: "rgba(126,242,154,0.9)" },
    { stroke: "rgba(255,224,224,0.95)", glow: "rgba(255,77,77,0.9)" },
  ];

  function makeBolt() {
    const color = COLORS[Math.floor(Math.random() * COLORS.length)];
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.classList.add("bolt");
    const startX = 30 + Math.random() * 280;
    const endY = 380 + Math.random() * 580;
    const pts = [[startX, -20]];
    let x = startX;
    let y = -20;
    while (y < endY) {
      y += 60 + Math.random() * 90;
      x += Math.random() * 200 - 100;
      pts.push([x, y]);
    }
    const poly = document.createElementNS(SVG_NS, "polyline");
    poly.setAttribute(
      "points",
      pts.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" "),
    );
    poly.setAttribute("fill", "none");
    poly.setAttribute("stroke", color.stroke);
    poly.setAttribute("stroke-width", "3");
    poly.setAttribute("stroke-linejoin", "miter");
    poly.setAttribute("stroke-linecap", "square");
    poly.style.filter =
      "drop-shadow(0 0 6px " +
      color.glow +
      ") drop-shadow(0 0 16px " +
      color.glow +
      ")";
    svg.appendChild(poly);

    const branches = 2 + Math.floor(Math.random() * 4);
    for (let i = 0; i < branches; i++) {
      const from = pts[Math.floor(Math.random() * pts.length)];
      const dir = Math.random() < 0.5 ? -1 : 1;
      const bpts = [[from[0], from[1]]];
      let bx = from[0];
      let by = from[1];
      const len = 70 + Math.random() * 130;
      while (by - from[1] < len) {
        by += 30 + Math.random() * 50;
        bx += dir * (20 + Math.random() * 70);
        bpts.push([bx, by]);
      }
      const bp = document.createElementNS(SVG_NS, "polyline");
      bp.setAttribute(
        "points",
        bpts.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" "),
      );
      bp.setAttribute("fill", "none");
      bp.setAttribute("stroke", color.stroke);
      bp.setAttribute("stroke-width", "1.5");
      bp.style.filter = "drop-shadow(0 0 4px " + color.glow + ")";
      svg.appendChild(bp);
    }

    host.appendChild(svg);
    svg.addEventListener("animationend", () => svg.remove(), { once: true });
  }

  function strike() {
    const n = 1 + Math.floor(Math.random() * 2);
    for (let i = 0; i < n; i++) {
      setTimeout(makeBolt, i * 90);
    }
    host.classList.remove("flash");
    void host.offsetWidth;
    host.classList.add("flash");
    // Recolor the hero digits and recount sums when lightning fires.
    if (window.__heroLightning) window.__heroLightning();
    // Remove a random 10-20 red digits on each strike.
    if (window.__heroRemoveReds) window.__heroRemoveReds();
  }

  function schedule() {
    const delay = 2175 + Math.random() * 6960;
    setTimeout(function () {
      if (!document.hidden) strike();
      schedule();
    }, delay);
  }

  setTimeout(strike, 1200);
  schedule();
})();

(function () {
  const canvas = document.getElementById("matrix");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const fontSize = 16;
  const letterSpacing = 350;
  const trailLen = 88;
  const chars =
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルワヲン0123456789";
  const rnd = Math.random;
  const TARGET_FPS = 40;
  const FRAME_MS = 1000 / TARGET_FPS;

  let w, h, columns, drops, speeds, trails, active;
  let heroTop = null;
  let heroBottom = null;

  function updateHeroBounds() {
    const el = document.getElementById("hero");
    if (el) {
      const r = el.getBoundingClientRect();
      heroTop = r.top;
      heroBottom = r.bottom;
    }
  }

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    ctx.font = fontSize + "px Terminus, monospace";
    columns = Math.max(1, Math.floor(w / fontSize));
    const rows = h / letterSpacing;
    drops = Array.from({ length: columns }, function () {
      return rnd() * rows;
    });
    speeds = Array.from({ length: columns }, function () {
      return 0.5 + rnd() * 1.5;
    });
    trails = Array.from({ length: columns }, function () {
      return "";
    });
    active = Array.from({ length: columns }, function () {
      return rnd() < 0.15;
    });
    updateHeroBounds();
  }
  resize();
  window.addEventListener("resize", resize);
  window.addEventListener("scroll", updateHeroBounds);

  function draw(dt) {
    ctx.fillStyle = "rgba(0, 0, 0, 0.12)";
    ctx.fillRect(0, 0, w, h);
    const charsLen = chars.length;
    const rows = h / letterSpacing;
    const heroHit = window.__heroHit;
    for (let i = 0; i < columns; i++) {
      if (!active[i]) continue;
      const x = i * fontSize;
      const y = drops[i] * letterSpacing;
      if (y - (trailLen - 1) * letterSpacing > h) {
        drops[i] = -rnd() * rows;
        trails[i] = "";
        active[i] = rnd() < 0.15;
        continue;
      }
      // When the head approaches the hero digit table, hit the nearest digit.
      if (heroHit && heroTop !== null && y >= heroTop && y <= heroBottom) {
        heroHit(x, y);
      }
      const head = chars[(rnd() * charsLen) | 0];
      trails[i] = (head + trails[i]).slice(0, trailLen);
      ctx.fillStyle = "rgba(255, 255, 255, 0.47)";
      ctx.fillText(head, x, y);
      for (let j = 1; j < trails[i].length; j++) {
        const ty = y - j * letterSpacing;
        if (ty < -fontSize) break;
        const a = 1 - j / (trailLen + 1);
        ctx.fillStyle = "rgba(0, 255, 65, " + (a * 0.45).toFixed(3) + ")";
        ctx.fillText(trails[i][j], x, ty);
      }
      drops[i] += speeds[i] * dt;
    }
  }

  let last = performance.now();
  let acc = 0;
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) {
      last = performance.now();
      acc = 0;
      requestAnimationFrame(loop);
    }
  });
  function loop(t) {
    if (document.hidden) return;
    const elapsed = Math.min(100, t - last);
    last = t;
    acc += elapsed;
    if (acc >= FRAME_MS) {
      draw(FRAME_MS / 1000);
      acc = 0;
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();

// Ion Storm Effect - Red Alert style cyan lightning
(function () {
  const canvas = document.getElementById("ion-storm");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  const bolts = [];
  const MAX_BOLTS = 4;

  function randomColor() {
    // Cyan variations like Red Alert ion storm
    const hue = 180 + Math.random() * 20; // 180-200 (cyan to blue-cyan)
    const sat = 80 + Math.random() * 20;
    const light = 50 + Math.random() * 30;
    return `hsl(${hue}, ${sat}%, ${light}%)`;
  }

  function createBolt() {
    if (bolts.length >= MAX_BOLTS) return;

    // Start from top of screen, random x
    const startX = Math.random() * w;
    const startY = 0;

    // Create a branching lightning bolt
    const segments = [];
    let x = startX;
    let y = startY;
    const numSegments = 15 + Math.floor(Math.random() * 10);
    const maxLength = h * 1.5;
    const segmentLength = maxLength / numSegments;

    for (let i = 0; i < numSegments; i++) {
      // Main bolt goes down with some horizontal drift
      const angle = (Math.random() - 0.5) * Math.PI * 0.5; // mostly down, some spread
      const dx = Math.sin(angle) * segmentLength;
      const dy = Math.cos(angle) * segmentLength;

      const nextX = x + dx;
      const nextY = y + dy;

      segments.push({
        x1: x,
        y1: y,
        x2: nextX,
        y2: nextY,
        thickness: Math.max(1, 3 - i * 0.15),
        branch: Math.random() < 0.15, // chance to branch
      });

      x = nextX;
      y = nextY;

      // Create branch
      if (segments[segments.length - 1].branch && i < numSegments - 3) {
        const branchAngle = angle + (Math.random() - 0.5) * Math.PI * 0.8;
        const branchLength = segmentLength * (0.5 + Math.random() * 0.5);
        const branchX = x + Math.sin(branchAngle) * branchLength;
        const branchY = y + Math.cos(branchAngle) * branchLength;
        segments.push({
          x1: x,
          y1: y,
          x2: branchX,
          y2: branchY,
          thickness: Math.max(0.5, 2 - i * 0.1),
          branch: false,
        });
      }
    }

    bolts.push({
      segments: segments,
      color: randomColor(),
      life: 100 + Math.random() * 200, // frames to live
      maxLife: 100 + Math.random() * 200,
      born: performance.now(),
      flicker: 0,
    });
  }

  function drawBolt(bolt) {
    const age = bolt.maxLife - bolt.life;
    const progress = 1 - bolt.life / bolt.maxLife;

    // Flicker effect
    bolt.flicker = (bolt.flicker + 1) % 3;
    const flickerAlpha = bolt.flicker === 0 ? 0.7 : 1;

    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    bolt.segments.forEach((seg) => {
      const alpha = (1 - progress) * flickerAlpha * 0.8;
      const thickness = seg.thickness * (1 - progress * 0.5);

      // Main bolt
      ctx.strokeStyle = bolt.color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = thickness;
      ctx.shadowBlur = 15;
      ctx.shadowColor = bolt.color;

      ctx.beginPath();
      ctx.moveTo(seg.x1, seg.y1);
      ctx.lineTo(seg.x2, seg.y2);
      ctx.stroke();

      // Inner bright core
      ctx.shadowBlur = 0;
      ctx.globalAlpha = alpha * 0.6;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = Math.max(0.5, thickness * 0.3);
      ctx.beginPath();
      ctx.moveTo(seg.x1, seg.y1);
      ctx.lineTo(seg.x2, seg.y2);
      ctx.stroke();
    });

    ctx.restore();
  }

  function spawn() {
    if (bolts.length < MAX_BOLTS && Math.random() < 0.02) {
      createBolt();
    }
    setTimeout(spawn, 100);
  }
  spawn();

  function animate(now) {
    if (document.hidden) {
      requestAnimationFrame(animate);
      return;
    }

    // Clear with slight trail effect
    ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
    ctx.fillRect(0, 0, w, h);

    for (let i = bolts.length - 1; i >= 0; i--) {
      const bolt = bolts[i];
      bolt.life--;

      if (bolt.life <= 0) {
        bolts.splice(i, 1);
        continue;
      }

      drawBolt(bolt);
    }

    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
})();
