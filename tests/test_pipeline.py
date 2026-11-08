"""Unit tests for training and evaluation pipeline components."""
import os
import shutil
import tempfile
import unittest

from evaluation.evaluate import run_score
from training.train import format_training_prompt, load_config, load_dataset, record_loss


class TestTrainingAndEvaluation(unittest.TestCase):
    """Test training dataset preparation and evaluation scoring."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_dataset_slicing_limit(self):
        """Verify load_dataset strictly honors the max_records limit."""
        dummy_file = os.path.join(self.test_dir.name, "sample.jsonl")
        with open(dummy_file, "w", encoding="utf-8") as f:
            for i in range(100):
                f.write(f'{{"id": {i}, "text": "cmd {i}"}}\n')

        # Test subset of 50
        subset_50 = load_dataset(dummy_file, max_records=50)
        self.assertEqual(len(subset_50), 50)

        # Test 1500 limit on smaller file
        full = load_dataset(dummy_file, max_records=1500)
        self.assertEqual(len(full), 100)

    def test_format_training_prompt(self):
        """Verify prompt formatting for causal language model fine-tuning."""
        text = "set alarm for tomorrow at seven am"
        label = {"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": None}
        prompt = format_training_prompt(text, label)
        self.assertIn("Command: set alarm for tomorrow at seven am", prompt)
        self.assertIn('"intent": "alarm_set"', prompt)
        self.assertIn('"date": "tomorrow"', prompt)
        self.assertIn('"time": "seven am"', prompt)
        self.assertIn('"place": null', prompt)

    def test_record_loss_creates_csv(self):
        """Verify loss history is recorded correctly to CSV format."""
        loss_csv = os.path.join(self.test_dir.name, "loss.csv")
        sample_losses = [
            {"epoch": 1, "loss": 2.1054},
            {"epoch": 2, "loss": 1.4521},
            {"epoch": 3, "loss": 0.9850},
        ]
        record_loss(loss_csv, sample_losses)
        self.assertTrue(os.path.exists(loss_csv))

        with open(loss_csv, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(lines[0], "epoch,loss")
        self.assertEqual(lines[1], "1,2.1054")
        self.assertEqual(lines[2], "2,1.4521")
        self.assertEqual(lines[3], "3,0.9850")

    def test_load_config_fallback_defaults(self):
        """Verify load_config returns default configuration when file is absent."""
        cfg = load_config("non_existent_config.yaml")
        self.assertEqual(cfg["model"]["base_model"], "EleutherAI/pythia-70m")
        self.assertEqual(cfg["model"]["max_records"], 1500)

    def test_evaluation_baseline_scoring(self):
        """Verify evaluation scoring execution on genuine student predictions."""
        gold_path = "cloud_assignment/data/validation.jsonl"
        source_preds = "results/student_v1_predictions.jsonl"
        preds_path = os.path.join(self.test_dir.name, "preds.jsonl")

        # Copy genuine predictions to temporary evaluation path
        shutil.copyfile(source_preds, preds_path)
        self.assertTrue(os.path.exists(preds_path))

        # Run score
        report = run_score(preds_path, gold_path, min_validity=95.0)
        self.assertGreaterEqual(report["json_validity"], 95.0)
        self.assertEqual(report["examples"], 100)
        self.assertGreaterEqual(report["intent_accuracy"], 70.0)


if __name__ == "__main__":
    unittest.main()
