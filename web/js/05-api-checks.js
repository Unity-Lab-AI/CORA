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

async function checkPollinations() {
    try {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            setTimeout(() => resolve(false), 5000);
            img.src = 'https://image.pollinations.ai/prompt/test?width=64&height=64&nologo=true';
        });
    } catch { return false; }
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

async function get3DayForecast(location = '') {
    // Uses wttr.in JSON format for 3-day forecast (same as desktop app)
    try {
        const url = `https://wttr.in/${encodeURIComponent(location)}?format=j1`;
        const res = await fetch(url, {
            headers: { 'User-Agent': 'CORA/2.0' }
        });
        if (res.ok) {
            const data = await res.json();
            const weather = data.weather || [];
            const forecast = [];
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

            for (let i = 0; i < Math.min(3, weather.length); i++) {
                const day = weather[i];
                const dateStr = day.date || '';
                let dayName = i === 0 ? 'Today' : (i === 1 ? 'Tomorrow' : '');
                if (!dayName && dateStr) {
                    try {
                        const d = new Date(dateStr);
                        dayName = dayNames[d.getDay()];
                    } catch { dayName = `Day ${i + 1}`; }
                }
                // Get midday conditions
                const hourly = day.hourly || [];
                const midIdx = Math.min(4, hourly.length - 1);
                const conditions = hourly[midIdx]?.weatherDesc?.[0]?.value || 'N/A';

                forecast.push({
                    day: dayName,
                    high: day.maxtempF + '°F',
                    low: day.mintempF + '°F',
                    conditions: conditions
                });
            }
            return { forecast, success: true };
        }
    } catch (e) {
        log(`Forecast error: ${e.message}`, 'warn');
    }
    return { forecast: [], success: false };
}

async function getNews() {
    try {
        const res = await fetch('https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=en-US');
        if (res.ok) {
            const d = await res.json();
            return d.items?.slice(0, 5).map(i => i.title) || [];
        }
    } catch {}
    return [];
}

// ============================================================
// AMBIENT AWARENESS SYSTEM - Like desktop ambient_awareness.py
// CORA monitors audio, camera, screen and builds context
// ============================================================

const ambientContext = {
    recentSpeech: [],          // Last 20 things CORA heard
    messageHistory: [],         // Last 20 chat messages
    lastCameraAnalysis: '',     // What CORA last saw through camera
    lastScreenshot: '',         // What CORA last saw on screen
    userActivity: 'unknown',    // working, relaxing, talking, away
    userMood: 'neutral',        // positive, negative, neutral, stressed
    lastInteraction: Date.now()
};

// Store ambient speech (everything CORA hears)
function addAmbientSpeech(text) {
    if (!text.trim()) return;
    ambientContext.recentSpeech.push({
        text: text.trim(),
        time: new Date().toLocaleTimeString()
    });
    if (ambientContext.recentSpeech.length > 20) {
        ambientContext.recentSpeech.shift();
    }
}

// Store message history
function addMessageHistory(role, text) {
    ambientContext.messageHistory.push({
        role: role,
        text: text.substring(0, 500),
        time: new Date().toLocaleTimeString()
    });
    if (ambientContext.messageHistory.length > 20) {
        ambientContext.messageHistory.shift();
    }
    ambientContext.lastInteraction = Date.now();
}

// Capture and analyze camera with LLAVA
async function captureAndAnalyzeCamera() {
    if (!navigator.mediaDevices?.getUserMedia) return null;
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        await new Promise(r => video.onloadedmetadata = r);
        await new Promise(r => setTimeout(r, 500));

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getTracks().forEach(t => t.stop());

        // Convert to base64 for llava
        const base64Image = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

        // Send to llava for REAL analysis
        const analysis = await analyzImageWithLlava(base64Image, 'Describe what you see. Is the user there? What are they doing? What is their mood? Keep it brief.');

        if (analysis) {
            ambientContext.lastCameraAnalysis = analysis;
            console.log('[AMBIENT] Camera analyzed:', analysis.substring(0, 100));
        } else {
            const timestamp = new Date().toLocaleTimeString();
            ambientContext.lastCameraAnalysis = `Camera captured at ${timestamp} (analysis unavailable)`;
        }

        return base64Image;
    } catch (e) {
        console.log('[AMBIENT] Camera capture failed:', e.message);
        return null;
    }
}

