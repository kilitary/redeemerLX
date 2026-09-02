  (function () {
  const status = document.getElementById("live-status");
  const form = document.getElementById("filters");
  const qEl = document.getElementById("f-q");
  const colorEl = document.getElementById("f-color");
  const sizeEl = document.getElementById("f-size");
  const offerEl = document.getElementById("f-offer");
  const waterEl = document.getElementById("f-water");
  const sdEl = document.getElementById("f-sd");
  const parasiteEl = document.getElementById("f-parasite");
  const revisionEl = document.getElementById("f-revision");
  const abilityTrigger = document.getElementById("ability-trigger");
  const abilityPopup = document.getElementById("ability-popup");
  const abilityGrid = document.getElementById("ability-grid");
  const abilityCount = document.getElementById("ability-count");
  const sortEl = document.getElementById("f-sort");
  const orderEl = document.getElementById("f-order");
  const priceMin = document.getElementById("price-min");
  const priceMax = document.getElementById("price-max");
  const weightMin = document.getElementById("weight-min");
  const weightMax = document.getElementById("weight-max");
  const hpMin = document.getElementById("hp-min");
  const hpMax = document.getElementById("hp-max");
  const oilMin = document.getElementById("oil-min");
  const oilMax = document.getElementById("oil-max");
  const qtyMin = document.getElementById("qty-min");
  const qtyMax = document.getElementById("qty-max");
  const pchanceMin = document.getElementById("pchance-min");
  const pchanceMax = document.getElementById("pchance-max");
  const priceLabel = document.getElementById("price-label");
  const weightLabel = document.getElementById("weight-label");
  const hpLabel = document.getElementById("hp-label");
  const oilLabel = document.getElementById("oil-label");
  const qtyLabel = document.getElementById("qty-label");
  const pchanceLabel = document.getElementById("pchance-label");

  const BOOLS = new Set(["true", "false"]);
  const PRICE_MAX = 1000;
  const WEIGHT_MAX = 100;
  const HP_MAX = 50000;
  const OIL_MAX = 25;
  const QTY_MAX = 30;
  const PCHANCE_MAX = 99;

  function syncSliders(minEl, maxEl, labelEl, unit, maxVal) {
    let min = parseInt(minEl.value);
    let max = parseInt(maxEl.value);
    if (min > max) {
      if (document.activeElement === minEl) {
        maxEl.value = min;
        max = min;
      } else {
        minEl.value = max;
        min = max;
      }
    }
    if (min === 0 && max === maxVal) {
      labelEl.textContent = "Any";
    } else if (min === max) {
      labelEl.textContent = min + (unit ? " " + unit : "");
    } else {
      labelEl.textContent = min + " – " + max + (unit ? " " + unit : "");
    }
  }

  function filterParams() {
    const p = new URLSearchParams();
    const q = qEl.value.trim();
    const color = colorEl.value;
    const size = sizeEl.value;
    const offer = offerEl.value;
    const water = waterEl.value;
    const sd = sdEl.value;
    const parasite = parasiteEl.value;
    const abilities = Array.from(
      abilityGrid.querySelectorAll('input[type="checkbox"]:checked')
    ).map((cb) => cb.value);
    const pMin = parseInt(priceMin.value);
    const pMax = parseInt(priceMax.value);
    const wMin = parseInt(weightMin.value);
    const wMax = parseInt(weightMax.value);
    const hMin = parseInt(hpMin.value);
    const hMax = parseInt(hpMax.value);
    const oMin = parseInt(oilMin.value);
    const oMax = parseInt(oilMax.value);
    const qMin = parseInt(qtyMin.value);
    const qMax = parseInt(qtyMax.value);
    const pcMin = parseInt(pchanceMin.value);
    const pcMax = parseInt(pchanceMax.value);
    if (q) p.set("q", q);
    if (color) p.set("color", color);
    if (size) p.set("size", size);
    if (BOOLS.has(offer)) p.set("is_offer", offer);
    if (BOOLS.has(water)) p.set("water_resistant", water);
    if (BOOLS.has(sd)) p.set("self_desentry", sd);
    if (BOOLS.has(parasite)) p.set("is_parasite", parasite);
    if (revisionEl.value) p.set("revision", revisionEl.value);
    for (const a of abilities) p.append("ability", a);
    if (pMin > 0) p.set("min_price", pMin);
    if (pMax < PRICE_MAX) p.set("max_price", pMax);
    if (wMin > 0) p.set("weight_min", wMin);
    if (wMax < WEIGHT_MAX) p.set("weight_max", wMax);
    if (hMin > 0) p.set("hp_min", hMin);
    if (hMax < HP_MAX) p.set("hp_max", hMax);
    if (oMin > 0) p.set("oil_min", oMin);
    if (oMax < OIL_MAX) p.set("oil_max", oMax);
    if (qMin > 0) p.set("quantity_min", qMin);
    if (qMax < QTY_MAX) p.set("quantity_max", qMax);
    if (pcMin > 0) p.set("parasite_chance_min", pcMin);
    if (pcMax < PCHANCE_MAX) p.set("parasite_chance_max", pcMax);
    if (sortEl.value && sortEl.value !== "id") p.set("sort", sortEl.value);
    if (orderEl.value && orderEl.value !== "asc") p.set("order", orderEl.value);
    return p;
  }

  function fillSelect(sel, values, current) {
    const clean = (values || []).filter((x) => x != null);
    sel.replaceChildren();
    sel.add(new Option(sel.dataset.label || "All", ""));
    for (const v of clean) sel.add(new Option(String(v), String(v)));
    sel.value = clean.some((x) => String(x) === current) ? current : "";
  }

  function fillAbilities(list) {
    const selected = new Set(
      Array.from(
        abilityGrid.querySelectorAll('input[type="checkbox"]:checked')
      ).map((cb) => cb.value)
    );
    const clean = (list || []).filter(Boolean);
    abilityGrid.replaceChildren();
    for (const item of clean) {
      const name = typeof item === "string" ? item : item.name;
      const desc = typeof item === "string" ? "" : item.description || "";
      const descRu = typeof item === "string" ? "" : item.description_ru || "";
      const label = document.createElement("label");
      label.className = "ability-cell";
      const tip = desc + (descRu ? " · " + descRu : "");
      label.title = name + " — " + (tip || name);
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = name;
      cb.checked = selected.has(name);
      cb.addEventListener("change", () => {
        updateAbilityCount();
        apply();
      });
      label.appendChild(cb);
      label.appendChild(document.createTextNode(name));
      abilityGrid.appendChild(label);
    }
    updateAbilityCount();
  }

  function updateAbilityCount() {
    const n = abilityGrid.querySelectorAll('input[type="checkbox"]:checked').length;
    abilityCount.textContent = n ? String(n) : "";
    abilityCount.classList.toggle("active", n > 0);
  }

  function toggleAbilityPopup(open) {
    abilityPopup.hidden = !open;
    abilityTrigger.setAttribute("aria-expanded", String(open));
  }

  function updateOptions() {
    fetch("/ui/filters/options?" + filterParams().toString())
      .then((r) => (r.ok ? r.json() : null))
      .then((o) => {
        if (!o) return;
        fillSelect(colorEl, o.colors, colorEl.value);
        fillSelect(sizeEl, o.sizes, sizeEl.value);
        fillSelect(revisionEl, o.revisions, revisionEl.value);
        fillAbilities(o.abilities);
      })
      .catch(() => {});
  }

  function fmtDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    const p = (n) => String(n).padStart(2, "0");
    return (
      d.getFullYear() +
      "-" +
      p(d.getMonth() + 1) +
      "-" +
      p(d.getDate()) +
      " " +
      p(d.getHours()) +
      ":" +
      p(d.getMinutes())
    );
  }

  function render(items) {
    const grid = document.querySelector(".cards-grid");
    if (!grid) return;

    grid.innerHTML = "";

    if (!items.length) {
      const emptyDiv = document.createElement("div");
      emptyDiv.className = "empty";
      emptyDiv.textContent = "No items match.";
      grid.appendChild(emptyDiv);
      return;
    }

    for (const item of items) {
      const card = document.createElement("div");
      card.className = "card compact";

      const header = document.createElement("div");
      header.className = "card-header";
      const link = document.createElement("a");
      link.href = "/ui/items/" + item.id;
      link.style.color = "var(--md-primary)";
      link.style.textDecoration = "none";
      link.style.fontWeight = "500";
      link.textContent = item.name;
      header.appendChild(link);
      card.appendChild(header);

      const props = document.createElement("div");
      props.className = "card-props";

      const addProp = (label, value, isMuted = false) => {
        const span = document.createElement("span");
        span.className = "prop" + (isMuted ? " muted" : "");
        if (label) {
          const strong = document.createElement("strong");
          strong.textContent = label;
          span.appendChild(strong);
        }
        span.appendChild(document.createTextNode(value));
        props.appendChild(span);
      };

      addProp("Price: ", "$" + item.price.toFixed(2));
      addProp("Offer: ", item.is_offer ? "Offer" : "—");
      addProp("Color: ", item.color || "—");
      addProp("Size: ", item.size || "—");
      addProp("Qty: ", item.quantity ? String(item.quantity) : "—");
      addProp("Weight: ", item.weight ? item.weight.toFixed(2) + " kg" : "—");
      addProp("HP: ", item.hp ? String(item.hp) : "—");
      addProp("Proof: ", item.is_proof ? "yes" : "—");
      addProp("Water: ", item.water_resistant ? "yes" : "—");
      addProp("Oil/Day: ", item.oil ? item.oil.toFixed(2) + " kg" : "—");
      addProp("P.chance: ", (item.parasite_chance || 0) + "%");
      addProp("Added: ", fmtDate(item.added_at), true);
      addProp("Updated: ", fmtDate(item.updated_at), true);

      card.appendChild(props);

      const actions = document.createElement("div");
      actions.className = "card-actions";
      const edit = document.createElement("a");
      edit.className = "btn btn-tonal";
      edit.href = "/ui/items/" + item.id + "/edit";
      edit.textContent = "Edit";
      actions.appendChild(edit);
      const del = document.createElement("button");
      del.className = "btn btn-error";
      del.type = "button";
      del.textContent = "Delete";
      del.addEventListener("click", () => deleteItem(item.id));
      actions.appendChild(del);
      card.appendChild(actions);

      grid.appendChild(card);
    }
  }

  function refresh() {
    fetch("/items?" + filterParams().toString() + "&limit=50")
      .then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        const prof = r.headers.get("X-Profile");
        if (prof) {
          try {
            window.renderProfile && window.renderProfile(JSON.parse(prof));
          } catch (e) {}
        }
        return r.json();
      })
      .then((data) => {
        render(data);
        status.textContent =
          "Live · " +
          new Date().toLocaleTimeString() +
          " · " +
          data.length +
          " item(s)";
      })
      .catch((err) => {
        status.textContent = "Refresh failed: " + err.message;
      });
  }

  function apply() {
    refresh();
    updateOptions();
  }

  let timer = null;
  function debounced() {
    clearTimeout(timer);
    timer = setTimeout(apply, 250);
  }

  qEl.addEventListener("input", debounced);
  colorEl.addEventListener("change", apply);
  sizeEl.addEventListener("change", apply);
  offerEl.addEventListener("change", apply);
  waterEl.addEventListener("change", apply);
  sdEl.addEventListener("change", apply);
  parasiteEl.addEventListener("change", apply);
  sortEl.addEventListener("change", apply);
  orderEl.addEventListener("change", apply);
  abilityTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleAbilityPopup(abilityPopup.hidden);
  });
  document.addEventListener("click", (e) => {
    if (!abilityPopup.hidden && !abilityPopup.contains(e.target) && e.target !== abilityTrigger) {
      toggleAbilityPopup(false);
    }
  });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    apply();
  });

  // Delegated handler for delete buttons (works for server-rendered and dynamic cards)
  document.addEventListener("click", (e) => {
    const delBtn = e.target.closest(".card-actions .btn-error, [data-delete]");
    if (delBtn) {
      const id = delBtn.dataset.delete || delBtn.getAttribute("data-delete");
      if (id) deleteItem(id);
    }
  });

  function onSliderInput() {
    syncSliders(priceMin, priceMax, priceLabel, "", PRICE_MAX);
    syncSliders(weightMin, weightMax, weightLabel, "kg", WEIGHT_MAX);
    syncSliders(hpMin, hpMax, hpLabel, "", HP_MAX);
    syncSliders(oilMin, oilMax, oilLabel, "kg", OIL_MAX);
    syncSliders(qtyMin, qtyMax, qtyLabel, "", QTY_MAX);
    syncSliders(pchanceMin, pchanceMax, pchanceLabel, "%", PCHANCE_MAX);
    debounced();
  }

  priceMin.addEventListener("input", onSliderInput);
  priceMax.addEventListener("input", onSliderInput);
  weightMin.addEventListener("input", onSliderInput);
  weightMax.addEventListener("input", onSliderInput);
  hpMin.addEventListener("input", onSliderInput);
  hpMax.addEventListener("input", onSliderInput);
  oilMin.addEventListener("input", onSliderInput);
  oilMax.addEventListener("input", onSliderInput);
  qtyMin.addEventListener("input", onSliderInput);
  qtyMax.addEventListener("input", onSliderInput);
  pchanceMin.addEventListener("input", onSliderInput);
  pchanceMax.addEventListener("input", onSliderInput);

  function deleteItem(id) {
    if (!confirm("Delete this item?")) return;
    fetch("/items/" + id, { method: "DELETE" })
      .then((res) => {
        if (res.status === 204) refresh();
        else status.textContent = "Delete failed: HTTP " + res.status;
      })
      .catch(() => {
        status.textContent = "Delete failed: network error";
      });
  }

  syncSliders(priceMin, priceMax, priceLabel, "", PRICE_MAX);
  syncSliders(weightMin, weightMax, weightLabel, "kg", WEIGHT_MAX);
  syncSliders(hpMin, hpMax, hpLabel, "", HP_MAX);
  syncSliders(oilMin, oilMax, oilLabel, "kg", OIL_MAX);
  syncSliders(qtyMin, qtyMax, qtyLabel, "", QTY_MAX);
  syncSliders(pchanceMin, pchanceMax, pchanceLabel, "%", PCHANCE_MAX);
  apply();
  setInterval(function () {
    if (!document.hidden) refresh();
  }, 5000);
})();
