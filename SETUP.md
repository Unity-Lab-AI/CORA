# C.O.R.A - Setup Guide

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 3.0.0
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

## Quick Install (5 Minutes)

### Step 1: Python
Make sure you have Python 3.13 (3.12 works):
```bash
python --version
```
If not installed: [Download Python](https://www.python.org/downloads/)

### Step 2: Install Dependencies
The launcher does this for you (`windows\start.bat` / `linux/start.sh` / `CORA.bat`). By hand:
```bash
py -3.13 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### Step 3: Install Ollama (AI Brain)
```bash
winget install Ollama.Ollama
```
Or download from: [ollama.com](https://ollama.com)

### Step 4: Download AI Models
```bash
# The launcher pulls the configured models (config/config.json `models`):
#   unity-brain                     - her brain: chat, tools, vision (built in the lab's Backrooms repo, models/unity-brain)
#   huihui_ai/qwen3-abliterated:8b  - fallback brain
ollama pull huihui_ai/qwen3-abliterated:8b
```

### Step 5: Install mpv (Optional - for YouTube)
Download from: https://sourceforge.net/projects/mpv-player-windows/files/64bit/

Extract to `./tools/` folder - CORA auto-detects mpv.exe (any subfolder works).

### Step 6: Run CORA
```
windows\start.bat      (or linux/start.sh, or CORA.bat)
```
Stop everything she started with `windows\stop.bat` / `linux/stop.sh`.

---

---

## API Keys Setup

CORA works great with NO API keys - Ollama runs locally for free! But these optional keys enable extra features:

### Images need no key

Pictures render on CORA's own image engine (see **Image Engine Setup** below): local Stable Diffusion, nothing hosted, no account.

### GitHub Token (FREE - Git Operations)

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it "CORA" and select scopes: `repo`, `user`
4. Copy the token (starts with `ghp_`)
5. Add to your `.env` file:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### Weather API (FREE - Weather Data)

1. Go to: https://openweathermap.org/api
2. Sign up for free account
3. Go to "API Keys" tab
4. Copy your API key
5. Add to your `.env` file:
   ```
   WEATHER_API_KEY=your_key_here
   ```

### News API (FREE - Headlines)

1. Go to: https://newsapi.org/
2. Click "Get API Key"
3. Sign up for free
4. Copy your API key
5. Add to your `.env` file:
   ```
   NEWS_API_KEY=your_key_here
   ```

### Setting Up Your .env File

1. Copy `env.example` to `.env`:
   ```bash
   copy env.example .env
   ```
2. Open `.env` in a text editor
3. Replace the placeholder values with your actual keys
4. Save the file

**Note:** The `.env` file contains secrets - never commit it to git!

See `env.example` for detailed instructions on each API key.

---

## Detailed Installation

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| Python | 3.12 | 3.13 |
| RAM | 8 GB | 16 GB |
| GPU | None | NVIDIA (CUDA) |
| VRAM | 8 GB | 16 GB (brain + voice + whisper together) |
| Storage | 5 GB | 10 GB |
| mpv | Optional | For YouTube playback |

### Python Dependencies

Core packages installed via `requirements.txt`:

| Package | Purpose |
|---------|---------|
| customtkinter | Modern GUI framework |
| ollama | AI model integration |
| (sidecar) | unity-voice-v2, her own voice, runs as a separate process |
| soundfile | Audio processing |
| sounddevice | Audio playback |
| psutil | System monitoring |
| opencv-python | Webcam/vision |
| pillow | Image processing |
| requests | API calls |
| faster-whisper | Local GPU speech recognition |
| openwakeword | Optional wake-word model |

Install all:
```bash
pip install -r requirements.txt
```

---

## Ollama Setup

### Installing Ollama

**Windows (winget):**
```bash
winget install Ollama.Ollama
```

**Windows (manual):**
1. Go to [ollama.com](https://ollama.com)
2. Download the Windows installer
3. Run the installer
4. Restart your terminal

### Starting Ollama

Ollama runs as a background service. Start it:
```bash
ollama serve
```

Or it starts automatically when you pull/run a model.

### Downloading Models

**Required models:**
```bash
ollama create unity-brain -f <Backrooms>/models/unity-brain/Modelfile   # her brain (5.3 GB + 0.9 GB vision)
ollama pull huihui_ai/qwen3-abliterated:8b                              # fallback brain
```

**Optional models:** any Ollama model works as `models.primary` in `config/config.json`; models with a tools template get native tool calling, others get the JSON fallback protocol.

### Verifying Ollama

Check if Ollama is running:
```bash
ollama list
```

Should show your downloaded models.

---

## Voice Setup

### TTS (Text-to-Speech)

CORA speaks with `unity-voice-v2`, Unity AI Lab's own trained voice, served as a sidecar on 127.0.0.1:5123 (`tts.unity_voice` in `config/config.json`: model dir, Python with torch + misaki, autostart). The launcher starts it. There is no other voice and no fallback voice.

### STT (Speech-to-Text)

Voice input is faster-whisper on the GPU (`stt.whisper_model` in `config/config.json`, default `base.en`; the model downloads on first use). Vosk is only a fallback engine if faster-whisper cannot load.

---

## Image Engine Setup

CORA paints with her own engine: `services/image_sidecar.py`, local Stable Diffusion with the `realistic-vision-v51` checkpoint (the same rig Unity's stream renders with) through diffusers. Text to image, img2img edits, inpainting, and webcam recreations with the face kept (IP-Adapter Plus Face).

What it needs (`config/config.json` `image` block):

| Key | Meaning |
|---|---|
| `checkpoint` | path to `realistic-vision-v51.safetensors` (2.1 GB, SD 1.5 family) |
| `python` | an interpreter with torch + diffusers + transformers + accelerate; `null` = auto-detect (the voice sidecar's interpreter is tried first, then `C:\Program Files\Python310\python.exe`); or set `CORA_IMAGE_PYTHON` |
| `device` | `auto` (GPU when there is one), `cuda`, `cpu` |
| `offload` | `true` keeps the model in RAM and streams layers to the GPU (about 3 GB of VRAM while rendering, so her brain and voice keep their room) |
| `url` | `http://127.0.0.1:5124` |
| `width` / `height` / `steps` | defaults for a picture (768x768; steps `null` = 25 on GPU, 12 on CPU) |
| `save_dir` | where pictures land (`data/images`) |
| `selfie_look` / `selfie_negative` | who she is in pictures of herself (girl next door with a soft emo edge); every selfie leads with this and bans the negative. Tune the words here. |

The engine starts on the first picture and the checkpoint loads then (about a second on an RTX 4070 Ti; a picture takes 3-5 s on the GPU, 1-2 minutes on a CPU). The face adapter weights (`h94/IP-Adapter`) download once into the Hugging Face cache. Health: `http://127.0.0.1:5124/health`; log: `data/image-sidecar.log`. The stop scripts end the engine when CORA started it, and every normal exit unloads it with her brain.

Every picture opens in her viewer (`ui/image_viewer.py`: Save As, Open folder, Copy path); "save that to my desktop" calls her `save_image` tool.

---

## GPU Setup (Optional)

For faster AI responses with NVIDIA GPU:

### CUDA Installation

1. Install NVIDIA drivers (latest)
2. The venv brings the CUDA 12 runtime libraries whisper needs (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`)

### Verify GPU

CORA auto-detects GPU via nvidia-smi:
```bash
nvidia-smi
```

You should see your GPU listed with VRAM stats.

---

## Running CORA

### Visual Boot (Recommended)
```
windows\start.bat        (Linux: linux/start.sh)
```
or, inside the venv, `python src/boot_sequence.py`.
- Full cyberpunk visual display
- 10-phase diagnostic with TTS
- Live system stats
- Dynamic AI responses

### GUI Mode
```bash
python src/gui_launcher.py
```

### CLI Mode
```bash
python cora.py
```

### Quick Boot (No TTS)
```bash
python src/boot_sequence.py --quick
```

### Web Version
Served locally with her voice and the configured models:
```bash
python services/stats_server.py      # then open http://127.0.0.1:11435/
```
Opened from anywhere else the page is text only against a local Ollama.

---

## Configuration

### Settings Location

| File | Purpose |
|------|---------|
| `config/config.json` | The one config: models, ollama, tts.unity_voice, stt, camera, boot, assistant, web |
| `config/system_prompt.txt` | Her persona (also served to the web page) |
| `config/voice_commands.json` | Wake words, voice command aliases |

### Default Settings

`config/config.json` (excerpt):
```json
{
  "models": {"primary": "unity-brain", "vision": "unity-brain", "fallback": "huihui_ai/qwen3-abliterated:8b"},
  "ollama": {"api_url": "http://127.0.0.1:11434", "num_ctx": 16384, "keep_alive": "30m"},
  "tts": {"enabled": true, "engine": "unity-voice-v2", "unity_voice": {"url": "http://127.0.0.1:5123", "autostart": true}},
  "stt": {"engine": "faster-whisper", "whisper_model": "base.en"},
  "camera": {"index": "auto", "backend": "auto", "open_timeout": 4.0},
  "boot": {"demo_phases": false, "popups": false}
}
```

---

## Troubleshooting

### CORA won't start

**Check Python version:**
```bash
python --version
```
Must be 3.12 or 3.13

**Check dependencies:**
```bash
pip install -r requirements.txt
```

### No AI responses

**Check Ollama is running:**
```bash
ollama list
```

**Start Ollama:**
```bash
ollama serve
```

**Pull models:**
```bash
python scripts/bootstrap.py      # pulls whatever config/config.json names
```

### No voice output

**Check her voice:**
```bash
curl http://127.0.0.1:5123/health          # the sidecar; its log is data/voice-sidecar.log
```

**Test TTS:**
```bash
python -c "from voice.tts import speak; speak('Hello')"
```

### No GPU detected

**Check NVIDIA drivers:**
```bash
nvidia-smi
```

**Update drivers:** [nvidia.com/drivers](https://www.nvidia.com/drivers)

### No images

**Check her image engine:**
```bash
curl http://127.0.0.1:5124/health        # the sidecar; its log is data/image-sidecar.log
python cora_tools/image_gen.py           # prints the checkpoint path, finds the torch interpreter, starts the engine
```
A missing checkpoint or an interpreter without torch + diffusers is the usual cause (`config/config.json` `image.checkpoint` / `image.python`).

### Webcam not working

**Check OpenCV:**
```bash
pip install opencv-python
```

**Test webcam:**
```bash
python services/camera.py                 # probes every index/backend with a timeout
```

---

## Directory Structure

After installation:
```
C.O.R.A/
├── src/
│   ├── boot_sequence.py     # Main boot with visual display
│   ├── cora.py              # CLI application
│   └── gui_launcher.py      # GUI launcher
├── ui/
│   ├── boot_display.py      # Visual boot display
│   ├── app.py               # Main GUI
│   ├── image_viewer.py      # Picture window (Save As, Open folder)
│   └── panels.py            # GUI panels
├── voice/
│   ├── tts.py               # unity-voice-v2 client
│   ├── stt.py               # faster-whisper
│   └── wake_word.py         # Wake word detection
├── ai/
│   ├── dispatcher.py        # the conversation loop
│   ├── tools_registry.py    # 116 tools
│   ├── ollama.py            # Ollama client
│   └── settings.py          # models, URLs, options
├── cora_tools/              # Python tool modules (20+)
├── tools/                   # Downloaded binaries (mpv, ffmpeg)
├── services/                # Camera, image engine sidecar, stats server, weather, location
├── config/
│   └── config.json          # Configuration
├── data/
│   ├── images/              # Generated images
│   └── camera/              # Camera captures
└── requirements.txt         # Python dependencies
```

**Note:** `cora_tools/` = Python code, `tools/` = binaries only

---

## Updating CORA

### Pull Latest Code
```bash
git pull origin main
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Update AI Models
```bash
python scripts/bootstrap.py
```

---

## Need Help?

- **Website:** https://www.unityailab.com
- **GitHub:** https://github.com/Unity-Lab-AI
- **Email:** unityailabcontact@gmail.com

---

*C.O.R.A v3.0.0 - Setup Guide*
*Unity AI Lab - Hackall360, Sponge, GFourteen, Alfreddo*
