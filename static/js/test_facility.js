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

    function abilityCell(row) {
        const td = document.createElement("td");
        if (row.kind === "ability" && row.ability) {
            td.textContent = row.ability;
        } else {
            td.className = "muted";
            td.textContent = "—";
        }
        return td;
    }

    function operationCell(row) {
        const td = document.createElement("td");
        if (row.kind === "ability" && row.operation) {
            td.className = "operation op-" + row.operation;
            td.textContent = row.operation.toUpperCase();
            td.title = row.detail || row.operation;
        } else {
            td.className = "muted";
            td.textContent = "—";
        }
        return td;
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
        if (!unit.rows.length) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 4;
            td.className = "empty";
            td.textContent = "No abilities or parameters registered for this unit.";
            tr.appendChild(td);
            body.appendChild(tr);
        }
        unit.rows.forEach((row) => {
            const tr = document.createElement("tr");
            tr.appendChild(abilityCell(row));
            const paramTd = document.createElement("td");
            if (row.param) {
                paramTd.textContent = row.param;
                if (row.param_category) paramTd.title = row.param_category;
            } else {
                paramTd.className = "muted";
                paramTd.textContent = "—";
            }
            tr.appendChild(paramTd);
            tr.appendChild(operationCell(row));
            const valTd = document.createElement("td");
            valTd.textContent = row.value || "—";
            tr.appendChild(valTd);
            body.appendChild(tr);
        });
        summary.textContent =
            unit.item.name + " · " +
            (unit.rows.length) + " parameter rows · " +
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
