#!/usr/bin/env python3
"""
C.O.R.A image viewer: the window every generated or edited image opens in.

Runs as its own process (cora_tools.image_gen.show_image starts it), so it never
blocks CORA and never touches the app's Tk thread:

    python ui/image_viewer.py <image> [--caption "text"] [--close-after 15]

Fit to the screen, with Save As (file dialog), Open folder, Copy path and Close.
Esc or a click on the picture closes it; Ctrl+S is Save As.
"""
import argparse
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

BG, FG, ACCENT, BTN = '#0a0a0f', '#dddddd', '#ff00ff', '#1e1e2a'


def open_folder(path: Path):
    folder = str(path.parent)
    try:
        if sys.platform.startswith('win'):
            subprocess.Popen(['explorer', '/select,', str(path)])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', str(path)])
        else:
            subprocess.Popen(['xdg-open', folder])
    except Exception as e:
        messagebox.showerror('CORA', f'could not open the folder: {e}')


class Viewer:
    def __init__(self, path: Path, caption: str = '', close_after: float = 0.0):
        from PIL import Image, ImageTk
        self.path = path
        self.root = tk.Tk()
        self.root.title(f'CORA - {path.name}')
        self.root.configure(bg=BG)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        img = Image.open(path)
        self.size = img.size
        max_w, max_h = int(sw * 0.85), int(sh * 0.78)
        scale = min(max_w / img.width, max_h / img.height, 1.0)
        shown = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(shown)

        top = tk.Frame(self.root, bg=BG)
        top.pack(fill='x', padx=10, pady=(8, 4))
        tk.Label(top, text=f'{path.name}   {img.width}x{img.height}', bg=BG, fg=ACCENT,
                 font=('Consolas', 11, 'bold')).pack(side='left')
        if caption:
            tk.Label(self.root, text=caption, bg=BG, fg=FG, wraplength=shown.width, justify='left',
                     font=('Consolas', 9)).pack(fill='x', padx=10)

        pic = tk.Label(self.root, image=self.photo, bg=BG, cursor='hand2')
        pic.pack(padx=10, pady=6)
        pic.bind('<Button-1>', lambda e: self.close())

        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill='x', padx=10, pady=(0, 10))
        for text, cmd in (('Save As...', self.save_as), ('Open folder', lambda: open_folder(self.path)),
                          ('Copy path', self.copy_path), ('Close', self.close)):
            tk.Button(bar, text=text, command=cmd, bg=BTN, fg=FG, activebackground=ACCENT, activeforeground='#000',
                      relief='flat', padx=14, pady=6, font=('Consolas', 10, 'bold'), cursor='hand2').pack(side='left', padx=(0, 8))
        self.status = tk.Label(bar, text='', bg=BG, fg='#888', font=('Consolas', 9))
        self.status.pack(side='right')

        self.root.bind('<Escape>', lambda e: self.close())
        self.root.bind('<Control-s>', lambda e: self.save_as())
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.geometry(f'+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}')
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(300, lambda: self.root.attributes('-topmost', False))
        if close_after and close_after > 0:
            self.root.after(int(close_after * 1000), self.close)

    def save_as(self):
        ext = self.path.suffix.lower() or '.png'
        target = filedialog.asksaveasfilename(
            parent=self.root, title='Save image as', initialfile=self.path.name, defaultextension=ext,
            initialdir=str(Path.home() / 'Pictures') if (Path.home() / 'Pictures').exists() else str(Path.home()),
            filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg *.jpeg'), ('WebP', '*.webp'), ('All files', '*.*')])
        if not target:
            return
        try:
            from PIL import Image
            dest = Path(target)
            if dest.suffix.lower() == ext:
                dest.write_bytes(self.path.read_bytes())
            else:
                img = Image.open(self.path)
                if dest.suffix.lower() in ('.jpg', '.jpeg'):
                    img = img.convert('RGB')
                img.save(dest)
            self.status.configure(text=f'saved: {dest}')
        except Exception as e:
            messagebox.showerror('CORA', f'could not save: {e}')

    def copy_path(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(str(self.path))
        self.status.configure(text='path copied')

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description='CORA image viewer')
    ap.add_argument('image')
    ap.add_argument('--caption', default='')
    ap.add_argument('--close-after', type=float, default=0.0)
    a = ap.parse_args()
    p = Path(a.image)
    if not p.exists():
        print(f'image not found: {p}', file=sys.stderr)
        sys.exit(1)
    Viewer(p, a.caption, a.close_after).run()


if __name__ == '__main__':
    main()
