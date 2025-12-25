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

self.onmessage = async function(e) {
    const { type, id, data } = e.data;

    switch (type) {
        case 'init':
            await handleInit(id, data);
            break;
        case 'generate':
            await handleGenerate(id, data);
            break;
        case 'checkStatus':
            self.postMessage({
                type: 'status',
                id,
                data: { initialized: isInitialized, initializing: isInitializing }
            });
            break;
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
    if (!isInitialized || !tts) {
        self.postMessage({ type: 'error', id, error: 'TTS not initialized' });
        return;
    }

    const { text, voice, speed } = data;

    // Validate text before generating
    if (!text || typeof text !== 'string' || text.trim().length < 2) {
        console.warn('[KOKORO] Empty or invalid text received, skipping generation');
        self.postMessage({ type: 'error', id, error: 'Text too short or empty' });
        return;
    }

    const cleanText = text.trim();
    console.log(`[KOKORO] Generating audio for: "${cleanText.substring(0, 50)}..."`);

    try {
        self.postMessage({ type: 'generating', id });

        const audio = await tts.generate(cleanText, {
            voice: voice || DEFAULT_VOICE,
            speed: speed || 1.0
        });

        if (audio && audio.audio) {
            const audioBuffer = audio.audio.buffer.slice(0);

            self.postMessage(
                {
                    type: 'audioReady',
                    id,
                    data: {
                        audio: audioBuffer,
                        sampleRate: audio.sampling_rate
                    }
                },
                [audioBuffer]
            );
        } else {
            self.postMessage({ type: 'error', id, error: 'No audio generated' });
        }

    } catch (error) {
        self.postMessage({ type: 'error', id, error: error.message });
    }
}
