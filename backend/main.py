import io
import os
import sys
import pandas as pd
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.predictor import predictor_instance, SlothPredictor
from backend.dataset_samples import get_sample_catalog, load_sample_df

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


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": "SlothPFN",
        "python_version": sys.version.split(" ")[0],
        "has_token": bool(predictor_instance.api_token),
        "is_live_tabpfn": predictor_instance.is_live_tabpfn_active(),
        "mode": "Prior Labs TabPFN-3.5 Active" if predictor_instance.is_live_tabpfn_active() else "Prior Simulator / Local Demo Mode",
        "has_active_dataset": SESSION_STATE["df"] is not None,
        "active_filename": SESSION_STATE["filename"]
    }


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


@app.post("/api/settings/token")
async def set_token(payload: Dict[str, str] = Body(...)):
    token = payload.get("token", "").strip()
    predictor_instance.set_token(token)
    return {
        "status": "updated",
        "has_token": bool(token),
        "is_live_tabpfn": predictor_instance.is_live_tabpfn_active(),
        "mode": "Prior Labs TabPFN-3.5 Active" if predictor_instance.is_live_tabpfn_active() else "Prior Simulator / Local Demo Mode"
    }


# Mount frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
