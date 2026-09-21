// Subitem Detail page JavaScript - extracted from subitem_detail.html

function initSubitemAbilities() {
    var grid = document.getElementById('subitem-ability-grid');
    var btn = document.getElementById('subitem-rearm');
    var list = document.getElementById('active-abilities-list');
    if (!grid || !btn) return;

    function refresh() {
        if (!list) return;
        list.innerHTML = '';
        var boxes = Array.prototype.slice.call(grid.querySelectorAll('input[name="ability_ids"]:checked'));
        if (!boxes.length) {
            var li = document.createElement('li');
            li.className = 'muted';
            li.textContent = 'None selected.';
            list.appendChild(li);
            return;
        }
        boxes.forEach(function (b) {
            var li = document.createElement('li');
            var name = document.createElement('strong');
            name.textContent = b.dataset.name + ': ';
            li.appendChild(name);
            li.appendChild(document.createTextNode(b.dataset.description || ''));
            if (b.dataset.descriptionRu) {
                var br = document.createElement('br');
                var ru = document.createElement('span');
                ru.className = 'ability-ru';
                ru.textContent = b.dataset.descriptionRu;
                li.appendChild(br);
                li.appendChild(ru);
            }
            var rm = document.createElement('a');
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
        var boxes = Array.prototype.slice.call(grid.querySelectorAll('input[name="ability_ids"]'));
        var n = 3 + Math.floor(Math.random() * 3);
        boxes.forEach(function (b) { b.checked = false; });
        var pool = boxes.slice();
        var chosen = [];
        while (chosen.length < n && pool.length) {
            var idx = Math.floor(Math.random() * pool.length);
            chosen.push(pool.splice(idx, 1)[0]);
        }
        chosen.forEach(function (b) { b.checked = true; });
        refresh();
    });
    refresh();
}

// Auto-initialize on DOM ready
if (document.getElementById('subitem-ability-grid')) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSubitemAbilities);
    } else {
        initSubitemAbilities();
    }
}