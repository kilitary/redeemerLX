// Test Facility page JavaScript - unit parameter inspector

function initTestFacility() {
    const $ = (id) => document.getElementById(id);
    const body = $("tf-body");
    const summary = $("tf-summary");
    const threat = $("tf-threat");
    const select = $("tf-unit");
    let units = {};

    async function loadUnits() {
        const r = await fetch("/api/units");
        const arr = await r.json();
        units = {};
        select.innerHTML = '<option value="" disabled selected>— select a unit —</option>';
        arr.forEach((u) => {
            units[u.id] = u.name;
            const o = document.createElement("option");
            o.value = u.id;
            o.textContent = u.name;
            select.appendChild(o);
        });
    }

    function getSelectedId() {
        const val = select.value;
        return val ? parseInt(val, 10) : null;
    }

    // Build one wide table per distinct ability. Params are laid out as wide
    // columns; each cell shows the param's operation / coefficient value.
    function abilityTables(abilityGroups) {
        const frag = document.createDocumentFragment();
        abilityGroups.forEach(({ ability, rows }) => {
            const card = document.createElement("div");
            card.className = "tf-ability";

            const title = document.createElement("h3");
            title.textContent = "▸ " + ability;
            card.appendChild(title);

            const desc = document.createElement("div");
            desc.className = "tf-desc";
            const en = rows[0] && rows[0].description;
            const ru = rows[0] && rows[0].description_ru;
            if (en) {
                const enSpan = document.createElement("span");
                enSpan.className = "tf-desc-en";
                enSpan.textContent = en;
                desc.appendChild(enSpan);
            }
            if (ru) {
                const ruSpan = document.createElement("span");
                ruSpan.className = "tf-desc-ru";
                ruSpan.textContent = " · " + ru;
                desc.appendChild(ruSpan);
            }
            if (en || ru) card.appendChild(desc);

            const table = document.createElement("table");
            table.className = "tf-wide";

            const thead = document.createElement("thead");
            const hRow = document.createElement("tr");
            const th = document.createElement("th");
            th.textContent = "OP / PARAM";
            hRow.appendChild(th);
            // distinct params, wide
            rows.forEach((row) => {
                if (!row.param) return;
                const thd = document.createElement("th");
                thd.textContent = row.param;
                if (row.param_category) thd.title = row.param_category;
                hRow.appendChild(thd);
            });
            thead.appendChild(hRow);
            table.appendChild(thead);

            const tbody = document.createElement("tbody");
            const opRow = document.createElement("tr");
            const opLabel = document.createElement("td");
            opLabel.className = "op-label";
            opLabel.textContent = "Operation";
            opRow.appendChild(opLabel);
            rows.forEach((row) => {
                if (!row.param) return;
                const td = document.createElement("td");
                if (row.operation) {
                    td.className = "operation op-" + row.operation;
                    td.textContent = row.operation.toUpperCase();
                    td.title = row.detail || row.operation;
                } else {
                    td.className = "muted";
                    td.textContent = "—";
                }
                opRow.appendChild(td);
            });
            tbody.appendChild(opRow);

            const valRow = document.createElement("tr");
            const valLabel = document.createElement("td");
            valLabel.className = "op-label";
            valLabel.textContent = "Value";
            valRow.appendChild(valLabel);
            rows.forEach((row) => {
                if (!row.param) return;
                const td = document.createElement("td");
                td.textContent = row.value || "—";
                valRow.appendChild(td);
            });
            tbody.appendChild(valRow);

            table.appendChild(tbody);
            card.appendChild(table);
            frag.appendChild(card);
        });
        return frag;
    }

    // Separate table for the item's own measured parameters (kind=param rows).
    function paramTable(paramRows) {
        const frag = document.createDocumentFragment();
        if (!paramRows.length) return frag;
        const card = document.createElement("div");
        card.className = "tf-ability";

        const title = document.createElement("h3");
        title.textContent = "▸ Measured Parameters";
        card.appendChild(title);

        const table = document.createElement("table");
        table.className = "tf-table";
        const thead = document.createElement("thead");
        const hRow = document.createElement("tr");
        ["Parameter", "Category", "Value", "Source"].forEach((h) => {
            const th = document.createElement("th");
            th.textContent = h;
            hRow.appendChild(th);
        });
        thead.appendChild(hRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        paramRows.forEach((row) => {
            const tr = document.createElement("tr");
            const nameTd = document.createElement("td");
            nameTd.textContent = row.param || "—";
            tr.appendChild(nameTd);
            const catTd = document.createElement("td");
            catTd.textContent = row.param_category || "—";
            tr.appendChild(catTd);
            const valTd = document.createElement("td");
            valTd.textContent = row.value || "—";
            tr.appendChild(valTd);
            const srcTd = document.createElement("td");
            srcTd.className = "muted";
            srcTd.textContent = row.detail || "—";
            tr.appendChild(srcTd);
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        card.appendChild(table);
        frag.appendChild(card);
        return frag;
    }

    async function inspect(id) {
        summary.textContent = "analyzing unit #" + id + "…";
        threat.textContent = "ANALYZING";
        threat.style.color = "#ffb454";
        const r = await fetch("/api/units/" + id);
        if (!r.ok) {
            summary.textContent = "unit not found.";
            threat.textContent = "ERROR";
            threat.style.color = "#ff7a7a";
            return;
        }
        const unit = await r.json();
        body.replaceChildren();

        const abilityGroups = new Map();
        const paramRows = [];
        (unit.rows || []).forEach((row) => {
            if (row.kind === "ability") {
                if (!abilityGroups.has(row.ability_id)) {
                    abilityGroups.set(row.ability_id, { ability: row.ability, rows: [] });
                }
                abilityGroups.get(row.ability_id).rows.push(row);
            } else if (row.kind === "param") {
                paramRows.push(row);
            }
        });

        if (!abilityGroups.size && !paramRows.length) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 4;
            td.className = "empty";
            td.textContent = "No abilities or parameters registered for this unit.";
            tr.appendChild(td);
            body.appendChild(tr);
        } else {
            body.appendChild(abilityTables(abilityGroups));
            body.appendChild(paramTable(paramRows));
        }

        summary.textContent =
            unit.item.name + " · " +
            abilityGroups.size + " abilities · " +
            (unit.rows.length) + " rows · " +
            unit.subitems.length + " subitems";
        threat.textContent = "READY";
        threat.style.color = "#7ef29a";
    }

    $("tf-inspect").addEventListener("click", () => {
        const id = getSelectedId();
        if (!id) {
            summary.textContent = "select a valid unit first.";
            return;
        }
        inspect(id);
    });
    select.addEventListener("change", () => {
        const id = getSelectedId();
        if (id) {
            inspect(id);
        }
    });

    loadUnits();
}

// Auto-initialize on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTestFacility);
} else {
    initTestFacility();
}
