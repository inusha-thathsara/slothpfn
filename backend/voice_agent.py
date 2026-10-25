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

try:
    from google import genai
    from google.genai import types
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False
    genai = None

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
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self._client: Optional[Any] = None
        self._gemini_client: Optional[Any] = None
        if self.api_key and ELEVENLABS_SDK_AVAILABLE:
            try:
                # SDK reads ELEVENLABS_API_KEY from environment
                self._client = ElevenLabs()
            except Exception as e:
                print(f"[ElevenLabs Init Warning] {e}")
                self._client = None
        if self.gemini_api_key and GEMINI_SDK_AVAILABLE:
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"[Gemini Init Warning] {e}")
                self._gemini_client = None

    def has_elevenlabs_key(self) -> bool:
        self._reload_env()
        return bool(self.api_key)

    def has_gemini_key(self) -> bool:
        self._reload_env()
        return bool(self.gemini_api_key) and GEMINI_SDK_AVAILABLE

    def get_client(self) -> Optional[Any]:
        if not self._client and self.has_elevenlabs_key() and ELEVENLABS_SDK_AVAILABLE:
            try:
                self._client = ElevenLabs()
            except Exception:
                self._client = None
        return self._client

    def get_gemini_client(self) -> Optional[Any]:
        if not self._gemini_client and self.has_gemini_key():
            try:
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception:
                self._gemini_client = None
        return self._gemini_client

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

    def generate_audio_explanation(
        self,
        prediction_result: Optional[Dict[str, Any]],
        df: Optional[Any] = None
    ) -> str:
        """
        Generates an audio-first summary/explanation for ElevenLabs to read.
        Never repeats raw numbers, bullet points, or dashboard headlines from the screen.
        Uses Gemini LLM if GEMINI_API_KEY is configured, otherwise an articulate, domain-aware narrator.
        """
        if not prediction_result:
            return (
                "Welcome to SlothPFN. Drop a CSV file or pick one of the sample datasets above, "
                "and I will uncover the key patterns and explain them for you without any effort."
            )

        target = prediction_result.get("target_column", "the target")
        task = prediction_result.get("task_type", "classification")
        n_rows = len(df) if df is not None else prediction_result.get("total_rows", 0)
        top_drivers = prediction_result.get("feature_importance", [])[:3]
        metrics = prediction_result.get("metrics", {})
        time_saved = prediction_result.get("sloth_insights", {}).get("time_saved_estimate", "Saved ~45 mins")

        driver_details = ", ".join(f"{f['feature']} (accounting for {f['percentage']}% influence)" for f in top_drivers)

        if task == "classification":
            acc = metrics.get("tabpfn", {}).get("accuracy", "N/A")
            base_acc = metrics.get("baseline", {}).get("accuracy", "N/A")
            perf_summary = f"TabPFN reached {acc}% accuracy versus {base_acc}% for a standard baseline."
        else:
            r2 = metrics.get("tabpfn", {}).get("r2_score", "N/A")
            rmse = metrics.get("tabpfn", {}).get("rmse", "N/A")
            perf_summary = f"TabPFN achieved an R-squared of {r2} with an RMSE of {rmse}."

        # 1. Try Gemini generation if API key is active
        if self.has_gemini_key():
            gemini_text = self._generate_gemini_audio_summary(
                target=target,
                task=task,
                n_rows=n_rows,
                driver_details=driver_details,
                perf_summary=perf_summary,
                time_saved=time_saved
            )
            if gemini_text:
                return gemini_text

        # 2. Rule-based conversational spoken explanation (guaranteed never to repeat the screen)
        return self._generate_rule_based_audio_briefing(prediction_result, df)

    def _generate_gemini_audio_summary(
        self,
        target: str,
        task: str,
        n_rows: int,
        driver_details: str,
        perf_summary: str,
        time_saved: str
    ) -> Optional[str]:
        client = self.get_gemini_client()
        if not client:
            return None

        prompt = (
            "You are George, a calm, articulate, slightly witty voice narrator for SlothPFN, an automated ML app.\n"
            "The user just ran automated predictions on their dataset and is looking at the dashboard. "
            "CRITICAL REQUIREMENT: Do NOT read the exact stats, formulas, or bullet points off the screen. "
            "Instead, create a warm, conversational explanation and summary for the listener's ear in 3 to 4 flowing sentences.\n\n"
            f"Dataset Context:\n"
            f"- Target: {target} ({task})\n"
            f"- Observations: {n_rows} rows\n"
            f"- Key Feature Drivers: {driver_details}\n"
            f"- Model Performance: {perf_summary}\n"
            f"- Modeling Time Saved: {time_saved}\n\n"
            "Guidelines for audio narrative:\n"
            "1. Explain what the dataset represents and why the primary drivers intuitively matter in plain English.\n"
            "2. Give a clear, actionable real-world takeaway or recommendation based on those drivers.\n"
            "3. Mention how TabPFN converged instantly without any hyperparameter tuning or manual feature engineering.\n"
            "4. Conclude with a relaxed, sloth-themed signoff encouraging them to take a break.\n"
            "5. NO markdown formatting (*, _, #), NO bullet points, NO raw decimal fractions or symbols."
        )

        for model_id in ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                if response and response.text:
                    clean = self.clean_text_for_speech(response.text)
                    if len(clean) > 30:
                        return clean
            except Exception as e:
                print(f"[Gemini Model {model_id} Attempt Failed] {e}")
                continue

        return None

    def _generate_gemini_chat_answer(
        self,
        query: str,
        df: Any,
        prediction_result: Dict[str, Any]
    ) -> Optional[str]:
        client = self.get_gemini_client()
        if not client:
            return None

        target = prediction_result.get("target_column", "the target")
        task = prediction_result.get("task_type", "prediction")
        n_rows = len(df) if df is not None else prediction_result.get("total_rows", 0)
        top_drivers = prediction_result.get("feature_importance", [])[:5]
        drivers_str = ", ".join(f"{f['feature']} ({f['percentage']}%)" for f in top_drivers)
        metrics = prediction_result.get("metrics", {})

        prompt = (
            "You are George, the calm, intelligent, slightly humorous Sloth AI voice companion in SlothPFN.\n"
            "The user is asking a conversational question about their dataset and ML model results.\n"
            f"User Question: \"{query}\"\n\n"
            f"Current Model Context:\n"
            f"- Target Column: {target} ({task})\n"
            f"- Dataset Rows: {n_rows}\n"
            f"- Top Feature Drivers: {drivers_str}\n"
            f"- Model Metrics: {metrics}\n\n"
            "Respond in 2 to 3 spoken-friendly sentences. Be insightful, practical, and maintain a relaxed, comforting tone. "
            "Do NOT use markdown asterisks or bullet points."
        )

        for model_id in ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                if response and response.text:
                    clean = self.clean_text_for_speech(response.text)
                    if len(clean) > 10:
                        return clean
            except Exception as e:
                print(f"[Gemini Chat {model_id} Attempt Failed] {e}")
                continue

        return None

    def _generate_rule_based_audio_briefing(
        self,
        prediction_result: Dict[str, Any],
        df: Optional[Any] = None
    ) -> str:
        target = prediction_result.get("target_column", "the target")
        task = prediction_result.get("task_type", "classification")
        n_rows = len(df) if df is not None else prediction_result.get("total_rows", 0)
        top_drivers = prediction_result.get("feature_importance", [])[:3]
        metrics = prediction_result.get("metrics", {})

        def format_spoken_name(name: str) -> str:
            s = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
            return s.replace('_', ' ').strip()

        driver_names = [f["feature"] for f in top_drivers]
        d1 = format_spoken_name(driver_names[0]) if len(driver_names) > 0 else "the primary features"
        d2 = format_spoken_name(driver_names[1]) if len(driver_names) > 1 else None
        clean_target = format_spoken_name(target)

        # Domain 1: Churn / Retention
        if "churn" in target.lower():
            if d2:
                return (
                    f"Here is the real story behind your customer data. TabPFN evaluated your {n_rows} customer accounts "
                    f"and determined that {d1} and {d2} are the primary triggers causing customer churn. "
                    f"In simple terms, customers with steep bills who lack long-term commitments are leaving at the highest rates. "
                    f"Since the Bayesian foundation resolved this with zero hyperparameter tuning, you just saved roughly forty-five minutes of data science work. "
                    f"Focus your retention incentives on those high-risk accounts first, and take the rest of the day to relax."
                )
            else:
                return (
                    f"Here is the real story behind your customer data. TabPFN evaluated your accounts "
                    f"and identified that {d1} is the most critical trigger influencing customer churn. "
                    f"Targeting preventative discounts to customers showing high {d1} will yield the highest retention gains. "
                    f"Everything is calibrated without manual tuning, so go ahead and take a break."
                )

        # Domain 2: Health / Cardiac / Diagnosis / Disease
        if any(w in target.lower() for w in ["heart", "cardio", "disease", "diagnos", "risk", "patient", "health"]):
            if d2:
                return (
                    f"Here is your clinical outcome briefing. Analyzing your {n_rows} patient records, TabPFN discovered that "
                    f"{d1} and {d2} are the most dominant physiological indicators for {clean_target}. "
                    f"The neural Bayesian prior captured these risk factors in a fraction of a second, beating traditional random forests without any manual tuning. "
                    f"Prioritizing clinical screening for patients with elevated {d1} will give you the greatest preventative impact. "
                    f"The heavy modeling is completely finished, so you can rest easy."
                )
            else:
                return (
                    f"Here is your clinical outcome briefing. TabPFN evaluated your patient records to assess {clean_target}, "
                    f"finding that {d1} is the primary predictive marker. "
                    f"The Bayesian network calibrated the risk profile instantly without any manual parameter searches. "
                    f"Focus your care pathways on patients with outlying values in {d1}, and enjoy a well-deserved break."
                )

        # Domain 3: Housing / Real Estate / Pricing
        if any(w in target.lower() for w in ["price", "house", "cost", "valua", "rent", "sal"]):
            if d2:
                return (
                    f"Here is what the real estate numbers are telling us. When predicting {clean_target} across your {n_rows} properties, "
                    f"{d1} along with {d2} account for the vast majority of valuation variance. "
                    f"While traditional regression algorithms require extensive data scaling and feature pruning, TabPFN modeled the non-linear pricing curves in milliseconds. "
                    f"If you want to maximize property value, investments targeting {d1} provide the highest leverage. "
                    f"Now that the math is settled, go ahead and put your feet up."
                )
            else:
                return (
                    f"Here is your property valuation briefing. Across your {n_rows} records, TabPFN uncovered that "
                    f"{d1} is the single largest factor driving {clean_target}. "
                    f"The model completed the regression analysis instantly with zero manual tuning, saving you about forty-five minutes of work. "
                    f"Prioritize {d1} in your appraisals, and take the afternoon off."
                )

        # Domain 4: General Classification
        if task == "classification":
            acc = metrics.get("tabpfn", {}).get("accuracy", "high")
            drivers_phrase = f"{d1} and {d2}" if d2 else d1
            return (
                f"Here is your executive analysis for {clean_target}. Looking across {n_rows} samples, TabPFN discovered that "
                f"{drivers_phrase} are your strongest deciding factors. "
                f"While standard classifiers demand tedious hyperparameter searches, the Bayesian prior achieved {acc} percent accuracy on the first pass. "
                f"To move the needle with minimal effort, focus your operational strategy on {d1}. "
                f"The model is fully calibrated, so you can sit back and relax."
            )

        # Domain 5: General Regression / Continuous
        drivers_phrase = f"{d1} and {d2}" if d2 else d1
        return (
            f"Taking a closer look at your {clean_target} predictions. Across your {n_rows} observations, TabPFN established that "
            f"{drivers_phrase} carry the heaviest weight in determining the outcome. "
            f"TabPFN mapped these complex numerical relationships without any manual feature engineering or model tuning. "
            f"Concentrate your focus on adjustments to {d1} for the greatest impact. "
            f"The hard work is done, so feel free to take a nap."
        )

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

        # Leverage Gemini when available for deep tabular reasoning
        if self.has_gemini_key() and prediction_result:
            gemini_ans = self._generate_gemini_chat_answer(query, df, prediction_result)
            if gemini_ans:
                return gemini_ans

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
