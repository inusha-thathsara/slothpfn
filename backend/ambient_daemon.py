import os
import sys
import time
import json
import re
import argparse
import tempfile
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification

# Setup paths and environment
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Add ROOT_DIR to sys.path so imports resolve
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.predictor import predictor_instance
from backend.voice_agent import voice_agent_instance, DEFAULT_VOICE_ID

SESSION_FILE = ROOT_DIR / "active_session.json"
DROP_DATA_DIR = ROOT_DIR / "drop_data"
DROP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def play_audio_file_silent(file_path: str):
    """
    Plays an MP3/WAV file in the background on Windows using Media Player COM,
    without popping up any external window or player interface.
    """
    escaped_path = str(Path(file_path).resolve()).replace("'", "''")
    ps_script = f"""
    $wmp = New-Object -ComObject wmplayer.ocx
    $media = $wmp.newMedia('{escaped_path}')
    $wmp.currentPlaylist.appendItem($media)
    $wmp.controls.play()
    while ($wmp.playState -ne 1) {{ Start-Sleep -Milliseconds 200 }}
    """
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"[Audio Playback Error] {e}")


def speak_windows_native(text: str):
    """
    Native Windows text-to-speech fallback using System.Speech.
    Guarantees audio always speaks out loud even without an ElevenLabs API key.
    """
    clean = re.sub(r"[*_#`🦥⚡🌿]", "", text).replace('"', '`"')
    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 0
    $synth.Speak("{clean}")
    """
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"[Windows Speech Error] {e}")


def speak_aloud(text: str, voice_id: Optional[str] = None):
    """
    Speaks text out loud through PC speakers using ElevenLabs (or Windows native fallback).
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    clean_text = voice_agent_instance.clean_text_for_speech(text)

    # 1. Try ElevenLabs
    if voice_agent_instance.has_elevenlabs_key():
        try:
            client = voice_agent_instance.get_client()
            if client:
                target_voice = voice_id or voice_agent_instance.voice_id or DEFAULT_VOICE_ID
                audio_gen = client.text_to_speech.convert(
                    text=clean_text,
                    voice_id=target_voice,
                    model_id="eleven_flash_v2_5"
                )
                audio_bytes = b"".join(audio_gen)
                if audio_bytes:
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                        temp_path = f.name
                        f.write(audio_bytes)

                    play_audio_file_silent(temp_path)
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    return
        except Exception as e:
            print(f"[ElevenLabs Ambient Notice] {e}. Falling back to native Windows voice.")

    # 2. Windows Native Fallback
    speak_windows_native(clean_text)


def show_toast(title: str, message: str):
    """
    Displays a native Windows desktop toast notification without blocking.
    """
    t_clean = title.replace("'", "''").replace('"', '')
    m_clean = message.replace("'", "''").replace('"', '')
    ps_code = f"""
    [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.Visible = $true
    $notify.ShowBalloonTip(6000, '{t_clean}', '{m_clean}', [System.Windows.Forms.ToolTipIcon]::Info)
    Start-Sleep -Seconds 2
    $notify.Dispose()
    """
    def _run():
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def analyze_and_narrate_file(
    file_path: str,
    voice_id: Optional[str] = None,
    speak: bool = True,
    toast: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Zero-effort core: Ingests any CSV, detects schema, executes TabPFN,
    saves session state, speaks executive briefing, and pops toast.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        print(f"[Error] File not found: {path}")
        return None

    filename = path.name
    print(f"\n🦥 [SlothAmbient] Waking up to analyze: {filename}")

    try:
        # Load tabular data
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.read_csv(path, sep=None, engine="python")

        if len(df) == 0:
            print("[Warning] CSV has 0 rows.")
            return None

        # Inspect and auto-detect target
        inspection = predictor_instance.inspect_dataframe(df)
        target = inspection.get("probable_target")
        task = inspection.get("suggested_task", "classification")

        if not target:
            target = df.columns[-1]

        print(f"   • Detected Target: '{target}' | Task: '{task}' | Rows: {len(df)} | Columns: {len(df.columns)}")

        # Run TabPFN foundation inference
        result = predictor_instance.run_prediction_pipeline(
            df=df,
            target_column=target,
            task_type=task
        )
        result["filename"] = filename
        result["source_path"] = str(path)

        # Save session to shared disk state so web UI stays in sync
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "filename": filename,
                    "target_column": target,
                    "task_type": task,
                    "row_count": len(df),
                    "timestamp": time.time(),
                    "result": result
                }, f, indent=2)
        except Exception as e:
            print(f"[Session Save Warning] {e}")

        # Formulate Lazy Audio Briefing
        insights = result.get("sloth_insights", {})
        headline = insights.get("headline", f"Analyzed {filename}")
        top_drivers = result.get("feature_importance", [])[:2]
        top_driver_str = top_drivers[0]["feature"] if top_drivers else "key factors"
        time_saved = insights.get("time_saved", "45 minutes")
        metrics = result.get("metrics", {})
        tabpfn_speed = metrics.get("tabpfn", {}).get("inference_time_sec", "under a second")

        spoken_script = (
            f"SlothPFN detected a new dataset: {filename.replace('_', ' ')}. "
            f"{headline}. "
            f"TabPFN solved this in {tabpfn_speed} seconds without hyperparameter tuning loops. "
            f"The primary causal driver is {top_driver_str}. "
            f"You saved roughly {time_saved} of manual data science work. Now go take a break."
        )

        print(f"🦥 Verdict: {headline} (Top driver: {top_driver_str})")

        # Desktop notification
        if toast:
            show_toast(
                title=f"🦥 SlothPFN: {filename}",
                message=f"{headline} • Top driver: {top_driver_str} • Saved {time_saved}"
            )

        # Speak aloud
        if speak:
            print("🔊 Narrating audio briefing through speakers...")
            threading.Thread(
                target=speak_aloud,
                args=(spoken_script, voice_id),
                daemon=True
            ).start()

        return result

    except Exception as e:
        print(f"[Error analyzing file {filename}] {e}")
        return None


