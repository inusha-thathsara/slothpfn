import io
import os
import sys
import base64
import pandas as pd
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from dotenv import load_dotenv

from backend.predictor import predictor_instance, SlothPredictor
from backend.dataset_samples import get_sample_catalog, load_sample_df
from backend.voice_agent import voice_agent_instance

app = FastAPI(
    title="SlothPFN - Zero-Effort Tabular AI Agent",
    description="The lazy tabular AI predictor powered by Prior Labs' TabPFN foundation model.",
    version="1.0.0"
)

# Enable CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store for current active dataset
SESSION_STATE: Dict[str, Any] = {
    "df": None,
    "filename": None,
    "last_result": None
}

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(ROOT_DIR, ".env")


@app.get("/api/health")
async def health_check():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    token = os.environ.get("TABPFN_TOKEN", "").strip()
    predictor_instance.set_token(token)
    return {
        "status": "healthy",
        "app_name": "SlothPFN",
        "python_version": sys.version.split(" ")[0],
        "has_token": bool(predictor_instance.api_token),
        "is_live_tabpfn": predictor_instance.is_live_tabpfn_active(),
        "mode": "Prior Labs TabPFN-3.5 Active (.env)" if predictor_instance.is_live_tabpfn_active() else "Prior Simulator / Local Demo Mode",
        "has_active_dataset": SESSION_STATE["df"] is not None,
        "active_filename": SESSION_STATE["filename"]
    }


@app.get("/api/ambient/session")
async def get_ambient_session():
    """
    Returns the latest ambient analysis result (from right-click context menu,
    watchdog folder drop, or scheduled morning briefing).
    """
    import json
    session_path = os.path.join(ROOT_DIR, "active_session.json")
    if os.path.exists(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Sync into in-memory session if not set
            if SESSION_STATE["last_result"] is None and "result" in data:
                SESSION_STATE["last_result"] = data["result"]
                SESSION_STATE["filename"] = data.get("filename", "ambient_dataset.csv")
            return {"has_ambient_session": True, "session": data}
        except Exception as e:
            return {"has_ambient_session": False, "error": str(e)}
    return {"has_ambient_session": False}


@app.get("/api/samples")
async def list_samples():
    return {"samples": get_sample_catalog()}


@app.post("/api/samples/{sample_id}")
async def load_sample(sample_id: str):
    try:
        df = load_sample_df(sample_id)
        SESSION_STATE["df"] = df
        SESSION_STATE["filename"] = f"sample_{sample_id}.csv"
        SESSION_STATE["last_result"] = None

        inspection = predictor_instance.inspect_dataframe(df)
        inspection["filename"] = SESSION_STATE["filename"]
        inspection["source"] = "sample"
        inspection["sample_id"] = sample_id
        return inspection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # Decode CSV or TSV
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception:
            # Fallback to semicolon or tab separator
            df = pd.read_csv(io.BytesIO(contents), sep=None, engine="python")

        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file contains no rows.")

        SESSION_STATE["df"] = df
        SESSION_STATE["filename"] = file.filename
        SESSION_STATE["last_result"] = None

        inspection = predictor_instance.inspect_dataframe(df)
        inspection["filename"] = file.filename
        inspection["source"] = "upload"
        return inspection
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse tabular file: {str(e)}")


@app.post("/api/predict")
async def run_predict(
    target_column: str = Form(...),
    task_type: str = Form(...)
):
    df = SESSION_STATE["df"]
    if df is None:
        raise HTTPException(status_code=400, detail="No active dataset loaded. Please upload a CSV or pick a sample first.")

    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{target_column}' does not exist in dataset.")

    task_type = task_type.lower()
    if task_type not in ["classification", "regression"]:
        raise HTTPException(status_code=400, detail="Task type must be 'classification' or 'regression'.")

    try:
        result = predictor_instance.run_prediction_pipeline(
            df=df,
            target_column=target_column,
            task_type=task_type
        )
        result["filename"] = SESSION_STATE["filename"]
        SESSION_STATE["last_result"] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/api/simulate")
async def simulate_what_if(payload: Dict[str, Any] = Body(...)):
    df = SESSION_STATE["df"]
    if df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")

    target_column = payload.get("target_column")
    task_type = payload.get("task_type", "classification")
    features = payload.get("features", {})

    if not target_column or target_column not in df.columns:
        raise HTTPException(status_code=400, detail="Valid target_column required.")

    try:
        sim_result = predictor_instance.simulate_scenario(
            df=df,
            target_column=target_column,
            task_type=task_type,
            input_values=features
        )
        return sim_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@app.get("/api/voice/status")
async def get_voice_status():
    has_key = voice_agent_instance.has_elevenlabs_key()
    return {
        "has_elevenlabs": has_key,
        "provider": "elevenlabs" if has_key else "browser_fallback",
        "voice_id": voice_agent_instance.voice_id,
        "voices": voice_agent_instance.list_voices()
    }


@app.get("/api/voice/voices")
async def get_voices():
    return {"voices": voice_agent_instance.list_voices()}


@app.post("/api/voice/narrate")
async def narrate_text(payload: Dict[str, Any] = Body(...)):
    text = payload.get("text", "").strip()
    voice_id = payload.get("voice_id")
    if not text:
        if SESSION_STATE["last_result"]:
            insights = SESSION_STATE["last_result"].get("sloth_insights", {})
            text = f"{insights.get('headline', '')}. {insights.get('summary', '')} {insights.get('key_drivers', '')}"
        else:
            raise HTTPException(status_code=400, detail="No text provided to narrate.")

    audio_bytes = await voice_agent_instance.generate_speech(text, voice_id=voice_id)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "has_audio": True,
            "provider": "elevenlabs",
            "audio_data": f"data:audio/mpeg;base64,{audio_b64}",
            "text": text,
            "voice_id": voice_id or voice_agent_instance.voice_id
        }
    else:
        return {
            "has_audio": False,
            "provider": "browser_fallback",
            "audio_data": None,
            "text": text,
            "message": "ElevenLabs API key not configured or failed. Using browser speech synthesis fallback."
        }


