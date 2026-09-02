// Nav Overlay JavaScript - extracted from base.html

(function () {
    const o = document.getElementById('nav-overlay');
    if (!o) return;
    const N = 30;
    for (let i = 0; i < N; i++) {
        const t = document.createElement('div');
        t.className = 'tile';
        t.style.animationDelay = i * 0.03 + 's';
        o.appendChild(t);
    }
})();

window.addEventListener('pagehide', (e) => {
    const overlay = document.getElementById('nav-overlay');
    if (overlay && !overlay.classList.contains('crumbling')) {
        overlay.classList.add('crumbling');
    }
});