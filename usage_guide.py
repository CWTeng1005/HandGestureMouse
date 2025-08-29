import os
import tkinter as tk

try:
    from tkinter import PhotoImage
except Exception:
    PhotoImage = None


def draw_quick_guide(img, corner="tr", margin=(14, 46), alpha=0.88):
    import cv2
    import numpy as np

    lines = [
        "Quick Guide",
        "H : show/hide this guide",
        "C : open/close calculator",
        "F9: toggle volume mode",
        "Q : quit",
    ]

    pad_x, pad_y = 10, 10
    max_w, total_h = 0, 0
    for i, t in enumerate(lines):
        (tw, th), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.5 if i else 0.6, 2)
        max_w = max(max_w, tw)
        total_h += th + (4 if i else 6)
    total_h += pad_y * 2
    box_w = max_w + pad_x * 2
    box_h = total_h

    H, W = img.shape[:2]
    dx, dy = margin

    if corner == "tl":
        x1, y1 = dx, dy
    elif corner == "tr":
        x1, y1 = W - box_w - dx, dy
    elif corner == "bl":
        x1, y1 = dx, H - box_h - dy
    else:
        x1, y1 = W - box_w - dx, H - box_h - dy

    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x1 + box_w, y1 + box_h), (40, 40, 40), -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    y = y1 + pad_y + 6
    for i, t in enumerate(lines):
        scale = 0.6 if i == 0 else 0.5
        cv2.putText(img, t, (x1 + pad_x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 2)
        y += int(18 if i == 0 else 16)


def _load_png(path):
    if PhotoImage is None:
        return None
    if not os.path.exists(path):
        return None
    try:
        return PhotoImage(file=path)
    except Exception:
        return None


def open_detailed_guide(master=None):
    win = tk.Toplevel(master) if master is not None else tk.Tk()
    win.title("User Guide")
    try:
        win.attributes("-topmost", True)
    except Exception:
        pass

    frm = tk.Frame(win, padx=12, pady=12)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="Hand Gesture Mouse — User Guide", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 6))

    bullets = [
        "Mouse (Right hand):",
        "  • Move: index finger",
        "  • Left click: index + middle pinch",
        "  • Right click: thumb + index + middle (pinch)",
        "  • Double click: index + middle + ring pinch",
        "  • Scroll: pinky up/down",
        "",
        "Calculator (Left-hand digits):",
        "  • Press 'C' to show/hide calculator",
        "  • Left hand shows digits (1–9,0) after fist 'arming'",
        "",
        "Volume (Left hand):",
        "  • Press F9 (or button) to toggle volume mode",
        "  • Adjust by thumb–index distance",
        "",
        "Hotkeys: H (quick guide), C (calculator), F9 (volume), Q (quit).",
    ]
    for b in bullets:
        tk.Label(frm, text=b, anchor="w", justify="left", font=("Segoe UI", 10)).pack(anchor="w")

    img_path = os.path.join(os.path.dirname(__file__), "hand123.png")
    img_obj = _load_png(img_path)
    if img_obj is not None:
        lbl = tk.Label(frm, image=img_obj)
        lbl.image = img_obj
        lbl.pack(pady=(8, 0))

    tk.Button(frm, text="Close", command=win.destroy).pack(pady=10)

    if master is None:
        win.mainloop()

if __name__ == "__main__":
    open_detailed_guide(None)