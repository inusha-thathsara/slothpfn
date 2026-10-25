# 🦥 SlothPFN: Complete User Guide

> **"Channel your inner sloth. Build something that does the hard work so you don't have to."**

Welcome to the **SlothPFN User Guide**. SlothPFN is an autonomous, zero-effort tabular AI system that combines **Prior Labs' TabPFN-3.5** foundation model with **ElevenLabs streaming voice narration** and a background Windows ambient desktop daemon.

This guide walks you through every feature, workflow, and setting available in SlothPFN.

---

## 📑 Table of Contents

1. [Quickstart in 60 Seconds](#1-quickstart-in-60-seconds)
2. [Zero-Touch Desktop Workflows](#2-zero-touch-desktop-workflows)
   - [Windows Explorer Right-Click Integration](#windows-explorer-right-click-integration)
   - [Drop Folder Watchdog (`drop_data/`)](#drop-folder-watchdog-drop_data)
   - [System Tray Resident Agent](#system-tray-resident-agent)
3. [Web Dashboard Tour](#3-web-dashboard-tour)
   - [1-Click Sample Datasets](#1-click-sample-datasets)
   - [Drag & Drop Upload](#drag--drop-upload)
   - [Target Inference & One-Click Prediction](#target-inference--one-click-prediction)
   - [Results, Metrics & Benchmark](#results-metrics--benchmark)
   - [Voice Agent & Narration Personas](#voice-agent--narration-personas)
   - [Hands-Free "Hey Sloth" Voice Wake](#hands-free-hey-sloth-voice-wake)
   - [Interactive "What-If" Scenario Simulator](#interactive-what-if-scenario-simulator)
   - [Export Predictions](#export-predictions)
4. [Environment & Keys Configuration (`.env`)](#4-environment--keys-configuration-env)
   - [Prior Labs TabPFN-3.5 Token](#prior-labs-tabpfn-35-token)
   - [ElevenLabs AI Voice Setup](#elevenlabs-ai-voice-setup)
5. [Running the Audit Test Suite](#5-running-the-audit-test-suite)
6. [Stopping Background Services & Uninstalling](#6-stopping-background-services--uninstalling)

---

## 1. ⚡ Quickstart in 60 Seconds

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git (optional if downloading as ZIP)

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/inusha-thathsara/slothpfn.git
cd slothpfn

# 2. Create and activate virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Launching the Full Suite
Double-click `run_sloth.bat` in the repository root. This 1-click launcher:
1. Starts the FastAPI server on `http://127.0.0.1:8000`.
2. Starts the background file-watchdog daemon on `drop_data/`.
3. Minimizes a resident Sloth icon in your Windows system tray.
4. Opens your default web browser to the dashboard.

*(Manual alternative: `uvicorn backend.main:app --port 8000 --reload`)*

---

## 2. 🖱️ Zero-Touch Desktop Workflows

SlothPFN was designed for users who never want to open a command line or type a URL.

### Windows Explorer Right-Click Integration
1. Double-click `tools\install_context_menu.bat` (or run `python tools/install_context_menu.py`).
   *(Installs cleanly into `HKEY_CURRENT_USER\Software\Classes` without requiring administrator privileges).*
2. Open Windows File Explorer and locate any `.csv` or `.tsv` file.
3. Right-click the file and select **"🦥 Analyze with SlothPFN"**.

**What happens automatically:**
- SlothPFN wakes up in the background.
- It detects the target column and task type (classification vs regression).
- TabPFN executes a single-pass Bayesian inference in ~200ms.
- A Windows desktop notification appears with accuracy and time saved.
- An audio briefing is spoken aloud through your PC speakers.
- Your browser opens directly to the results dashboard with the full interactive simulator pre-loaded.

---

### Drop Folder Watchdog (`drop_data/`)
- Simply copy, save, or drag any CSV file into the `drop_data/` folder in the project root.
- The background watchdog detects the file arrival, waits for write completion, and automatically triggers the complete TabPFN analysis pipeline.

---

### System Tray Resident Agent
SlothPFN lives quietly in your Windows notification tray (taskbar icons):
- **Right-click the Sloth tray icon** to:
  - 🔄 **Replay Last Briefing**: Hear your last dataset's voice summary again.
  - 🎭 **Change Voice Persona**: Switch between George, Sarah, Daniel, and Charlotte.
  - 📁 **Open Drop Folder**: Instant shortcut to `drop_data/`.
  - 🌐 **Open Web Dashboard**: Quick 1-click link to `http://127.0.0.1:8000`.
  - ❌ **Exit**: Safely terminates background background daemons.

---

## 3. 🌐 Web Dashboard Tour

![SlothPFN Dashboard](https://raw.githubusercontent.com/inusha-thathsara/slothpfn/main/docs/images/sloth_hero_banner.png)

### 1-Click Sample Datasets
At the top of the dashboard, you will find 3 pre-loaded datasets:
- **📞 Customer Churn**: Telecom customer attrition prediction (Classification).
- **🏡 Housing Prices**: Property market valuation (Continuous Regression).
- **❤️ Cardiac Risk**: Clinical cardiovascular risk detection (Classification).

Clicking any sample instantly parses the schema without uploading anything.

### Drag & Drop Upload
Drop any custom `.csv` or `.tsv` onto the upload zone. SlothPFN inspects the schema, detects missing values, and identifies the best target column automatically.

### Results, Metrics & Benchmark
Once you click **⚡ Predict**, the dashboard displays:
- **Executive Callout Card**:
  - Model latency and estimated manual tuning time saved.
  - Top causal feature drivers ranked by relative importance percentage.
  - Sloth verdict and recommendation.
- **Side-by-Side Benchmark**:
  - **TabPFN**: Accuracy/R² and inference speed.
  - **Baseline**: Classical Scikit-Learn Random Forest fitted on the same split.
  - **Advantage**: Speedup factor and metric comparison.
- **Interactive Visualizations**:
  - Horizontal bar chart of top causal feature drivers.
  - Confusion Matrix (for classification) or Predicted vs Actual scatter distribution (for regression).
- **Predictions Preview Table**:
  - Ground truth vs TabPFN zero-shot prediction for holdout records with individual confidence percentages.
  - 📥 **Export CSV Button**: Download the test set predictions directly.

---

### Voice Agent & Narration Personas
Click the **🎙️ Listen** button in the results card to hear a spoken executive summary.

You can switch narrator personas using the dropdown:
- **George (Calm)**: Warm, relaxed British narrator (*Recommended*).
- **Sarah (Gentle)**: Friendly and conversational.
- **Daniel (Analyst)**: Authoritative executive briefing.
- **Charlotte (Dynamic)**: Bright and expressive.

*Note: If no ElevenLabs API key is configured in `.env`, the browser gracefully falls back to native Web Speech API synthesis.*

---

### Hands-Free "Hey Sloth" Voice Wake
Toggle the **🎙️ "Hey Sloth"** switch in the bottom card:
1. Allow microphone permissions in your browser.
2. Say aloud: *"Hey Sloth, what are the top drivers?"*
3. The dashboard detects the wake-phrase, captures your question, and reads the answer aloud.

Alternatively, type your query into the text box or use the quick query chips:
- **Drivers**: Asks which features most heavily influence the target.
- **Baseline**: Inquires how TabPFN compares against the classical Random Forest baseline.
- **Summary**: Requests a concise conversational summary.

---

### Interactive "What-If" Scenario Simulator
Located just above the voice bar:
1. Adjust the sliders or categorical dropdowns for any feature attribute.
2. Click **⚡ Recalculate**.
3. TabPFN instantly recalculates the posterior class probabilities on the fly, animating the live probability meter without retraining!

---

## 4. 🔑 Environment & Keys Configuration (`.env`)

SlothPFN works immediately out of the box in **Prior Simulator Mode** and **Web Speech Fallback Mode**.

To connect official foundation model weights and high-fidelity ElevenLabs voice streaming:

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Prior Labs TabPFN-3.5 Token
1. Register at [ux.priorlabs.ai](https://ux.priorlabs.ai) (or [priorlabs.ai](https://priorlabs.ai)).
2. Accept the non-commercial license on the **Licenses** tab.
3. Copy your API Key from [ux.priorlabs.ai/account](https://ux.priorlabs.ai/account).
4. Paste it into `.env`:
   ```env
   TABPFN_TOKEN=your_priorlabs_token_here
   ```

### ElevenLabs AI Voice Setup
1. Register at [elevenlabs.io](https://elevenlabs.io).
2. Copy your API Key from your profile settings.
3. Paste it into `.env`:
   ```env
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb  # George: Calm Sloth Narrator
   ```

*(Keys are hot-reloaded automatically by SlothPFN without restarting the server).*

---

## 5. 🧪 Running the Audit Test Suite

SlothPFN includes a comprehensive 11-test audit suite covering:
- API health and sample dataset loading.
- CSV parsing and target inference.
- Classification & regression prediction pipelines.
- What-If scenario simulation.
- ElevenLabs streaming audio endpoints.
- Speech-to-text audio transcription.

To run the suite:
```bash
python -m unittest tests/test_audit_suite.py
```

Expected output:
```
...........
----------------------------------------------------------------------
Ran 11 tests in ~17s

OK
```

---

## 6. 🛑 Stopping Background Services & Uninstalling

- **To cleanly stop all background processes:**
  Double-click `tools\stop_sloth.bat`. This gracefully terminates any running Uvicorn server, watchdog daemons, and system tray icons.

- **To remove the right-click context menu:**
  Double-click `tools\uninstall_context_menu.bat`. This cleanly removes the registry key from `HKEY_CURRENT_USER`.

---

*Enjoy your lazy data science journey with SlothPFN! 🦥☕*
