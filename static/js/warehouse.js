// Warehouse page JavaScript - extracted from warehouse.html

function initWarehouseMutate(itemOptions) {
    const items = itemOptions.map(it => it.id);
    const opts = itemOptions;
    const countEl = document.getElementById('slut-count');
    const grid = document.getElementById('mutate-grid');
    const form = document.getElementById('mutate-form');

    function selectHtml(index) {
        let out = '<select name="item_ids" required>';
        out += '<option value="" disabled selected>— unit ' + (index + 1) + ' —</option>';
        opts.forEach(function (it) {
            const label = it.name + ' — $' + Number(it.price).toFixed(2) + (it.size ? ' · ' + it.size : '') + ' · Rev ' + (it.revision || 1);
            out += '<option value="' + it.id + '">' + label + '</option>';
        });
        out += '</select>';
        return out;
    }

    function render() {
        const n = Math.min(255, Math.max(2, parseInt(countEl.value, 10) || 2));
        grid.innerHTML = '';
        for (let i = 0; i < n; i++) {
            const field = document.createElement('div');
            field.className = 'field';
            field.innerHTML = '<label>Unit ' + String.fromCharCode(65 + i) + '</label>' + selectHtml(i);
            grid.appendChild(field);
            if (i < n - 1) {
                const x = document.createElement('span');
                x.className = 'mutate-x';
                x.textContent = '×';
                grid.appendChild(x);
            }
        }
    }

    countEl.addEventListener('input', render);
    render();
}

(function(){
  const el=document.getElementById('warehouse-data');
  if(el){ try{ initWarehouseMutate(JSON.parse(el.textContent)); }catch(e){} }
  else if(window.WAREHOUSE_ITEM_OPTIONS){ initWarehouseMutate(window.WAREHOUSE_ITEM_OPTIONS); }
})();