// Capture screenshot using getDisplayMedia
async function captureAndAnalyzeScreenshot() {
    if (!navigator.mediaDevices?.getDisplayMedia) return null;
    try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        await new Promise(r => video.onloadedmetadata = r);
        await new Promise(r => setTimeout(r, 300));

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 1920;
        canvas.height = video.videoHeight || 1080;
        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getTracks().forEach(t => t.stop());

        // Convert to base64 for llava
        const base64Image = canvas.toDataURL('image/jpeg', 0.7).split(',')[1];

        // Send to llava for analysis
        const analysis = await analyzImageWithLlava(base64Image, 'Describe what is on the screen. What application or website is open? What is the user working on? Keep it brief.');

        if (analysis) {
            ambientContext.lastScreenshot = analysis;
            console.log('[AMBIENT] Screenshot analyzed:', analysis.substring(0, 100));
        } else {
            const timestamp = new Date().toLocaleTimeString();
            ambientContext.lastScreenshot = `Screenshot at ${timestamp} (analysis unavailable)`;
        }

        return base64Image;
    } catch (e) {
        console.log('[AMBIENT] Screenshot failed:', e.message);
        return null;
    }
}

// Analyze image with llava model
async function analyzImageWithLlava(base64Image, prompt) {
    try {
        const res = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODELS.vision,
                prompt: prompt,
                images: [base64Image],
                stream: false,
                think: false,
                options: { num_ctx: CORA_NUM_CTX, temperature: 0.5, num_predict: 150 }
            })
        });
        if (res.ok) {
            const d = await res.json();
            return d.response?.trim() || null;
        }
    } catch (e) {
        console.log('[LLAVA] Analysis failed:', e.message);
    }
    return null;
}

// Quick camera capture without llava (for immediate use)
async function quickCameraCapture() {
    if (!navigator.mediaDevices?.getUserMedia) return null;
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        await new Promise(r => video.onloadedmetadata = r);
        await new Promise(r => setTimeout(r, 300));

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        canvas.getContext('2d').drawImage(video, 0, 0);
        stream.getTracks().forEach(t => t.stop());

        return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    } catch (e) {
        return null;
    }
}

// Build full context for AI
function buildAmbientContextPrompt() {
    let context = '';

    // Recent ambient speech (what CORA overheard)
    if (ambientContext.recentSpeech.length > 0) {
        context += 'AMBIENT AUDIO (what you overheard recently):\n';
        ambientContext.recentSpeech.slice(-5).forEach(s => {
            context += `- [${s.time}] "${s.text}"\n`;
        });
        context += '\n';
    }

    // Recent chat history
    if (ambientContext.messageHistory.length > 0) {
        context += 'RECENT CONVERSATION:\n';
        ambientContext.messageHistory.slice(-5).forEach(m => {
            context += `- [${m.time}] ${m.role}: ${m.text}\n`;
        });
        context += '\n';
    }

    // Camera context
    if (ambientContext.lastCameraAnalysis) {
        context += `WHAT YOU SEE (camera): ${ambientContext.lastCameraAnalysis}\n`;
    }

    // Screenshot context
    if (ambientContext.lastScreenshot) {
        context += `THEIR SCREEN: ${ambientContext.lastScreenshot}\n`;
    }

    // User activity/mood inference
    if (ambientContext.userActivity !== 'unknown') {
        context += `USER ACTIVITY: ${ambientContext.userActivity}\n`;
    }
    if (ambientContext.userMood !== 'neutral') {
        context += `USER MOOD: ${ambientContext.userMood}\n`;
    }

    // Time since last interaction
    const timeSince = Date.now() - ambientContext.lastInteraction;
    if (timeSince > 60000) {
        const mins = Math.floor(timeSince / 60000);
        context += `TIME SINCE LAST INTERACTION: ${mins} minute${mins > 1 ? 's' : ''}\n`;
    }

    return context;
}

// ============================================================
// Wake Word Detection - "Hey CORA" using Web Speech API
// Now with AMBIENT AWARENESS context!
// ============================================================

let wakeWordRecognition = null;
let wakeWordActive = false;

