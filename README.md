---
title: SlothPFN Zero Effort Tabular AI
emoji: 🦥
colorFrom: yellow
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🦥 SlothPFN: Zero-Effort Tabular AI Agent with TabPFN

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-Week%203%20Challenge-orange?style=for-the-badge&logo=hacktoberfest)](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)
[![Prior Labs TabPFN](https://img.shields.io/badge/AI%20Core-Prior%20Labs%20TabPFN-blueviolet?style=for-the-badge)](https://priorlabs.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **"Channel your inner sloth. Build something that does the work so you don't have to."**  
> *Submitted for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19) & the **Best Use of TabPFN** Partner Track.*

![SlothPFN Hero Banner](https://raw.githubusercontent.com/inusha-thathsara/slothpfn/main/docs/images/sloth_hero_banner.png)

---

## 🌟 Executive Summary

Traditional tabular machine learning is exhausting. Before you can evaluate a single prediction, you are forced into a tedious gauntlet:
- Imputing missing values
- Encoding categorical strings (One-Hot, Target, Ordinal)
- Scaling numeric distributions
- Iterating through hyperparameter grids (tree depths, learning rates, subsamples)
- Cross-validation splits and overfitting checks

**SlothPFN changes the game.** Powered by Prior Labs' open-weight **TabPFN** (Prior-data Fitted Network) foundation model, SlothPFN allows developers and analysts to drop any raw CSV and do **literally nothing**. 

In less than 2 seconds, SlothPFN's pre-trained Bayesian transformer infers column semantics, auto-detects classification or regression objectives, calculates calibrated class probabilities, and serves a modern, interactive dashboard with an interactive "What-If" scenario simulator.

---

## ✨ Key Features

1. **🦥 SlothAmbient: The Zero-Touch Suite for Lazy Data People**:
   - **Windows 1-Click Context Menu**: Right-click any `.csv` or `.tsv` in Windows Explorer -> `🦥 Analyze with SlothPFN`. Never type a URL or drag a file again.
   - **Automated Folder Watchdog**: Watches `drop_data/` and your `Downloads/` directory in the background. The second a CSV lands on your machine, SlothPFN wakes up, runs Bayesian inference, and syncs results.
   - **System Tray Resident Agent**: Lives peacefully in the Windows taskbar tray with dynamic sloth icon, 1-click audio replay, voice persona switcher, and direct folder shortcuts.
   - **Ambient "Hey Sloth" Voice-Wake**: Hands-free voice trigger on the dashboard. Simply say *"Hey Sloth..."* to query causal drivers or request a lazy briefing without touching keyboard or mouse.
   - **Morning Wake-Up Briefing**: Automatically delivers an audio executive summary of your freshest datasets when you start your day.
2. **Zero-Touch Ingestion & Target Inference**:
   - Drag & drop any CSV or launch with 1-click built-in realistic datasets (Customer Churn, Real Estate Valuation, Cardiac Health Risk).
   - Intelligently filters uninformative IDs and determines whether the objective is classification or continuous regression.
3. **Prior Labs TabPFN-3.5 Foundation Model**:
   - Uses pre-trained causal Bayesian transformer priors to produce calibrated posterior probabilities in a single forward pass without iterative gradient descent.
   - Dual-engine support: Connect your free Prior Labs token for live TabPFN-3.5 weights with Thinking Mode, or test offline using the local demo prior simulator.
4. **Sloth vs Traditional Baseline Benchmark**:
   - Instant head-to-head comparison against classical Random Forest / Gradient Boosting baselines.
   - Highlights inference latency, accuracy/R², and estimated time saved.
5. **Explainable "Lazy Insights"**:
   - Natural language executive summaries explaining the top causal feature drivers in plain English.
6. **🎙️ Sloth Voice Agent & Audio Briefing (Official ElevenLabs SDK Integration)**:
   - **Real-Time Streaming Briefing**: 1-click "Listen to Sloth Briefing" audio summary of TabPFN predictions, causal drivers, and time saved, streamed via chunked transfer with sub-second time-to-first-byte.
   - **Interactive Conversational Tabular Q&A**: Ask questions about feature importance, baseline accuracy, or dataset takeaways.
   - **🎤 Hands-Free Microphone Input (Speech-to-Text)**: Speak your questions directly to the agent using the integrated microphone button or ambient "Hey Sloth" voice detection.
   - **🎭 Multi-Voice Persona Selector**: Easily switch narrator voices on the fly:
     - *George (Calm)* — Warm, relaxed British narrator.
     - *Sarah (Gentle)* — Friendly, conversational tone.
     - *Daniel (Analyst)* — Authoritative, professional delivery.
     - *Charlotte (Dynamic)* — Expressive and bright.
   - **Dual-Engine Graceful Fallback**: Automatically switches to the browser's native Web Speech API (`window.speechSynthesis`) if no API key is supplied, guaranteeing a working experience for everyone.
7. **Interactive What-If Scenario Simulator**:
   - Real-time sliders and selectors for all feature attributes.
   - Instant live posterior recalculation with probability distribution meters.
8. **Minimalist, Text-Clutter-Free UI**:
   - Built specifically for lazy builders who hate walls of text. Clean glassmorphic design system with punchy, actionable metrics.
9. **Comprehensive 11-Test Audit Suite**:
   - Automated test coverage across FastAPI endpoints, TabPFN inference, scenario simulation, and ElevenLabs audio streaming (`tests/test_audit_suite.py`).

📖 **Looking for a full step-by-step walkthrough? Check out the [User Guide](docs/USER_GUIDE.md)!**

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### 2. Clone & Setup Virtual Environment
```bash
git clone https://github.com/inusha-thathsara/slothpfn.git
cd slothpfn

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application

#### 🦥 Option A: The Truly Lazy Way (Windows 1-Click)
Simply double-click `run_sloth.bat` in the repository root:
- Automatically starts the FastAPI backend in the background.
- Spawns the Sloth System Tray Agent (with audio briefing replay and voice switcher).
- Activates the `drop_data/` folder watchdog.
- Opens your default web browser to `http://127.0.0.1:8000`.

#### Option B: Manual Command Line
```bash
# Start FastAPI and the Web Dashboard
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🖱️ Windows 1-Click Context Menu Integration

For the ultimate zero-touch workflow, integrate SlothPFN directly into Windows Explorer:

1. Double-click `tools\install_context_menu.bat` (or run `python tools/install_context_menu.py`).
2. Right-click **any** `.csv` or `.tsv` file anywhere on your computer.
3. Click **"🦥 Analyze with SlothPFN"**.

SlothPFN will wake up in the background, infer targets, run TabPFN prior inference, save the session, pop a desktop toast notification, narrate the executive briefing through your speakers, and automatically display the results on your dashboard!

*(To remove the right-click menu at any time, run `tools\uninstall_context_menu.bat`).*

---

## 🔑 Authentication & Environment Setup (Optional via `.env`)

SlothPFN works immediately out of the box in **Prior Simulator & Browser Speech Mode**. To connect live TabPFN-3.5 foundation weights and official ElevenLabs AI Voice:

### 1. Prior Labs TabPFN Token:
- Register at [ux.priorlabs.ai](https://ux.priorlabs.ai) (or [priorlabs.ai](https://priorlabs.ai)).
- Under **Licenses**, accept the non-commercial license for model weights.
- Copy your access token from [ux.priorlabs.ai/account](https://ux.priorlabs.ai/account) and paste it into `.env`:
  ```env
  TABPFN_TOKEN=your_tabpfn_api_key_here
  ```

### 2. ElevenLabs Voice Agent Setup:
- **Interactive Onboarding (Recommended)**: Run the official CLI from your project directory:
  ```bash
  npx -y @elevenlabs/cli@latest onboard init
  ```
  Follow the prompt to connect your ElevenLabs account and automatically configure `.env`.
- **Manual Setup**: Add your key directly into `.env`:
  ```env
  ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
  ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb  # Default: George (Calm Sloth Narrator)
  ```

SlothPFN dynamically reloads environment keys upon startup and on incoming requests. If no keys are configured, SlothPFN seamlessly operates with its built-in Prior Simulator and browser SpeechSynthesis engine.

---

## 📁 Repository Structure

```
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI server, REST API, streaming & transcription endpoints
│   ├── predictor.py         # TabPFN foundation engine, feature encoding & simulator
│   ├── voice_agent.py       # Official ElevenLabs SDK integration, streaming & Q&A
│   ├── ambient_daemon.py    # Zero-touch background daemon: folder watchdog & audio toast
│   ├── tray_agent.py        # Windows system tray app, morning wake-up & quick controls
│   └── dataset_samples.py   # One-click sample datasets catalog
├── frontend/
│   ├── index.html           # Dark-mode dashboard with 'Hey Sloth' wake & mic STT
│   ├── style.css            # Glassmorphic CSS design system, voice pulses & badges
│   └── app.js               # Reactive state, ambient session sync, wake word & Chart.js
├── tools/
│   ├── install_context_menu.py    # HKCU context menu installer (no admin needed)
│   ├── install_context_menu.bat   # 1-Click installer
│   ├── uninstall_context_menu.bat # 1-Click uninstaller
│   └── stop_sloth.bat             # Cleanly stop background Sloth processes
├── drop_data/               # Drop any CSV here for instant background analysis
├── sample_data/
│   ├── telecom_customer_churn.csv
│   ├── housing_prices.csv
│   └── heart_disease_risk.csv
├── run_sloth.bat            # 1-Click Windows desktop suite launcher
├── chat_history/            # Preserved Antigravity session transcripts & audits
├── active_session.json      # Shared ambient state between background daemons & web UI
├── requirements.txt         # Pinned Python dependencies (TabPFN, ElevenLabs, Watchdog, Pystray)
├── LICENSE                  # MIT License
└── README.md                # Documentation
```

---

## 💡 Why Open Innovation Matters

In enterprise and personal machine learning, tabular data frequently contains sensitive, proprietary information: patient vitals, customer financial history, private logs, and pricing data.

Sending raw tabular records across closed third-party cloud APIs presents significant privacy, compliance (GDPR/HIPAA), and cost risks. Open-source tabular foundation models like **TabPFN** prove that world-class Bayesian inference can run **entirely locally on commodity hardware**, offline, with zero subscription fees, empowering builders with true digital sovereignty.

---

## 🏆 Hacktoberfest Week 3 Challenge Alignment

- **Prompt:** Build something with open-source AI at its core.
- **Theme:** *Slow and Steady* (rewards laziness by automating tedious manual data science workflows).
- **Partner Track:** Best Use of TabPFN (Prior Labs $200 prize category).
- **Required Tags:** `#devchallenge`, `#hf26challenge`

---

## 📜 License
Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
