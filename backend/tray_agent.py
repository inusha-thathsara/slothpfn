import os
import sys
import json
import time
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item, Menu

# Setup paths and environment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.ambient_daemon import (
    start_ambient_watcher,
    morning_wake_up_briefing,
    speak_aloud,
    show_toast,
    SESSION_FILE,
    DROP_DATA_DIR,
    DEFAULT_VOICE_ID,
)
from backend.voice_agent import POPULAR_VOICES

# Current active voice state for the tray app
CURRENT_VOICE_ID = DEFAULT_VOICE_ID
WATCHER_OBSERVER = None
TRAY_ICON = None


def create_sloth_icon_image() -> Image.Image:
    """
    Generates a crisp 64x64 sloth icon for the Windows taskbar tray.
    """
    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer circle (amber sloth badge)
    draw.ellipse((4, 4, 60, 60), fill="#d97706", outline="#f59e0b", width=2)
    # Face background (warm cream)
    draw.ellipse((14, 16, 50, 52), fill="#fef3c7")
    # Eye patches (characteristic sloth eye bands)
    draw.ellipse((16, 26, 30, 36), fill="#92400e")
    draw.ellipse((34, 26, 48, 36), fill="#92400e")
    # Eyes (dark dots)
    draw.ellipse((22, 29, 26, 33), fill="#1f2937")
    draw.ellipse((38, 29, 42, 33), fill="#1f2937")
    # Nose & smile
    draw.ellipse((28, 36, 36, 42), fill="#451a03")
    draw.arc((26, 38, 38, 46), start=0, end=180, fill="#451a03", width=2)

    return image


def on_open_dashboard(icon, item):
    webbrowser.open("http://127.0.0.1:8000")


def on_open_drop_folder(icon, item):
    if DROP_DATA_DIR.exists():
        os.startfile(str(DROP_DATA_DIR))


def on_open_downloads_folder(icon, item):
    downloads = Path.home() / "Downloads"
    if downloads.exists():
        os.startfile(str(downloads))


def on_speak_latest(icon, item):
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = data.get("result", {})
            insights = result.get("sloth_insights", {})
            headline = insights.get("headline", "Model is ready")
            summary = insights.get("summary", "")
            script = f"Latest model update: {headline}. {summary}"
            show_toast("🦥 Latest SlothPFN Briefing", headline)
            threading.Thread(target=speak_aloud, args=(script, CURRENT_VOICE_ID), daemon=True).start()
            return
        except Exception as e:
            print(f"[Tray Audio Notice] {e}")

    script = "SlothPFN is active in your system tray. Drop a CSV into your Downloads folder to hear an analysis."
    show_toast("🦥 SlothPFN Ambient Agent", script)
    threading.Thread(target=speak_aloud, args=(script, CURRENT_VOICE_ID), daemon=True).start()


def on_morning_greeting(icon, item):
    threading.Thread(target=morning_wake_up_briefing, args=(CURRENT_VOICE_ID,), daemon=True).start()


def make_voice_picker(voice_id: str, label: str):
    def _setter(icon, item):
        global CURRENT_VOICE_ID
        CURRENT_VOICE_ID = voice_id
        show_toast("🎭 Sloth Voice Changed", f"Selected: {label}")
    return _setter


def on_exit(icon, item):
    global WATCHER_OBSERVER
    if WATCHER_OBSERVER:
        try:
            WATCHER_OBSERVER.stop()
            WATCHER_OBSERVER.join(timeout=2)
        except Exception:
            pass
    icon.stop()


def setup_tray():
    global TRAY_ICON, WATCHER_OBSERVER

    icon_img = create_sloth_icon_image()

    # Build voice submenu
    voice_menu_items = [
        item(v["label"], make_voice_picker(v["voice_id"], v["name"]))
        for v in POPULAR_VOICES
    ]

    menu = Menu(
        item("🦥 SlothDesk (Ambient Agent)", lambda icon, item: None, enabled=False),
        item("🌐 Open Web Dashboard", on_open_dashboard, default=True),
        item("🔊 Speak Latest Briefing", on_speak_latest),
        item("🌅 Morning Wake-Up Greeting", on_morning_greeting),
        Menu.SEPARATOR,
        item("📂 Open Drop Folder", on_open_drop_folder),
        item("📥 Open Downloads Folder", on_open_downloads_folder),
        item("🎭 Voice Persona", Menu(*voice_menu_items)),
        Menu.SEPARATOR,
        item("❌ Exit SlothDesk", on_exit)
    )

    TRAY_ICON = pystray.Icon("SlothPFN", icon_img, "SlothPFN - Zero-Effort Tabular AI", menu)

    # Start folder watcher in background thread
    WATCHER_OBSERVER = start_ambient_watcher(blocking=False, voice_id=CURRENT_VOICE_ID)

    show_toast(
        "🦥 SlothDesk Ambient Agent Running",
        "Watching Downloads & drop_data. Right-click tray icon for options."
    )

    # Run the tray icon loop
    TRAY_ICON.run()


if __name__ == "__main__":
    setup_tray()