def morning_wake_up_briefing(voice_id: Optional[str] = None):
    """
    Scheduled Morning Wake-Up Briefing: Greet the user when they wake up / log in.
    """
    greeting = (
        "Good morning! While you were resting, SlothPFN kept an eye on your tabular data with TabPFN. "
        "All models are calibrated and ready. Go make your coffee; everything is under control."
    )
    show_toast("🌅 SlothPFN Morning Briefing", "All models calibrated with TabPFN. Go make coffee!")
    speak_aloud(greeting, voice_id=voice_id)


class SlothFileEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler that debounces and inspects newly downloaded or dropped CSVs.
    """
    def __init__(self, voice_id: Optional[str] = None):
        super().__init__()
        self.voice_id = voice_id
        self._recently_processed: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _should_process(self, path: Path) -> bool:
        if not path.is_file():
            return False
        if path.suffix.lower() not in [".csv", ".tsv"]:
            return False
        # Filter temp / browser downloading files
        name = path.name.lower()
        if any(name.endswith(ext) for ext in [".crdownload", ".tmp", ".part", ".download"]):
            return False
        if name.startswith("~$") or name.startswith("."):
            return False

        # Debounce: avoid processing same file repeatedly within 60s
        now = time.time()
        with self._lock:
            last_time = self._recently_processed.get(str(path), 0)
            if now - last_time < 60:
                return False
            self._recently_processed[str(path)] = now
        return True

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_process(path):
            self._schedule_analysis(path)

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_process(path):
            self._schedule_analysis(path)

    def _schedule_analysis(self, path: Path):
        def _delayed():
            # Wait 1.5 seconds for browser to finish writing file
            time.sleep(1.5)
            # Check if file size is stable
            try:
                size1 = path.stat().st_size
                time.sleep(0.5)
                size2 = path.stat().st_size
                if size1 == size2 and size1 > 0:
                    analyze_and_narrate_file(str(path), voice_id=self.voice_id)
            except Exception as e:
                print(f"[Watcher Delayed Read Notice] {e}")

        threading.Thread(target=_delayed, daemon=True).start()


def start_ambient_watcher(
    watch_dirs: Optional[List[str]] = None,
    voice_id: Optional[str] = None,
    blocking: bool = True
) -> Observer:
    """
    Starts the background watchdog observer watching Downloads and drop_data.
    """
    observer = Observer()
    handler = SlothFileEventHandler(voice_id=voice_id)

    # Resolve default watch directories
    if not watch_dirs:
        watch_dirs = [
            str(DROP_DATA_DIR),
            str(Path.home() / "Downloads")
        ]

    for d in watch_dirs:
        dir_path = Path(d).resolve()
        if dir_path.exists():
            print(f"👀 [Watcher] Monitoring folder: {dir_path}")
            observer.schedule(handler, str(dir_path), recursive=False)
        else:
            print(f"[Watcher Notice] Folder not found, skipped: {dir_path}")

    observer.start()

    show_toast(
        "🦥 SlothAmbient Watcher Active",
        f"Monitoring Downloads & drop_data. Drop any CSV to get voice briefing."
    )

    if blocking:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    return observer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SlothAmbient Zero-Touch Tabular Agent")
    parser.add_argument("--file", type=str, help="Analyze a specific CSV/TSV file (Windows Context Menu)")
    parser.add_argument("--watch", action="store_true", help="Start the ambient folder watcher")
    parser.add_argument("--morning", action="store_true", help="Trigger the Morning Wake-Up Briefing")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE_ID, help="ElevenLabs Voice ID")
    args = parser.parse_args()

    if args.file:
        analyze_and_narrate_file(args.file, voice_id=args.voice, speak=True, toast=True)
        # Keep process alive briefly so audio finishes playing
        time.sleep(12)
    elif args.morning:
        morning_wake_up_briefing(voice_id=args.voice)
        time.sleep(8)
    elif args.watch or len(sys.argv) == 1:
        start_ambient_watcher(voice_id=args.voice, blocking=True)
