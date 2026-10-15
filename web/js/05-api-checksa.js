// C.O.R.A web - API Checks
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// API Checks
// ============================================================

async function checkOllama() {
    try {
        const r = await fetch(OLLAMA_URL + '/api/tags', { method: 'GET' });
        return r.ok;
    } catch { return false; }
}

async function checkStatsServer() {
    try {
        const r = await fetch('http://localhost:11435/ping', { method: 'GET' });
        return r.ok;
    } catch { return false; }
}

let statsServerSkipped = false;

async function retryStatsServer() {
    if (await checkStatsServer()) {
        document.getElementById('statsGateOverlay').classList.remove('visible');
        continueAfterStatsCheck();
    } else {
        alert('Stats server not responding. Make sure to run:\npython services/stats_server.py');
    }
}

function skipStatsServer() {
    statsServerSkipped = true;
    document.getElementById('statsGateOverlay').classList.remove('visible');
    // Set all stats to N/A
    document.getElementById('statCpu').textContent = 'N/A';
    document.getElementById('statMem').textContent = 'N/A';
    document.getElementById('statDisk').textContent = 'N/A';
    document.getElementById('statGpu').textContent = 'N/A';
    document.getElementById('statVram').textContent = 'N/A';
    continueAfterStatsCheck();
}

async function downloadStatsServer() {
    try {
        const url = 'https://raw.githubusercontent.com/Unity-Lab-AI/CORA/main/services/stats_server.py';
        const response = await fetch(url);
        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'stats_server.py';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    } catch (e) {
        alert('Download failed. Try right-clicking the button and "Save Link As..."');
    }
}

function continueAfterStatsCheck() {
    // Check if this is first boot or returning user
    // Use cora_first_time for consistency (set in init and acceptFirstTime)
    const hasBootedBefore = localStorage.getItem('cora_first_time') === 'done';

    if (hasBootedBefore) {
        // Returning user - quick boot
        runQuickBoot();
    } else {
        // First time - run full boot sequence
        runBootSequence();
    }
}

// First-time modal handlers
async function acceptFirstTime() {
    // User has patience - continue with normal setup flow
    document.getElementById('firstTimeModal').classList.remove('visible');
    // Don't set cora_first_time yet - let runBootSequence set it when complete
    // This ensures returning users only get quick boot after successful first boot

    // Continue with normal gate checks (Ollama, stats server, etc.)
    await continueInit();
}

function rejectFirstTime() {
    // User doesn't have time - send them to puppy videos lol
    window.location.href = 'https://www.youtube.com/results?search_query=cute+puppies';
}

async function autoInstallEverything() {
    // User wants auto-install - check if stats server is running first
    document.getElementById('firstTimeModal').classList.remove('visible');

    // Gate: Stats server required for auto-install
    const statsOk = await checkStatsServer();
    if (!statsOk) {
        // Show the stats server gate modal
        document.getElementById('autoInstallGate').classList.add('visible');
        return;
    }

    // Stats server running - proceed with auto-install
    await runAutoInstall();
}

async function retryAutoInstall() {
    // User says they started the stats server - check again
    const statsOk = await checkStatsServer();
    if (statsOk) {
        document.getElementById('autoInstallGate').classList.remove('visible');
        await runAutoInstall();
    } else {
        alert('Stats server still not responding.\n\nMake sure you ran:\npython services/stats_server.py\n\nAnd it shows "Server running on http://localhost:11435"');
    }
}

function backToFirstTime() {
    // Go back to first-time modal
    document.getElementById('autoInstallGate').classList.remove('visible');
    document.getElementById('firstTimeModal').classList.add('visible');
}

async function downloadStatsServer() {
    // Fetch file and show native Save As dialog
    try {
        const response = await fetch('https://raw.githubusercontent.com/Unity-Lab-AI/CORA/main/services/stats_server.py');
        if (!response.ok) throw new Error('Failed to fetch');
        const blob = await response.blob();

        // Use File System Access API for native Save As dialog
        if (window.showSaveFilePicker) {
            const handle = await window.showSaveFilePicker({
                suggestedName: 'stats_server.py',
                types: [{ description: 'Python File', accept: { 'text/x-python': ['.py'] } }]
            });
            const writable = await handle.createWritable();
            await writable.write(blob);
            await writable.close();
        } else {
            // Fallback for browsers without File System Access API
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'stats_server.py';
            a.click();
            window.URL.revokeObjectURL(url);
        }
    } catch (e) {
        if (e.name === 'AbortError') return; // User cancelled save dialog
        alert('Download failed. Opening file in new tab - right-click and "Save As"');
        window.open('https://raw.githubusercontent.com/Unity-Lab-AI/CORA/main/services/stats_server.py', '_blank');
    }
}

