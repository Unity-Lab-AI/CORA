#!/usr/bin/env python3
"""
C.O.R.A Presence Detection Service
Webcam + AI vision to detect if user is present

Per ARCHITECTURE.md v2.2.0:
- Quick check: Is anyone at the desk?
- Full analysis: Emotion, activity, posture, holding
- Uses Ollama llava model for vision
"""

import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Optional imports
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Ollama API for vision
OLLAMA_API = "http://localhost:11434/api/generate"
VISION_MODEL = "llava:7b"  # or llava:13b for better accuracy

# Snapshot location
SNAPSHOT_DIR = Path(__file__).parent.parent / 'data' / 'snapshots'


@dataclass
class PresenceResult:
    """Result of presence detection."""
    present: bool
    confidence: float
    emotion: Optional[str] = None
    activity: Optional[str] = None
    posture: Optional[str] = None
    holding: Optional[str] = None
    raw_response: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


def capture_webcam(camera_index: int = 0, save_path: Optional[Path] = None) -> Optional[Path]:
    """Capture a frame from the webcam.

    Args:
        camera_index: Camera device index (0 = default)
        save_path: Optional path to save image

    Returns:
        Path to saved image or None on failure
    """
    if not CV2_AVAILABLE:
        print("[!] OpenCV not available - install with: pip install opencv-python")
        return None

    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"[!] Could not open camera {camera_index}")
            return None

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            print("[!] Failed to capture frame")
            return None

        # Determine save path
        if save_path is None:
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = SNAPSHOT_DIR / f'snapshot_{timestamp}.jpg'

        # Save image
        cv2.imwrite(str(save_path), frame)
        return save_path

    except Exception as e:
        print(f"[!] Webcam capture error: {e}")
        return None


def image_to_base64(image_path: Path) -> Optional[str]:
    """Convert image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string or None
    """
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"[!] Image encoding error: {e}")
        return None


def ask_vision(image_path: Path, prompt: str, model: str = VISION_MODEL) -> Optional[str]:
    """Send image to Ollama vision model for analysis.

    Args:
        image_path: Path to image
        prompt: Question about the image
        model: Vision model to use

    Returns:
        Model's response or None
    """
    if not REQUESTS_AVAILABLE:
        print("[!] requests not available")
        return None

    # Encode image
    image_b64 = image_to_base64(image_path)
    if not image_b64:
        return None

    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'images': [image_b64],
            'stream': False
        }

        resp = requests.post(OLLAMA_API, json=payload, timeout=60)

        if resp.status_code == 200:
            data = resp.json()
            return data.get('response', '')
        else:
            print(f"[!] Vision API error: {resp.status_code}")
            return None

    except requests.ConnectionError:
        print("[!] Ollama not running")
        return None
    except Exception as e:
        print(f"[!] Vision error: {e}")
        return None


def check_human_present(camera_index: int = 0) -> PresenceResult:
    """Quick check if someone is at the desk.

    Two-pass detection:
    1. Capture webcam image
    2. Ask llava: Is anyone there?

    Args:
        camera_index: Camera device index

    Returns:
        PresenceResult with present=True/False
    """
    # Capture image
    image_path = capture_webcam(camera_index)
    if not image_path:
        return PresenceResult(
            present=False,
            confidence=0.0,
            error="Failed to capture webcam"
        )

    # Quick presence check
    prompt = """Look at this webcam image. Is there a person visible at the desk?
Answer with just: YES or NO"""

    response = ask_vision(image_path, prompt)

    if response is None:
        return PresenceResult(
            present=False,
            confidence=0.0,
            error="Vision model unavailable"
        )

    # Parse response
    response_lower = response.lower().strip()
    present = 'yes' in response_lower

    return PresenceResult(
        present=present,
        confidence=0.9 if present else 0.8,
        raw_response=response,
        timestamp=datetime.now().isoformat()
    )