function initWakeWord() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    wakeWordRecognition = new SpeechRecognition();
    wakeWordRecognition.continuous = true;
    wakeWordRecognition.interimResults = true;
    wakeWordRecognition.lang = 'en-US';

    wakeWordRecognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript.toLowerCase().trim();

            // Store ALL speech for ambient awareness (not just wake word)
            if (event.results[i].isFinal && transcript.length > 3) {
                addAmbientSpeech(transcript);
            }

            // Check for wake words
            if (transcript.includes('hey cora') ||
                transcript.includes('hey kora') ||
                transcript.includes('hey corra') ||
                transcript.includes('okay cora') ||
                (transcript.includes('cora') && transcript.length < 15)) {

                if (event.results[i].isFinal) {
                    onWakeWordDetected();
                }
            }
        }
    };

    wakeWordRecognition.onerror = (event) => {
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            console.log('Wake word error:', event.error);
        }
        if (wakeWordActive) {
            setTimeout(() => startWakeWordListening(), 1000);
        }
    };

    wakeWordRecognition.onend = () => {
        if (wakeWordActive) {
            setTimeout(() => startWakeWordListening(), 100);
        }
    };

    startWakeWordListening();

    // Start periodic camera captures (every 60 seconds)
    setInterval(captureAndAnalyzeCamera, 60000);

    // Start proactive interjection system
    startProactiveInterjections();
}

// ============================================================
// PROACTIVE INTERJECTIONS - CORA speaks up on her own
// Like desktop ambient_awareness.py - she can comment, check in, etc.
// ============================================================

let interjectionCooldown = 0;  // Cooldown in ms
const INTERJECTION_INTERVAL = 45000;  // Check every 45 seconds
const MIN_COOLDOWN = 120000;  // At least 2 minutes between interjections

// Interjection reasons (like desktop)
const InterjectReason = {
    HELPFUL_INFO: 'helpful_info',
    JOKE: 'joke',
    CHECK_IN: 'check_in',
    COMMENT: 'comment',
    QUESTION: 'question',
    ALERT: 'alert',
    VIBE: 'vibe'
};

// Helpful topics that might trigger interjection
const helpfulTopics = ['stuck', 'help', 'error', 'broken', 'how do', 'what is', 'why is', 'problem', 'issue', 'bug', 'fix'];
const funTopics = ['music', 'game', 'movie', 'funny', 'meme', 'joke', 'youtube', 'video'];
const stressIndicators = ['fuck', 'shit', 'damn', 'frustrated', 'angry', 'hate', 'ugh', 'argh', 'wtf'];

function shouldInterject() {
    // Check cooldown
    if (Date.now() < interjectionCooldown) return null;

    const speech = ambientContext.recentSpeech.slice(-10);
    const recentText = speech.map(s => s.text.toLowerCase()).join(' ');

    // Check for stress indicators - high priority check-in
    for (const indicator of stressIndicators) {
        if (recentText.includes(indicator)) {
            return { reason: InterjectReason.CHECK_IN, boost: 0.5, topic: indicator };
        }
    }

    // Check for helpful topics
    for (const topic of helpfulTopics) {
        if (recentText.includes(topic)) {
            return { reason: InterjectReason.HELPFUL_INFO, boost: 0.4, topic: topic };
        }
    }

    // Check for fun topics - occasional comment
    for (const topic of funTopics) {
        if (recentText.includes(topic)) {
            return { reason: InterjectReason.COMMENT, boost: 0.2, topic: topic };
        }
    }

    // Long silence check-in (5+ minutes)
    const silenceTime = Date.now() - ambientContext.lastInteraction;
    if (silenceTime > 300000 && Math.random() < 0.1) {
        return { reason: InterjectReason.CHECK_IN, boost: 0.15, topic: 'silence' };
    }

    // Random vibe check (very low chance)
    if (Math.random() < 0.02) {
        return { reason: InterjectReason.VIBE, boost: 0.05, topic: 'random' };
    }

    return null;
}

