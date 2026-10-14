#!/usr/bin/env python3
"""
C.O.R.A Image Generation
Generate images using the Pollinations.AI API.

Updated 2026-10-14 for the current API:
- auth is a Bearer token (POLLINATIONS_API_KEY in .env); a `pk_` key is also
  passed as `?key=` for endpoints that still document it
- model ids are fully qualified (e.g. black-forest-labs/flux.1-schnell); the
  configured model (config.json models.image) is resolved against the live
  /image/models list, so an alias like "flux" keeps working as long as a flux
  model exists, and a missing model falls back to the service default
- `nologo` / `enhance` are no longer documented and are only sent on request
- `safe` is passed through as given

Per ARCHITECTURE.md:
- generate_boot_image(prompt) - returns image path, 1920x1080
- show_fullscreen_image(path) - tkinter Toplevel with X button
- Save to CORA data/images directory
"""

import json
import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from datetime import datetime

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_DIR / 'data' / 'images'

# Load .env file for API keys
from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / '.env')

# Pollinations.AI API settings
IMAGE_API = os.environ.get("POLLINATIONS_IMAGE_API", "https://gen.pollinations.ai/image").rstrip('/')
API_KEY = os.environ.get("POLLINATIONS_API_KEY", "")

_models_cache: Dict[str, Any] = {'at': 0.0, 'models': []}


def _configured_model() -> str:
    try:
        with open(PROJECT_DIR / 'config' / 'config.json', 'r', encoding='utf-8') as f:
            return (json.load(f).get('models') or {}).get('image') or 'flux'
    except Exception:
        return 'flux'


def _headers() -> Dict[str, str]:
    h = {'User-Agent': 'CORA/3.0'}
    if API_KEY:
        h['Authorization'] = f'Bearer {API_KEY}'
    return h


def encode_prompt(prompt: str) -> str:
    """URL-encode a prompt string."""
    return quote(prompt, safe='')


