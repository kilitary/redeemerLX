// Abilities editor – wrapped in IIFE for bundle safety (shares global scope
// with events.js which also declares `abilities` / `selected`).
(function () {
let abilities = [],
  params = [],
  selected = null;

async function load() {
  abilities = await (await fetch("/api/abilities")).json();
  params = await (await fetch("/api/parameters")).json();
  const sel = document.getElementById("ap-param");
  sel.innerHTML = "";
  params.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.id;
    o.textContent = p.par_name;
    sel.appendChild(o);
  });
  renderAb();
  const preEl = document.getElementById("abilities-data");
  if (preEl) {
    try {
      const pre = JSON.parse(preEl.textContent).preselect;
      const target = abilities.find((a) => String(a.id) === String(pre));
      if (target) selectAb(target);
    } catch (e) {}
  }
}

function renderAb() {
  const q = (document.getElementById("ab-filter").value || "").toLowerCase();
  const grid = document.getElementById("ab-grid");
  grid.innerHTML = "";
  abilities
    .filter((a) => !q || a.name.toLowerCase().includes(q))
    .forEach((a) => {
      const d = document.createElement("div");
      d.className = "ab-item" + (selected === a.id ? " active" : "");
      d.textContent = a.name;
      d.onclick = () => selectAb(a);
      grid.appendChild(d);
    });
}

function selectAb(a) {
  selected = a.id;
  document.getElementById("ab-edit-title").textContent = "Edit: " + a.name;
  document.getElementById("ab-name").value = a.name;
  document.getElementById("ab-desc").value = a.description || "";
  document.getElementById("ab-desc-ru").value = a.description_ru || "";
  document.getElementById("ab-current").textContent = "— " + a.name;
  renderAb();
  loadParams();
}

async function loadParams() {
  if (!selected) return;
  const rows = await (
    await fetch("/api/ability-params?ability_id=" + selected)
  ).json();
  const body = document.getElementById("ap-body");
  body.innerHTML = "";
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.param_name}</td><td>${r.modify_coefficient_per_10msec}</td><td>${r.operation}</td><td>${r.curve}</td><td>${r.stack_mode}</td><td>${r.priority}</td><td>${r.enabled ? "yes" : "no"}</td><td><button data-del="${r.id}" class="btn btn-error btn-small">del</button> <button data-edit="${r.id}" class="btn btn-tonal btn-small">edit</button></td>`;
    // inline edit via prompt-like: click edit allows modifying coeff
    tr.querySelector("[data-edit]").onclick = async () => {
      const v = prompt("new coeff/10ms", r.modify_coefficient_per_10msec);
      if (v === null) return;
      await fetch("/api/ability-params/" + r.id, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modify_coefficient_per_10msec: parseFloat(v) }),
      });
      loadParams();
    };
    tr.querySelector("[data-del]").onclick = async () => {
      await fetch("/api/ability-params/" + r.id, { method: "DELETE" });
      loadParams();
    };
    body.appendChild(tr);
  });
}

// Only initialise on the abilities page (safe to include in a bundle).
if (document.getElementById("ab-grid")) {
  document.getElementById("ab-filter").addEventListener("input", renderAb);
  document
    .getElementById("ab-edit-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selected) return;
      await fetch("/api/abilities/" + selected, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("ab-name").value,
          description: document.getElementById("ab-desc").value,
          description_ru: document.getElementById("ab-desc-ru").value,
        }),
      });
      abilities = await (await fetch("/api/abilities")).json();
      renderAb();
    });
  document.getElementById("ap-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selected) return alert("select ability");
    const body = {
      ability_id: selected,
      param_id: parseInt(document.getElementById("ap-param").value),
      modify_coefficient_per_10msec:
        parseFloat(document.getElementById("ap-coeff").value) || 0,
      operation: document.getElementById("ap-op").value,
      curve: document.getElementById("ap-curve").value,
      stack_mode: document.getElementById("ap-stack").value,
      priority: parseInt(document.getElementById("ap-priority").value) || 0,
      min_value: document.getElementById("ap-min").value
        ? parseFloat(document.getElementById("ap-min").value)
        : null,
      max_value: document.getElementById("ap-max").value
        ? parseFloat(document.getElementById("ap-max").value)
        : null,
      base_value: document.getElementById("ap-base").value
        ? parseFloat(document.getElementById("ap-base").value)
        : null,
      enabled: document.getElementById("ap-enabled").checked,
      description: document.getElementById("ap-desc").value,
    };
    const r = await fetch("/api/ability-params", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      alert(await r.text());
      return;
    }
    loadParams();
  });
  load();
}
})();
