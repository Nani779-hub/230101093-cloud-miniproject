"""Unit tests for worker/clean.py data cleaning rules."""
import unittest
from worker.clean import clean_records


class TestCleaningRules(unittest.TestCase):

    def test_valid_record(self):
        records = [{
            "id": "C0001",
            "text": "set an alarm for seven am tomorrow",
            "teacher_raw": '{"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": null}',
        }]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["kept"], 1)
        self.assertEqual(stats["rejected_invalid_json"], 0)
        self.assertEqual(stats["rejected_wrong_keys"], 0)
        self.assertEqual(stats["rejected_bad_intent"], 0)
        self.assertEqual(stats["rejected_bad_slot"], 0)

    def test_rule_a_invalid_json(self):
        records = [
            {"id": "C0001", "text": "test", "teacher_raw": "{not json"},
            {"id": "C0002", "text": "test", "teacher_raw": "plain string"},
            {"id": "C0003", "text": "test", "teacher_raw": "12345"},
        ]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(stats["rejected_invalid_json"], 3)

    def test_rule_b_wrong_keys(self):
        records = [
            {"id": "C0001", "text": "test", "teacher_raw": '{"intent": "alarm_set"}'},
            {"id": "C0002", "text": "test", "teacher_raw": '{"intent": "alarm_set", "date": null, "time": null, "place": null, "extra": 1}'},
            {"id": "C0003", "text": "test", "teacher_raw": '{"intent": "alarm_set", "date": null, "time": null, "location": null}'},
        ]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(stats["rejected_wrong_keys"], 3)

    def test_rule_c_bad_intent(self):
        records = [{
            "id": "C0001",
            "text": "play music",
            "teacher_raw": '{"intent": "music_play", "date": null, "time": null, "place": null}',
        }]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(stats["rejected_bad_intent"], 1)

    def test_rule_d_bad_slot_value(self):
        records = [{
            "id": "C0001",
            "text": "set an alarm for seven am",
            "teacher_raw": '{"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": null}',
        }]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(stats["rejected_bad_slot"], 1)

    def test_rule_e_duplicate_commands(self):
        records = [
            {"id": "C0002", "text": "what time is it", "teacher_raw": '{"intent": "datetime_query", "date": null, "time": null, "place": null}'},
            {"id": "C0001", "text": "what time is it", "teacher_raw": '{"intent": "datetime_query", "date": null, "time": null, "place": null}'},
        ]
        cleaned, stats = clean_records(records)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["id"], "C0001")  # Keep smallest id
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(stats["kept"], 1)

    def test_accounting_identity(self):
        records = [
            {"id": "C0001", "text": "alarm", "teacher_raw": "not json"},
            {"id": "C0002", "text": "alarm", "teacher_raw": '{"intent": "alarm_set"}'},
            {"id": "C0003", "text": "alarm", "teacher_raw": '{"intent": "bad_intent", "date": null, "time": null, "place": null}'},
            {"id": "C0004", "text": "alarm", "teacher_raw": '{"intent": "alarm_set", "date": "hallucinated", "time": null, "place": null}'},
            {"id": "C0005", "text": "what time is it", "teacher_raw": '{"intent": "datetime_query", "date": null, "time": null, "place": null}'},
            {"id": "C0006", "text": "what time is it", "teacher_raw": '{"intent": "datetime_query", "date": null, "time": null, "place": null}'},
        ]
        cleaned, stats = clean_records(records)
        total_rejected = (
            stats["rejected_invalid_json"]
            + stats["rejected_wrong_keys"]
            + stats["rejected_bad_intent"]
            + stats["rejected_bad_slot"]
            + stats["duplicates"]
        )
        self.assertEqual(stats["input"], total_rejected + stats["kept"])


if __name__ == "__main__":
    unittest.main()