async function runAutoInstall() {
    // Switch to backend terminal view so user can see progress
    const mainContainer = document.getElementById('mainContainer');
    const setupTerminal = document.getElementById('setupTerminal');
    mainContainer.style.display = 'none';
    setupTerminal.style.display = 'flex';
    viewMode = 'setup';  // Track view state correctly
    document.getElementById('toggleBtn').textContent = '[ BACK TO MAIN ]';

    setupLog('', '#ffffff');
    setupLog('============================================================', '#ff00ff');
    setupLog('  AUTO-INSTALL MODE - Sit back and relax!', '#ff00ff');
    setupLog('============================================================', '#ffffff');
    setupLog('', '#ffffff');

    // Step 1: Check/Start Ollama
    setupLog('[AUTO] Checking Ollama...', '#ffff00');
    let ollamaOk = await checkOllama();

    if (!ollamaOk) {
        setupLog('  Ollama not running - attempting to start...', '#ffaa00');
        try {
            const startResp = await fetch('http://localhost:11435/setup/start-ollama', {
                method: 'POST',
                signal: AbortSignal.timeout(10000)
            });
            const result = await startResp.json();
            if (result.success) {
                setupLog('  [OK] Ollama service starting...', '#00ff00');
                setupLog('  Waiting 5 seconds for initialization...', '#ffff00');
                await new Promise(r => setTimeout(r, 5000));
                ollamaOk = await checkOllama();
            }
        } catch (e) {
            setupLog(`  [ERROR] Stats server not running: ${e.message}`, '#ff4444');
            setupLog('  Run: python services/stats_server.py', '#ffaa00');
        }
    }

    if (ollamaOk) {
        setupLog('[OK] Ollama is running!', '#00ff00');
    } else {
        setupLog('[WARN] Ollama not available - some features disabled', '#ffaa00');
        setupLogHTML('  <a href="https://ollama.com/download" target="_blank" style="color: #ff00ff;">Download Ollama</a> to enable AI features');
    }

    // Step 2: Check/Download Models
    if (ollamaOk) {
        setupLog('', '#ffffff');
        setupLog('[AUTO] Checking AI models...', '#ffff00');

        const requiredModels = [
            { name: CORA_MODELS.chat, display: CORA_MODELS.chat, desc: 'Main chat model (CORA brain)' },
            { name: CORA_MODELS.vision, display: CORA_MODELS.vision, desc: 'Vision model (image analysis)' },
            { name: CORA_MODELS.code, display: CORA_MODELS.code, desc: 'Coding model' }
        ].filter((m, i, a) => m.name && a.findIndex(x => x.name === m.name) === i);

        const ollamaStatus = await checkOllamaRunning();
        for (const model of requiredModels) {
            if (hasModel(ollamaStatus.models, model.name)) {
                setupLog(`  [OK] ${model.display} - already installed`, '#00ff00');
            } else {
                setupLog(`  [DOWNLOAD] ${model.display} (~4GB) - this may take a while...`, '#ffaa00');
                try {
                    const pullResp = await fetch(`http://localhost:11435/setup/pull-model/${model.display}`, {
                        method: 'POST',
                        signal: AbortSignal.timeout(600000)
                    });
                    const result = await pullResp.json();
                    if (result.success) {
                        setupLog(`  [OK] ${model.display} installed!`, '#00ff00');
                    } else {
                        setupLog(`  [FAIL] ${model.display}: ${result.message}`, '#ff4444');
                    }
                } catch (e) {
                    setupLog(`  [ERROR] ${model.display}: ${e.message}`, '#ff4444');
                }
            }
        }
    }

    setupLog('', '#ffffff');
    setupLog('============================================================', '#00ff00');
    setupLog('  AUTO-INSTALL COMPLETE - Starting boot sequence!', '#00ff00');
    setupLog('============================================================', '#ffffff');
    setupLog('', '#ffffff');

    // Mark as complete and start boot
    localStorage.setItem('cora_first_time', 'done');

    // Small delay then start boot
    await new Promise(r => setTimeout(r, 1000));
    runBootSequence();
}

