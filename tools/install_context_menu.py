import os
import sys
import winreg
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "pythonw.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable).parent / "pythonw.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

DAEMON_SCRIPT = ROOT_DIR / "backend" / "ambient_daemon.py"


def install_context_menu():
    command_str = f'"{PYTHON_EXE}" "{DAEMON_SCRIPT}" --file "%1"'

    for ext in [".csv", ".tsv"]:
        key_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell\\SlothAnalyze"
        try:
            # 1. Create verb key
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "🦥 Analyze with SlothPFN")
            winreg.CloseKey(key)

            # 2. Create command key
            cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command_str)
            winreg.CloseKey(cmd_key)

            print(f"✅ Registered Context Menu for {ext}: 🦥 Analyze with SlothPFN")
        except Exception as e:
            print(f"❌ Failed to register for {ext}: {e}")

    print("\n🎉 Windows Explorer context menu installed successfully!")
    print("👉 Right-click any CSV or TSV file and select '🦥 Analyze with SlothPFN'.")


def uninstall_context_menu():
    for ext in [".csv", ".tsv"]:
        key_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell\\SlothAnalyze"
        try:
            # Delete subkey first
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
            except FileNotFoundError:
                pass
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            print(f"🗑️ Removed Context Menu for {ext}")
        except FileNotFoundError:
            print(f"ℹ️ {ext} context menu was not installed.")
        except Exception as e:
            print(f"❌ Failed to uninstall for {ext}: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall_context_menu()
    else:
        install_context_menu()
