#!/usr/bin/env python3
"""
C.O.R.A Image Generation
Generate images using Pollinations.AI API (PolliLibPy)

Per ARCHITECTURE.md v1.0.0:
- generate_boot_image(prompt) - returns image path, 1920x1080
- show_fullscreen_image(path) - tkinter Toplevel with X button
- Save to CORA data/images directory
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import quote
from datetime import datetime

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_DIR / 'data' / 'images'

# Load .env file for API keys
from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / '.env')

# Pollinations.AI API settings
IMAGE_API = "https://gen.pollinations.ai/image"
# API key from .env file (POLLINATIONS_API_KEY)
API_KEY = os.environ.get("POLLINATIONS_API_KEY", "")


def encode_prompt(prompt: str) -> str:
    """URL-encode a prompt string."""
    return quote(prompt)


def generate_image(
    prompt: str,
    model: str = "flux",
    width: int = 1920,
    height: int = 1080,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
    nologo: bool = True,
    enhance: bool = False,
    safe: bool = False
) -> Dict[str, Any]:
    """
    Generate an image from a text prompt using Pollinations.AI.

    Args:
        prompt: Description of the image to generate
        model: AI model to use (flux, turbo, etc.)
        width: Image width in pixels
        height: Image height in pixels
        seed: Random seed for deterministic generation
        output_path: Path to save the image
        nologo: Remove watermark
        enhance: Let AI improve the prompt
        safe: Enable NSFW filtering

    Returns:
        Dict with success status, path, and metadata
    """
    start_time = time.time()

    # Build URL
    encoded_prompt = encode_prompt(prompt)
    url = f"{IMAGE_API}/{encoded_prompt}"

    # Build parameters
    params = {
        "model": model,
        "width": width,
        "height": height,
        "key": API_KEY
    }

    if seed is not None:
        params["seed"] = seed
    if nologo:
        params["nologo"] = "true"
    if enhance:
        params["enhance"] = "true"
    if safe:
        params["safe"] = "true"

    try:
        # Make request with retry logic
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=120)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"[!] Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e

        inference_time = time.time() - start_time

        # Determine format
        content_type = response.headers.get('Content-Type', '')
        file_ext = 'png' if 'png' in content_type else 'jpg'

        # Generate output path if not provided
        if not output_path:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = IMAGES_DIR / f"generated_{timestamp}.{file_ext}"
        else:
            output_path = Path(output_path)
            if not str(output_path).endswith(('.jpg', '.jpeg', '.png')):
                output_path = Path(f"{output_path}.{file_ext}")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save image
        with open(output_path, 'wb') as f:
            f.write(response.content)

        result = {
            "success": True,
            "path": str(output_path),
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "seed": seed,
            "format": file_ext,
            "inference_time": inference_time,
            "size_bytes": len(response.content)
        }

        # Note: Don't auto-show modal here - let caller decide whether to display
        # This prevents double popups when boot_sequence also shows the image

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt,
            "inference_time": time.time() - start_time
        }


def generate_boot_image(prompt: str = None) -> Dict[str, Any]:
    """
    Generate a boot/splash image for CORA at 1920x1080.

    Args:
        prompt: Custom prompt or uses default CORA boot prompt

    Returns:
        Dict with success status and image path
    """
    if prompt is None:
        prompt = (
            "futuristic AI assistant boot screen, holographic interface, "
            "glowing blue circuits, dark background, sleek modern design, "
            "text 'C.O.R.A' in elegant futuristic font, digital consciousness awakening"
        )

    result = generate_image(
        prompt=prompt,
        width=1920,
        height=1080,
        model="flux",
        nologo=True,
        enhance=True
    )

    if result["success"]:
        print(f"[+] Boot image generated: {result['path']}")
        print(f"    Size: {result['width']}x{result['height']}")
        print(f"    Time: {result['inference_time']:.2f}s")
    else:
        print(f"[!] Boot image generation failed: {result.get('error')}")

    return result


def show_fullscreen_image(image_path: str) -> bool:
    """
    Display an image in fullscreen with a close button.

    Args:
        image_path: Path to the image file

    Returns:
        True if displayed successfully
    """
    try:
        import tkinter as tk
        from PIL import Image, ImageTk

        image_path = Path(image_path)
        if not image_path.exists():
            print(f"[!] Image not found: {image_path}")
            return False

        # Use window manager for proper z-layering
        try:
            from ui.window_manager import create_image_window
            root = create_image_window(title="CORA", maximized=True)
        except:
            # Fallback if window manager not available
            root = tk.Toplevel() if tk._default_root else tk.Tk()
            root.title("CORA")
            root.state('zoomed')
            root.configure(bg='black')
            root.lift()
            root.focus_force()

        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Load and resize image
        img = Image.open(image_path)
        img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        # Display image
        label = tk.Label(root, image=photo, bg='black')
        label.image = photo  # Keep reference
        label.pack(fill=tk.BOTH, expand=True)

        # Close button (red X, top-right)
        close_btn = tk.Button(
            root,
            text="X",
            command=root.destroy,
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#cc0000',
            activebackground='#ff0000',
            activeforeground='white',
            width=3,
            height=1,
            relief=tk.FLAT,
            cursor='hand2'
        )
        close_btn.place(x=screen_width - 50, y=10)

        # Bind Escape to close
        root.bind('<Escape>', lambda e: root.destroy())
        # Click anywhere to close
        label.bind('<Button-1>', lambda e: root.destroy())

        # Start mainloop if we created the root
        if not tk._default_root:
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
    """
    Get list of recently generated images.

    Args:
        limit: Maximum number of images to return

    Returns:
        List of image paths sorted by modification time
    """
    if not IMAGES_DIR.exists():
        return []

    images = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        images.extend(IMAGES_DIR.glob(ext))

    # Sort by modification time, newest first
    images.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(p) for p in images[:limit]]


if __name__ == "__main__":
    print("=== CORA Image Generation Test ===")
    print()

    # Test boot image generation
    print("1. Generating boot image...")
    result = generate_boot_image()

    if result["success"]:
        print(f"\n2. Displaying image...")
        show_fullscreen_image(result["path"])

    print("\n3. Recent images:")
    for img in get_recent_images(5):
        print(f"   - {img}")

    print("\n=== Test Complete ===")