// Quick boot for returning users - system checks only, no CORA responses
async function runQuickBoot() {
    bootStartTime = Date.now();
    const logEl = document.getElementById('logContainer');

    log('═══════════════════════════════════════════════', 'system');
    log('    QUICK BOOT - Returning User', 'system');
    log('═══════════════════════════════════════════════', 'system');
    log('Skipping full boot sequence (first-time setup already done)', 'info');
    updateProgress(10, 'Quick boot...');

    // Initialize essentials silently
    initWaveform();
    setPhase('waveform', 'ok');
    setPhase('about', 'ok');

    // Quick voice check
    updateProgress(20, 'Checking voice...');
    try {
        ttsEnabled = await initVoice((msg, pct) => {});
        setPhase('voice', ttsEnabled ? 'ok' : 'warn');
    } catch {
        ttsEnabled = false;
        setPhase('voice', 'warn');
    }

    // Quick AI check
    updateProgress(30, 'Checking AI...');
    try {
        const r = await fetch(OLLAMA_URL + '/api/tags', { signal: AbortSignal.timeout(3000) });
        if (r.ok) {
            aiReady = true;
            setPhase('ai_engine', 'ok');
            setPhase('ai_models', 'ok');
            log('Ollama: Online', 'ok');
        } else {
            setPhase('ai_engine', 'warn');
            setPhase('ai_models', 'warn');
            log('Ollama: Offline', 'warn');
        }
    } catch {
        setPhase('ai_engine', 'warn');
        setPhase('ai_models', 'warn');
        log('Ollama: Offline', 'warn');
    }

    // Quick hardware check
    updateProgress(40, 'Checking hardware...');
    const stats = await fetchSystemStats();
    if (stats) {
        log(`CPU: ${Math.round(stats.cpu.percent)}% | RAM: ${Math.round(stats.memory.percent)}%`, 'ok');
        setPhase('hardware', 'ok');
    } else {
        setPhase('hardware', 'warn');
    }

    // Load saved permissions from localStorage
    updateProgress(50, 'Loading permissions...');
    const savedPerms = JSON.parse(localStorage.getItem('cora_permissions') || '{}');
    log(`Loaded saved permissions: camera=${savedPerms.camera || 'unknown'}, location=${savedPerms.location || 'unknown'}`, 'info');

    // Set phase statuses based on saved state
    setPhase('camera', savedPerms.camera === 'granted' ? 'ok' : 'warn');
    setPhase('tools', 'ok');
    setPhase('code_import', 'ok');
    setPhase('youtube', 'ok');
    setPhase('modals', 'ok');
    setPhase('voice_sys', 'ok');
    setPhase('external', savedPerms.location === 'granted' ? 'ok' : 'warn');
    setPhase('audio', 'ok');
    setPhase('weather', savedPerms.location === 'granted' ? 'ok' : 'warn');
    setPhase('news', 'ok');
    setPhase('vision', 'ok');
    setPhase('imagegen', 'ok');

    updateProgress(80, 'Finalizing...');

    // Quick audio test (silent)
    try {
        const actx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = actx.createOscillator();
        osc.connect(actx.destination);
        osc.start();
        osc.stop(actx.currentTime + 0.01);
    } catch {}

    updateProgress(100, 'Ready!');
    setPhase('final', 'ok');

    const bootTime = ((Date.now() - bootStartTime) / 1000).toFixed(1);
    log(`Quick boot complete in ${bootTime}s`, 'ok');
    log('C.O.R.A IS READY', 'ok');

    // CORA says something quick - system prompt handles personality
    if (aiReady) {
        try {
            const res = await fetch(OLLAMA_URL + '/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: CORA_MODEL,
                    prompt: `Quick boot finished.`,
                    system: CORA_SYSTEM_PROMPT,
                    stream: false,
                think: false,
                    options: { num_ctx: CORA_NUM_CTX, temperature: 0.95, num_predict: 25 }
                })
            });
            if (res.ok) {
                const d = await res.json();
                let response = d.response?.trim();
                // Only use if it's short and reasonable
                if (response && response.length > 5 && response.length < 60) {
                    log(`CORA: "${response}"`, 'cora');
                    await speakAndWait(response);
                }
            }
        } catch {
            // Silent fail - no fallback needed
        }
    }

    // Show chat
    document.getElementById('chatSection').classList.add('visible');
    document.getElementById('chatInput').focus();
}

