// 00-runtime (part 2): continues the previous file, same global scope

let kokoroWorker = null;          // kept for old references; always null now
let kokoroReady = false;          // true when her voice answered /voice/health
let kokoroLoading = false;
let audioContext = null;
let pendingCallbacks = {};
let messageId = 0;
let useFallbackTTS = false;       // there is no fallback voice

async function initVoice(progressCallback) {
    if (kokoroReady) return true;
    if (kokoroLoading) return false;
    kokoroLoading = true;
    try {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (!CORA_LOCAL) {
            if (progressCallback) progressCallback('No local CORA server: her voice is not available here', 100);
            return false;
        }
        if (progressCallback) progressCallback('Checking her voice...', 30);
        const r = await fetch(STATS_BASE + '/voice/health', { signal: AbortSignal.timeout(4000) });
        const j = r.ok ? await r.json() : {};
        kokoroReady = !!j.up;
        if (progressCallback) progressCallback(kokoroReady ? 'Unity voice v2 online' : ('Her voice is down: ' + (j.error || 'sidecar not responding')), 100);
        return kokoroReady;
    } catch (e) {
        console.error('[VOICE] health check failed:', e);
        return false;
    } finally {
        kokoroLoading = false;
    }
}
const initKokoro = initVoice;     // old call sites

