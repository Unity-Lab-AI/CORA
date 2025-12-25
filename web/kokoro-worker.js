// ═══════════════════════════════════════════════════════════════
// C.O.R.A KOKORO TTS WEB WORKER
// Neural TTS running in browser using Kokoro-82M
// Voice: af_bella (CORA's voice from desktop app)
// ═══════════════════════════════════════════════════════════════

let tts = null;
let isInitialized = false;
let isInitializing = false;

const MODEL_ID = 'onnx-community/Kokoro-82M-v1.0-ONNX';
const DEFAULT_VOICE = 'af_bella';  // CORA's voice

let generateCount = 0;  // Track number of generate calls

self.onmessage = async function(e) {
    const { type, id, data } = e.data;

    console.log(`[WORKER] Received message: type=${type}, id=${id}`);

    switch (type) {
        case 'init':
            await handleInit(id, data);
            break;
        case 'generate':
            generateCount++;
            console.log(`[WORKER] Generate call #${generateCount}, id=${id}`);
            await handleGenerate(id, data);
            break;
        case 'checkStatus':
            self.postMessage({
                type: 'status',
                id,
                data: { initialized: isInitialized, initializing: isInitializing }
            });
            break;
        default:
            console.warn(`[WORKER] Unknown message type: ${type}`);
    }
};

async function handleInit(id, data) {
    if (isInitialized) {
        self.postMessage({ type: 'initComplete', id, data: { success: true, cached: true } });
        return;
    }

    if (isInitializing) {
        self.postMessage({ type: 'error', id, error: 'Already initializing' });
        return;
    }

    isInitializing = true;

    try {
        self.postMessage({ type: 'progress', id, data: { message: 'Loading Kokoro library...', progress: 10 } });

        const module = await import('https://cdn.jsdelivr.net/npm/kokoro-js@1.2.0/+esm');
        const KokoroTTS = module.KokoroTTS;

        self.postMessage({ type: 'progress', id, data: { message: 'Loading neural voice model...', progress: 20 } });

        tts = await KokoroTTS.from_pretrained(MODEL_ID, {
            dtype: 'q8',
            device: 'wasm',
            progress_callback: (progress) => {
                if (progress.status === 'progress') {
                    const pct = progress.progress || 0;
                    self.postMessage({
                        type: 'progress',
                        id,
                        data: { message: `Loading model... ${Math.round(pct)}%`, progress: 20 + (pct * 0.7) }
                    });
                }
            }
        });

        isInitialized = true;
        isInitializing = false;

        self.postMessage({ type: 'progress', id, data: { message: 'Kokoro ready!', progress: 100 } });
        self.postMessage({ type: 'initComplete', id, data: { success: true } });

    } catch (error) {
        isInitializing = false;
        self.postMessage({ type: 'error', id, error: error.message });
    }
}

async function handleGenerate(id, data) {
    console.log(`[WORKER] handleGenerate: id=${id}, isInitialized=${isInitialized}, hasTTS=${!!tts}`);

    if (!isInitialized || !tts) {
        console.error(`[WORKER] TTS not ready: initialized=${isInitialized}, tts=${!!tts}`);
        self.postMessage({ type: 'error', id, error: 'TTS not initialized' });
        return;
    }

    const { text, voice, speed } = data;
    console.log(`[WORKER] Generating: text="${text?.substring(0, 50)}...", voice=${voice}, speed=${speed}`);

    try {
        self.postMessage({ type: 'generating', id });

        const startTime = Date.now();
        const audio = await tts.generate(text, {
            voice: voice || DEFAULT_VOICE,
            speed: speed || 1.0
        });
        const genTime = Date.now() - startTime;

        console.log(`[WORKER] Generation complete in ${genTime}ms, hasAudio=${!!audio}, hasAudioData=${!!(audio?.audio)}`);

        if (audio && audio.audio) {
            const audioBuffer = audio.audio.buffer.slice(0);
            const sampleRate = audio.sampling_rate || 24000;
            const duration = audioBuffer.byteLength / 4 / sampleRate;  // Float32 = 4 bytes

            console.log(`[WORKER] Audio: ${audioBuffer.byteLength} bytes, ${sampleRate}Hz, ${duration.toFixed(2)}s`);

            self.postMessage(
                {
                    type: 'audioReady',
                    id,
                    data: {
                        audio: audioBuffer,
                        sampleRate: sampleRate
                    }
                },
                [audioBuffer]
            );
            console.log(`[WORKER] Audio sent to main thread for id=${id}`);
        } else {
            console.error(`[WORKER] No audio generated for id=${id}`);
            self.postMessage({ type: 'error', id, error: 'No audio generated' });
        }

    } catch (error) {
        console.error(`[WORKER] Generation error for id=${id}:`, error);
        self.postMessage({ type: 'error', id, error: error.message });
    }
}
