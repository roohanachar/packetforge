"""
Integration and functional tests for the IPv4 Simulator HTTP API.
"""

import time
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app


class TestSimulatorAPI(unittest.TestCase):
    """Test suite verifying the FastAPI endpoints for packet simulation."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_1_health_endpoint(self):
        """
        1. GET /api/health
        - HTTP success (200)
        - Expected JSON response {"status": "ok"}
        """
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_2_simulate_normal_packet(self):
        """
        2. POST /api/simulate
        - Normal packet fitting in MTU
        - Successful result
        """
        payload = {
            "payload_size": 1000,
            "mtu": 1500,
            "identification": 1001,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["payload_size"], 1000)
        self.assertEqual(data["fragment_count"], 1)
        self.assertEqual(len(data["generated_fragments"]), 1)
        self.assertTrue(data["reassembly_result"]["success"])
        self.assertEqual(data["reassembly_result"]["payload_size"], 1000)

    def test_3_simulate_packet_requiring_fragmentation(self):
        """
        3. POST /api/simulate
        - Packet requiring fragmentation
        - Multiple fragments returned
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 2002,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["fragment_count"], 3)
        self.assertEqual(len(data["generated_fragments"]), 3)
        self.assertEqual([f["payload_size"] for f in data["generated_fragments"]], [1480, 1480, 1020])
        self.assertEqual([f["offset"] for f in data["generated_fragments"]], [0, 185, 370])
        self.assertEqual([f["more_fragments"] for f in data["generated_fragments"]], [True, True, False])

    def test_4_simulate_out_of_order_transmission(self):
        """
        4. POST /api/simulate
        - Out-of-order transmission
        - Successful reassembly
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 3003,
            "transmission": {
                "reorder": True,
                "seed": 42,
            },
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Reassembly must succeed despite out-of-order delivery
        self.assertTrue(data["success"])
        self.assertTrue(data["reassembly_result"]["success"])
        self.assertEqual(data["reassembly_result"]["payload_size"], 3980)

        # Delivered order should differ from generated order
        delivered_offsets = [f["offset"] for f in data["transmission_result"]["delivered_fragments"]]
        generated_offsets = [f["offset"] for f in data["generated_fragments"]]
        self.assertNotEqual(delivered_offsets, generated_offsets)
        self.assertCountEqual(delivered_offsets, generated_offsets)

    def test_5_simulate_fragment_loss(self):
        """
        5. POST /api/simulate
        - Fragment loss
        - Failed reassembly
        - Missing range information reported
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 4004,
            "transmission": {
                "drop_indices": [1],
            },
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertFalse(data["success"])
        self.assertFalse(data["reassembly_result"]["success"])
        self.assertEqual(data["transmission_result"]["dropped_count"], 1)
        self.assertEqual(data["transmission_result"]["delivered_count"], 2)
        # Missing range [1480, 2960)
        self.assertIn([1480, 2960], data["reassembly_result"]["missing_ranges"])

    def test_6_simulate_duplicate_fragment(self):
        """
        6. POST /api/simulate
        - Duplicate fragment
        - Overlap detected
        - Reassembly failure
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 5005,
            "transmission": {
                "duplicate_indices": [1],
            },
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertFalse(data["success"])
        self.assertFalse(data["reassembly_result"]["success"])
        self.assertEqual(data["transmission_result"]["duplicate_count"], 1)
        self.assertEqual(data["transmission_result"]["delivered_count"], 4)
        self.assertTrue(len(data["reassembly_result"]["overlaps"]) > 0)
        self.assertIn([1480, 2960], data["reassembly_result"]["overlaps"])

    def test_7_simulate_metadata_corruption(self):
        """
        7. POST /api/simulate
        - Metadata corruption
        - Appropriate failure
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 6006,
            "transmission": {
                "corrupt_indices": [1],
                "corruption_offset_shift": 10,
            },
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertFalse(data["success"])
        self.assertFalse(data["reassembly_result"]["success"])
        self.assertEqual(data["transmission_result"]["corrupted_count"], 1)
        has_anomalies = (
            len(data["reassembly_result"]["missing_ranges"]) > 0
            or len(data["reassembly_result"]["overlaps"]) > 0
        )
        self.assertTrue(has_anomalies)

    def test_8_simulate_transmission_delay(self):
        """
        8. POST /api/simulate
        - Simulated delay
        - Request does NOT actually wait
        """
        start = time.monotonic()
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 7007,
            "transmission": {
                "delay_ms": 3000,
            },
        }
        response = self.client.post("/api/simulate", json=payload)
        elapsed = time.monotonic() - start

        self.assertLess(elapsed, 0.2)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(e["delay_ms"] == 3000 for e in data["transmission_result"]["events"]))

    def test_9_invalid_payload(self):
        """
        9. Invalid payload:
        - Negative payload_size
        - Appropriate HTTP validation error (422)
        """
        payload = {
            "payload_size": -50,
            "mtu": 1500,
            "identification": 1001,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

    def test_10_invalid_mtu(self):
        """
        10. Invalid MTU:
        - MTU <= header_size
        - Appropriate HTTP validation error
        """
        payload = {
            "payload_size": 100,
            "mtu": 20,
            "header_size": 20,
            "identification": 1001,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertIn(response.status_code, (400, 422))
        self.assertIn("detail", response.json())

    def test_11_invalid_identification(self):
        """
        11. Invalid identification:
        - Value > 65535 or < 0
        - Appropriate HTTP validation error (422)
        """
        payload_high = {
            "payload_size": 100,
            "mtu": 1500,
            "identification": 70000,
        }
        response_high = self.client.post("/api/simulate", json=payload_high)
        self.assertEqual(response_high.status_code, 422)

        payload_neg = {
            "payload_size": 100,
            "mtu": 1500,
            "identification": -1,
        }
        response_neg = self.client.post("/api/simulate", json=payload_neg)
        self.assertEqual(response_neg.status_code, 422)

    def test_12_response_structure(self):
        """
        12. Response structure:
        - Packet information exists
        - Fragments exist
        - Transmission result exists
        - Reassembly result exists
        - Overall success exists
        """
        payload = {
            "payload_size": 3980,
            "mtu": 1500,
            "identification": 8008,
            "header_size": 20,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 1. Packet information
        self.assertIn("payload_size", data)
        self.assertIn("mtu", data)
        self.assertIn("identification", data)
        self.assertIn("header_size", data)

        # 2. Generated fragments
        self.assertIn("fragment_count", data)
        self.assertIn("generated_fragments", data)
        self.assertIsInstance(data["generated_fragments"], list)
        frag = data["generated_fragments"][0]
        for key in ("identification", "offset", "payload_size", "total_size", "more_fragments"):
            self.assertIn(key, frag)

        # 3. Transmission result
        self.assertIn("transmission_result", data)
        tx = data["transmission_result"]
        for key in (
            "delivered_fragments",
            "events",
            "total_input",
            "delivered_count",
            "dropped_count",
            "duplicate_count",
            "corrupted_count",
        ):
            self.assertIn(key, tx)

        # 4. Reassembly result
        self.assertIn("reassembly_result", data)
        rx = data["reassembly_result"]
        for key in (
            "success",
            "identification",
            "fragment_count",
            "payload_size",
            "missing_ranges",
            "overlaps",
            "reason",
            "expected_end_offset",
        ):
            self.assertIn(key, rx)

        # 5. Overall success
        self.assertIn("success", data)
        self.assertIsInstance(data["success"], bool)

    def test_13_public_api_import(self):
        """
        13. Public API/import test:
        - API application imports successfully from backend.api
        """
        from backend.api import app as imported_app

        self.assertIsNotNone(imported_app)
        self.assertEqual(imported_app.title, "Intelligent IPv4 Fragmentation & Network Failure Simulator API")

    def test_14_simulate_df_within_mtu(self):
        """
        14. POST /api/simulate with DF=1 fitting in MTU:
        - Payload 400, MTU 1500, DF=1
        - Successful, 1 fragment with DF=1, offset 0, MF=0
        """
        payload = {
            "payload_size": 400,
            "mtu": 1500,
            "identification": 9001,
            "df": True,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertTrue(data["df"])
        self.assertFalse(data.get("fragmentation_prevented", False))
        self.assertEqual(data["fragment_count"], 1)
        frag = data["generated_fragments"][0]
        self.assertEqual(frag["payload_size"], 400)
        self.assertEqual(frag["total_size"], 420)
        self.assertEqual(frag["offset"], 0)
        self.assertFalse(frag["more_fragments"])
        self.assertTrue(frag.get("df", False))
        self.assertTrue(data["reassembly_result"]["success"])

    def test_15_simulate_df_oversized_prevented(self):
        """
        15. POST /api/simulate with DF=1 exceeding MTU:
        - Payload 3000, MTU 1500, DF=1
        - Fragmentation prevented: success=False, fragment_count=0, fragmentation_prevented=True
        - Reassembly is NOT reported as successful
        """
        payload = {
            "payload_size": 3000,
            "mtu": 1500,
            "identification": 9002,
            "df": True,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertFalse(data["success"])
        self.assertTrue(data["df"])
        self.assertTrue(data["fragmentation_prevented"])
        self.assertEqual(data["status"], "fragmentation_prevented")
        self.assertIn("DF", data["reason"])
        self.assertEqual(data["fragment_count"], 0)
        self.assertEqual(data["generated_fragments"], [])
        self.assertEqual(data["transmission_result"]["delivered_count"], 0)
        self.assertFalse(data["reassembly_result"]["success"])


if __name__ == "__main__":
    unittest.main()
