// C.O.R.A web - View Toggle - Split / Setup Terminal / Console / Status
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// View Toggle - Split / Setup Terminal / Console / Status
// ============================================================

let viewMode = 'split';  // 'split', 'setup'

// Show backend terminal fullscreen
async function toggleView() {
    const container = document.getElementById('mainContainer');
    const setupTerminal = document.getElementById('setupTerminal');
    const btn = document.getElementById('toggleBtn');

    if (viewMode === 'split') {
        // Show setup terminal (like CORA.bat output)
        viewMode = 'setup';
        setupTerminal.style.display = 'flex';
        container.style.display = 'none';
        btn.textContent = '[ BACK TO MAIN ]';
        // Just scroll to bottom - logs already accumulated during boot
        const setupLog = document.getElementById('setupLog');
        if (setupLog) setupLog.scrollTop = setupLog.scrollHeight;
    } else {
        // Back to main split view
        backToMain();
    }
}

// Back to main split view
function backToMain() {
    const container = document.getElementById('mainContainer');
    const setupTerminal = document.getElementById('setupTerminal');
    const btn = document.getElementById('toggleBtn');

    viewMode = 'split';
    setupTerminal.style.display = 'none';
    container.style.display = 'grid';
    container.classList.remove('fullscreen-console', 'fullscreen-status');
    btn.textContent = '[ BACKEND TERMINAL ]';
}

// Show split view with terminal on the right side
function showSplitWithTerminal() {
    const container = document.getElementById('mainContainer');
    const setupTerminal = document.getElementById('setupTerminal');
    const btn = document.getElementById('toggleBtn');
    const logContainer = document.getElementById('logContainer');
    const setupLog = document.getElementById('setupLog');

    // Copy terminal content to the right panel log
    if (setupLog && logContainer) {
        logContainer.innerHTML = setupLog.innerHTML;
    }

    viewMode = 'split';
    setupTerminal.style.display = 'none';
    container.style.display = 'grid';
    container.classList.remove('fullscreen-console', 'fullscreen-status');
    btn.textContent = '[ BACKEND TERMINAL ]';
}

// Keyboard shortcut: F key toggles view
document.addEventListener('keydown', (e) => {
    if (e.key === 'f' || e.key === 'F') {
        if (document.activeElement.tagName !== 'INPUT') {
            toggleView();
        }
    }
});
