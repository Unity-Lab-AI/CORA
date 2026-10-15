// C.O.R.A web - Boot Sequence - EXACT match to desktop boot_sequence.py
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Boot Sequence - EXACT match to desktop boot_sequence.py
// ============================================================

let ttsEnabled = true;  // Track if TTS is working

async function runBootSequence() {
    bootStartTime = Date.now();

    // Load system prompt from GitHub FIRST (config/system_prompt.txt)
    log('Loading CORA personality from system_prompt.txt...', 'info');
    const promptSource = await loadSystemPrompt();
    log(`System prompt: ${CORA_SYSTEM_PROMPT ? CORA_SYSTEM_PROMPT.length + ' chars' : 'MISSING!'} (${promptSource})`, promptSource === 'github' ? 'ok' : 'warn');

    // ================================================================
    // PHASE 0.8: WAVEFORM INITIALIZATION
    // ================================================================
    setPhase('waveform', 'running');
    log('PHASE 0.8: WAVEFORM VISUAL', 'phase');
    updateProgress(3, 'Initializing waveform...');
    initWaveform();
    log('AudioWaveform module loaded', 'ok');
    log('Boot display exists', 'ok');
    log('Waveform widget created', 'ok');
    log('Audio buffer initialized', 'ok');
    log('All waveform checks passed', 'ok');
    setPhase('waveform', 'ok');
    await sleep(200);

    // ================================================================
    // PHASE 0.9: ABOUT CORA (Introduction)
    // ================================================================
    setPhase('about', 'running');
    log('PHASE 0.9: ABOUT CORA', 'phase');
    updateProgress(6, 'Loading identity...');
    log('═══════════════════════════════════════════════', 'system');
    log('    C.O.R.A - Cognitive Operations & Reasoning Assistant', 'system');
    log('    Version 1.0.0 | Unity AI Lab | 2025', 'system');
    log('═══════════════════════════════════════════════', 'system');
    log('', 'info');
    log('Developers:', 'info');
    log('  Hackall360 - Lead Code Necromancer', 'info');
    log('  Sponge - Chaos Engineer', 'info');
    log('  GFourteen - Digital Alchemist', 'info');
    log('', 'info');
    log('Links:', 'info');
    log('  Website: https://www.unityailab.com', 'info');
    log('  GitHub: https://github.com/Unity-Lab-AI', 'info');
    log('  Discord: https://discord.gg/D33Bk6Ay', 'info');
    log('  Email: unityailabcontact@gmail.com', 'info');
    log('', 'info');
    log('© 2025 Unity AI Lab. All rights reserved.', 'info');
    log('═══════════════════════════════════════════════', 'system');

    // Don't try to speak here - AI isn't ready yet!
    // CORA introduces herself in Phase 2.1 AFTER models are confirmed and aiReady=true
    // This prevents raw data from being spoken before the system prompt kicks in
    log('Identity loaded - CORA will introduce herself after AI is online', 'info');

    setPhase('about', 'ok');
    await sleep(200);

    // ================================================================
    // PHASE 1.0: VOICE SYNTHESIS (unity-voice-v2, her own voice)
    // ================================================================
    setPhase('voice', 'running');
    log('PHASE 1.0: VOICE SYNTHESIS', 'phase');
    updateProgress(8, 'Connecting to her voice...');
    log('Connecting to unity-voice-v2 (her own trained voice)...', 'info');

    const voiceOk = await initVoice((msg, progress) => {
        log(msg, 'info');
        updateProgress(8 + (progress * 0.07), msg);
    });

    if (voiceOk) {
        log('Unity voice v2 online', 'ok');
        document.getElementById('ttsNotice').textContent = 'Unity voice v2 - her own voice';
        document.getElementById('ttsNotice').style.color = '#00ff88';
        setPhase('voice', 'ok');
        ttsEnabled = true;
        updateProgress(15, 'Voice online');
        if (audioContext && audioContext.state === 'suspended') {
            await audioContext.resume();
            log('AudioContext resumed', 'info');
        }
        log('Testing her voice...', 'info');
        await speakAndWait('Voice synthesis online. Her own voice, version two.');
        log('Voice test passed', 'ok');
    } else {
        log(CORA_LOCAL ? 'Her voice is not reachable (unity-voice-v2 sidecar down) - text only' : 'No local CORA server - text only here', 'warn');
        document.getElementById('ttsNotice').textContent = CORA_LOCAL ? 'Voice offline (sidecar down) - text only' : 'Text only (run CORA locally for her voice)';
        document.getElementById('ttsNotice').style.color = '#ffaa00';
        ttsEnabled = false;
        setPhase('voice', 'warn');
        updateProgress(15, 'Text only');
    }
    // ================================================================
    // PHASE 2.0: AI ENGINE (Ollama)
    // ================================================================
    setPhase('ai_engine', 'running');
    log('PHASE 2.0: AI ENGINE', 'phase');
    updateProgress(20, 'Checking Ollama...');
    log('Checking Ollama connection...', 'info');
    const ollamaOk = await checkOllama();
    if (ollamaOk) {
        log('AI Engine online - Ollama', 'ok');
        document.getElementById('statOllama').textContent = 'Online';
        document.getElementById('statOllama').className = 'stat-value';
        setPhase('ai_engine', 'ok');
        // Don't speak hardcoded - CORA will introduce herself after AI models are confirmed
    } else {
        log('AI Engine not responding', 'fail');
        document.getElementById('statOllama').textContent = 'Offline';
        document.getElementById('statOllama').className = 'stat-value fail';
        setPhase('ai_engine', 'fail');
        document.getElementById('gateOverlay').classList.add('visible');
        return;  // Blocked - can't continue without AI
    }

    // ================================================================
    // PHASE 2.1: AI MODELS CHECK
    // ================================================================
    setPhase('ai_models', 'running');
    log('PHASE 2.1: AI MODELS CHECK', 'phase');
    updateProgress(25, 'Checking models...');
    const models = await getOllamaModels();
    log(`Found ${models.length} models installed`, 'info');
    if (models.length > 0) {
        models.slice(0, 5).forEach(m => log(`  - ${m.name}`, 'ok'));
        setPhase('ai_models', 'ok');
        // AI is now ready for CORA responses!
        aiReady = true;
        log('CORA AI responses enabled', 'ok');

        // The configured brain if it is installed, else the first installed model
        const wanted = CORA_MODELS.chat;
        const installed = models.find(m => m.name === wanted || m.name.split(':')[0] === wanted.split(':')[0]);
        CORA_MODEL = installed ? installed.name : (models[0]?.name || wanted);
        log(`CORA brain: ${CORA_MODEL}`, 'ok');

        // CORA introduces herself - JUST DATA, system prompt is the personality
        const introData = `Just came online. CORA v${CORA_VERSION}. Unity AI Lab. Creators: Hackall360, Sponge, GFourteen, Alfreddo. Website https://www.unityailab.com, GitHub https://github.com/Unity-Lab-AI, Discord https://discord.gg/D33Bk6Ay. Introduce yourself.`;
        const coraIntro = await coraRespond('Introduction', introData, 'ok', 'full');
        await speakAndWait(coraIntro);

        // Log models count
        log(`${models.length} AI models ready`, 'ok');
    } else {
        log('No models found - need to pull some', 'warn');
        setPhase('ai_models', 'warn');
        // Can't use AI since no models - this is a system error message, not CORA
        log(`SYSTEM: No AI models found. Pull the brain with: ollama pull ${CORA_MODELS.chat}`, 'fail');
    }

    // ================================================================
    // PHASE 3.0: HARDWARE CHECK - Fetch from local stats server
    // ================================================================
    setPhase('hardware', 'running');
    log('PHASE 3.0: HARDWARE CHECK', 'phase');
    updateProgress(30, 'Checking hardware...');

    // Try to fetch real stats from localhost:11435
    log('Connecting to stats server...', 'info');
    const stats = await fetchSystemStats();

    if (stats) {
        log(`CPU Usage: ${Math.round(stats.cpu.percent)}%`, 'ok');
        log(`Memory: ${Math.round(stats.memory.percent)}% (${stats.memory.used_gb}GB / ${stats.memory.total_gb}GB)`, 'ok');
        log(`Disk: ${Math.round(stats.disk.percent)}%`, 'ok');

        if (stats.gpu && stats.gpu.available) {
            log(`GPU: ${stats.gpu.name}`, 'ok');
            log(`GPU Load: ${stats.gpu.utilization}%`, 'ok');
            log(`VRAM: ${stats.gpu.memory_used}MB / ${stats.gpu.memory_total}MB`, 'ok');
            log(`GPU Temp: ${stats.gpu.temperature}°C`, 'ok');
        } else {
            log('GPU: No NVIDIA GPU detected', 'warn');
        }

        log('Network: Connected', 'ok');
        setPhase('hardware', 'ok');

        // Start polling for live updates
        startStatsPolling();

        // Hardware summary - give CORA the ACTUAL stats
        let hw_data = `Hardware scan done. CPU at ${Math.round(stats.cpu.percent)}%, RAM at ${Math.round(stats.memory.percent)}%, Disk at ${Math.round(stats.disk.percent)}%`;
        if (stats.gpu && stats.gpu.available) {
            hw_data += `, GPU ${stats.gpu.name} at ${stats.gpu.utilization}% load, ${stats.gpu.temperature}°C`;
        } else {
            hw_data += `, no dedicated GPU`;
        }
        const hwResponse = await coraRespond('Hardware', hw_data, 'ok');
        await speakAndWait(hwResponse);
    } else {
        // Stats server not running
        log('Stats server not running (start with: python services/stats_server.py)', 'warn');
        log('Network: ' + (navigator.onLine ? 'Connected' : 'Disconnected'), navigator.onLine ? 'ok' : 'warn');
        document.getElementById('statNet').textContent = navigator.onLine ? 'Online' : 'Offline';
        setPhase('hardware', 'warn');
        const hwWarn = await coraRespond('Hardware', 'Hardware stats server not running. No real-time monitoring.', 'warn');
        await speakAndWait(hwWarn);
    }

    // ================================================================
    // PHASE 3.1: LIVE CAMERA FEED TEST - Actually test camera like desktop
    // ================================================================
    setPhase('camera', 'running');
    log('PHASE 3.1: LIVE CAMERA FEED TEST', 'phase');
    updateProgress(35, 'Testing camera...');

    let liveCameraWorking = false;
    let cameraTestModal = null;

    if (navigator.mediaDevices?.getUserMedia) {
        // Show permission prompt and wait for user
        log('Camera permission required...', 'info');
        const permResult = await showPermissionPrompt(
            'Camera Permission Required',
            'CORA needs access to your camera to test live video feed and enable vision features.',
            '📷'
        );

        if (permResult === 'skip' || permResult === 'denied') {
            log(`Camera permission ${permResult} by user`, 'warn');
            setPhase('camera', 'warn');
            const camSkip = await coraRespond('Camera', `Camera permission ${permResult}.`, 'warn');
            await speakAndWait(camSkip);
        } else if (permResult === 'granted') {
            log('Testing live camera feed...', 'info');

            // Try multiple camera devices like desktop (indices 0, 1, 2)
            let stream = null;
            let cameraError = null;
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(d => d.kind === 'videoinput');
            log(`Found ${videoDevices.length} camera device(s)`, 'info');

            for (let i = 0; i < Math.max(videoDevices.length, 3); i++) {
                try {
                    log(`Trying camera ${i}...`, 'info');
                    const constraints = videoDevices[i]
                        ? { video: { deviceId: { exact: videoDevices[i].deviceId } } }
                        : { video: true };
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    log(`Camera ${i} working!`, 'ok');
                    break;
                } catch (e) {
                    log(`Camera ${i}: ${e.message}`, 'warn');
                    cameraError = e;
                    await sleep(500);  // Brief delay before trying next
                }
            }

            try {
                if (!stream) throw cameraError || new Error('No camera available');
                log('Live camera feed started', 'ok');
                // Save camera permission for quick boot
                const perms = JSON.parse(localStorage.getItem('cora_permissions') || '{}');
                perms.camera = 'granted';
                localStorage.setItem('cora_permissions', JSON.stringify(perms));

                // Show camera in modal - stays live until user closes it
                const { content, close, modal } = createDynamicModal('CORA - Live Camera Feed', 800, 600);

                // Store stream reference so it stops when modal closes
                const originalClose = close;
                cameraTestModal = {
                    close: () => {
                        stream.getTracks().forEach(t => t.stop());
                        log('Camera feed closed', 'info');
                        originalClose();
                    },
                    modal: modal,
                    minimize: () => {
                        if (modal) modal.style.zIndex = '100';  // Send behind main content
                    },
                    restore: () => {
                        if (modal) modal.style.zIndex = '2000';  // Bring back to front
                    }
                };

                const video = document.createElement('video');
                video.srcObject = stream;
                video.autoplay = true;
                video.style.cssText = 'width: 100%; height: 100%; object-fit: contain; background: black;';
                content.style.padding = '0';
                content.appendChild(video);

                log('Camera feed live - window stays open', 'info');
                await sleep(2000);  // Brief pause to let video stabilize

                // Take snapshot for AI analysis
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
                canvas.getContext('2d').drawImage(video, 0, 0);
                log(`Snapshot captured: ${canvas.width}x${canvas.height}`, 'ok');

                // Send to llava for REAL vision analysis like desktop
                log('Analyzing snapshot with llava...', 'info');
                const base64Image = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
                let camera_desc = null;
                try {
                    camera_desc = await analyzImageWithLlava(base64Image, 'Describe what you see briefly. Is the user visible? What are they doing?');
                    if (camera_desc) {
                        log(`Vision: ${camera_desc.substring(0, 80)}...`, 'ok');
                    }
                } catch (e) {
                    log('Vision analysis skipped', 'warn');
                }

                // DON'T stop camera - keep it live until user closes modal
                liveCameraWorking = true;
                setPhase('camera', 'ok');

                // Minimize modal during TTS so it doesn't block the log
                cameraTestModal.minimize();

                // Camera phase - give CORA the vision data
                let camResponse;
                if (camera_desc && camera_desc.length > 10) {
                    camResponse = await coraRespond('Live Camera', `Camera online. I see: ${camera_desc}`, 'ok', 'full');
                } else {
                    camResponse = await coraRespond('Live Camera', 'Camera online, vision test passed.', 'ok');
                }
                await speakAndWait(camResponse);

                // During boot: auto-close camera after 3 seconds so boot continues cleanly
                // Camera can be reopened on command later
                cameraTestModal.restore();
                log('Camera test passed - closing in 3s...', 'info');
                await sleep(3000);
                cameraTestModal.close();
                log('Camera closed - can be reopened on command', 'info');

            } catch (e) {
                log('Live camera not available: ' + e.message, 'warn');
                setPhase('camera', 'warn');
                const camWarn = await coraRespond('Camera', 'Camera test failed, not available.', 'warn');
                await speakAndWait(camWarn);
            }
        }
    } else {
        log('Camera API not available in this browser', 'warn');
        setPhase('camera', 'warn');
        const camWarn = await coraRespond('Camera', 'Browser camera API not available.', 'warn');
        await speakAndWait(camWarn);
    }

    // ================================================================
    // PHASE 4.0: CORE TOOLS
    // ================================================================
    setPhase('tools', 'running');
    log('PHASE 4.0: CORE TOOLS TEST', 'phase');
    updateProgress(40, 'Loading tools...');
    const webTools = [
        { name: 'LocalStorage', ok: typeof localStorage !== 'undefined' },
        { name: 'Fetch API', ok: typeof fetch !== 'undefined' },
        { name: 'WebSocket', ok: typeof WebSocket !== 'undefined' },
        { name: 'Canvas API', ok: typeof HTMLCanvasElement !== 'undefined' },
        { name: 'Web Audio', ok: typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined' },
        { name: 'Geolocation', ok: 'geolocation' in navigator },
        { name: 'Notifications', ok: 'Notification' in window },
        { name: 'Clipboard', ok: navigator.clipboard !== undefined }
    ];
    let toolsOk = 0;
    webTools.forEach(t => {
        log(`  ${t.name} - ${t.ok ? 'Available' : 'Missing'}`, t.ok ? 'ok' : 'warn');
        if (t.ok) toolsOk++;
    });
    setPhase('tools', 'ok');
    // Tools phase - give CORA the count
    const tools_result = `Core tools check done. ${toolsOk} of ${webTools.length} browser APIs available.`;
    const tools_status = toolsOk >= webTools.length - 2 ? 'ok' : (toolsOk >= webTools.length / 2 ? 'warn' : 'fail');
    const toolsResponse = await coraRespond('Tools', tools_result, tools_status);
    await speakAndWait(toolsResponse);

    // ================================================================
    // PHASE 4.1: CODE BROWSER - CORA's own codebase viewer
    // ================================================================
    setPhase('code_import', 'running');
    log('PHASE 4.1: CODE BROWSER - CORA CODEBASE', 'phase');
    updateProgress(45, 'Loading CORA code browser...');

    try {
        // Test GitHub API access first
        log('Connecting to Unity-Lab-AI/CORA repository...', 'info');
        const testResp = await fetch('https://api.github.com/repos/Unity-Lab-AI/CORA/contents/');

        if (testResp.ok) {
            const files = await testResp.json();
            const fileCount = files.length;
            const pyFiles = files.filter(f => f.name.endsWith('.py')).length;
            log(`Repository loaded: ${fileCount} items at root, ${pyFiles} Python files`, 'ok');

            // Show the full code browser modal
            const modal = showCodeBrowserModal();
            log('Code browser opened - browse CORA source!', 'ok');

            setPhase('code_import', 'ok');
            const codeResponse = await coraRespond('Code Browser', `My source code is now viewable. ${fileCount} files loaded from the CORA repo.`, 'ok');
            await speakAndWait(codeResponse);

            // Give time to browse, then close before moving on
            await sleep(5000);
            modal.close();
            log('Code browser closed, moving on', 'info');
        } else {
            throw new Error(`GitHub API returned ${testResp.status}`);
        }
    } catch (e) {
        log(`Code browser: ${e.message}`, 'warn');
        setPhase('code_import', 'warn');
        const codeWarn = await coraRespond('Code Browser', 'Code browser failed, GitHub API rate limited.', 'warn');
        await speakAndWait(codeWarn);
    }

    // ================================================================
    // PHASE 4.2: YOUTUBE TEST - Actually embed a video!
    // ================================================================
    setPhase('youtube', 'running');
    log('PHASE 4.2: YOUTUBE VIDEO TEST', 'phase');
    updateProgress(50, 'Finding a video...');

    // Random YouTube search - different crazy search each time
    const randomSearchTerms = [
        'synthwave mix', 'vaporwave aesthetic', 'lofi beats', 'retro gaming music',
        'cyberpunk ambience', 'space ambient', 'dark synthwave', 'outrun music',
        'chillwave', 'retrowave driving', 'neon lights aesthetic', 'rain sounds',
        'city night ambience', 'coding music', 'hacker music', 'matrix soundtrack',
        'blade runner vibes', 'stranger things music', 'synth pop', 'new retro wave',
        'midnight drive music', 'aesthetic visuals', 'vapor aesthetic', '80s nostalgia',
        'electronic chill', 'ambient electronic', 'future funk', 'french house',
        'deep house mix', 'techno ambient', 'industrial music', 'darkwave',
        'goth music mix', 'post punk', 'shoegaze', 'dream pop', 'indie electronic'
    ];
    const searchTerm = randomSearchTerms[Math.floor(Math.random() * randomSearchTerms.length)];
    log(`Searching YouTube: "${searchTerm}"`, 'info');

    let video = { id: 'jfKfPfyJRdk', title: 'Lofi Hip Hop Radio' }; // Default
    let searchWorked = false;
    try {
        // Use Invidious API (no API key needed) for random YouTube search
        const instances = ['https://inv.nadeko.net', 'https://invidious.nerdvpn.de', 'https://yt.artemislena.eu'];
        const instance = instances[Math.floor(Math.random() * instances.length)];
        const searchUrl = `${instance}/api/v1/search?q=${encodeURIComponent(searchTerm)}&type=video`;

        const searchRes = await fetch(searchUrl, { signal: AbortSignal.timeout(5000) });
        if (searchRes.ok) {
            const results = await searchRes.json();
            if (results && results.length > 0) {
                // Pick random result from first 10
                const randomIndex = Math.floor(Math.random() * Math.min(10, results.length));
                const found = results[randomIndex];
                video = { id: found.videoId, title: found.title?.substring(0, 50) || searchTerm };
                searchWorked = true;
            }
        }
    } catch (e) {
        log('Search timeout, using default video', 'info');
    }

    if (searchWorked) {
        log(`YouTube search working - found: ${video.title}`, 'ok');
    } else {
        log('YouTube ready (search API down, will use direct links)', 'ok');
    }
    setPhase('youtube', 'ok');
    // Don't auto-play videos on boot - just verify the system works
    // User can request music/videos anytime after boot

    // ================================================================
    // PHASE 4.3: MODAL WINDOWS - Show actual test modal!
    // ================================================================
    setPhase('modals', 'running');
    log('PHASE 4.3: MODAL WINDOWS TEST', 'phase');
    updateProgress(52, 'Testing modals...');

    // Random quotes like desktop
    const quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Stay hungry, stay foolish. - Steve Jobs",
        "Code is like humor. When you have to explain it, it's bad. - Cory House",
        "First, solve the problem. Then, write the code. - John Johnson",
        "The best way to predict the future is to invent it. - Alan Kay"
    ];
    const quote = quotes[Math.floor(Math.random() * quotes.length)];

    log('Opening test modal with quote...', 'info');
    const quoteModal = showQuoteModal(quote);
    log('Modal displayed successfully', 'ok');

    setPhase('modals', 'ok');
    // Modal phase - confirm working
    const modalResponse = await coraRespond('Modals', 'Modal windows test passed. Report.', 'ok');
    await speakAndWait(modalResponse);

    // Wait then close modal before moving on
    await sleep(2000);
    quoteModal.close();
    log('Modal test complete, modal closed', 'info');

    // ================================================================
    // PHASE 5.0: VOICE SYSTEMS
    // ================================================================
    setPhase('voice_sys', 'running');
    log('PHASE 5.0: VOICE SYSTEMS', 'phase');
    updateProgress(55, 'Voice systems...');
    log('Speech Synthesis (TTS) - ' + (ttsEnabled ? 'OK' : 'Fallback'), ttsEnabled ? 'ok' : 'warn');
    const hasSpeechRecog = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
    log('Speech Recognition - ' + (hasSpeechRecog ? 'Available' : 'Not supported'), hasSpeechRecog ? 'ok' : 'warn');
    log('Echo Filter - N/A (web mode)', 'info');
    if (hasSpeechRecog) {
        log('Wake Word - Available (say "Hey CORA")', 'ok');
        initWakeWord();  // Start listening for wake word
    } else {
        log('Wake Word - Not supported in this browser', 'warn');
    }
    setPhase('voice_sys', 'ok');
    // Voice phase - give CORA the TTS/STT status
    const ttsType = kokoroReady ? 'Kokoro neural TTS' : 'Web Speech fallback';
    const voice_result = `Voice systems done. Using ${ttsType}. Wake word ${hasSpeechRecog ? 'active' : 'not supported'}.`;
    const voiceResponse = await coraRespond('Voice', voice_result, 'ok');
    await speakAndWait(voiceResponse);

    // ================================================================
    // PHASE 6.0: EXTERNAL APIs (Location)
    // ================================================================
    setPhase('external', 'running');
    log('PHASE 6.0: EXTERNAL SERVICES', 'phase');
    updateProgress(60, 'Checking location...');

    // Show permission prompt for location
    log('Location permission required...', 'info');
    const locPermResult = await showPermissionPrompt(
        'Location Permission Required',
        'CORA needs your location to provide weather, local news, and location-aware features.',
        '📍'
    );

    let location = null;
    if (locPermResult === 'skip' || locPermResult === 'denied') {
        log(`Location permission ${locPermResult} by user`, 'warn');
    } else if (locPermResult === 'granted') {
        log('Requesting location...', 'info');
        location = await getLocation();
    }
    if (location?.city) {
        const locStr = [location.city, location.state, location.country].filter(Boolean).join(', ');
        log(`Location: ${locStr}`, 'ok');
        log(`Coordinates: ${location.lat?.toFixed(4)}, ${location.lon?.toFixed(4)}`, 'info');
        // Location phase - give CORA the location
        const locResponse = await coraRespond('Location', `Location acquired: ${locStr}.`, 'ok');
        await speakAndWait(locResponse);
    } else {
        log('Location not available or denied', 'warn');
        const locWarn = await coraRespond('Location', 'Location unavailable or denied.', 'warn');
        await speakAndWait(locWarn);
    }
    setPhase('external', 'ok');

    // ================================================================
    // PHASE 6.1: AUDIO TEST - Uses CORA's playSynth() tool
    // ================================================================
    setPhase('audio', 'running');
    log('PHASE 6.1: AUDIO PLAYBACK TEST', 'phase');
    updateProgress(65, 'Testing audio...');

    // Use CORA's synth tool
    const audioResult = playSynth();
    if (audioResult.success) {
        await new Promise(r => setTimeout(r, 3000));
        log('Audio test complete!', 'ok');
        setPhase('audio', 'ok');
        const audioResponse = await coraRespond('Audio', `Audio test passed. Played ${audioResult.played || 'synth tone'}.`, 'ok');
        await speakAndWait(audioResponse);
    } else {
        log('Audio test failed: ' + audioResult.error, 'warn');
        setPhase('audio', 'warn');
        const audioWarn = await coraRespond('Audio', 'Audio test failed.', 'warn');
        await speakAndWait(audioWarn);
    }

    // ================================================================
    // PHASE 6.2: WEATHER - Get current conditions and 3-day forecast
    // ================================================================
    setPhase('weather', 'running');
    log('PHASE 6.2: WEATHER', 'phase');
    updateProgress(70, 'Checking weather...');

    log('Fetching weather and 3-day forecast from wttr.in...', 'info');
    const weather = await getWeather(location?.city || '');
    const forecastData = await get3DayForecast(location?.city || '');

    if (weather.success) {
        log(`Current: ${weather.temp}, ${weather.conditions}`, 'ok');
        log(`Feels like: ${weather.feels_like}`, 'info');
        log(`Humidity: ${weather.humidity}`, 'info');
        document.getElementById('statWeather').textContent = weather.temp;
        document.getElementById('statWeather').className = 'stat-value';

        // Show 3-day forecast
        if (forecastData.success && forecastData.forecast.length > 0) {
            log('3-Day Forecast:', 'ok');
            forecastData.forecast.forEach(day => {
                log(`  ${day.day}: ${day.high}/${day.low} - ${day.conditions}`, 'info');
            });
        }

        setPhase('weather', 'ok');

        // Weather phase - give CORA actual temp and conditions
        const tempSpoken = weather.temp.replace('°F', ' degrees').replace('+', '');
        let weather_report = `Weather done. Currently ${tempSpoken}, ${weather.conditions.toLowerCase()}`;
        if (location?.city) weather_report += ` in ${location.city}`;
        weather_report += `. `;
        if (forecastData.success && forecastData.forecast.length >= 2) {
            weather_report += `Forecast: `;
            forecastData.forecast.slice(1, 3).forEach(day => {
                weather_report += `${day.day} ${day.high}/${day.low}. `;
            });
        }
        weather_report += `Report.`;
        // mode='full' for weather - more detail allowed
        const weatherResponse = await coraRespond('Weather', weather_report, 'ok', 'full');
        await speakAndWait(weatherResponse);
    } else {
        document.getElementById('statWeather').textContent = 'N/A';
        document.getElementById('statWeather').className = 'stat-value na';
        setPhase('weather', 'warn');
        const weatherWarn = await coraRespond('Weather', 'Weather service unavailable.', 'warn');
        await speakAndWait(weatherWarn);
    }

    // ================================================================
    // PHASE 7.0: NEWS HEADLINES
    // ================================================================
    setPhase('news', 'running');
    log('PHASE 7.0: NEWS HEADLINES', 'phase');
    updateProgress(75, 'Fetching news...');
    log('Fetching top headlines from Google News...', 'info');
    const headlines = await getNews();
    if (headlines.length > 0) {
        log(`Found ${headlines.length} headlines`, 'ok');
        log('Top 3 Headlines:', 'ok');
        headlines.slice(0, 3).forEach((h, i) => log(`  ${i+1}. ${h}`, 'info'));
        setPhase('news', 'ok');
        // News phase - give CORA actual headlines
        const clean_headlines = headlines.slice(0, 3).map(hl => {
            let clean = hl.split(' - ')[0] || hl;
            if (clean.length > 80) clean = clean.substring(0, 77) + '...';
            return clean;
        });
        const news_data = `News done. ${headlines.length} headlines found. Top 3: ${clean_headlines.join('. ')}.`;
        const newsResponse = await coraRespond('News', news_data, 'ok', 'full');
        await speakAndWait(newsResponse);
    } else {
        log('News unavailable', 'warn');
        setPhase('news', 'warn');
        const newsWarn = await coraRespond('News', 'News service unavailable.', 'warn');
        await speakAndWait(newsWarn);
    }

    // ================================================================
    // PHASE 8.0: VISION TEST - Screenshot + Camera (EXACT match to desktop)
    // Desktop: Takes screenshot, analyzes with llava, SPEAKS the description
    // Then takes camera frame, analyzes with llava, SPEAKS the description
    // Finally gives summary via cora_respond
    // ================================================================
    setPhase('vision', 'running');
    log('PHASE 8.0: VISION TEST', 'phase');
    updateProgress(82, 'Testing vision...');

    let screenshotOk = false;
    let visionCameraOk = false;
    let screen_description = null;
    let camera_description = null;

    // TEST 1: Screenshot capture + llava analysis
    const hasScreenCapture = 'getDisplayMedia' in navigator.mediaDevices;
    log('Screen Capture API - ' + (hasScreenCapture ? 'Available' : 'Unavailable'), hasScreenCapture ? 'ok' : 'warn');

    if (hasScreenCapture) {
        log('Requesting screen capture permission...', 'info');
        try {
            const ssStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
            const ssVideo = document.createElement('video');
            ssVideo.srcObject = ssStream;
            ssVideo.autoplay = true;
            await new Promise(r => ssVideo.onloadedmetadata = r);
            await sleep(500);

            const ssCanvas = document.createElement('canvas');
            ssCanvas.width = ssVideo.videoWidth || 1920;
            ssCanvas.height = ssVideo.videoHeight || 1080;
            ssCanvas.getContext('2d').drawImage(ssVideo, 0, 0);
            ssStream.getTracks().forEach(t => t.stop());

            log(`Screenshot captured: ${ssCanvas.width}x${ssCanvas.height}`, 'ok');
            screenshotOk = true;

            // Analyze with llava - CORA describes what she sees
            log('Analyzing screenshot with llava...', 'info');
            const ssBase64 = ssCanvas.toDataURL('image/jpeg', 0.7).split(',')[1];
            try {
                screen_description = await analyzImageWithLlava(ssBase64, 'Describe what you see on this screen. What application or website is open? What is the user working on?');
                if (screen_description) {
                    // Clean markdown like desktop
                    screen_description = screen_description.replace(/\*\*([^*]+)\*\*/g, '$1');
                    screen_description = screen_description.replace(/\*([^*]+)\*/g, '$1');
                    screen_description = screen_description.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
                    log(`Vision: ${screen_description.substring(0, 80)}...`, 'ok');
                    // SPEAK the actual description like desktop line 2158
                    await speakAndWait(screen_description);
                }
            } catch (e) {
                log('Screenshot vision analysis skipped', 'warn');
            }
        } catch (e) {
            log('Screenshot: ' + (e.name === 'NotAllowedError' ? 'Permission denied' : e.message), 'warn');
        }
    }

    // TEST 2: Camera vision test + llava analysis
    log('Vision camera permission required...', 'info');
    const visionPermResult = await showPermissionPrompt(
        'Vision Camera Permission',
        'CORA needs camera access for the Vision Test to analyze what she sees.',
        '👁'
    );

    if (visionPermResult === 'skip' || visionPermResult === 'denied') {
        log(`Vision camera ${visionPermResult} by user`, 'warn');
    } else if (visionPermResult === 'granted') {
        log('Testing camera for vision...', 'info');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            log('Camera stream acquired for vision test', 'ok');

            // Create modal with camera view
            const { content, close } = createDynamicModal('CORA - Vision Test', 800, 600);
            const visionModal = { close };

            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;
            video.style.cssText = 'width: 100%; height: 100%; object-fit: contain; background: black;';
            content.style.padding = '0';
            content.appendChild(video);

            // Show for 3 seconds like desktop
            log('Showing camera for vision analysis...', 'info');
            await sleep(3000);

            // Capture frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            log(`Vision frame captured: ${canvas.width}x${canvas.height}`, 'ok');

            // Stop stream
            stream.getTracks().forEach(t => t.stop());
            visionCameraOk = true;

            // Analyze with llava - CORA describes what she sees
            log('Analyzing camera with llava...', 'info');
            const camBase64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
            try {
                camera_description = await analyzImageWithLlava(camBase64, 'Describe what you see. Is the user visible? What are they doing? What is in the background?');
                if (camera_description) {
                    // Clean markdown like desktop
                    camera_description = camera_description.replace(/\*\*([^*]+)\*\*/g, '$1');
                    camera_description = camera_description.replace(/\*([^*]+)\*/g, '$1');
                    camera_description = camera_description.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
                    log(`Vision: ${camera_description.substring(0, 80)}...`, 'ok');
                    // SPEAK the actual description like desktop line 2278
                    await speakAndWait(camera_description);
                }
            } catch (e) {
                log('Camera vision analysis skipped', 'warn');
            }

            // Wait then close modal before moving on
            await sleep(1000);
            visionModal.close();
            log('Vision test complete, modal closed', 'info');
        } catch (e) {
            log('Vision camera: ' + (e.name === 'NotAllowedError' ? 'Permission denied' : e.message), 'warn');
        }
    }

    // Vision summary - give CORA the actual status
    let vision_result;
    if (screenshotOk && visionCameraOk) {
        vision_result = "Vision test done. Screenshot and camera both working.";
    } else if (screenshotOk) {
        vision_result = "Vision test done. Screenshot working, camera unavailable.";
    } else if (visionCameraOk) {
        vision_result = "Vision test done. Camera working, screenshot failed.";
    } else {
        vision_result = "Vision test failed. Both screenshot and camera unavailable.";
    }
    setPhase('vision', (screenshotOk || visionCameraOk) ? 'ok' : 'warn');
    const visionResponse = await coraRespond('Vision', vision_result, (screenshotOk || visionCameraOk) ? 'ok' : 'warn', 'full');
    await speakAndWait(visionResponse);

    // ================================================================
    // PHASE 9.0: IMAGE GENERATION - her own local engine, test + generate image
    // ================================================================
    setPhase('imagegen', 'running');
    log('PHASE 9.0: IMAGE GENERATION', 'phase');
    updateProgress(90, 'Testing image generation...');

    // Her image engine: local Stable Diffusion behind the local CORA server
    log('Checking her image engine...', 'info');
    const imageOk = await checkImageEngine();
    const statImages = document.getElementById('statImages');
    if (imageOk) {
        log('Image engine - Online (local)', 'ok');
        statImages.textContent = 'Local';
        statImages.className = 'stat-value';
    } else {
        log(CORA_LOCAL ? 'Image engine - Unavailable (checkpoint or sidecar missing)' : 'Image engine - needs the local CORA server', 'warn');
        statImages.textContent = 'N/A';
        statImages.className = 'stat-value na';
    }

    if (imageOk) {
        // Random dark/creative prompts like desktop
        const imagePrompts = [
            "cyberpunk city at night, neon lights, rain, dark atmosphere",
            "dark gothic castle on a mountain, lightning, dramatic sky",
            "futuristic AI robot with glowing eyes, dark background",
            "synthwave sunset over digital ocean, purple and pink",
            "haunted forest with glowing mushrooms, fog, mysterious"
        ];
        const prompt = imagePrompts[Math.floor(Math.random() * imagePrompts.length)];
        const seed = Math.floor(Math.random() * 999999999);

        log(`Prompt: ${prompt}`, 'info');
        log('Generating on her own image engine...', 'info');
        const genStart = Date.now();

        let imgModal = null;
        let image_description = null;
        try {
            const gen = await generateImageLocal(prompt, { width: 1024, height: 576, seed });
            const genTime = ((Date.now() - genStart) / 1000).toFixed(1);
            log(`Image generated in ${genTime}s (seed ${gen.seed}) - saved at ${gen.path}`, 'ok');

            // the picture with its Download link; the file is already on disk
            imgModal = showGeneratedImage(gen, prompt);

            // Analyze what she made with her own eyes
            log('Analyzing generated image with vision...', 'info');
            try {
                const imgBase64 = await imageUrlToBase64(gen.url);
                image_description = await analyzImageWithLlava(imgBase64, 'Describe this image in detail. What do you see? Be specific about the scene, objects, colors, mood, and style.');
                if (image_description) {
                    image_description = image_description.replace(/\*\*([^*]+)\*\*/g, '$1');
                    image_description = image_description.replace(/\*([^*]+)\*/g, '$1');
                    image_description = image_description.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
                    log(`Vision: ${image_description.substring(0, 80)}...`, 'ok');
                }
            } catch (e) {
                log('Image vision analysis skipped', 'warn');
            }

            setPhase('imagegen', 'ok');

            if (image_description && image_description.length > 10) {
                await speakAndWait(image_description);
            } else {
                const imgResponse = await coraRespond('Image', `Image generated in ${genTime}s but vision analysis failed.`, 'warn');
                await speakAndWait(imgResponse);
            }
        } catch (e) {
            log('Image generation failed: ' + e.message, 'warn');
            setPhase('imagegen', 'warn');
            const imgFail = await coraRespond('Image', `Image generation failed: ${e.message.substring(0, 40)}.`, 'fail');
            await speakAndWait(imgFail);
        }

        // Wait then close the modal before moving on (the file stays in data/images)
        await sleep(5000);
        if (imgModal) imgModal.close();
        log('Image generation complete, modal closed', 'info');
    } else {
        log('Image generation unavailable - engine offline', 'warn');
        setPhase('imagegen', 'warn');
        const imgWarn = await coraRespond('Image', 'Image generation unavailable, image engine offline.', 'warn');
        await speakAndWait(imgWarn);
    }

    // ================================================================
    // PHASE 10.0: FINAL CHECK (Boot Complete)
    // ================================================================
    setPhase('final', 'running');
    log('PHASE 10.0: FINAL CHECK', 'phase');
    updateProgress(95, 'Final check...');

    // Calculate boot time
    const bootTime = ((Date.now() - bootStartTime) / 1000).toFixed(1);
    document.getElementById('statBootTime').textContent = bootTime + 's';

    // Count results
    let okCount = 0, warnCount = 0, failCount = 0;
    PHASES.forEach(p => {
        if (p.status === 'ok') okCount++;
        else if (p.status === 'warn') warnCount++;
        else if (p.status === 'fail') failCount++;
    });

    log(`Systems: ${okCount} OK / ${warnCount} WARN / ${failCount} FAIL`, 'system');
    log(`Boot time: ${bootTime} seconds`, 'system');

    // Time greeting
    const now = new Date();
    const hour = now.getHours();
    const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    const dayStr = now.toLocaleDateString('en-US', { weekday: 'long' });
    const monthStr = now.toLocaleDateString('en-US', { month: 'long' });
    const day = now.getDate();
    // Add ordinal suffix for natural speech (1st, 2nd, 3rd, 4th, etc.)
    const ordinal = (d) => {
        if (d > 3 && d < 21) return d + 'th';
        switch (d % 10) {
            case 1: return d + 'st';
            case 2: return d + 'nd';
            case 3: return d + 'rd';
            default: return d + 'th';
        }
    };
    const dateStr = `${monthStr} ${ordinal(day)}`;
    let greeting;
    if (hour < 12) greeting = `Good morning. Today is ${dayStr}, ${dateStr}. It's ${timeStr}.`;
    else if (hour < 17) greeting = `Good afternoon. Today is ${dayStr}, ${dateStr}. It's ${timeStr}.`;
    else greeting = `Evening. Today is ${dayStr}, ${dateStr}. It's ${timeStr}.`;

    log('═══════════════════════════════════════════════════', 'phase');
    log('           BOOT SEQUENCE COMPLETE', 'phase');
    log('═══════════════════════════════════════════════════', 'phase');
    log(greeting, 'system');

    let statusText;
    if (failCount > 0) {
        statusText = `Got ${failCount} systems that failed. Something's broken.`;
    } else if (warnCount > 0) {
        statusText = `All the important stuff is working. Just ${warnCount} minor issues.`;
    } else {
        statusText = "Everything is up and running perfectly.";
    }
    log(statusText, failCount > 0 ? 'fail' : (warnCount > 0 ? 'warn' : 'ok'));

    updateProgress(100, 'Boot complete!');
    setPhase('final', 'ok');

    // Boot complete - give CORA the stats to report
    log('CORA is waking up...', 'cora');
    try {
        const bootContext = `Boot done in ${bootTime} seconds. ${okCount} systems OK, ${warnCount} warnings, ${failCount} failures. Report.`;

        const res = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODEL,
                prompt: bootContext,
                system: CORA_SYSTEM_PROMPT,
                stream: false,
                think: false,
                options: { num_ctx: CORA_NUM_CTX, temperature: 0.9, num_predict: 100 }
            })
        });
        if (res.ok) {
            const d = await res.json();
            let coraResponse = d.response?.trim();
            if (coraResponse && coraResponse.length > 5) {
                // Remove any "good morning/have a great day" bullshit
                coraResponse = coraResponse.replace(/good morning[,.]?/gi, '').replace(/have a (great|good|nice) day[!.]?/gi, '').trim();
                if (coraResponse.length > 5) {
                    log(`CORA: "${coraResponse}"`, 'cora');
                    await speakAndWait(coraResponse);
                }
            }
        }
        // No fallback - if AI fails, just skip speaking (no hardcoded text)
    } catch (e) {
        // Silent fail - CORA only speaks when AI generates her response
    }

    // ================================================================
    // ABILITIES ANNOUNCEMENT - Like desktop boot_sequence.py
    // ================================================================
    log('─── CORA\'s Abilities ───', 'info');
    log('Vision: see, look, screenshot, camera', 'info');
    log('Images: imagine, draw, generate', 'info');
    log('Web: search, browse, fetch', 'info');
    log('Media: play, pause, volume', 'info');
    log('Tasks: add, list, done, remind', 'info');
    log('Code: explain, write, fix, run', 'info');

    // CORA asks what user is working on - system prompt handles personality
    try {
        const nosyRes = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODEL,
                prompt: `Boot complete. Ready.`,
                system: CORA_SYSTEM_PROMPT,
                stream: false,
                think: false,
                options: { num_ctx: CORA_NUM_CTX, temperature: 0.9, num_predict: 60 }
            })
        });
        if (nosyRes.ok) {
            const nosyData = await nosyRes.json();
            let nosyResponse = nosyData.response?.trim();
            // Only use if it's reasonable - short and a question
            if (nosyResponse && nosyResponse.length > 5 && nosyResponse.length < 100) {
                log(`CORA: "${nosyResponse}"`, 'cora');
                await speakAndWait(nosyResponse);
            } else {
                // Retry with simpler prompt
                const retry = await fetch(OLLAMA_URL + '/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: CORA_MODEL,
                        prompt: 'Boot done.',
                        system: CORA_SYSTEM_PROMPT,
                        stream: false,
                think: false,
                        options: { num_ctx: CORA_NUM_CTX, temperature: 0.95, num_predict: 25 }
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
        log('CORA AI not responding', 'warn');
    }

    log('C.O.R.A IS READY', 'ok');

    // Save boot complete flag for quick boot next time
    localStorage.setItem('cora_first_time', 'done');  // Key for returning user detection
    localStorage.setItem('cora_boot_complete', 'true');
    localStorage.setItem('cora_boot_date', new Date().toISOString());
    log('First-time setup saved - next boot will be faster!', 'info');

    // If we're in setup terminal view (from auto-install), switch back to main
    if (viewMode === 'setup') {
        setupLog('[BOOT COMPLETE] Switching to main interface...', '#00ff00');
        await sleep(1000);  // Brief pause so user sees the message
        backToMain();
    }

    // Show chat interface
    document.getElementById('chatSection').classList.add('visible');
    document.getElementById('chatInput').focus();
}

// Force full boot (for testing or re-setup)
function forceFullBoot() {
    localStorage.removeItem('cora_first_time');  // Returning user detection
    localStorage.removeItem('cora_boot_complete');
    localStorage.removeItem('cora_permissions');
    location.reload();
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
