// War Factory page JavaScript - extracted from war_factory.html

function initWarFactory() {
    const $ = (id) => document.getElementById(id);
    const statusEl = $("wf-status");
    const lastEl = $("wf-last");
    const logRowsEl = $("wf-log-rows");
    const genEl = $("wf-gen");
    const tbody = $("wf-leaderboard-body");
    let timer = null;
    let stopping = false;

    function readParams() {
        return {
            build_count: parseInt($("wf-build").value, 10) || 0,
            join_pairs: parseInt($("wf-join").value, 10) || 0,
            props_fraction: parseFloat($("wf-pf").value) || 0,
            props_strength: parseFloat($("wf-ps").value) || 0,
            test_sample: parseInt($("wf-test").value, 10) || 1,
            seed: $("wf-seed").value ? parseInt($("wf-seed").value, 10) : null,
            ticks: parseInt($("wf-ticks").value, 10) || 1,
        };
    }

    function renderLeaderboard(rows) {
        tbody.replaceChildren();
        if (!rows || !rows.length) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 8;
            td.className = "empty";
            td.textContent = "No winners yet.";
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }
        const medals = ["🥇", "🥈", "🥉"];
        rows.forEach((r, idx) => {
            const tr = document.createElement("tr");
            const rank = medals[idx] || String(idx + 1);
            const rankTd = document.createElement("td");
            rankTd.textContent = rank;
            if (idx < 3) rankTd.className = "rank-" + (idx + 1);
            tr.appendChild(rankTd);

            const nameTd = document.createElement("td");
            nameTd.textContent = r.name;
            tr.appendChild(nameTd);

            const winsTd = document.createElement("td");
            winsTd.textContent = String(r.wins);
            winsTd.className = "num-ok";
            tr.appendChild(winsTd);

            const fitTd = document.createElement("td");
            fitTd.textContent = r.fitness.toFixed(2);
            fitTd.className = "num-neu";
            tr.appendChild(fitTd);

            const stats = [
                [r.attack.toFixed(2), "num-bad"],
                [r.defense.toFixed(2), "num-neu"],
                [r.speed.toFixed(2), "num-ok"],
                [r.hp.toFixed(2), "num-neu"],
            ];
            stats.forEach(([v, cls]) => {
                const td = document.createElement("td");
                td.textContent = v;
                td.className = cls;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    async function refreshState() {
        try {
            const r = await fetch("/war/factory/state");
            if (!r.ok) return;
            const s = await r.json();
            genEl.textContent = "· gen " + s.generation;
            logRowsEl.textContent = s.total_log_rows;
            renderAuto(s.auto);
            renderLastTick(s.auto && s.auto.last_result ? s.auto.last_result : null);
        } catch (_) {}
        try {
            const r = await fetch("/war/factory/leaderboard?limit=20");
            if (!r.ok) return;
            renderLeaderboard(await r.json());
        } catch (_) {}
    }

    function renderLastTick(t) {
        const el = $("wf-last-tick-summary");
        if (!t) { el.textContent = ""; return; }
        const broken = t.tested.broken;
        const brokenHtml = broken > 0
            ? '<span class="num-bad">🔴 ' + broken + " broken</span>"
            : '<span class="num-ok">🟢 0 broken</span>';
        el.innerHTML =
            "built=<span class='num-ok'>" + t.built + "</span>" +
            " · joined=<span class='num-neu'>" + t.joined + "</span>" +
            " · mutated=<span class='num-neu'>" + t.mutated_props + "</span>" +
            " · tested=<span class='num-neu'>" + t.tested.ok + "/" + t.tested.sample + "</span> · " +
            brokenHtml +
            " · battles=<span class='num-ok'>" + t.battles.length + "</span>";
    }

    function renderAuto(a) {
        if (!a) return;
        const st = $("wf-auto-state");
        const running = a.running;
        const dotCls = running ? "dot dot-on" : (a.errors > 0 ? "dot dot-err" : "dot dot-off");
        st.innerHTML = '<span class="' + dotCls + '"></span>' + (running ? "running" : "stopped");
        const detail = $("wf-auto-detail");
        const err = a.last_error ? " · <span class='num-bad'>error: " + a.last_error + "</span>" : "";
        detail.innerHTML =
            " · ticks=<span class='num-neu'>" + a.tick_count + "</span>" +
            " · gen=<span class='num-neu'>" + a.generation + "</span>" +
            " · interval=" + a.interval + "s" +
            " · pop≤" + a.max_population +
            " · errors=" + a.errors + err;
    }

    function buildQuery(p) {
        const q = new URLSearchParams();
        q.set("build_count", String(p.build_count));
        q.set("join_pairs", String(p.join_pairs));
        q.set("props_fraction", String(p.props_fraction));
        q.set("props_strength", String(p.props_strength));
        q.set("test_sample", String(p.test_sample));
        if (p.seed != null) q.set("seed", String(p.seed));
        return q.toString();
    }

    async function runOnce() {
        const p = readParams();
        statusEl.textContent = "running…";
        const url = "/war/factory/tick?" + buildQuery(p);
        const r = await fetch(url, { method: "POST" });
        const j = await r.json();
        lastEl.textContent = JSON.stringify(j, null, 2);
        statusEl.textContent = "idle";
        await refreshState();
    }

    async function runMany() {
        const p = readParams();
        stopping = false;
        const ticks = Math.max(1, p.ticks);
        for (let i = 0; i < ticks; i++) {
            if (stopping) break;
            statusEl.textContent = "running tick " + (i + 1) + "/" + ticks;
            const url = "/war/factory/tick?" + buildQuery(p);
            const r = await fetch(url, { method: "POST" });
            const j = await r.json();
            lastEl.textContent = JSON.stringify(j, null, 2);
            // Advance seed so a fixed seed yields distinct ticks.
            if (p.seed != null) {
                p.seed = (p.seed * 1103515245 + 12345) & 0x7FFFFFFF;
                $("wf-seed").value = String(p.seed);
            }
            await refreshState();
        }
        statusEl.textContent = "idle";
    }

    $("wf-tick").addEventListener("click", runOnce);
    $("wf-run").addEventListener("click", runMany);
    $("wf-stop").addEventListener("click", () => {
        stopping = true;
        statusEl.textContent = "stopping…";
    });

    async function autoStart() {
        const q = new URLSearchParams();
        q.set("interval", String(parseFloat($("wf-auto-interval").value) || 5));
        q.set("max_population", String(parseInt($("wf-auto-maxpop").value, 10) || 400));
        const mg = $("wf-auto-maxgen").value.trim();
        if (mg) q.set("max_generations", String(parseInt(mg, 10)));
        const r = await fetch("/war/factory/auto/start?" + q.toString(), {
            method: "POST",
        });
        const j = await r.json();
        renderAuto(j.status);
    }

    async function autoStop() {
        const r = await fetch("/war/factory/auto/stop", { method: "POST" });
        const j = await r.json();
        renderAuto(j.status);
    }

    $("wf-auto-start").addEventListener("click", autoStart);
    $("wf-auto-stop").addEventListener("click", autoStop);

    refreshState();
    setInterval(refreshState, 5000);
}

// Auto-initialize on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWarFactory);
} else {
    initWarFactory();
}