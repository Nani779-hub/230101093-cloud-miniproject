"""Unit tests for stateless NACL rule evaluation and network design."""
import json
import unittest

from cloud_assignment.tools.nacl_sim import decide, load_rules


class TestNaclRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules("network/nacl.json")

    def test_inbound_sample_packets(self):
        with open("cloud_assignment/network/packets_sample.jsonl", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                pkt = json.loads(line)
                action, rule = decide(self.rules, pkt)
                self.assertEqual(action, pkt["expected"], f"Failed on packet {pkt['id']}")

    def test_inbound_abusive_range_blocked_on_web(self):
        pkt = {
            "direction": "inbound",
            "protocol": "tcp",
            "port": 80,
            "address": "198.51.100.42",
        }
        action, rule = decide(self.rules, pkt)
        self.assertEqual(action, "deny")
        self.assertEqual(rule, 100)

    def test_inbound_ssh_only_from_management(self):
        # From management subnet: ALLOW
        pkt_mgmt = {
            "direction": "inbound",
            "protocol": "tcp",
            "port": 22,
            "address": "10.20.5.135",
        }
        action, rule = decide(self.rules, pkt_mgmt)
        self.assertEqual(action, "allow")
        self.assertEqual(rule, 130)

        # From app subnet: DENY
        pkt_app = {
            "direction": "inbound",
            "protocol": "tcp",
            "port": 22,
            "address": "10.20.1.10",
        }
        action, rule = decide(self.rules, pkt_app)
        self.assertEqual(action, "deny")

        # From public internet: DENY
        pkt_ext = {
            "direction": "inbound",
            "protocol": "tcp",
            "port": 22,
            "address": "203.0.113.1",
        }
        action, rule = decide(self.rules, pkt_ext)
        self.assertEqual(action, "deny")

    def test_inbound_app_replies_allowed(self):
        pkt = {
            "direction": "inbound",
            "protocol": "tcp",
            "port": 45000,
            "address": "10.20.2.100",
        }
        action, rule = decide(self.rules, pkt)
        self.assertEqual(action, "allow")
        self.assertEqual(rule, 140)

    def test_outbound_to_app_port_8000(self):
        pkt = {
            "direction": "outbound",
            "protocol": "tcp",
            "port": 8000,
            "address": "10.20.0.50",
        }
        action, rule = decide(self.rules, pkt)
        self.assertEqual(action, "allow")
        self.assertEqual(rule, 100)

    def test_outbound_client_replies_allowed(self):
        pkt = {
            "direction": "outbound",
            "protocol": "tcp",
            "port": 54321,
            "address": "192.0.2.100",
        }
        action, rule = decide(self.rules, pkt)
        self.assertEqual(action, "allow")
        self.assertEqual(rule, 110)


if __name__ == "__main__":
    unittest.main()
