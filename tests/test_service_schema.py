"""Unit tests for service schema validation and FastAPI endpoints."""
import json
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
import service.app as app_module
from service.app import app, validate_output


class TestServiceSchema(unittest.TestCase):

    def test_validate_output_valid_payload(self):
        raw = json.dumps({
            "intent": "alarm_set",
            "date": "tomorrow",
            "time": "seven am",
            "place": None,
        })
        is_valid, obj = validate_output(raw)
        self.assertTrue(is_valid)
        self.assertEqual(obj["intent"], "alarm_set")
        self.assertEqual(obj["date"], "tomorrow")
        self.assertEqual(obj["time"], "seven am")
        self.assertIsNone(obj["place"])

    def test_validate_output_invalid_json(self):
        is_valid, obj = validate_output("{invalid json")
        self.assertFalse(is_valid)
        self.assertIsNone(obj)

    def test_validate_output_wrong_keys_missing(self):
        raw = json.dumps({"intent": "alarm_set", "date": "tomorrow"})
        is_valid, obj = validate_output(raw)
        self.assertFalse(is_valid)
        self.assertIsNone(obj)

    def test_validate_output_wrong_keys_extra(self):
        raw = json.dumps({
            "intent": "alarm_set",
            "date": "tomorrow",
            "time": "seven am",
            "place": None,
            "extra_key": "unexpected",
        })
        is_valid, obj = validate_output(raw)
        self.assertFalse(is_valid)
        self.assertIsNone(obj)

    def test_validate_output_invalid_intent(self):
        raw = json.dumps({
            "intent": "play_music",
            "date": None,
            "time": None,
            "place": None,
        })
        is_valid, obj = validate_output(raw)
        self.assertFalse(is_valid)
        self.assertIsNone(obj)

    def test_validate_output_invalid_slot_type(self):
        raw = json.dumps({
            "intent": "alarm_set",
            "date": 12345,  # must be str or None
            "time": None,
            "place": None,
        })
        is_valid, obj = validate_output(raw)
        self.assertFalse(is_valid)
        self.assertIsNone(obj)

    def test_healthz_endpoint(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "ok")

    def test_readyz_when_not_ready(self):
        with patch.object(app_module, "model_ready", False):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/readyz")
            self.assertEqual(resp.status_code, 503)

    def test_readyz_when_ready(self):
        with patch.object(app_module, "model_ready", True):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/readyz")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.text, "ready")

    def test_fault_injection(self):
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock(shape=[1, 10])}
        with patch.object(app_module, "model_ready", True), \
             patch.object(app_module, "model", mock_model), \
             patch.object(app_module, "tokenizer", mock_tokenizer), \
             patch.object(app_module, "FAULT_INJECT", True):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/parse", json={"text": "set an alarm"})
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.json(), {"error": "invalid_model_output"})


if __name__ == "__main__":
    unittest.main()
