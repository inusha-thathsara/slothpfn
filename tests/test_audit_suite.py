import io
import os
import re
import sys
import unittest
import pandas as pd
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.main import app, SESSION_STATE
from backend.predictor import SlothPredictor


class SlothPFNAuditTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Audit /api/health endpoint integrity and TabPFN mode reporting."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("app_name"), "SlothPFN")
        self.assertIn("mode", data)
        self.assertIn("is_live_tabpfn", data)
        self.assertIn("has_token", data)

    def test_02_sample_catalog(self):
        """Audit sample catalog contains all expected benchmark datasets."""
        res = self.client.get("/api/samples")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("samples", data)
        samples = data["samples"]
        self.assertGreaterEqual(len(samples), 3)

        sample_ids = [s["id"] for s in samples]
        self.assertIn("telecom_churn", sample_ids)
        self.assertIn("housing_prices", sample_ids)
        self.assertIn("heart_disease", sample_ids)

        for s in samples:
            self.assertIn("rows", s)
            self.assertIn("features", s)
            self.assertIn("task", s)

    def test_03_load_samples_and_inspect(self):
        """Audit loading and inspecting every sample dataset."""
        sample_ids = ["telecom_churn", "housing_prices", "heart_disease"]
        for s_id in sample_ids:
            res = self.client.post(f"/api/samples/{s_id}")
            self.assertEqual(res.status_code, 200, f"Failed loading sample {s_id}")
            data = res.json()
            self.assertIn("filename", data)
            self.assertIn("total_rows", data)
            self.assertIn("total_columns", data)
            self.assertIn("suggested_target", data)
            self.assertIn("suggested_task", data)
            self.assertIn("columns", data)
            self.assertGreater(data["total_rows"], 0)

    def test_04_classification_prediction_pipeline(self):
        """Audit end-to-end classification prediction on customer churn."""
        # Load sample
        load_res = self.client.post("/api/samples/telecom_churn")
        self.assertEqual(load_res.status_code, 200)

        # Run prediction
        res = self.client.post("/api/predict", data={
            "target_column": "Churned",
            "task_type": "classification"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Audit response structure
        self.assertEqual(data["task_type"], "classification")
        self.assertEqual(data["target_column"], "Churned")
        self.assertIn("metrics", data)
        self.assertIn("tabpfn", data["metrics"])
        self.assertIn("baseline", data["metrics"])

        # TabPFN metrics
        tabpfn = data["metrics"]["tabpfn"]
        self.assertIn("accuracy", tabpfn)
        self.assertIn("inference_time_sec", tabpfn)
        self.assertGreaterEqual(tabpfn["accuracy"], 0)
        self.assertLessEqual(tabpfn["accuracy"], 100)

        # Feature importance
        self.assertIn("feature_importance", data)
        self.assertGreater(len(data["feature_importance"]), 0)

        # Sloth insights
        self.assertIn("sloth_insights", data)
        insights = data["sloth_insights"]
        self.assertIn("headline", insights)
        self.assertIn("summary", insights)
        self.assertIn("key_drivers", insights)
        self.assertIn("lazy_verdict", insights)

    def test_05_regression_prediction_pipeline(self):
        """Audit end-to-end regression prediction on housing prices."""
        # Load sample
        load_res = self.client.post("/api/samples/housing_prices")
        self.assertEqual(load_res.status_code, 200)

        # Run prediction
        res = self.client.post("/api/predict", data={
            "target_column": "PriceUSD",
            "task_type": "regression"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["task_type"], "regression")
        self.assertEqual(data["target_column"], "PriceUSD")
        self.assertIn("metrics", data)
        tabpfn = data["metrics"]["tabpfn"]
        self.assertIn("r2_score", tabpfn)
        self.assertIn("rmse", tabpfn)
        self.assertIn("inference_time_sec", tabpfn)

    def test_06_what_if_scenario_simulator(self):
        """Audit interactive scenario simulator posterior recalculations."""
        # Ensure churn dataset is active
        self.client.post("/api/samples/telecom_churn")
        pred_res = self.client.post("/api/predict", data={
            "target_column": "Churned",
            "task_type": "classification"
        })
        self.assertEqual(pred_res.status_code, 200)

        # Simulate change
        sim_payload = {
            "target_column": "Churned",
            "task_type": "classification",
            "features": {
                "MonthlyCharges": 120.0,
                "TenureMonths": 1,
                "ContractType": "Month-to-month",
                "TechSupport": "No"
            }
        }
        res = self.client.post("/api/simulate", json=sim_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("predicted_value", data)
        self.assertIn("confidence", data)
        self.assertGreaterEqual(data["confidence"], 0)
        self.assertLessEqual(data["confidence"], 100)

    def test_07_csv_upload_handling(self):
        """Audit file upload endpoint with valid CSV, semicolon CSV, and edge cases."""
        # Valid CSV
        valid_csv = "FeatureA,FeatureB,Target\n10,20,Yes\n15,25,No\n12,22,Yes\n18,28,No\n"
        files = {"file": ("test_valid.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")}
        res = self.client.post("/api/upload", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_rows"], 4)
        self.assertEqual(data["total_columns"], 3)

        # Semicolon delimited CSV
        semi_csv = "Col1;Col2;Outcome\n100;200;1\n110;210;0\n105;205;1\n"
        files = {"file": ("test_semi.csv", io.BytesIO(semi_csv.encode("utf-8")), "text/csv")}
        res = self.client.post("/api/upload", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_rows"], 3)

        # Empty CSV edge case (must return 400 Bad Request)
        empty_csv = ""
        files = {"file": ("empty.csv", io.BytesIO(empty_csv.encode("utf-8")), "text/csv")}
        res = self.client.post("/api/upload", files=files)
        self.assertEqual(res.status_code, 400)

    def test_08_voice_agent_status_and_voices(self):
        """Audit ElevenLabs voice status and persona listing endpoints."""
        res = self.client.get("/api/voice/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("has_elevenlabs", data)
        self.assertIn("voice_id", data)
        self.assertIn("voices", data)
        self.assertGreaterEqual(len(data["voices"]), 4)

        # Check voices catalog
        res_voices = self.client.get("/api/voice/voices")
        self.assertEqual(res_voices.status_code, 200)
        voices_data = res_voices.json()
        self.assertIn("voices", voices_data)
        voice_ids = [v["voice_id"] for v in voices_data["voices"]]
        # George should be default calm sloth narrator
        self.assertIn("JBFqnCBsd6RMkjVDRZzb", voice_ids)

    def test_09_voice_chat_and_narration(self):
        """Audit voice Q&A chat endpoint returns structured answer."""
        # Ensure a prediction result is in session
        self.client.post("/api/samples/telecom_churn")
        self.client.post("/api/predict", data={
            "target_column": "Churned",
            "task_type": "classification"
        })

        chat_res = self.client.post("/api/voice/chat", json={
            "query": "What are the top causal drivers in this dataset?",
            "voice_id": "JBFqnCBsd6RMkjVDRZzb"
        })
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertIn("query", data)
        self.assertIn("answer", data)
        self.assertIn("has_audio", data)
        self.assertGreater(len(data["answer"]), 10)

    def test_10_ambient_session_endpoint(self):
        """Audit /api/ambient/session returns disk session if available."""
        res = self.client.get("/api/ambient/session")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("has_ambient_session", data)
        if data["has_ambient_session"]:
            self.assertIn("session", data)
            self.assertIn("result", data["session"])

    def test_11_predictor_engine_data_cleaning_and_boundary(self):
        """Audit predictor engine internal data cleaning and handling of missing values."""
        predictor = SlothPredictor()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "numeric_feature": [1.5, 2.5, None, 4.5, 5.5],  # Contains NaN
            "category_feature": ["A", "B", "A", None, "B"],  # Categorical with NaN
            "constant_col": [9, 9, 9, 9, 9],  # Zero variance
            "target": [0, 1, 0, 1, 0]
        })

        X_train, X_test, y_train, y_test, feature_names, metadata = predictor.prepare_data(
            df, "target", "classification"
        )
        self.assertNotIn("id", feature_names)
        self.assertIn("numeric_feature", feature_names)
        self.assertIn("category_feature", feature_names)
        # Ensure no NaNs remain in processed feature matrices
        self.assertEqual(pd.isna(X_train).sum(), 0)
        self.assertEqual(pd.isna(X_test).sum(), 0)

    def test_12_audio_briefing_narrative_distinct_from_screen_text(self):
        """Audit that audio briefing generates a natural explanation rather than repeating screen labels."""
        self.client.post("/api/samples/telecom_churn")
        pred_res = self.client.post("/api/predict", data={
            "target_column": "Churned",
            "task_type": "classification"
        })
        self.assertEqual(pred_res.status_code, 200)
        last_result = pred_res.json()
        screen_headline = last_result["sloth_insights"]["headline"]
        screen_summary = last_result["sloth_insights"]["summary"]

        briefing_res = self.client.get("/api/voice/briefing-text")
        self.assertEqual(briefing_res.status_code, 200)
        data = briefing_res.json()
        self.assertIn("text", data)
        audio_text = data["text"]

        # Ensure audio explanation is distinct from screen headline & summary
        self.assertNotEqual(audio_text, screen_headline)
        self.assertNotEqual(audio_text, screen_summary)
        self.assertNotIn("TabPFN: ", audio_text)
        self.assertGreater(len(audio_text), 80)
        self.assertTrue(any(w in audio_text.lower() for w in ["customer", "churn", "story", "relax"]))

    def test_13_frontend_dom_elements_consistency(self):
        """Audit that all elements referenced in app.js exist in both the elements map and index.html."""
        js_path = os.path.join(ROOT_DIR, "frontend", "app.js")
        html_path = os.path.join(ROOT_DIR, "frontend", "index.html")

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        html_ids = set(re.findall(r'id="([^"]+)"', html))

        match = re.search(r"const elements = \{([^}]+)\};", js, re.DOTALL)
        self.assertIsNotNone(match, "Could not locate elements definition in app.js")
        elements_block = match.group(1)

        pairs = re.findall(r"(\w+):\s*document\.getElementById\('([^']+)'\)", elements_block)
        defined_props = {prop for prop, el_id in pairs}
        defined_ids = {el_id for prop, el_id in pairs}

        # Check: Every ID mapped in elements exists in index.html
        missing_in_html = [el_id for el_id in defined_ids if el_id not in html_ids]
        self.assertEqual(missing_in_html, [], f"Elements mapped in app.js but missing in index.html: {missing_in_html}")

        # Check: Every elements.<property> used in app.js is defined in elements dictionary
        usages = set(re.findall(r"elements\.(\w+)", js))
        missing_in_elements = sorted(list(usages - defined_props))
        self.assertEqual(missing_in_elements, [], f"Properties accessed on elements but not defined: {missing_in_elements}")


if __name__ == "__main__":
    unittest.main()