async function getOllamaModels() {
    try {
        const r = await fetch(OLLAMA_URL + '/api/tags');
        const d = await r.json();
        return d.models || [];
    } catch { return []; }
}

// ------------------------------------------------------------
// Her image engine: local Stable Diffusion behind the local CORA server
// (/image/health, /image/generate, the pictures under /images/). Opened
// without the local server there is no image engine.
// ------------------------------------------------------------
async function checkImageEngine() {
    if (!CORA_LOCAL) return false;
    try {
        const r = await fetch(STATS_BASE + '/image/health', { signal: AbortSignal.timeout(4000) });
        if (!r.ok) return false;
        const h = await r.json();
        return !!h.available;
    } catch { return false; }
}

async function generateImageLocal(prompt, opts = {}) {
    if (!CORA_LOCAL) throw new Error('needs the local CORA server');
    const r = await fetch(STATS_BASE + '/image/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CORA-Token': CORA_LOCAL.token },
        body: JSON.stringify(Object.assign({ prompt }, opts)),
        signal: AbortSignal.timeout(900000)
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.success) throw new Error(d.error || ('HTTP ' + r.status));
    d.url = STATS_BASE + d.url;
    return d;
}

function showGeneratedImage(gen, prompt) {
    // the picture, a Download link (the same file she saved) and where it lives on disk
    const { content, close } = createDynamicModal('CORA - Generated Image', 1000, 760);
    const name = String(gen.path || gen.url).split(/[\\/]/).pop();
    const esc = (t) => String(t || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    content.style.padding = '0';
    content.style.display = 'flex';
    content.style.flexDirection = 'column';
    content.innerHTML = `
        <img src="${gen.url}" style="flex: 1; min-height: 0; width: 100%; object-fit: contain; background: black;">
        <div style="padding: 8px 12px; background: #0a0a0f; color: #ccc; font-size: 12px; display: flex; gap: 14px; align-items: center;">
            <a href="${gen.url}" download="${esc(name)}" style="color: #000; background: #ff00ff; padding: 6px 12px; border-radius: 4px; font-weight: bold; text-decoration: none;">Download</a>
            <span style="color: #888; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${esc(gen.path)}">saved at ${esc(gen.path || name)}</span>
        </div>
        <div style="padding: 0 12px 8px; background: #0a0a0f; color: #888; font-size: 11px;">${esc(prompt)}</div>`;
    return { close };
}

async function imageUrlToBase64(url) {
    const blob = await (await fetch(url)).blob();
    return new Promise((resolve, reject) => {
        const fr = new FileReader();
        fr.onload = () => resolve(String(fr.result).split(',')[1]);
        fr.onerror = reject;
        fr.readAsDataURL(blob);
    });
}

// Store location coords for reuse
let cachedCoords = null;

async function requestLocationPermission() {
    // Request location with generous timeout
    return new Promise((resolve) => {
        log('Requesting location permission...', 'info');
        log('Please click "Allow" when browser asks for location', 'system');

        // Try up to 2 times
        let attempts = 0;
        const maxAttempts = 2;

        function tryGetLocation() {
            attempts++;
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    cachedCoords = pos.coords;
                    log(`Location acquired on attempt ${attempts}`, 'ok');
                    // Save permission for quick boot
                    const perms = JSON.parse(localStorage.getItem('cora_permissions') || '{}');
                    perms.location = 'granted';
                    localStorage.setItem('cora_permissions', JSON.stringify(perms));
                    resolve(pos.coords);
                },
                (err) => {
                    if (err.code === 1) {
                        log('Location permission denied by user', 'warn');
                        resolve(null);  // User denied, don't retry
                    } else if (err.code === 2) {
                        log('Location unavailable', 'warn');
                        resolve(null);
                    } else if (err.code === 3) {
                        if (attempts < maxAttempts) {
                            log(`Location timed out, retrying (${attempts}/${maxAttempts})...`, 'warn');
                            setTimeout(tryGetLocation, 1000);
                        } else {
                            log('Location request timed out after retries', 'warn');
                            resolve(null);
                        }
                    } else {
                        resolve(null);
                    }
                },
                {
                    timeout: 60000,           // 60 sec timeout
                    enableHighAccuracy: false,
                    maximumAge: 300000        // Accept cached location up to 5 min old
                }
            );
        }

        tryGetLocation();
    });
}

