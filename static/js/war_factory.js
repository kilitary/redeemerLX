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

    function esc(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    // Classify one battle-log line into {icon, cls, title, body}.
    function classifyLogLine(line) {
        // Strip the leading "r<rounds> " so each line starts with the action.
        let md = /^r(\d+)\s+(.*)$/.exec(line.trim());
        const rounds = md ? md[1] : null;
        let text = md ? md[2] : line.trim();

        if (text === "ROSTER:") return { icon: "📜", cls: "wf-roster", title: text, body: "" };
        if (/^unit /.test(text)) return { icon: "🤖", cls: "wf-roster", title: text, body: "" };
        if (/^parameters:/.test(text)) return { icon: "⚙️", cls: "wf-roster-sub", title: text, body: "" };
        if (/^ability .*->/.test(text)) return { icon: "🔧", cls: "wf-roster-sub", title: text, body: "" };
        if (/^abilities:/.test(text)) return { icon: "🔋", cls: "wf-roster-sub", title: text, body: "" };
        if (/^battle rejected$/.test(text)) return { icon: "⛔", cls: "wf-reject", title: text, body: "" };
        if (/^draw$/.test(text)) return { icon: "🤝", cls: "wf-neu", title: text, body: "" };
        if (/^[A-Z]: /.test(text) && /initiative/.test(text)) return { icon: "🏁", cls: "wf-init", title: text, body: "" };

        const tail = rounds ? " r" + rounds : "";
        if (/PARASITE strike/.test(text)) return { icon: "🦠", cls: "wf-para", title: text.replace(/PARASITE/, "").trim(), body: "", rounds: tail };
        if (/MALFUNCTION/.test(text)) return { icon: "💥", cls: "wf-malf", title: text, body: "" };
        if (/DISARMED/.test(text)) return { icon: "🔒", cls: "wf-disarm", title: text, body: "" };
        if (/NO-HIT/.test(text)) return { icon: "🛑", cls: "wf-disarm", title: text, body: "" };
        if (/eliminated/.test(text)) return { icon: "💀", cls: "wf-elim", title: text, body: "" };
        if (/ disabled via /.test(text)) return { icon: "🔌", cls: "wf-disarm", title: text, body: "" };
        if (/ counter /.test(text)) return { icon: "🔁", cls: "wf-counter", title: text, body: "" };
        if (/src=.*delta=.*dst=.*edge=/.test(text)) return { icon: "🎯", cls: "wf-strike", title: text, body: "" };
        if (/exceeded bounds/.test(text)) return { icon: "🚨", cls: "wf-malf", title: text, body: "" };

        // Fall back to a plain row.
        return { icon: "•", cls: "wf-raw", title: text, body: "" };
    }

    function renderBattle(b) {
        const head = document.createElement("div");
        head.className = "wf-battle-head " + (b.battle_rejected ? "wf-reject" : (b.winner_name ? "wf-win" : "wf-neu"));
        const status = b.battle_rejected
            ? "⛔ rejected"
            : (b.winner_name
                ? "🏆 " + esc(b.winner_name)
                : "🤝 draw");
        head.innerHTML =
            esc(b.map) + " · " + status +
            " · <span class='wf-rounds'>" + b.rounds + " round" + (b.rounds === 1 ? "" : "s") + "</span>";

        const body = document.createElement("div");
        body.className = "wf-battle-body";
        (b.log || []).forEach((line) => {
            const { icon, cls, title, body: _b } = classifyLogLine(line);
            const row = document.createElement("div");
            row.className = "wf-line " + cls;
            const ic = document.createElement("span");
            ic.className = "wf-ic";
            ic.textContent = icon;
            const tx = document.createElement("span");
            tx.textContent = title;
            row.appendChild(ic);
            row.appendChild(tx);
            body.appendChild(row);
        });

        const wrap = document.createElement("div");
        wrap.className = "wf-battle";
        wrap.appendChild(head);
        wrap.appendChild(body);
        return wrap;
    }

    function renderLastTickDetail(j, jsonMode) {
        const el = $("wf-last");
        if (!j) { el.innerHTML = ""; return; }
        if (jsonMode) {
            el.innerHTML = esc(JSON.stringify(j, null, 2));
            el.classList.add("wf-pre");
            return;
        }

        el.classList.remove("wf-pre");
        const container = document.createElement("div");
        container.className = "wf-log";
        const header = document.createElement("div");
        header.className = "wf-tick-head";
        header.innerHTML =
            "🔄 gen <span class='num-ok'>" + j.generation + "</span>" +
            " · built <span class='num-ok'>" + j.built + "</span>" +
            " · joined <span class='num-neu'>" + j.joined + "</span>" +
            " · mutated <span class='num-neu'>" + j.mutated_props + "</span>" +
            " · tested <span class='num-neu'>" + j.tested.ok + "/" + j.tested.sample + "</span>";
        container.appendChild(header);
        (j.battles || []).forEach((b) => container.appendChild(renderBattle(b)));
        el.appendChild(container);
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
    $("wf-json-mode").addEventListener("change", () => {
        renderLastTickDetail(lastTick, $("wf-json-mode").checked);
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