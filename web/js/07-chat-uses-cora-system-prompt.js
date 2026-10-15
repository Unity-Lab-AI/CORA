// C.O.R.A web - Chat - Uses CORA_SYSTEM_PROMPT loaded from config/system_prompt.txt
// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.

// ============================================================
// Chat - Uses CORA_SYSTEM_PROMPT loaded from config/system_prompt.txt
// ============================================================

async function sendChat() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    log(`USER: ${msg}`, 'system');

    // Store user message in ambient context
    addMessageHistory('USER', msg);

    // Show thinking state
    document.getElementById('speechText').textContent = '"Thinking..."';

    // Build context from ambient awareness (speech, messages, camera, screenshot)
    const context = buildAmbientContextPrompt();

    try {
        // Include context in prompt for full awareness
        const fullPrompt = context ? `${context}\n\nUSER: ${msg}` : msg;

        const res = await fetch(OLLAMA_URL + '/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CORA_MODEL,
                prompt: fullPrompt,
                system: CORA_SYSTEM_PROMPT,
                stream: false,
                think: false,
                options: {
                    num_ctx: CORA_NUM_CTX,
                    temperature: 0.8,
                    num_predict: 500
                }
            })
        });
        if (res.ok) {
            const d = await res.json();
            const reply = d.response || 'No response';

            // Store CORA's response in ambient context
            addMessageHistory('CORA', reply);

            log(`CORA: "${reply}"`, 'ok');
            speak(reply);
        } else {
            log('Ollama error', 'fail');
            document.getElementById('speechText').textContent = '"Fuck, something broke."';
        }
    } catch (e) {
        log(`Error: ${e.message}`, 'fail');
        document.getElementById('speechText').textContent = '"Ollama is being a bitch right now."';
    }
}

document.getElementById('chatInput')?.addEventListener('keypress', e => { if (e.key === 'Enter') sendChat(); });
