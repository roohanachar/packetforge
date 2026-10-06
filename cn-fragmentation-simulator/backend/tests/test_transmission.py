"""
Unit tests for IPv4 Transmission Simulator.
"""

import time
import unittest
from backend.core.models import Fragment
from backend.core.fragmenter import fragment_packet
from backend.core.reassembler import reassemble_fragments
from backend.core.transmitter import (
    TransmissionConfig,
    TransmissionEvent,
    TransmissionResult,
    TransmissionSimulator,
    simulate_transmission,
)


class TestIPv4Transmission(unittest.TestCase):
    """Test suite for IPv4 fragment transmission simulator."""

    def setUp(self):
        # 3 standard fragments representing a 3980-byte payload (MTU=1500, header=20)
        self.frag0 = Fragment(
            identification=1001,
            offset=0,
            payload_size=1480,
            total_size=1500,
            more_fragments=True,
        )
        self.frag1 = Fragment(
            identification=1001,
            offset=185,
            payload_size=1480,
            total_size=1500,
            more_fragments=True,
        )
        self.frag2 = Fragment(
            identification=1001,
            offset=370,
            payload_size=1020,
            total_size=1040,
            more_fragments=False,
        )
        self.fragments = [self.frag0, self.frag1, self.frag2]

    def test_1_normal_transmission(self):
        """
        1. Normal transmission:
        - All fragments delivered
        - Original order preserved
        """
        config = TransmissionConfig()
        result = TransmissionSimulator.simulate(self.fragments, config)

        self.assertEqual(result.total_input, 3)
        self.assertEqual(result.delivered_count, 3)
        self.assertEqual(result.dropped_count, 0)
        self.assertEqual(result.duplicate_count, 0)
        self.assertEqual(result.corrupted_count, 0)
        self.assertEqual(result.delivered_fragments, self.fragments)

        # Verify all events are 'delivered'
        self.assertEqual(len(result.events), 3)
        for i, event in enumerate(result.events):
            self.assertEqual(event.action, "delivered")
            self.assertEqual(event.original_fragment_index, i)
            self.assertEqual(event.sequence_number, i + 1)
            self.assertEqual(event.delay_ms, 0)

    def test_2_out_of_order_transmission(self):
        """
        2. Out-of-order transmission:
        - Same fragments are delivered
        - Order changes
        - Deterministic when a seed is supplied
        """
        config = TransmissionConfig(reorder=True, seed=42)
        result1 = TransmissionSimulator.simulate(self.fragments, config)

        # Same fragments delivered, but in a different order
        self.assertEqual(len(result1.delivered_fragments), 3)
        self.assertCountEqual(result1.delivered_fragments, self.fragments)
        self.assertNotEqual(result1.delivered_fragments, self.fragments)

        # Deterministic when same seed is supplied
        result2 = TransmissionSimulator.simulate(self.fragments, config)
        self.assertEqual(result1.delivered_fragments, result2.delivered_fragments)
        self.assertEqual(
            [e.original_fragment_index for e in result1.events],
            [e.original_fragment_index for e in result2.events],
        )

    def test_3_fragment_loss(self):
        """
        3. Fragment loss:
        - Selected fragment is absent
        - Dropped event exists
        """
        # Drop middle fragment (index 1)
        config = TransmissionConfig(drop_indices=[1])
        result = TransmissionSimulator.simulate(self.fragments, config)

        self.assertEqual(result.total_input, 3)
        self.assertEqual(result.delivered_count, 2)
        self.assertEqual(result.dropped_count, 1)

        # Fragment 1 must be absent
        self.assertEqual(result.delivered_fragments, [self.frag0, self.frag2])

        # Verify 'dropped' event exists
        dropped_events = [e for e in result.events if e.action == "dropped"]
        self.assertEqual(len(dropped_events), 1)
        self.assertEqual(dropped_events[0].original_fragment_index, 1)
        self.assertIn("dropped", dropped_events[0].detail.lower())

    def test_4_fragment_duplication(self):
        """
        4. Fragment duplication:
        - Selected fragment appears twice
        - Duplicate event exists
        """
        # Duplicate fragment index 1
        config = TransmissionConfig(duplicate_indices=[1])
        result = TransmissionSimulator.simulate(self.fragments, config)

        self.assertEqual(result.total_input, 3)
        self.assertEqual(result.delivered_count, 4)
        self.assertEqual(result.duplicate_count, 1)

        # Fragment 1 appears twice
        delivered = result.delivered_fragments
        self.assertEqual(len(delivered), 4)
        self.assertEqual(delivered.count(self.frag1), 2)
        self.assertEqual(delivered, [self.frag0, self.frag1, self.frag1, self.frag2])

        # Verify 'duplicated' event exists
        dup_events = [e for e in result.events if e.action == "duplicated"]
        self.assertEqual(len(dup_events), 1)
        self.assertEqual(dup_events[0].original_fragment_index, 1)

    def test_5_simulated_delay(self):
        """
        5. Simulated delay:
        - No real waiting (executes fast)
        - Delay is represented in events
        """
        start_time = time.monotonic()
        config = TransmissionConfig(delay_ms=2500)
        result = TransmissionSimulator.simulate(self.fragments, config)
        elapsed = time.monotonic() - start_time

        # Simulation must be fast without actual sleep (< 0.1 seconds)
        self.assertLess(elapsed, 0.1)

        # Delay must be recorded in events
        self.assertEqual(len(result.events), 3)
        for event in result.events:
            self.assertEqual(event.delay_ms, 2500)

    def test_6_corruption(self):
        """
        6. Corruption:
        - Original Fragment remains unchanged
        - Corrupted copy is delivered
        - Metadata is altered
        - Corruption event exists
        """
        original_offset = self.frag1.offset
        config = TransmissionConfig(corrupt_indices=[1], corruption_offset_shift=20)
        result = TransmissionSimulator.simulate(self.fragments, config)

        # Original Fragment MUST remain unchanged
        self.assertEqual(self.frag1.offset, original_offset)

        # Corrupted copy is delivered
        corrupted_delivered = result.delivered_fragments[1]
        self.assertIsNot(corrupted_delivered, self.frag1)
        self.assertEqual(corrupted_delivered.offset, original_offset + 20)
        self.assertNotEqual(corrupted_delivered.offset, self.frag1.offset)

        # Corruption count and event exist
        self.assertEqual(result.corrupted_count, 1)
        corrupt_events = [e for e in result.events if e.action == "corrupted"]
        self.assertEqual(len(corrupt_events), 1)
        self.assertEqual(corrupt_events[0].original_fragment_index, 1)

    def test_7_deterministic_behavior(self):
        """
        7. Deterministic behavior:
        - Same input + same seed produces the same transmission result
        """
        config_a = TransmissionConfig(reorder=True, seed=12345)
        config_b = TransmissionConfig(reorder=True, seed=12345)

        res_a = TransmissionSimulator.simulate(self.fragments, config_a)
        res_b = TransmissionSimulator.simulate(self.fragments, config_b)

        self.assertEqual(res_a.delivered_fragments, res_b.delivered_fragments)
        self.assertEqual(
            [(e.sequence_number, e.original_fragment_index, e.action) for e in res_a.events],
            [(e.sequence_number, e.original_fragment_index, e.action) for e in res_b.events],
        )

    def test_8_combined_scenario(self):
        """
        8. Combined scenario:
        - Reorder = True
        - Fragment index 1 is lost
        - Fragment index 2 is duplicated
        - Delay_ms = 100
        - Verify result is predictable
        """
        config = TransmissionConfig(
            reorder=True,
            drop_indices=[1],
            duplicate_indices=[2],
            delay_ms=100,
            seed=99,
        )
        result = TransmissionSimulator.simulate(self.fragments, config)

        self.assertEqual(result.total_input, 3)
        self.assertEqual(result.dropped_count, 1)
        self.assertEqual(result.duplicate_count, 1)
        self.assertEqual(result.delivered_count, 3)  # frag0, frag2, frag2 duplicated

        # Frag 1 is absent
        self.assertNotIn(self.frag1, result.delivered_fragments)
        # Frag 2 appears twice
        self.assertEqual(result.delivered_fragments.count(self.frag2), 2)
        # Frag 0 appears once
        self.assertEqual(result.delivered_fragments.count(self.frag0), 1)

        # Verify all events have delay_ms = 100
        self.assertTrue(all(e.delay_ms == 100 for e in result.events))

        # Sequence numbers must be strictly sequential [1, 2, 3, 4]
        self.assertEqual([e.sequence_number for e in result.events], [1, 2, 3, 4])

    def test_9_integration_with_reassembly(self):
        """
        9. Integration with reassembly:
        - Normal transmission -> reassembly succeeds
        - Out-of-order transmission -> reassembly succeeds
        - Loss -> reassembly fails with missing range
        - Duplicate -> reassembly detects overlap
        - Corrupted metadata -> reassembly fails appropriately
        """
        # A. Normal transmission -> Reassembly succeeds
        res_normal = TransmissionSimulator.simulate(self.fragments)
        reassemble_normal = reassemble_fragments(res_normal.delivered_fragments)
        self.assertTrue(reassemble_normal.success)
        self.assertEqual(reassemble_normal.payload_size, 3980)

        # B. Out-of-order transmission -> Reassembly succeeds
        res_ooo = TransmissionSimulator.simulate(self.fragments, TransmissionConfig(reorder=True, seed=7))
        reassemble_ooo = reassemble_fragments(res_ooo.delivered_fragments)
        self.assertTrue(reassemble_ooo.success)
        self.assertEqual(reassemble_ooo.payload_size, 3980)

        # C. Loss -> Reassembly fails with missing range
        res_loss = TransmissionSimulator.simulate(self.fragments, TransmissionConfig(drop_indices=[1]))
        reassemble_loss = reassemble_fragments(res_loss.delivered_fragments)
        self.assertFalse(reassemble_loss.success)
        self.assertIn((1480, 2960), reassemble_loss.missing_ranges)

        # D. Duplicate -> Reassembly detects overlap
        res_dup = TransmissionSimulator.simulate(self.fragments, TransmissionConfig(duplicate_indices=[1]))
        reassemble_dup = reassemble_fragments(res_dup.delivered_fragments)
        self.assertFalse(reassemble_dup.success)
        self.assertTrue(len(reassemble_dup.overlaps) > 0)
        self.assertIn((1480, 2960), reassemble_dup.overlaps)

        # E. Corrupted metadata -> Reassembly fails appropriately
        res_corrupt = TransmissionSimulator.simulate(
            self.fragments, TransmissionConfig(corrupt_indices=[1], corruption_offset_shift=10)
        )
        reassemble_corrupt = reassemble_fragments(res_corrupt.delivered_fragments)
        self.assertFalse(reassemble_corrupt.success)
        # Altered offset creates a gap or overlap
        self.assertTrue(len(reassemble_corrupt.missing_ranges) > 0 or len(reassemble_corrupt.overlaps) > 0)

    def test_empty_fragments(self):
        """Empty input list returns clean empty TransmissionResult."""
        res = TransmissionSimulator.simulate([])
        self.assertEqual(res.total_input, 0)
        self.assertEqual(res.delivered_count, 0)
        self.assertEqual(res.events, [])

    def test_negative_delay_validation(self):
        """Negative delay_ms raises ValueError."""
        with self.assertRaises(ValueError):
            TransmissionSimulator.simulate(self.fragments, TransmissionConfig(delay_ms=-5))

    def test_function_and_class_interface_parity(self):
        """Verify simulate_transmission matches TransmissionSimulator.simulate."""
        cfg = TransmissionConfig(duplicate_indices=[0], delay_ms=50)
        res1 = simulate_transmission(self.fragments, cfg)
        res2 = TransmissionSimulator.simulate(self.fragments, cfg)
        self.assertEqual(res1.delivered_fragments, res2.delivered_fragments)
        self.assertEqual(len(res1.events), len(res2.events))


if __name__ == "__main__":
    unittest.main()