def full_human_check(camera_index: int = 0) -> PresenceResult:
    """Deep analysis of human state at desk.

    Returns detailed info:
    - present: Is anyone there?
    - emotion: focused, tired, happy, stressed, etc.
    - activity: typing, reading, watching, thinking, etc.
    - posture: leaning forward, sitting back, hunched, etc.
    - holding: coffee, phone, nothing, etc.

    Args:
        camera_index: Camera device index

    Returns:
        PresenceResult with full analysis
    """
    # Capture image
    image_path = capture_webcam(camera_index)
    if not image_path:
        return PresenceResult(
            present=False,
            confidence=0.0,
            error="Failed to capture webcam"
        )

    # Detailed analysis prompt
    prompt = """Analyze this webcam image of a person at their desk.
If no person is visible, say "NO PERSON".
If a person is visible, describe:
1. EMOTION: (focused, tired, happy, stressed, bored, etc.)
2. ACTIVITY: (typing, reading, watching screen, thinking, talking, etc.)
3. POSTURE: (leaning forward, sitting back, hunched, relaxed, etc.)
4. HOLDING: (coffee mug, phone, nothing, pen, etc.)

Format:
PERSON: YES/NO
EMOTION: <emotion>
ACTIVITY: <activity>
POSTURE: <posture>
HOLDING: <item>"""

    response = ask_vision(image_path, prompt)

    if response is None:
        return PresenceResult(
            present=False,
            confidence=0.0,
            error="Vision model unavailable"
        )

    # Parse response
    result = parse_human_analysis(response)
    result.raw_response = response
    result.timestamp = datetime.now().isoformat()

    return result


def parse_human_analysis(response: str) -> PresenceResult:
    """Parse the detailed human analysis response.

    Args:
        response: Raw response from vision model

    Returns:
        PresenceResult with parsed fields
    """
    lines = response.strip().split('\n')
    result = PresenceResult(present=False, confidence=0.5)

    for line in lines:
        line = line.strip().upper()

        if 'PERSON:' in line:
            result.present = 'YES' in line
            result.confidence = 0.9 if result.present else 0.8

        elif 'EMOTION:' in line:
            result.emotion = line.split(':', 1)[-1].strip().lower()

        elif 'ACTIVITY:' in line:
            result.activity = line.split(':', 1)[-1].strip().lower()

        elif 'POSTURE:' in line:
            result.posture = line.split(':', 1)[-1].strip().lower()

        elif 'HOLDING:' in line:
            result.holding = line.split(':', 1)[-1].strip().lower()

    # Fallback parsing if format not matched
    if not result.present and 'no person' not in response.lower():
        if any(word in response.lower() for word in ['person', 'human', 'someone', 'user']):
            result.present = True
            result.confidence = 0.6

    return result


def should_interrupt(camera_index: int = 0) -> bool:
    """Check if it's appropriate to interrupt the user.

    Returns False if:
    - User not present
    - User appears very focused
    - User appears stressed

    Args:
        camera_index: Camera device index

    Returns:
        True if OK to interrupt
    """
    result = full_human_check(camera_index)

    if not result.present:
        return False

    # Don't interrupt if very focused
    if result.emotion in ('focused', 'concentrating', 'deep thought'):
        return False

    # Don't interrupt if stressed
    if result.emotion in ('stressed', 'frustrated', 'angry'):
        return False

    # Don't interrupt if on phone
    if result.activity in ('talking', 'phone call', 'on call'):
        return False

    return True


def wait_for_presence(camera_index: int = 0, timeout: int = 300, check_interval: int = 10) -> bool:
    """Wait until user is present at desk.

    Args:
        camera_index: Camera device index
        timeout: Maximum wait time in seconds
        check_interval: Seconds between checks

    Returns:
        True if user appeared, False if timeout
    """
    import time

    elapsed = 0
    while elapsed < timeout:
        result = check_human_present(camera_index)
        if result.present:
            return True

        time.sleep(check_interval)
        elapsed += check_interval

    return False


if __name__ == "__main__":
    print("=== PRESENCE DETECTION TEST ===")

    if not CV2_AVAILABLE:
        print("[!] OpenCV not installed. Install with: pip install opencv-python")
        sys.exit(1)

    print("\n--- Quick Presence Check ---")
    result = check_human_present()
    print(f"Present: {result.present}")
    print(f"Confidence: {result.confidence}")
    if result.error:
        print(f"Error: {result.error}")

    if result.present:
        print("\n--- Full Analysis ---")
        full = full_human_check()
        print(f"Emotion: {full.emotion}")
        print(f"Activity: {full.activity}")
        print(f"Posture: {full.posture}")
        print(f"Holding: {full.holding}")
