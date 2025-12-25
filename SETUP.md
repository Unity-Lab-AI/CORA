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
  Version: 2.4.0
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

## Quick Install (5 Minutes)

### Step 1: Python
Make sure you have Python 3.10 or newer:
```bash
python --version
```
If not installed: [Download Python](https://www.python.org/downloads/)

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Ollama (AI Brain)
```bash
winget install Ollama.Ollama
```
Or download from: [ollama.com](https://ollama.com)

### Step 4: Download AI Models
```bash
ollama pull llama3.2
ollama pull llava
```

### Step 5: Install mpv (Optional - for YouTube)
Download from: https://sourceforge.net/projects/mpv-player-windows/files/64bit/

Extract to `CORA/tools/` - CORA will find mpv.exe automatically.

### Step 6: Run CORA
```bash
python src/boot_sequence.py
```

---

## Detailed Installation

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| Python | 3.10+ | 3.11+ |
| RAM | 8 GB | 16 GB |
| GPU | None | NVIDIA (CUDA) |
| VRAM | N/A | 8 GB+ |
| Storage | 5 GB | 10 GB |
| mpv | Optional | For YouTube playback |

### Python Dependencies

Core packages installed via `requirements.txt`:

| Package | Purpose |
|---------|---------|
| customtkinter | Modern GUI framework |
| ollama | AI model integration |
| kokoro | Neural TTS synthesis |
| soundfile | Audio processing |
| sounddevice | Audio playback |
| psutil | System monitoring |
| opencv-python | Webcam/vision |
| pillow | Image processing |
| requests | API calls |
| SpeechRecognition | Voice input |
| vosk | Offline speech recognition |

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
ollama pull llama3.2      # Text chat (2.0 GB)
ollama pull llava         # Vision/image analysis (4.7 GB)
```

**Optional models:**
```bash
ollama pull codellama     # Code generation
ollama pull mistral       # Alternative chat
ollama pull phi           # Small & fast
```

### Verifying Ollama

Check if Ollama is running:
```bash
ollama list
```

Should show your downloaded models.

---

## Voice Setup

### TTS (Text-to-Speech)

CORA uses Kokoro TTS by default (neural voice):

```bash
pip install kokoro soundfile sounddevice
```

The `af_bella` voice is used automatically.

### STT (Speech-to-Text)

For voice input:
```bash
pip install SpeechRecognition vosk
```

Download a Vosk model (optional, for offline):
- [vosk-model-small-en-us](https://alphacephei.com/vosk/models)
- Extract to `models/vosk/`

---

## GPU Setup (Optional)

For faster AI responses with NVIDIA GPU:

### CUDA Installation

1. Install NVIDIA drivers (latest)
2. Install CUDA Toolkit 11.8+
3. Install cuDNN

### Verify GPU

CORA auto-detects GPU via nvidia-smi:
```bash
nvidia-smi
```

You should see your GPU listed with VRAM stats.

---

## Running CORA

### Visual Boot (Recommended)
```bash
python src/boot_sequence.py
```
- Full cyberpunk visual display
- 10-phase diagnostic with TTS
- Live system stats
- Dynamic AI responses

### GUI Mode
```bash
python gui_launcher.py
```
or
```bash
python ui/app.py
```

### CLI Mode
```bash
python cora.py
```

### Quick Boot (No TTS)
```bash
python src/boot_sequence.py --quick
```

---

## Configuration

### Settings Location

| File | Purpose |
|------|---------|
| `config/settings.json` | GUI settings (TTS, Ollama, STT) |
| `config/voice_commands.json` | Wake words, voice config |
| `personality.json` | AI personality traits |

### Default Settings

`config/settings.json`:
```json
{
  "tts": {
    "enabled": true,
    "rate": 150,
    "volume": 1.0
  },
  "ollama": {
    "enabled": true,
    "model": "llama3.2"
  },
  "stt": {
    "enabled": true,
    "sensitivity": 0.7
  }
}
```

---

## Troubleshooting

### CORA won't start

**Check Python version:**
```bash
python --version
```
Must be 3.10+

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
ollama pull llama3.2
```

### No voice output

**Check Kokoro:**
```bash
pip install kokoro soundfile sounddevice
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

### Webcam not working

**Check OpenCV:**
```bash
pip install opencv-python
```

**Test webcam:**
```bash
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

---

## Directory Structure

After installation:
```
C.O.R.A/
├── src/
│   ├── boot_sequence.py     # Main boot with visual display
│   └── cora.py              # CLI application
├── ui/
│   ├── boot_display.py      # Visual boot display
│   ├── app.py               # Main GUI
│   └── panels.py            # GUI panels
├── voice/
│   ├── tts.py               # Kokoro TTS
│   ├── stt.py               # Speech recognition
│   └── wake_word.py         # Wake word detection
├── ai/
│   ├── ollama.py            # Ollama client
│   └── context.py           # Context management
├── tools/                   # 17+ tool modules
├── services/                # Weather, location, etc.
├── config/
│   └── settings.json        # Configuration
├── data/
│   ├── images/              # Generated images
│   └── camera/              # Camera captures
└── requirements.txt         # Python dependencies
```

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
ollama pull llama3.2
ollama pull llava
```

---

## Need Help?

- **Website:** https://www.unityailab.com
- **GitHub:** https://github.com/Unity-Lab-AI
- **Email:** unityailabcontact@gmail.com

---

*C.O.R.A v2.4.0 - Setup Guide*
*Unity AI Lab - Hackall360, Sponge, GFourteen*