async function getLocation() {
    try {
        let coords = cachedCoords;
        if (!coords) {
            coords = await requestLocationPermission();
        }

        // If browser geolocation failed, try IP-based fallback
        if (!coords) {
            log('Trying IP-based location fallback...', 'info');
            try {
                const ipRes = await fetch('https://ipapi.co/json/');
                if (ipRes.ok) {
                    const ipData = await ipRes.json();
                    if (ipData.latitude && ipData.longitude) {
                        log('Got location from IP', 'ok');
                        cachedCoords = { latitude: ipData.latitude, longitude: ipData.longitude };
                        return {
                            city: ipData.city || '',
                            state: ipData.region || '',
                            country: ipData.country_name || '',
                            lat: ipData.latitude,
                            lon: ipData.longitude
                        };
                    }
                }
            } catch (ipErr) {
                log('IP location fallback failed', 'warn');
            }
            return null;
        }

        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${coords.latitude}&lon=${coords.longitude}&format=json`);
        if (res.ok) {
            const d = await res.json();
            return {
                city: d.address?.city || d.address?.town || d.address?.village || '',
                state: d.address?.state || '',
                country: d.address?.country || '',
                lat: coords.latitude,
                lon: coords.longitude
            };
        }
    } catch (e) {
        log(`Location error: ${e.message}`, 'warn');
    }
    return null;
}

async function getWeather(location = '') {
    // Uses wttr.in - FREE, no API key needed (same as desktop app)
    try {
        // wttr.in format: %t=temp, %C=condition, %h=humidity, %w=wind, %f=feels like
        const url = `https://wttr.in/${encodeURIComponent(location)}?format=%t|%C|%h|%w|%f`;
        const res = await fetch(url, {
            headers: { 'User-Agent': 'CORA/2.0' }
        });
        if (res.ok) {
            const text = await res.text();
            const parts = text.trim().split('|');
            if (parts.length >= 5) {
                return {
                    temp: parts[0].trim(),
                    conditions: parts[1].trim(),
                    humidity: parts[2].trim(),
                    wind: parts[3].trim(),
                    feels_like: parts[4].trim(),
                    success: true
                };
            }
        }
    } catch (e) {
        log(`Weather error: ${e.message}`, 'warn');
    }
    return { success: false };
}

// ================================================================
// CORA's Synth Audio Tool - Plays random synth sounds on demand
// Available for CORA to use anytime: playSynth() or playSynth('Bass Drop')
// ================================================================
function playSynth(type = null) {
    const synthTypes = ['Synth Arpeggio', 'Ambient Pad', 'Bass Drop', 'Chiptune Melody'];
    const selected = type && synthTypes.includes(type) ? type : synthTypes[Math.floor(Math.random() * synthTypes.length)];

    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();

        if (selected === 'Synth Arpeggio') {
            const notes = [261.63, 329.63, 392.00, 523.25];
            notes.forEach((freq, i) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.2, ctx.currentTime + i * 0.3);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + i * 0.3 + 0.5);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.3);
                osc.stop(ctx.currentTime + i * 0.3 + 0.6);
            });
        } else if (selected === 'Ambient Pad') {
            const notes = [130.81, 164.81, 196.00, 261.63];
            notes.forEach(freq => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0, ctx.currentTime);
                gain.gain.linearRampToValueAtTime(0.1, ctx.currentTime + 0.5);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 3);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 3);
            });
        } else if (selected === 'Bass Drop') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(200, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(40, ctx.currentTime + 0.5);
            gain.gain.setValueAtTime(0.4, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 2);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 2);
        } else {
            // Chiptune melody
            const melody = [523.25, 587.33, 659.25, 698.46, 783.99, 698.46, 659.25, 523.25];
            melody.forEach((freq, i) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'square';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.1, ctx.currentTime + i * 0.15);
                gain.gain.setValueAtTime(0, ctx.currentTime + i * 0.15 + 0.12);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.15);
                osc.stop(ctx.currentTime + i * 0.15 + 0.15);
            });
        }

        log(`CORA played: ${selected}`, 'ok');
        return { success: true, played: selected };
    } catch (e) {
        log(`Synth error: ${e.message}`, 'warn');
        return { success: false, error: e.message };
    }
}