// Her phoneme vocabulary holds exactly four marks: space , . ?  Every other
// mark becomes the pause she has (a comma, or a full stop); words are never
// dropped; [laughter] and [breath] keep their brackets. Same rules as
// voice/unity_voice.py voice_text().
function voiceText(text) {
    let t = String(text || '');
    const keep = [];
    t = t.replace(/\[(laughter|breath)\]/gi, (m) => { keep.push(m.toLowerCase()); return `\u0000${keep.length - 1}\u0000`; });
    t = t.replace(/\u2026/g, '...').replace(/\.{2,}/g, '.');
    t = t.replace(/[?!]*!+[?!]*/g, (m) => (m.includes('?') ? '?' : '.'));
    t = t.replace(/&/g, ' and ').replace(/%/g, ' percent ').replace(/\+/g, ' plus ').replace(/@/g, ' at ');
    t = t.replace(/[;:\u2014\u2013]|--+/g, ',');
    t = t.replace(/[()\[\]{}<>"\u201c\u201d*_#=|\\\/~^`]/g, ',');
    t = t.replace(/[\u2018\u2019]/g, "'").replace(/(^|\s)'|'(\s|$)/g, '$1$2');
    t = t.replace(/\s*,\s*(,\s*)+/g, ', ').replace(/\s*([,.?])/g, '$1').replace(/([,.?])(?=\S)/g, '$1 ');
    t = t.replace(/^[\s,.]+/, '').replace(/\s+/g, ' ').trim();
    t = t.replace(/\u0000(\d+)\u0000/g, (m, i) => keep[+i]);
    return t;
}

// Delivery for a plain line (the rules her training data used)
function inferDelivery(text) {
    const low = (text || '').toLowerCase();
    const rules = [
        ['sad', /\b(died|dead|death|passed away|rip|funeral|grave|buried|miss (him|her|them)|lost (him|her))\b/],
        ['concerned', /\b(careful|danger|injur|bleed|sick|infection|starv|low on|toxic|overdue|urgent|worried|warning)\b/],
        ['frustrated', /\b(again|ugh|why would|seriously|every time|keeps? (doing|breaking|failing))\b/],
        ['surprised', /\b(wait|what\?|whoa|no way|huh)\b/],
        ['warm', /\b(welcome|thank|thanks|glad you|love (you|this)|appreciate|hi |hey |got you|i'm here)/],
        ['amused', /\[laughter\]|\b(funny|lol|hilarious|ridiculous)\b/],
        ['happy', /\b(finally|done|we did it|yes|nice|perfect|great|awesome)\b/],
    ];
    let emotion = 'neutral';
    for (const [e, re] of rules) { if (re.test(low)) { emotion = e; break; } }
    if (low.includes('[laughter]') && ['neutral', 'sad', 'concerned'].includes(emotion)) emotion = 'amused';
    const body = (text || '').replace(/\s*\[(laughter|breath|sigh)\]\s*/g, ' ').trim();
    let act = 'statement';
    if (body.endsWith('?')) {
        act = /^(what|where|why|how|who|which|when)\b/i.test(body) ? 'wh_question' : 'yes_no_question';
    } else if (body.endsWith('!')) {
        act = 'exclamation';
        if (emotion === 'neutral') emotion = 'excited';
    }
    return { emotion, speech_act: act };
}

// Ask her voice for one line and hand the samples to handleAudioReady (same
// playback + waveform path the page always had).
async function unityVoiceSay(speakText, displayText, callback) {
    const id = ++messageId;
    pendingCallbacks[id] = { resolve: callback || (() => {}), startTime: Date.now(), text: displayText, timeoutId: null };
    try {
        const delivery = inferDelivery(speakText);
        const res = await fetch(STATS_BASE + '/voice/say', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CORA-Token': CORA_LOCAL.token },
            body: JSON.stringify({ text: voiceText(speakText), emotion: delivery.emotion, speech_act: delivery.speech_act })
        });
        if (!res.ok) {
            let why = String(res.status);
            try { why = (await res.json()).error || why; } catch (e) {}
            throw new Error(why);
        }
        const wav = await res.arrayBuffer();
        if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const decoded = await audioContext.decodeAudioData(wav);
        const ch = decoded.getChannelData(0);
        const copy = new Float32Array(ch.length);
        copy.set(ch);
        await handleAudioReady(id, { audio: copy.buffer, sampleRate: decoded.sampleRate });
    } catch (e) {
        console.error('[VOICE] her voice refused the line:', e.message);
        const pending = pendingCallbacks[id];
        delete pendingCallbacks[id];
        document.getElementById('speechText').textContent = `"${displayText}"`;
        log(`CORA: "${displayText}"`, 'cora');
        log(`Voice: ${e.message}`, 'warn');
        if (pending && pending.resolve) pending.resolve();
    }
}

// Track active audio playback to prevent overlapping
let currentAudioSource = null;

async function handleAudioReady(id, data) {
    console.log(`[TTS] handleAudioReady called, id=${id}, pendingCallbacks keys=${Object.keys(pendingCallbacks).join(',')}`);

    if (!pendingCallbacks[id]) {
        console.warn(`[TTS] No pending callback for id=${id}, available ids: ${Object.keys(pendingCallbacks).join(',')}`);
        return;
    }

    const { resolve, startTime, text, timeoutId } = pendingCallbacks[id];
    delete pendingCallbacks[id];

    // Clear the timeout since audio arrived
    if (timeoutId) clearTimeout(timeoutId);

    try {
        // Ensure audio context exists and is ready
        if (!audioContext) {
            console.log('[TTS] Creating new AudioContext');
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume audio context if suspended (browser requires user interaction)
        console.log(`[TTS] AudioContext state: ${audioContext.state}`);
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
            console.log('[TTS] AudioContext resumed');
        }

        // Validate data.audio exists and has content
        console.log(`[TTS] Validating audio data: exists=${!!data.audio}, byteLength=${data.audio?.byteLength || 0}`);
        if (!data.audio || data.audio.byteLength === 0) {
            console.error('[TTS] Received empty audio buffer - THIS IS THE BUG');
            if (text) {
                document.getElementById('speechText').textContent = `"${text}"`;
                log(`CORA: "${text}"`, 'cora');
            }
            resolve();
            return;
        }

        // Convert ArrayBuffer back to Float32Array
        const float32Audio = new Float32Array(data.audio);
        const sampleRate = data.sampleRate || 24000;
        const duration = float32Audio.length / sampleRate;

        // Check if audio is actually silence (all zeros)
        let maxSample = 0;
        for (let i = 0; i < Math.min(1000, float32Audio.length); i++) {
            maxSample = Math.max(maxSample, Math.abs(float32Audio[i]));
        }
        console.log(`[TTS] Audio ready: ${float32Audio.length} samples, ${sampleRate}Hz, ${duration.toFixed(2)}s, maxSample=${maxSample.toFixed(4)}`);

        // Stop any currently playing audio first
        if (currentAudioSource) {
            try {
                currentAudioSource.stop();
            } catch (e) {
                // Source may have already ended
            }
            currentAudioSource = null;
        }

        // Create audio buffer and play it
        const audioBuffer = audioContext.createBuffer(1, float32Audio.length, sampleRate);
        audioBuffer.copyToChannel(float32Audio, 0);

        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        currentAudioSource = source;

        // Create analyser to feed real-time audio to waveform
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        const dataArray = new Float32Array(analyser.frequencyBinCount);

        // Update waveform while playing - use a flag specific to THIS playback
        let isThisPlaybackActive = true;
        let animFrame;
        const updateWaveform = () => {
            if (!isThisPlaybackActive) return;
            analyser.getFloatTimeDomainData(dataArray);
            feedAudioChunk(Array.from(dataArray));
            if (audio_is_active && isThisPlaybackActive) {
                animFrame = requestAnimationFrame(updateWaveform);
            }
        };

        // Track if we've resolved to prevent double-resolve
        let resolved = false;
        const doResolve = () => {
            if (resolved) return;
            resolved = true;
            isThisPlaybackActive = false;
            cancelAnimationFrame(animFrame);
            if (currentAudioSource === source) {
                currentAudioSource = null;
            }
            stopWaveform();
            console.log(`[TTS] Playback complete for id=${id}`);
            resolve();
        };

        // ONLY resolve when audio actually finishes
        source.onended = () => {
            console.log(`[TTS] Audio finished (onended) for id=${id}`);
            doResolve();
        };

        // Fallback: if onended doesn't fire, wait for audio duration + buffer
        const fallbackMs = (duration * 1000) + 1000;  // Extra buffer
        setTimeout(() => {
            if (!resolved) {
                console.log(`[TTS] Audio fallback timeout for id=${id} (onended never fired)`);
                doResolve();
            }
        }, fallbackMs);

        // Start waveform FIRST so it's active when audio starts
        console.log(`[TTS] Calling startWaveform() for id=${id}`);
        startWaveform();

        // NOW show the speech text - we're about to play
        if (text) {
            document.getElementById('speechText').textContent = `"${text}"`;
            log(`CORA: "${text}"`, 'cora');
        }

        // Start audio and waveform update loop
        console.log(`[TTS] About to call source.start(0) for id=${id}, audioContext.state=${audioContext.state}`);
        source.start(0);
        console.log(`[TTS] source.start(0) called successfully for id=${id}`);
        updateWaveform();
        console.log(`[TTS] Audio started for id=${id}, will wait ${duration.toFixed(2)}s`);

    } catch (e) {
        console.error('[TTS] Audio playback error:', e);
        // Show text anyway on error so user sees what CORA tried to say
        if (text) {
            document.getElementById('speechText').textContent = `"${text}"`;
            log(`CORA: "${text}"`, 'cora');
        }
        stopWaveform();
        currentAudioSource = null;
        // Wait a bit before resolving so boot doesn't race ahead
        await new Promise(r => setTimeout(r, 500));
        resolve();
    }
}

// Strip URLs, emails, links from text for TTS - keeps log readable, speech natural
function stripUrlsForSpeech(text) {
    if (!text || typeof text !== 'string') return '';
    let clean = text;
    // Strip URLs (https://, http://, www.)
    clean = clean.replace(/https?:\/\/[^\s]+/gi, '');
    clean = clean.replace(/www\.[^\s]+/gi, '');
    // Strip email addresses
    clean = clean.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi, '');
    // Strip discord.gg links
    clean = clean.replace(/discord\.gg\/[^\s]+/gi, '');
    // Clean up multiple spaces and trim
    clean = clean.replace(/\s+/g, ' ').trim();
    // Remove trailing commas from stripped URLs
    clean = clean.replace(/,\s*,/g, ',').replace(/,\s*\./g, '.').replace(/\s+,/g, ',');
    return clean;
}

function speak(text, callback) {
    // DON'T show speech text or log yet - wait until audio actually starts playing
    // Strip URLs for TTS but keep original for log display
    const displayText = text;  // Full text for log
    const speakText = stripUrlsForSpeech(text);  // Clean text for TTS

    // Skip empty text
    if (!speakText || speakText.trim().length === 0) {
        console.log('[TTS] speak() called with empty text, skipping');
        if (callback) setTimeout(callback, 10);
        return;
    }

    console.log(`[TTS] speak() called: voiceReady=${kokoroReady}, text="${speakText.substring(0,50)}..."`);

    if (kokoroReady && CORA_LOCAL) {
        unityVoiceSay(speakText, displayText, callback);
    } else {
        // No voice here (not served locally, or her sidecar is down): show the line, keep moving
        document.getElementById('speechText').textContent = `"${displayText}"`;
        log(`CORA: "${displayText}"`, 'cora');
        if (callback) setTimeout(callback, 400);
    }
}

function speakAndWait(text) {
    return new Promise(resolve => speak(text, resolve));
}

// ============================================================
// WAVEFORM - EXACT 1:1 PORT FROM boot_display.py AudioWaveform
// Lines 127-384 of boot_display.py
// THIS RUNS FOREVER - NEVER STOPS
// ============================================================

// EXACT values from boot_display.py lines 140-146
const NUM_POINTS = 100;  // self.num_points = 100
let wave_points = new Array(NUM_POINTS).fill(0.0);  // self.wave_points
let sample_buffer = new Array(NUM_POINTS).fill(0.0);  // self.sample_buffer

// Audio state - like _audio_buffer_singleton in desktop
let audio_chunk = null;  // Current audio samples
let audio_chunk_time = null;  // When chunk was received
let audio_is_active = false;  // Is TTS currently speaking

let waveformInitialized = false;  // Track if waveform animation is running

function initWaveform() {
    // Prevent double-init
    if (waveformInitialized) {
        console.log('[WAVEFORM] Already initialized, skipping');
        return;
    }

    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) {
        console.warn('[WAVEFORM] Canvas not found, retrying in 100ms');
        setTimeout(initWaveform, 100);
        return;
    }

    const rect = canvas.getBoundingClientRect();
    console.log(`[WAVEFORM] Canvas rect: ${rect.width}x${rect.height}`);

    if (rect.width === 0 || rect.height === 0) {
        console.warn('[WAVEFORM] Canvas has zero dimensions, retrying in 100ms');
        setTimeout(initWaveform, 100);
        return;
    }

    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    waveformCtx = canvas.getContext('2d');
    waveformCtx.scale(2, 2);

    waveformInitialized = true;
    console.log('[WAVEFORM] Initialized successfully, starting animation loop');

    // Start animation - RUNS FOREVER, NEVER STOPS
    _animate();
}

// These just set the audio state - animation NEVER stops
function startWaveform() {
    audio_is_active = true;
    audio_chunk_time = Date.now();
}

function stopWaveform() {
    audio_is_active = false;
}

// Feed actual audio samples to waveform (like _audio_buffer_singleton)
function feedAudioChunk(samples) {
    audio_chunk = samples;
    audio_chunk_time = Date.now();
}

function _animate() {
    // EXACT port of boot_display.py _animate() lines 205-322
    // "This runs FOREVER once started - never stops."

    const canvas = document.getElementById('waveformCanvas');
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    // Check for audio - like lines 219-236
    let has_audio = false;
    let chunk = null;

    if (audio_chunk_time !== null) {
        const time_since_chunk = Date.now() - audio_chunk_time;
        // Accept chunks up to 300ms old (line 231)
        if (audio_chunk !== null && time_since_chunk < 300 && audio_is_active) {
            has_audio = true;
            chunk = audio_chunk;
        }
    }

    if (has_audio && chunk !== null) {
        // Process audio chunk - lines 240-305
        const chunk_len = chunk.length;
        const samples_to_add = Math.min(20, Math.floor(NUM_POINTS / 5));  // line 254

        if (chunk_len >= samples_to_add) {
            // Downsample - line 258-259
            const new_samples = [];
            for (let i = 0; i < samples_to_add; i++) {
                const idx = Math.floor(i * chunk_len / samples_to_add);
                new_samples.push(chunk[idx]);
            }

            // Find peak for adaptive scaling - lines 263-270
            let chunk_peak = 0;
            for (let i = 0; i < chunk.length; i++) {
                chunk_peak = Math.max(chunk_peak, Math.abs(chunk[i]));
            }
            let scale_factor = 20.0;
            if (chunk_peak > 0.001) {
                scale_factor = Math.min(0.95 / chunk_peak, 40.0);
            }

            // Scale and clamp - lines 270-273
            for (let i = 0; i < new_samples.length; i++) {
                new_samples[i] = Math.max(-1.0, Math.min(1.0, new_samples[i] * scale_factor));
            }

            // Shift buffer left, add new on right - line 276
            sample_buffer = sample_buffer.slice(samples_to_add).concat(new_samples);
        }

        // Smooth transition - lines 302-305
        for (let i = 0; i < NUM_POINTS; i++) {
            wave_points[i] = wave_points[i] * 0.3 + sample_buffer[i] * 0.7;
        }

    } else {
        // No audio - DECAY toward zero (lines 312-316)
        // Desktop behavior: NO fake waves, only real audio or decay
        const decay = 0.92;
        for (let i = 0; i < NUM_POINTS; i++) {
            wave_points[i] *= decay;
            sample_buffer[i] *= decay;
        }
    }

    // Draw the wave - line 319
    _draw_wave(width, height);

    // Schedule next frame - 25ms = ~40 FPS - line 322
    setTimeout(() => requestAnimationFrame(_animate), 25);
}

function _draw_wave(width, height) {
    // Single continuous waveform oscillating above and below center line
    const ctx = waveformCtx;
    const center_y = height / 2;
    const max_amp = (height / 2) - 5;

    // Clear
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, width, height);

    // Center reference line (visible)
    ctx.strokeStyle = '#402060';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, center_y);
    ctx.lineTo(width, center_y);
    ctx.stroke();

    // Build single wave coordinates - signed values go above/below center
    const step = width / (NUM_POINTS - 1);
    const waveCoords = [];

    for (let i = 0; i < NUM_POINTS; i++) {
        const x = i * step;
        // wave_points contains signed values (-1 to 1)
        // Positive goes UP (above center), negative goes DOWN (below center)
        const y = center_y - (wave_points[i] * max_amp);
        waveCoords.push([x, y]);
    }

    if (waveCoords.length >= 4) {
        // 4 glow layers
        const layers = [
            { color: '#400060', width: 8 },   // Outer glow
            { color: '#8000a0', width: 5 },   // Mid glow
            { color: '#ff40ff', width: 3 },   // Main wave
            { color: '#ffc0ff', width: 1 }    // Bright core
        ];

        // Draw single continuous wave through all points
        layers.forEach(layer => {
            ctx.strokeStyle = layer.color;
            ctx.lineWidth = layer.width;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.beginPath();
            ctx.moveTo(waveCoords[0][0], waveCoords[0][1]);
            for (let i = 1; i < waveCoords.length - 1; i++) {
                const xc = (waveCoords[i][0] + waveCoords[i + 1][0]) / 2;
                const yc = (waveCoords[i][1] + waveCoords[i + 1][1]) / 2;
                ctx.quadraticCurveTo(waveCoords[i][0], waveCoords[i][1], xc, yc);
            }
            ctx.lineTo(waveCoords[waveCoords.length - 1][0], waveCoords[waveCoords.length - 1][1]);
            ctx.stroke();
        });
    }
}
