// 05-api-checks (part 2): continues the previous file, same global scope

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
