// Events page – wrapped in IIFE for bundle safety.
(function () {
let events = [],
  abilities = [],
  selected = null;

const $ = (id) => document.getElementById(id);

async function load() {
  const dataEl = $("events-data");
  let preEl = null;
  if (dataEl) {
    try {
      preEl = JSON.parse(dataEl.textContent);
      abilities = preEl.abilities || [];
    } catch (e) {
      abilities = [];
    }
  }
  buildAbilityGrid();
  try {
    events = await (await fetch("/api/events")).json();
  } catch (e) {
    events = [];
  }
  updateCounter();
  renderEv();
  if (preEl && preEl.preselect) {
    const target = events.find((e) => String(e.id) === String(preEl.preselect));
    if (target) selectEv(target);
  }
}

function updateCounter() {
  const el = $("ev-count");
  if (el) el.textContent = String(events.length).padStart(3, "0");
}

function renderEv() {
  const q = ($("ev-filter").value || "").toLowerCase();
  const grid = $("ev-grid");
  grid.innerHTML = "";
  events
    .filter((e) => !q || e.name.toLowerCase().includes(q))
    .forEach((e) => {
      const d = document.createElement("div");
      d.className = "ev-item" + (selected === e.id ? " active" : "");

      const main = document.createElement("div");
      main.className = "ev-item-main";
      const name = document.createElement("span");
      name.className = "ev-item-name";
      name.textContent = e.name;
      const rate = document.createElement("span");
      rate.className = "ev-item-rate";
      rate.textContent = e.event_per_10msec + "/10ms";
      main.appendChild(name);
      main.appendChild(rate);

      const tags = document.createElement("div");
      tags.className = "ev-item-tags";
      (e.abilities || []).forEach((a) => {
        const chip = document.createElement("span");
        chip.className = "ev-tag";
        chip.textContent = a.name;
        tags.appendChild(chip);
      });

      d.appendChild(main);
      d.appendChild(tags);
      d.onclick = () => selectEv(e);
      grid.appendChild(d);
    });
}

/* ── target ability fieldset: small grid + parameter tooltip ── */

function buildAbilityGrid() {
  const grid = $("ev-abil-grid");
  if (!grid) return;

  let focusIndex = 0;

  function makeCell(value, label) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "ev-abil-grid-opt";
    b.id = "ev-abil-cell-" + (value === "" ? "none" : value);
    b.textContent = label;
    b.dataset.value = value;
    b.setAttribute("role", "option");
    b.setAttribute("aria-selected", "false");
    b.tabIndex = -1;
    return b;
  }

  grid.appendChild(makeCell("", "NONE"));
  abilities.forEach((a) => grid.appendChild(makeCell(a.id, a.name)));

  if (abilities.length === 0) {
    const note = document.createElement("button");
    note.type = "button";
    note.className = "ev-abil-grid-note";
    note.textContent = "NO ABILITIES";
    note.disabled = true;
    grid.appendChild(note);
  }

  const cells = Array.from(grid.children);

  function setFocus(index) {
    focusIndex = Math.max(0, Math.min(index, cells.length - 1));
    cells.forEach((c, i) => {
      c.tabIndex = i === focusIndex ? 0 : -1;
    });
    cells[focusIndex].focus();
  }

  function currentValue() {
    return grid.dataset.value || "";
  }

  grid.addEventListener("click", (e) => {
    const cell = e.target.closest(".ev-abil-grid-opt");
    if (!cell) return;
    syncAbility(cell.dataset.value);
    setFocus(cells.indexOf(cell));
  });

  grid.addEventListener("keydown", (e) => {
    const idx = cells.indexOf(e.target);
    if (idx < 0) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      setFocus(Math.min(idx + 1, cells.length - 1));
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      setFocus(Math.max(idx - 1, 0));
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocus(Math.min(idx + 2, cells.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocus(Math.max(idx - 2, 0));
    } else if (e.key === "Home") {
      e.preventDefault();
      setFocus(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setFocus(cells.length - 1);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      syncAbility(cells[idx].dataset.value);
    }
  });

  grid.addEventListener("mouseover", (e) => {
    const cell = e.target.closest(".ev-abil-grid-opt");
    if (cell) showAbilityTooltip(cell.dataset.value);
  });

  grid.addEventListener("mouseleave", () => showAbilityTooltip(currentValue()));

  showAbilityTooltip(currentValue());
}

function syncAbility(value) {
  const grid = $("ev-abil-grid");
  if (!grid) return;

  const normalized = String(value ?? "");
  grid.dataset.value = normalized;
  Array.from(grid.children).forEach((c) => {
    const on = c.dataset.value === normalized;
    c.classList.toggle("selected", on);
    c.setAttribute("aria-selected", on ? "true" : "false");
  });
  updateAbilityCount();
  showAbilityTooltip(normalized);
}

function showAbilityTooltip(abilityId) {
  const tooltip = $("ev-abil-tooltip");
  const tooltipBody = $("ev-abil-tooltip-body");
  if (!tooltip || !tooltipBody) return;

  if (!abilityId) {
    tooltip.hidden = true;
    tooltipBody.innerHTML = "";
    return;
  }

  const ability = abilities.find((a) => String(a.id) === String(abilityId));
  if (!ability) {
    tooltip.hidden = true;
    tooltipBody.innerHTML = "";
    return;
  }

  tooltip.hidden = false;
  const en = ability.description || "";
  const ru = ability.description_ru || "";
  const entries = Object.entries(ability.params || {});

  const descBlock = (en || ru)
    ? `
    <div class="ev-abil-tooltip-desc">
      <span class="ev-abil-tooltip-desc-label">DESC // EN</span>
      <span class="ev-abil-tooltip-desc-text">${escapeHtml(en || "—")}</span>
      <span class="ev-abil-tooltip-desc-label">DESC // RU</span>
      <span class="ev-abil-tooltip-desc-text">${escapeHtml(ru || "—")}</span>
    </div>`
    : "";

  const paramsBlock = entries.length
    ? `
    <div class="ev-abil-tooltip-tbl">
      <div class="ev-abil-tooltip-th">
        <span>PARAM</span>
        <span>OP</span>
        <span>COEFF /10MS</span>
      </div>
      ${entries
        .map(([k, p]) => `
      <div class="ev-abil-tooltip-tr">
        <span class="ev-abil-tooltip-param" title="${escapeHtml(p.description ?? "")}">${escapeHtml(k)}</span>
        <span class="ev-abil-tooltip-op">${escapeHtml(p.operation ?? "—")}</span>
        <span class="ev-abil-tooltip-coeff">${escapeHtml(String(p.modify_coefficient_per_10msec ?? "—"))}</span>
      </div>
      ${p.description ? `<div class="ev-abil-tooltip-tr-desc">DESC — ${escapeHtml(p.description)}</div>` : ""}
      `)
        .join("")}
    </div>`
    : "";

  tooltipBody.innerHTML = descBlock + paramsBlock;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function updateAbilityCount() {
  const countEl = $("ev-abil-count");
  const grid = $("ev-abil-grid");
  const hasAbility = grid && grid.dataset.value && grid.dataset.value !== "";
  if (countEl) countEl.textContent = hasAbility ? "1 select" : "0 select";
}

function selectEv(e) {
  selected = e.id;
  const tgt = $("ev-edit-title") || $("ev-edit-tgt");
  if (tgt) tgt.textContent = "TARGET LOCKED :: " + e.name.toUpperCase();
  $("ev-name").value = e.name;
  $("ev-per").value = e.event_per_10msec;
  $("ev-desc").value = e.description || "";
  const abilityId = e.abilities && e.abilities[0] ? String(e.abilities[0].id) : "";
  syncAbility(abilityId);
  $("ev-delete").hidden = false;
  renderEv();
}

// Only initialise on the events page (safe to include in a bundle).
if ($("ev-grid")) {
  $("ev-filter").addEventListener("input", renderEv);

  $("ev-create").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const name = $("ev-new-name").value.trim();
    if (!name) return;
    const r = await fetch("/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!r.ok) {
      alert(await r.text());
      return;
    }
    $("ev-new-name").value = "";
    events = await (await fetch("/api/events")).json();
    updateCounter();
    renderEv();
  });

  $("ev-edit-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (selected === null) return;
    const grid = $("ev-abil-grid");
    const raw = grid && grid.dataset.value;
    const ability_id = raw ? parseInt(raw, 10) : null;
    const r = await fetch("/api/events/" + selected, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: $("ev-name").value,
        description: $("ev-desc").value,
        event_per_10msec: parseFloat($("ev-per").value) || 0,
        ability_id,
      }),
    });
    if (!r.ok) {
      alert(await r.text());
      return;
    }
    events = await (await fetch("/api/events")).json();
    const updated = events.find((x) => x.id === selected);
    if (updated) selectEv(updated);
  });

  $("ev-delete").addEventListener("click", async () => {
    if (selected === null) return;
    if (!confirm("Delete this event?")) return;
    await fetch("/api/events/" + selected, { method: "DELETE" });
    selected = null;
    const tgt = $("ev-edit-title") || $("ev-edit-tgt");
    if (tgt) tgt.textContent = "SELECT EVENT :: NONE";
    syncAbility("");
    $("ev-delete").hidden = true;
    events = await (await fetch("/api/events")).json();
    updateCounter();
    renderEv();
  });

  load();
}
})();
