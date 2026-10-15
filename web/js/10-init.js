// C.O.R.A web - Init
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Init
// ============================================================

async function init() {
    // Auto-open console in popup window (safe - won't break if blocked)
    try {
        consoleWindow = window.open('console.html', 'cora_console', 'width=800,height=600,menubar=no,toolbar=no');
    } catch (e) {
        console.log('Console popup blocked');
    }

    renderPhases();
    // keys of image services from before the local engine are dropped from old installs
    try { Object.keys(localStorage).filter(k => /^cora_.*_key$/.test(k) && !['cora_github_key', 'cora_weather_key'].includes(k)).forEach(k => localStorage.removeItem(k)); } catch (e) {}
    document.getElementById('githubToken').value = githubToken;

    // Check if first-time user - show warning FIRST before any gates
    const hasBootedBefore = localStorage.getItem('cora_first_time') === 'done';
    if (!hasBootedBefore) {
        // First time user - show the setup warning modal
        // They can choose to wait OR auto-install
        document.getElementById('firstTimeModal').classList.add('visible');
        return;  // Modal handlers will continue the flow
    }

    // Returning user - continue with normal gate checks
    await continueInit();
}

async function continueInit() {
    // Initialize backend terminal (runs checks like CORA.bat)
    await initSetupTerminal();

    // Gate 1: Ollama (required)
    if (!(await checkOllama())) {
        document.getElementById('gateOverlay').classList.add('visible');
        return;
    }

    // Gate 2: Stats Server (optional - can skip)
    if (!(await checkStatsServer())) {
        document.getElementById('statsGateOverlay').classList.add('visible');
        return;
    }

    // Stats server running - continue
    continueAfterStatsCheck();
}

if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => {};
}

window.addEventListener('load', () => setTimeout(init, 500));
