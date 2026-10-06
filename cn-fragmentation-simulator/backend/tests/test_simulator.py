"""
Unit tests for the Unified IPv4 Packet Simulation Pipeline.
"""

import time
import unittest

from backend.core import (
    Fragment,
    IPv4Fragmenter,
    IPv4Reassembler,
    PacketSimulator,
    ReassemblyResult,
    SimulationConfig,
    SimulationResult,
    TransmissionConfig,
    TransmissionEvent,
    TransmissionResult,
    TransmissionSimulator,
    fragment_packet,
    group_by_identification,
    reassemble_fragments,
    simulate_packet,
    simulate_transmission,
)


class TestPacketSimulator(unittest.TestCase):
    """Test suite for PacketSimulator unified pipeline."""

    def test_1_normal_end_to_end_simulation(self):
        """
        1. Normal end-to-end simulation:
        - Fragmentation occurs (3980 bytes into 1500 MTU -> 3 fragments)
        - All fragments transmitted normally
        - Reassembly succeeds
        - Overall success is True
        """
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=1001,
        )
        result = PacketSimulator.simulate(config)

        self.assertTrue(result.success)
        self.assertEqual(result.payload_size, 3980)
        self.assertEqual(result.mtu, 1500)
        self.assertEqual(result.identification, 1001)
        self.assertEqual(result.header_size, 20)
        self.assertEqual(result.fragment_count, 3)
        self.assertEqual(len(result.generated_fragments), 3)

        # Transmission metrics
        self.assertEqual(result.transmission_result.total_input, 3)
        self.assertEqual(result.transmission_result.delivered_count, 3)
        self.assertEqual(result.transmission_result.dropped_count, 0)

        # Reassembly metrics
        self.assertTrue(result.reassembly_result.success)
        self.assertEqual(result.reassembly_result.payload_size, 3980)
        self.assertEqual(result.reassembly_result.missing_ranges, [])
        self.assertEqual(result.reassembly_result.overlaps, [])

    def test_2_packet_fits_within_mtu(self):
        """
        2. Packet fits within MTU:
        - Exactly one fragment generated
        - Successful transmission
        - Successful reassembly
        """
        config = SimulationConfig(
            payload_size=1000,
            mtu=1500,
            identification=2002,
        )
        result = PacketSimulator.simulate(config)

        self.assertTrue(result.success)
        self.assertEqual(result.fragment_count, 1)
        self.assertEqual(result.generated_fragments[0].offset, 0)
        self.assertFalse(result.generated_fragments[0].more_fragments)
        self.assertEqual(result.reassembly_result.payload_size, 1000)

    def test_3_out_of_order_transmission(self):
        """
        3. Out-of-order transmission:
        - Transmission order changes
        - Reassembly still succeeds completely
        """
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=3003,
            transmission=TransmissionConfig(reorder=True, seed=42),
        )
        result = PacketSimulator.simulate(config)

        # Reassembly succeeds despite out-of-order delivery
        self.assertTrue(result.success)
        self.assertTrue(result.reassembly_result.success)
        self.assertEqual(result.reassembly_result.payload_size, 3980)

        # Delivered fragments order should differ from original generated order
        self.assertNotEqual(
            result.transmission_result.delivered_fragments,
            result.generated_fragments,
        )
        self.assertCountEqual(
            result.transmission_result.delivered_fragments,
            result.generated_fragments,
        )

    def test_4_fragment_loss(self):
        """
        4. Fragment loss:
        - Selected fragment is dropped during transmission
        - Reassembly fails
        - Missing range is reported
        """
        # Drop middle fragment (index 1: bytes [1480, 2960))
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=4004,
            transmission=TransmissionConfig(drop_indices=[1]),
        )
        result = PacketSimulator.simulate(config)

        self.assertFalse(result.success)
        self.assertFalse(result.reassembly_result.success)
        self.assertEqual(result.transmission_result.dropped_count, 1)
        self.assertEqual(result.transmission_result.delivered_count, 2)
        self.assertIn((1480, 2960), result.reassembly_result.missing_ranges)

    def test_5_fragment_duplication(self):
        """
        5. Fragment duplication:
        - Duplicate reaches reassembler
        - Overlap is detected
        - Reassembly fails
        """
        # Duplicate fragment 1
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=5005,
            transmission=TransmissionConfig(duplicate_indices=[1]),
        )
        result = PacketSimulator.simulate(config)

        self.assertFalse(result.success)
        self.assertFalse(result.reassembly_result.success)
        self.assertEqual(result.transmission_result.duplicate_count, 1)
        self.assertEqual(result.transmission_result.delivered_count, 4)
        self.assertTrue(len(result.reassembly_result.overlaps) > 0)
        self.assertIn((1480, 2960), result.reassembly_result.overlaps)

    def test_6_metadata_corruption(self):
        """
        6. Metadata corruption:
        - Corrupted fragment reaches reassembler
        - Reassembly fails appropriately
        """
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=6006,
            transmission=TransmissionConfig(corrupt_indices=[1], corruption_offset_shift=10),
        )
        result = PacketSimulator.simulate(config)

        self.assertFalse(result.success)
        self.assertFalse(result.reassembly_result.success)
        self.assertEqual(result.transmission_result.corrupted_count, 1)
        # Corrupted offset shifts start byte from 1480 to 1560, producing gap and/or overlap
        has_anomaly = (
            len(result.reassembly_result.missing_ranges) > 0
            or len(result.reassembly_result.overlaps) > 0
        )
        self.assertTrue(has_anomaly)

    def test_7_transmission_delay(self):
        """
        7. Transmission delay:
        - Simulation completes without actual waiting (< 0.1s)
        - Delay information remains available in the result events
        """
        start = time.monotonic()
        config = SimulationConfig(
            payload_size=3980,
            mtu=1500,
            identification=7007,
            transmission=TransmissionConfig(delay_ms=5000),
        )
        result = PacketSimulator.simulate(config)
        elapsed = time.monotonic() - start

        self.assertLess(elapsed, 0.1)
        self.assertTrue(result.success)
        for event in result.transmission_result.events:
            self.assertEqual(event.delay_ms, 5000)

    def test_8_combined_transmission_scenario(self):
        """
        8. Combined transmission scenario:
        - Multiple transmission conditions: reordering, packet loss, duplication, and delay
        - Verify final result reflects combined pipeline behavior
        """
        config = SimulationConfig(
            payload_size=7500,  # 6 fragments: [0, 1, 2, 3, 4, 5]
            mtu=1500,
            identification=8008,
            transmission=TransmissionConfig(
                reorder=True,
                drop_indices=[2],
                duplicate_indices=[4],
                delay_ms=75,
                seed=123,
            ),
        )
        result = PacketSimulator.simulate(config)

        # 6 fragments generated
        self.assertEqual(result.fragment_count, 6)
        # 1 dropped, 1 duplicated -> delivered = 6 - 1 + 1 = 6
        self.assertEqual(result.transmission_result.dropped_count, 1)
        self.assertEqual(result.transmission_result.duplicate_count, 1)
        self.assertEqual(result.transmission_result.delivered_count, 6)

        # Because fragment 2 was dropped, reassembly must fail with missing range
        self.assertFalse(result.success)
        self.assertIn((2960, 4440), result.reassembly_result.missing_ranges)

    def test_9_result_integrity(self):
        """
        9. Result integrity:
        - SimulationResult contains the original fragmentation result,
          transmission result, and reassembly result consistently
        """
        config = SimulationConfig(payload_size=3980, mtu=1500, identification=9009)
        result = PacketSimulator.simulate(config)

        # Check answers to conceptual frontend questions:
        # 1. What packet was simulated?
        self.assertEqual(result.payload_size, 3980)
        self.assertEqual(result.mtu, 1500)
        self.assertEqual(result.identification, 9009)
        self.assertEqual(result.header_size, 20)

        # 2. How many fragments were generated?
        self.assertEqual(result.fragment_count, 3)
        self.assertEqual(len(result.generated_fragments), 3)

        # 3. What happened to each fragment during transmission?
        self.assertEqual(len(result.transmission_result.events), 3)
        self.assertTrue(all(isinstance(e, TransmissionEvent) for e in result.transmission_result.events))

        # 4. What happened during reassembly?
        self.assertIsInstance(result.reassembly_result, ReassemblyResult)
        self.assertEqual(result.reassembly_result.payload_size, 3980)

        # 5. Did the original packet successfully reassemble?
        self.assertTrue(result.success)

    def test_10_interface_test(self):
        """
        10. Interface test:
        - Verify PacketSimulator and simulate_packet can be used cleanly through the public core package API
        """
        config = SimulationConfig(payload_size=1000, mtu=1500, identification=1010)

        # Static method call
        res_class = PacketSimulator.simulate(config)
        # Instance call
        res_inst = PacketSimulator().simulate(config)
        # Convenience function call
        res_func = simulate_packet(config)

        self.assertTrue(res_class.success)
        self.assertEqual(res_class.payload_size, res_inst.payload_size)
        self.assertEqual(res_class.payload_size, res_func.payload_size)

        # Invalid config type validation
        with self.assertRaises(TypeError):
            PacketSimulator.simulate(dict(payload_size=1000))

    def test_11_df_fits_within_mtu(self):
        """
        11. DF datagram fits within MTU:
        - Payload 400, MTU 1500, DF=True
        - Exactly 1 fragment generated with DF=True, MF=False, Offset=0
        - Transmission and Reassembly succeed
        """
        config = SimulationConfig(payload_size=400, mtu=1500, identification=1111, df=True)
        res = PacketSimulator.simulate(config)

        self.assertTrue(res.success)
        self.assertFalse(res.fragmentation_prevented)
        self.assertEqual(res.fragment_count, 1)
        self.assertEqual(len(res.generated_fragments), 1)
        frag = res.generated_fragments[0]
        self.assertEqual(frag.payload_size, 400)
        self.assertEqual(frag.total_size, 420)
        self.assertEqual(frag.offset, 0)
        self.assertFalse(frag.more_fragments)
        self.assertTrue(frag.df)
        self.assertTrue(res.reassembly_result.success)
        self.assertEqual(res.reassembly_result.payload_size, 400)

    def test_12_df_oversized_packet_prevented(self):
        """
        12. DF oversized datagram:
        - Payload 3000, MTU 1500, DF=True
        - Fragmentation is prevented
        - Zero fragments generated
        - Overall success is False
        - Reassembly reports failure with missing range
        """
        config = SimulationConfig(payload_size=3000, mtu=1500, identification=1212, df=True)
        res = PacketSimulator.simulate(config)

        self.assertFalse(res.success)
        self.assertTrue(res.fragmentation_prevented)
        self.assertEqual(res.status, "fragmentation_prevented")
        self.assertIn("DF", res.reason)
        self.assertEqual(res.fragment_count, 0)
        self.assertEqual(res.generated_fragments, [])
        self.assertEqual(res.transmission_result.delivered_count, 0)
        self.assertFalse(res.reassembly_result.success)
        self.assertEqual(res.reassembly_result.payload_size, 0)
        self.assertEqual(res.reassembly_result.missing_ranges, [(0, 3000)])


if __name__ == "__main__":
    unittest.main()