def list_image_models(max_age: float = 600.0) -> List[str]:
    """Model ids the service currently offers (cached)."""
    now = time.time()
    if _models_cache['models'] and now - _models_cache['at'] < max_age:
        return _models_cache['models']
    try:
        r = requests.get(f"{IMAGE_API}/models", headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
        names: List[str] = []
        if isinstance(data, list):
            for m in data:
                if isinstance(m, str):
                    names.append(m)
                elif isinstance(m, dict):
                    n = m.get('id') or m.get('name')
                    if n:
                        names.append(n)
        elif isinstance(data, dict):
            names = [k for k in data.keys()]
        _models_cache.update(at=now, models=names)
    except Exception:
        pass
    return _models_cache['models']


def resolve_model(requested: Optional[str] = None) -> Optional[str]:
    """Map an alias/partial name to a live model id. None = service default."""
    requested = (requested or _configured_model() or '').strip()
    models = list_image_models()
    if not models:
        return requested or None
    if requested in models:
        return requested
    rq = requested.lower()
    if rq:
        exact_tail = [m for m in models if m.lower().split('/')[-1] == rq]
        if exact_tail:
            return exact_tail[0]
        partial = [m for m in models if rq in m.lower()]
        if partial:
            return partial[0]
    return None


def generate_image(
    prompt: str,
    model: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
    nologo: bool = False,
    enhance: bool = False,
    safe: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an image from a text prompt using Pollinations.AI.

    Args:
        prompt: Description of the image to generate
        model: Model id or alias (default: config models.image, resolved live)
        width: Image width in pixels
        height: Image height in pixels
        seed: Random seed for deterministic generation
        output_path: Path to save the image
        nologo: Request no watermark (legacy flag, sent only if True)
        enhance: Let the service improve the prompt (legacy flag)
        safe: Safety filter list, passed through as given

    Returns:
        Dict with success status, path, and metadata
    """
    start_time = time.time()

    url = f"{IMAGE_API}/{encode_prompt(prompt)}"
    resolved = resolve_model(model)
    params: Dict[str, Any] = {"width": width, "height": height}
    if resolved:
        params["model"] = resolved
    if API_KEY.startswith('pk_'):
        params["key"] = API_KEY
    if seed is not None:
        params["seed"] = seed
    if nologo:
        params["nologo"] = "true"
    if enhance:
        params["enhance"] = "true"
    if safe:
        params["safe"] = safe

    try:
        response = None
        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=_headers(), timeout=120)
                if response.status_code == 401:
                    raise PermissionError("Pollinations rejected the API key (401). Set POLLINATIONS_API_KEY in .env")
                if response.status_code == 404 and 'model' in params:
                    # unknown model id -> retry with the service default
                    params.pop('model', None)
                    _models_cache['at'] = 0.0
                    continue
                response.raise_for_status()
                break
            except PermissionError:
                raise
            except requests.exceptions.RequestException as e:
                last_err = e
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"[!] Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        if response is None or not response.ok:
            raise last_err or RuntimeError("image request failed")

        inference_time = time.time() - start_time

        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            raise RuntimeError(f"unexpected response ({content_type}): {response.text[:120]}")
        file_ext = 'png' if 'png' in content_type else ('webp' if 'webp' in content_type else 'jpg')

        if not output_path:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = IMAGES_DIR / f"generated_{timestamp}.{file_ext}"
        else:
            output_path = Path(output_path)
            if not str(output_path).lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                output_path = Path(f"{output_path}.{file_ext}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)

        return {
            "success": True,
            "path": str(output_path),
            "prompt": prompt,
            "model": params.get("model", "default"),
            "width": width,
            "height": height,
            "seed": seed,
            "format": file_ext,
            "inference_time": inference_time,
            "size_bytes": len(response.content)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt,
            "inference_time": time.time() - start_time
        }


def generate_boot_image(prompt: str = None) -> Dict[str, Any]:
    """Generate a boot/splash image for CORA at 1920x1080."""
    if prompt is None:
        prompt = (
            "futuristic AI assistant boot screen, holographic interface, "
            "glowing blue circuits, dark background, sleek modern design, "
            "text 'C.O.R.A' in elegant futuristic font, digital consciousness awakening"
        )

    result = generate_image(prompt=prompt, width=1920, height=1080)

    if result["success"]:
        print(f"[+] Boot image generated: {result['path']}")
        print(f"    Size: {result['width']}x{result['height']}")
        print(f"    Time: {result['inference_time']:.2f}s")
    else:
        print(f"[!] Boot image generation failed: {result.get('error')}")

    return result


def show_fullscreen_image(image_path: str, duration: Optional[float] = None) -> bool:
    """Display an image fullscreen with a close button.

    Args:
        image_path: Path to the image file
        duration: Optional seconds after which the window closes itself
    """
    try:
        import tkinter as tk
        from PIL import Image, ImageTk

        image_path = Path(image_path)
        if not image_path.exists():
            print(f"[!] Image not found: {image_path}")
            return False

        try:
            from ui.window_manager import create_image_window
            root = create_image_window(title="CORA", maximized=True)
        except Exception:
            root = tk.Toplevel() if tk._default_root else tk.Tk()
            root.title("CORA")
            root.state('zoomed')
            root.configure(bg='black')
            root.lift()
            root.focus_force()

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        img = Image.open(image_path)
        img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        label = tk.Label(root, image=photo, bg='black')
        label.image = photo
        label.pack(fill=tk.BOTH, expand=True)

        close_btn = tk.Button(
            root, text="X", command=root.destroy, font=('Arial', 16, 'bold'),
            fg='white', bg='#cc0000', activebackground='#ff0000', activeforeground='white',
            width=3, height=1, relief=tk.FLAT, cursor='hand2'
        )
        close_btn.place(x=screen_width - 50, y=10)

        root.bind('<Escape>', lambda e: root.destroy())
        label.bind('<Button-1>', lambda e: root.destroy())
        if duration:
            root.after(int(duration * 1000), lambda: root.winfo_exists() and root.destroy())

        if not tk._default_root or tk._default_root is root:
            root.mainloop()
        return True

    except ImportError as e:
        print(f"[!] Missing dependency: {e}")
        print("    Install with: pip install pillow")
        return False
    except Exception as e:
        print(f"[!] Display error: {e}")
        return False


def get_recent_images(limit: int = 10) -> list:
    """Recently generated images, newest first."""
    if not IMAGES_DIR.exists():
        return []
    images = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
        images.extend(IMAGES_DIR.glob(ext))
    images.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in images[:limit]]


if __name__ == "__main__":
    print("=== CORA Image Generation Test ===")
    print(f"API: {IMAGE_API}  key: {'set' if API_KEY else 'missing'}")
    print(f"models: {list_image_models()[:10]}")
    print(f"resolved '{_configured_model()}' -> {resolve_model()}")
    result = generate_image("a small neon test pattern, dark background", width=512, height=512)
    print(result)
