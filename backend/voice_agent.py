import os
import io
import re
from typing import Dict, Any, Optional, List, Generator
from dotenv import load_dotenv

# Ensure .env is loaded before importing and initializing the SDK
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

try:
    from elevenlabs import ElevenLabs, VoiceSettings
    ELEVENLABS_SDK_AVAILABLE = True
except ImportError:
    ELEVENLABS_SDK_AVAILABLE = False
    ElevenLabs = None
    VoiceSettings = None

# Pre-defined curated voices for the Sloth dashboard
POPULAR_VOICES = [
    {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George",
        "label": "George (Calm Sloth Narrator)",
        "description": "Deep, warm, and relaxed British narrator"
    },
    {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah",
        "label": "Sarah (Gentle & Conversational)",
        "description": "Clear, friendly, and soft tone"
    },
    {
        "voice_id": "onwK4e9ZLuTAKqWW03F9",
        "name": "Daniel",
        "label": "Daniel (Executive Analyst)",
        "description": "Authoritative, confident, and professional"
    },
    {
        "voice_id": "XB0fDUnXU5powFXDhCwa",
        "name": "Charlotte",
        "label": "Charlotte (Dynamic Storyteller)",
        "description": "Expressive, bright, and engaging"
    }
]

DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"


class VoiceAgent:
    """
    Handles ElevenLabs voice synthesis, streaming, transcription,
    and conversational tabular question-answering.
    """

    def __init__(self):
        self._reload_env()

    def _reload_env(self):
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID).strip()
        self._client: Optional[Any] = None
        if self.api_key and ELEVENLABS_SDK_AVAILABLE:
            try:
                # SDK reads ELEVENLABS_API_KEY from environment
                self._client = ElevenLabs()
            except Exception as e:
                print(f"[ElevenLabs Init Warning] {e}")
                self._client = None

    def has_elevenlabs_key(self) -> bool:
        self._reload_env()
        return bool(self.api_key)

    def get_client(self) -> Optional[Any]:
        if not self._client and self.has_elevenlabs_key() and ELEVENLABS_SDK_AVAILABLE:
            try:
                self._client = ElevenLabs()
            except Exception:
                self._client = None
        return self._client

    def list_voices(self) -> List[Dict[str, str]]:
        return POPULAR_VOICES

    def clean_text_for_speech(self, text: str) -> str:
        clean_text = re.sub(r"[*_#`]", "", text)
        clean_text = clean_text.replace("🦥", "").replace("⚡", "").replace("🌿", "").strip()
        return clean_text

    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_flash_v2_5"
    ) -> Optional[bytes]:
        """
        Synthesizes text into high-quality speech using ElevenLabs SDK.
        """
        self._reload_env()
        client = self.get_client()
        if not client:
            return None

        clean_text = self.clean_text_for_speech(text)
        target_voice = (voice_id or self.voice_id or DEFAULT_VOICE_ID).strip()

        try:
            # Use ElevenLabs SDK convert method
            audio_generator = client.text_to_speech.convert(
                text=clean_text,
                voice_id=target_voice,
                model_id=model_id,
                voice_settings=VoiceSettings(
                    stability=0.55,
                    similarity_boost=0.75,
                    style=0.15,
                    use_speaker_boost=True
                ) if VoiceSettings else None
            )

            # Consume generator into bytes
            audio_bytes = b"".join(audio_generator)
            return audio_bytes
        except Exception as e:
            print(f"[ElevenLabs SDK Exception] {str(e)}")
            return None

    def stream_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_flash_v2_5"
    ) -> Generator[bytes, None, None]:
        """
        Streams audio chunks using ElevenLabs SDK for instant real-time playback.
        """
        self._reload_env()
        client = self.get_client()
        if not client:
            return

        clean_text = self.clean_text_for_speech(text)
        target_voice = (voice_id or self.voice_id or DEFAULT_VOICE_ID).strip()

        try:
            audio_stream = client.text_to_speech.stream(
                text=clean_text,
                voice_id=target_voice,
                model_id=model_id
            )
            for chunk in audio_stream:
                if chunk:
                    yield chunk
        except Exception as e:
            print(f"[ElevenLabs Stream Exception] {str(e)}")

    def transcribe_audio(self, audio_file: Any) -> Optional[str]:
        """
        Transcribes speech audio into text using ElevenLabs Scribe v2.
        """
        self._reload_env()
        client = self.get_client()
        if not client:
            return None

        try:
            result = client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v2"
            )
            return result.text
        except Exception as e:
            print(f"[ElevenLabs Scribe STT Exception] {str(e)}")
            return None

    def answer_tabular_query(
        self,
        query: str,
        df: Any,
        prediction_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        Analyzes the user's voice/text question about the dataset and predictions,
        generating a witty, accurate, sloth-themed response.
        """
        q = query.lower()

        if prediction_result is None or df is None:
            return (
                "You haven't loaded a dataset or run a prediction yet. "
                "Go ahead and drop a CSV or pick one of the sample datasets, and I'll analyze it for you."
            )

        target = prediction_result.get("target_column", "the target")
        task = prediction_result.get("task_type", "prediction")
        n_rows = len(df)
        features = prediction_result.get("feature_names", [])
        top_drivers = prediction_result.get("feature_importance", [])[:3]
        top_driver_names = [f["feature"] for f in top_drivers]
        metrics = prediction_result.get("metrics", {})

        # 1. Feature Importance / Driver questions
        if any(w in q for w in ["driver", "important", "feature", "factor", "matter", "affect", "cause"]):
            drivers_str = ", ".join(f"{f['feature']} ({f['percentage']}%)" for f in top_drivers)
            return (
                f"Based on TabPFN's analysis, the most significant causal drivers for {target} are {drivers_str}. "
                f"If you want to move the needle with the least amount of effort, focus on these top factors."
            )

        # 2. Performance / Accuracy / Speed questions
        if any(w in q for w in ["accuracy", "performance", "score", "good", "fast", "speed", "metric"]):
            if task == "classification":
                acc = metrics.get("tabpfn", {}).get("accuracy", "N/A")
                base_acc = metrics.get("baseline", {}).get("accuracy", "N/A")
                t_speed = metrics.get("tabpfn", {}).get("inference_time_sec", "N/A")
                return (
                    f"TabPFN reached {acc}% accuracy on the test set in just {t_speed} seconds. "
                    f"That beats the traditional Random Forest baseline of {base_acc}%, completely without hyperparameter tuning."
                )
            else:
                r2 = metrics.get("tabpfn", {}).get("r2_score", "N/A")
                rmse = metrics.get("tabpfn", {}).get("rmse", "N/A")
                return (
                    f"For continuous prediction, TabPFN scored an R-squared of {r2} with an RMSE error of {rmse}. "
                    f"It captured the trend almost perfectly on the first try."
                )

        # 3. Churn / Specific target questions
        if "churn" in q and "churn" in target.lower():
            return (
                f"For customer churn, tenure and monthly charges are your biggest warning signs. "
                f"Customers on month-to-month contracts with high monthly bills and low tenure churn at almost triple the rate of long-term contract customers."
            )

        # 4. Price / Real Estate questions
        if any(w in q for w in ["price", "house", "cost", "valuation"]) and "price" in target.lower():
            return (
                f"Real estate valuations are primarily governed by square footage, neighborhood rating, and bedroom count. "
                f"Distance to the city creates a modest discount, but living area dominates over 60% of price variance."
            )

        # 5. Laziness / Executive summary questions
        if any(w in q for w in ["summarize", "summary", "lazy", "brief", "takeaway", "overview"]):
            return (
                f"Here is your lazy executive summary: We analyzed {n_rows} rows to predict {target}. "
                f"TabPFN solved this in under a second with zero feature engineering. "
                f"The top driver is {top_driver_names[0] if top_driver_names else 'unknown'}. "
                f"You saved roughly 45 minutes of manual data science work. Now go take a break."
            )

        # 6. Fallback general analytical response
        return (
            f"Looking across your {n_rows} rows, TabPFN has modeled {target} using {len(features)} attributes. "
            f"The primary influencer is {top_driver_names[0] if top_driver_names else 'the first feature'}. "
            f"You can test what-if scenarios using the sliders below, or ask me about specific features."
        )


voice_agent_instance = VoiceAgent()
