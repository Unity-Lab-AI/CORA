// C.O.R.A web - Modal Handlers
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Modal Handlers
// ============================================================

function saveApiKeys() {
    pollinationsKey = document.getElementById('pollinationsKey').value.trim();
    githubToken = document.getElementById('githubToken').value.trim();
    if (pollinationsKey) localStorage.setItem('cora_pollinations_key', pollinationsKey);
    if (githubToken) localStorage.setItem('cora_github_key', githubToken);
    document.getElementById('apiModal').classList.remove('visible');
    runBootSequence();
}

function skipApiKeys() {
    document.getElementById('apiModal').classList.remove('visible');
    runBootSequence();
}

function openSettings() {
    document.getElementById('apiModal').classList.add('visible');
}

function openConsoleWindow() {
    consoleWindow = window.open('console.html', 'cora_console', 'width=800,height=600,menubar=no,toolbar=no');
    if (!consoleWindow || consoleWindow.closed) {
        alert('Popup blocked! Please allow popups for this site to open the console window.');
    }
}

function clearAllData() {
    // First warning
    if (!confirm('WARNING: This will delete ALL your CORA data including:\n\n- API keys\n- Chat history\n- Saved preferences\n- All localStorage data\n\nAre you sure?')) {
        return;
    }

    // Second warning
    if (!confirm('FINAL WARNING!\n\nThis action CANNOT be undone.\n\nType "DELETE" in the next prompt to confirm.')) {
        return;
    }

    // Final confirmation
    const confirmation = prompt('Type DELETE to confirm data wipe:');
    if (confirmation !== 'DELETE') {
        alert('Cancelled. Your data is safe.');
        return;
    }

    // Clear everything
    localStorage.clear();
    sessionStorage.clear();

    // Clear cookies for this domain
    document.cookie.split(';').forEach(c => {
        document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
    });

    alert('All CORA data has been wiped.\n\nThe page will now reload.');
    location.reload();
}

async function retryOllama() {
    if (await checkOllama()) {
        document.getElementById('gateOverlay').classList.remove('visible');
        // Now check stats server
        if (!(await checkStatsServer())) {
            document.getElementById('statsGateOverlay').classList.add('visible');
        } else {
            continueAfterStatsCheck();
        }
    } else {
        alert('Ollama still not responding. Make sure "ollama serve" is running.');
    }
}

async function autoInstallFromGate() {
    // Close the gate overlay
    document.getElementById('gateOverlay').classList.remove('visible');
    // Run auto-install
    await autoInstallEverything();
}