async function doProactiveInterjection(trigger) {
    if (!trigger) return;

    // Set cooldown
    interjectionCooldown = Date.now() + MIN_COOLDOWN;

    // Build context
    const context = buildAmbientContextPrompt();

    // Proactive prompts - direct context, no middleman bullshit
    let prompt = '';
    switch (trigger.reason) {
        case InterjectReason.CHECK_IN:
            prompt = `${context}\n\n${trigger.topic === 'silence' ? 'Been quiet for a while.' : 'Seems stressed.'}`;
            break;
        case InterjectReason.HELPFUL_INFO:
            prompt = `${context}\n\nHeard mention of "${trigger.topic}".`;
            break;
        case InterjectReason.COMMENT:
            prompt = `${context}\n\nOverheard: "${trigger.topic}".`;
            break;
        case InterjectReason.VIBE:
            prompt = `${context}`;
            break;
        default:
            prompt = `${context}`;
    }

    try {
        const res = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODEL,
                prompt: prompt,
                system: CORA_SYSTEM_PROMPT,
                stream: false,
                think: false,
                options: { num_ctx: CORA_NUM_CTX, temperature: 0.9, num_predict: 100 }
            })
        });

        if (res.ok) {
            const d = await res.json();
            let response = d.response?.trim() || '';
            if (response.toLowerCase().startsWith('cora:')) response = response.slice(5).trim();

            if (response.length > 10) {
                log(`[PROACTIVE] CORA: "${response}"`, 'cora');
                await speakAndWait(response);
            }
        }
    } catch (e) {
        console.log('[INTERJECTION] Failed:', e.message);
    }
}

function startProactiveInterjections() {
    setInterval(() => {
        if (!aiReady) return;

        const trigger = shouldInterject();
        if (trigger && Math.random() < trigger.boost) {
            doProactiveInterjection(trigger);
        }
    }, INTERJECTION_INTERVAL);
}

function startWakeWordListening() {
    if (wakeWordRecognition && !wakeWordActive) {
        try {
            wakeWordActive = true;
            wakeWordRecognition.start();
        } catch (e) {}
    }
}

function stopWakeWordListening() {
    wakeWordActive = false;
    if (wakeWordRecognition) {
        try {
            wakeWordRecognition.stop();
        } catch (e) {}
    }
}

async function onWakeWordDetected() {
    log('Wake word detected! Gathering context...', 'ok');

    // FIRST: Capture camera and screenshot BEFORE responding (like desktop)
    log('Capturing visual context...', 'info');
    let cameraImage = null;
    let screenshotImage = null;

    // Try to capture camera quickly
    try {
        cameraImage = await quickCameraCapture();
        if (cameraImage) {
            log('Camera captured for context', 'ok');
        }
    } catch (e) {}

    // Analyze what we see with llava if we got an image
    let visualContext = '';
    if (cameraImage) {
        const cameraAnalysis = await analyzImageWithLlava(cameraImage, 'Briefly describe: Is the user there? What are they doing? Their expression/mood?');
        if (cameraAnalysis) {
            visualContext = `CAMERA RIGHT NOW: ${cameraAnalysis}\n`;
            ambientContext.lastCameraAnalysis = cameraAnalysis;
        }
    }

    // Build full context from ambient awareness
    const ambientText = buildAmbientContextPrompt();
    const fullContext = visualContext + ambientText;

    // Ask AI for a contextual response
    try {
        const res = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODEL,
                prompt: `${fullContext}\n\nHey CORA.`,
                system: CORA_SYSTEM_PROMPT,
                stream: false,
                think: false,
                options: { num_ctx: CORA_NUM_CTX, temperature: 0.9, num_predict: 150 }
            })
        });

        if (res.ok) {
            const d = await res.json();
            let response = d.response?.trim();
            if (response && response.length > 3) {
                if (response.toLowerCase().startsWith('cora:')) response = response.slice(5).trim();
                log(`CORA: "${response}"`, 'cora');
                await speakAndWait(response);
            } else {
                // Retry once if empty response
                const retry = await fetch(OLLAMA_URL + '/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: CORA_MODEL,
                        prompt: 'Someone just called your name.',
                        system: CORA_SYSTEM_PROMPT,
                        stream: false,
                think: false,
                        options: { num_ctx: CORA_NUM_CTX, temperature: 0.95, num_predict: 30 }
                    })
                });
                if (retry.ok) {
                    const rd = await retry.json();
                    if (rd.response?.trim()) {
                        log(`CORA: "${rd.response.trim()}"`, 'cora');
                        await speakAndWait(rd.response.trim());
                    }
                }
            }
        }
    } catch (e) {
        log('CORA response failed - AI not responding', 'warn');
    }

    // Focus chat input
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.focus();
        chatInput.placeholder = "I'm listening...";
    }
}
