// War Factory page JavaScript - extracted from war_factory.html

function initWarFactory() {
    const $ = (id) => document.getElementById(id);
    const statusEl = $("wf-status");
    const lastEl = $("wf-last");
    const logRowsEl = $("wf-log-rows");
    const genEl = $("wf-gen");
    let timer = null;
    let stopping = false;
    let lastTick = null;

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

    function renderLastTick(t) {
        const el = $("wf-last-tick-summary");
        if (!t) {
            el.textContent = "";
            return;
        }
        const broken = t.tested.broken;
        const brokenHtml =
            broken > 0
                ? '<span class="num-bad">🔴 ' + broken + " broken</span>"
                : '<span class="num-ok">🟢 0 broken</span>';
        el.innerHTML =
            "built=<span class='num-ok'>" +
            t.built +
            "</span>" +
            " · joined=<span class='num-neu'>" +
            t.joined +
            "</span>" +
            " · mutated=<span class='num-neu'>" +
            t.mutated_props +
            "</span>" +
            " · tested=<span class='num-neu'>" +
            t.tested.ok +
            "/" +
            t.tested.sample +
            "</span> · " +
            brokenHtml;
    }

    function renderLastTickDetail(j, jsonMode) {
        const el = $("wf-last");
        if (!j) {
            el.innerHTML = "";
            return;
        }
        el.innerHTML = "";
        el.classList.remove("wf-pre");
        if (jsonMode) {
            el.innerHTML = esc(JSON.stringify(j, null, 2));
            el.classList.add("wf-pre");
            return;
        }

        const container = document.createElement("div");
        container.className = "wf-log";
        const header = document.createElement("div");
        header.className = "wf-tick-head";
        header.innerHTML =
            "🔄 gen <span class='num-ok'>" +
            j.generation +
            "</span>" +
            " · built <span class='num-ok'>" +
            j.built +
            "</span>" +
            " · joined <span class='num-neu'>" +
            j.joined +
            "</span>" +
            " · mutated <span class='num-neu'>" +
            j.mutated_props +
            "</span>" +
            " · tested <span class='num-neu'>" +
            j.tested.ok +
            "/" +
            j.tested.sample +
            "</span>";
        container.appendChild(header);
        el.appendChild(container);
    }

    function esc(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    function renderAuto(s) {
        const st = $("wf-auto-state");
        if (!s) { st.innerHTML = ""; return; }
        const running = s.running;
        const dotCls = running
            ? "dot dot-on"
            : s.errors > 0
              ? "dot dot-err"
              : "dot dot-off";
        st.innerHTML =
            '<span class="' + dotCls + '"></span>' +
            (running ? "running" : "stopped");
        const detail = $("wf-auto-detail");
        const err = s.last_error
            ? " · <span class='num-bad'>error: " + s.last_error + "</span>"
            : "";
        detail.innerHTML =
            " · ticks=<span class='num-neu'>" +
            s.tick_count +
            "</span>" +
            " · gen=<span class='num-neu'>" +
            s.generation +
            "</span>" +
            " · interval=" +
            s.interval +
            "s" +
            " · pop≤" +
            s.max_population +
            " · errors=" +
            s.errors +
            err;
    }

    async function refreshState() {
        try {
            const r = await fetch("/war/factory/state");
            if (!r.ok) return;
            const s = await r.json();
            genEl.textContent = "· gen " + s.generation;
            logRowsEl.textContent = s.total_log_rows;
            renderAuto(s.auto);
            renderLastTick(
                s.auto && s.auto.last_result ? s.auto.last_result : null,
            );
        } catch (_) {}
    }

    async function runOnce() {
        const p = readParams();
        statusEl.textContent = "running…";
        const url = "/war/factory/tick?" + buildQuery(p);
        const r = await fetch(url, { method: "POST" });
        const j = await r.json();
        lastTick = j;
        renderLastTickDetail(j, $("wf-json-mode").checked);
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
            lastTick = j;
            renderLastTickDetail(j, $("wf-json-mode").checked);
            if (p.seed != null) {
                p.seed = (p.seed * 1103515245 + 12345) & 0x7fffffff;
                $("wf-seed").value = String(p.seed);
            }
            await refreshState();
        }
        statusEl.textContent = "idle";
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

    $("wf-tick").addEventListener("click", runOnce);
    $("wf-run").addEventListener("click", runMany);
    $("wf-stop").addEventListener("click", () => {
        stopping = true;
        statusEl.textContent = "stopping…";
    });
    $("wf-json-mode").addEventListener("change", () => {
        renderLastTickDetail(lastTick, $("wf-json-mode").checked);
    });

    async function autoStart() {
        const q = new URLSearchParams();
        q.set("interval", String(parseFloat($("wf-auto-interval").value) || 5));
        q.set(
            "max_population",
            String(parseInt($("wf-auto-maxpop").value, 10) || 400),
        );
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
if (document.getElementById("wf-status")) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initWarFactory);
    } else {
        initWarFactory();
    }
}
