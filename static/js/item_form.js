// Item Form page JavaScript - extracted from item_form.html

function initItemForm(pickerNames, abilities) {
    window.PICKER_NAMES = pickerNames;
    window.ABILITIES = abilities;
    window.ABILITY_OPTIONS = abilities.map(function (a) {
        const desc = (a.description || '') + (a.description_ru ? ' · ' + a.description_ru : '');
        return '<option value="' + a.id + '" title="' + desc + '">' + a.name + '</option>';
    }).join("");

    // Range input sync for parasite_chance
    (function () {
        const el = document.getElementById("parasite_chance");
        const out = document.getElementById("pchance-value");
        function sync() {
            out.textContent = el.value + "%";
            el.style.setProperty("--fill", (el.value / (el.max - el.min) * 100) + "%");
        }
        if (el && out) {
            el.addEventListener("input", sync);
            sync();
        }
    })();

    // Range input sync for quantity
    (function () {
        const el = document.getElementById("quantity");
        const out = document.getElementById("quantity-value");
        function sync() {
            out.textContent = el.value;
            el.style.setProperty("--fill", (el.value / (el.max - el.min) * 100) + "%");
        }
        if (el && out) {
            el.addEventListener("input", sync);
            sync();
        }
    })();

    // Subitems editor
    (function () {
        const rows = document.getElementById("subitems-rows");
        const add = document.getElementById("sub-add");
        const rand = document.getElementById("sub-random");
        if (!rows) return;

        function makeRow() {
            const div = document.createElement("div");
            div.className = "sub-row";
            div.innerHTML =
                '<input type="hidden" name="sub_id" value="">' +
                '<div class="sub-name-wrap">' +
                '<input type="text" name="sub_name" maxlength="50" class="sub-name" aria-label="Subitem name" placeholder="Name">' +
                '<button type="button" class="btn btn-tonal sub-pick" aria-label="Pick item">▾</button>' +
                '</div>' +
                '<input type="number" name="sub_qty" value="1" min="1" step="1" aria-label="Quantity" placeholder="Qty">' +
                '<input type="number" name="sub_revision" value="1" min="1" step="1" aria-label="Revision" placeholder="Rev">' +
                '<input type="hidden" name="sub_is_parasite" value="0">' +
                '<label class="check"><input type="checkbox" class="sub-para-toggle"> para</label>' +
                '<input type="number" name="sub_chance" value="0" min="0" max="90" aria-label="Parasite chance" placeholder="%">' +
                '<select class="sub-abilities" name="sub_ability_0" multiple aria-label="Subitem abilities" title="Subitem abilities">' +
                window.ABILITY_OPTIONS +
                '</select>' +
                '<button type="button" class="btn btn-error sub-remove" aria-label="Remove">×</button>';
            return div;
        }

        function reindexAbilities() {
            rows.querySelectorAll(".sub-row").forEach(function (row, i) {
                const sel = row.querySelector(".sub-abilities");
                if (sel) sel.name = "sub_ability_" + i;
            });
        }

        const formEl = document.querySelector(".form-card form");
        if (formEl) formEl.addEventListener("submit", reindexAbilities);

        function syncParasite(toggle) {
            const row = toggle.closest(".sub-row");
            const input = row.querySelector('input[name="sub_is_parasite"]');
            if (input) input.value = toggle.checked ? "1" : "0";
        }

        rows.addEventListener("change", function (e) {
            if (e.target.classList.contains("sub-para-toggle")) {
                syncParasite(e.target);
            }
        });

        if (add) add.addEventListener("click", function () {
            const row = makeRow();
            rows.appendChild(row);
            const toggle = row.querySelector(".sub-para-toggle");
            if (toggle) syncParasite(toggle);
        });

        if (rand) rand.addEventListener("click", function () {
            const count = 3 + Math.floor(Math.random() * 6);
            const pool = window.PICKER_NAMES.length ? window.PICKER_NAMES : ["Random part"];
            for (let i = 0; i < count; i++) {
                const row = makeRow();
                const input = row.querySelector(".sub-name");
                if (input) input.value = pool[Math.floor(Math.random() * pool.length)];
                const qtyInput = row.querySelector('input[name="sub_qty"]');
                if (qtyInput) qtyInput.value = 1 + Math.floor(Math.random() * 10);
                const revInput = row.querySelector('input[name="sub_revision"]');
                if (revInput) revInput.value = 1 + Math.floor(Math.random() * 9);
                const chanceInput = row.querySelector('input[name="sub_chance"]');
                if (chanceInput) chanceInput.value = Math.random() < 0.2 ? 1 + Math.floor(Math.random() * 90) : 0;
                const toggle = row.querySelector(".sub-para-toggle");
                if (toggle && Math.random() < 0.2) toggle.checked = true;
                if (toggle) syncParasite(toggle);
                rows.appendChild(row);
            }
        });

        rows.addEventListener("click", function (e) {
            if (e.target.classList.contains("sub-remove")) {
                e.target.closest(".sub-row").remove();
            }
        });
    })();

    // Item picker overlay
    (function () {
        const COLS = 10, ROWS = 20, PAGE = COLS * ROWS;
        const overlay = document.getElementById("item-picker");
        const grid = document.getElementById("picker-grid");
        const filterEl = document.getElementById("picker-filter");
        const pageEl = document.getElementById("picker-page");
        const prevBtn = document.getElementById("picker-prev");
        const nextBtn = document.getElementById("picker-next");
        if (!overlay || !grid || !filterEl || !pageEl || !prevBtn || !nextBtn) return;

        let names = window.PICKER_NAMES.slice().sort((a, b) => {
            const la = a.trim().split(/\s+/).pop().toLowerCase();
            const lb = b.trim().split(/\s+/).pop().toLowerCase();
            if (la === lb) return a.localeCompare(b);
            return la.localeCompare(lb);
        });
        let page = 0;
        let target = null;
        let suppressOpen = false;

        function current() {
            const q = filterEl.value.trim().toLowerCase();
            return q ? names.filter((n) => n.toLowerCase().includes(q)) : names;
        }

        function render() {
            const list = current();
            const pages = Math.max(1, Math.ceil(list.length / PAGE));
            page = Math.min(page, pages - 1);
            const start = page * PAGE;
            const slice = list.slice(start, start + PAGE);
            grid.replaceChildren();
            for (const name of slice) {
                const b = document.createElement("button");
                b.type = "button";
                b.className = "cell";
                b.textContent = name;
                b.title = name;
                b.addEventListener("click", () => {
                    if (target) {
                        suppressOpen = true;
                        target.value = name;
                        target.dispatchEvent(new Event("input"));
                    }
                    close();
                });
                grid.appendChild(b);
            }
            pageEl.textContent = "Page " + (page + 1) + " / " + pages;
            prevBtn.disabled = page <= 0;
            nextBtn.disabled = page >= pages - 1;
        }

        function open(input, anchor, presetFilter) {
            target = input;
            page = 0;
            filterEl.value = presetFilter || "";
            overlay.hidden = false;
            render();
            // Position popup near the anchor, clamped to stay within the viewport
            if (anchor) {
                const rect = anchor.getBoundingClientRect();
                const margin = 8;
                const o = overlay.getBoundingClientRect();
                let left = rect.right + 5;
                let top = rect.top;
                if (left + o.width > window.innerWidth - margin) left = rect.left - o.width - 5;
                left = Math.max(margin, left);
                if (top + o.height > window.innerHeight - margin) top = window.innerHeight - o.height - margin;
                top = Math.max(margin, top);
                overlay.style.left = left + "px";
                overlay.style.top = top + "px";
            }
        }

        function close() {
            overlay.hidden = true;
            target = null;
        }

        document.addEventListener("click", (e) => {
            const btn = e.target.closest(".sub-pick");
            if (btn) {
                e.preventDefault();
                const row = btn.closest('.sub-row');
                const input = row ? row.querySelector('.sub-name') : null;
                if (input) open(input, btn);
            }
        });

        const rowsContainer = document.getElementById("subitems-rows");
        if (rowsContainer) {
            rowsContainer.addEventListener("input", (e) => {
                if (!e.target.classList.contains("sub-name")) return;
                if (suppressOpen) {
                    suppressOpen = false;
                    return;
                }
                const input = e.target;
                open(input, input, input.value);
            });
        }

        filterEl.addEventListener("input", () => { page = 0; render(); });
        prevBtn.addEventListener("click", () => { if (page > 0) { page--; render(); } });
        nextBtn.addEventListener("click", () => { page++; render(); });

        const closeBtn = document.getElementById("picker-close");
        if (closeBtn) closeBtn.addEventListener("click", close);

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) close();
        });
    })();

    // Ability filter
    (function () {
        const filter = document.getElementById("ability-filter");
        if (!filter) return;
        filter.addEventListener("input", function () {
            const q = filter.value.trim().toLowerCase();
            document.querySelectorAll("#ability-grid .ability-opt").forEach(function (opt) {
                opt.hidden = q && !opt.textContent.toLowerCase().includes(q);
            });
        });
    })();

    // Ability rearm
    (function () {
        const btn = document.getElementById("ability-rearm");
        const grid = document.getElementById("ability-grid");
        const list = document.getElementById("active-abilities-list");
        if (!btn || !grid) return;

        function refresh() {
            if (!list) return;
            list.innerHTML = '';
            const boxes = Array.prototype.slice.call(
                grid.querySelectorAll('input[name="ability_ids"]:checked')
            );
            if (!boxes.length) {
                const li = document.createElement('li');
                li.className = 'muted';
                li.textContent = 'None selected.';
                list.appendChild(li);
                return;
            }
            boxes.forEach(function (b) {
                const li = document.createElement('li');
                const name = document.createElement('strong');
                name.textContent = b.dataset.name + ': ';
                li.appendChild(name);
                li.appendChild(document.createTextNode(b.dataset.description || ''));
                if (b.dataset.descriptionRu) {
                    const br = document.createElement('br');
                    const ru = document.createElement('span');
                    ru.className = 'ability-ru';
                    ru.textContent = b.dataset.descriptionRu;
                    li.appendChild(br);
                    li.appendChild(ru);
                }
                const rm = document.createElement('a');
                rm.className = 'ability-remove';
                rm.href = '#';
                rm.title = 'Remove ' + b.dataset.name;
                rm.textContent = '×';
                rm.addEventListener('click', function (e) {
                    e.preventDefault();
                    b.checked = false;
                    refresh();
                });
                li.appendChild(rm);
                list.appendChild(li);
            });
        }

        grid.addEventListener('change', refresh);
        btn.addEventListener('click', function () {
            const boxes = Array.prototype.slice.call(
                grid.querySelectorAll('input[name="ability_ids"]')
            );
            const n = 3 + Math.floor(Math.random() * 3);
            boxes.forEach(function (b) { b.checked = false; });
            const pool = boxes.slice();
            const chosen = [];
            while (chosen.length < n && pool.length) {
                const idx = Math.floor(Math.random() * pool.length);
                chosen.push(pool.splice(idx, 1)[0]);
            }
            chosen.forEach(function (b) { b.checked = true; });
            refresh();
        });
        refresh();
    })();
}

(function(){
 const el=document.getElementById('item-form-data');
 if(el){ try{ const d=JSON.parse(el.textContent); initItemForm(d.picker_names||[], d.abilities||[]);}catch(e){} }
 else if(window.ITEM_FORM_PICKER_NAMES && window.ITEM_FORM_ABILITIES){ initItemForm(window.ITEM_FORM_PICKER_NAMES, window.ITEM_FORM_ABILITIES); }
})();