@app.get("/api/voice/stream")
async def stream_voice_audio(text: str = "", voice_id: Optional[str] = None):
    if not text:
        if SESSION_STATE["last_result"]:
            insights = SESSION_STATE["last_result"].get("sloth_insights", {})
            text = f"{insights.get('headline', '')}. {insights.get('summary', '')} {insights.get('key_drivers', '')}"
        else:
            raise HTTPException(status_code=400, detail="No text provided to stream.")

    if not voice_agent_instance.has_elevenlabs_key():
        raise HTTPException(status_code=400, detail="ElevenLabs API key not configured.")

    return StreamingResponse(
        voice_agent_instance.stream_speech(text=text, voice_id=voice_id),
        media_type="audio/mpeg"
    )


@app.post("/api/voice/chat")
async def chat_with_agent(payload: Dict[str, Any] = Body(...)):
    query = payload.get("query", "").strip()
    voice_id = payload.get("voice_id")
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    answer = voice_agent_instance.answer_tabular_query(
        query=query,
        df=SESSION_STATE["df"],
        prediction_result=SESSION_STATE["last_result"]
    )

    audio_bytes = await voice_agent_instance.generate_speech(answer, voice_id=voice_id)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    return {
        "query": query,
        "answer": answer,
        "has_audio": audio_bytes is not None,
        "provider": "elevenlabs" if audio_bytes else "browser_fallback",
        "audio_data": f"data:audio/mpeg;base64,{audio_b64}" if audio_b64 else None,
        "voice_id": voice_id or voice_agent_instance.voice_id
    }


@app.post("/api/voice/transcribe")
async def transcribe_speech(audio: UploadFile = File(...)):
    if not voice_agent_instance.has_elevenlabs_key():
        raise HTTPException(status_code=400, detail="ElevenLabs API key required for transcription.")

    try:
        contents = await audio.read()
        audio_stream = io.BytesIO(contents)
        audio_stream.name = audio.filename or "recording.wav"
        text = voice_agent_instance.transcribe_audio(audio_stream)
        if not text:
            raise HTTPException(status_code=500, detail="Transcription produced no text.")
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")



# Mount frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
