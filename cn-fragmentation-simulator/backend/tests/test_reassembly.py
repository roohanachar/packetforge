"""
Unit tests for IPv4 Fragment Reassembly Engine.
"""

import random
import unittest
from backend.core.models import Fragment
from backend.core.fragmenter import fragment_packet
from backend.core.reassembler import (
    IPv4Reassembler,
    ReassemblyResult,
    group_by_identification,
    reassemble_fragments,
)


class TestIPv4Reassembly(unittest.TestCase):
    """Test suite for IPv4 fragment reassembly conforming to RFC 791."""

    def setUp(self):
        # Standard 3 fragments representing 3980 bytes payload (MTU=1500, header=20)
        self.frag1 = Fragment(
            identification=1001,
            offset=0,
            payload_size=1480,
            total_size=1500,
            more_fragments=True,
        )
        self.frag2 = Fragment(
            identification=1001,
            offset=185,
            payload_size=1480,
            total_size=1500,
            more_fragments=True,
        )
        self.frag3 = Fragment(
            identification=1001,
            offset=370,
            payload_size=1020,
            total_size=1040,
            more_fragments=False,
        )
        self.standard_fragments = [self.frag1, self.frag2, self.frag3]

    def test_1_normal_ordered_reassembly(self):
        """
        TEST 1 — Normal ordered reassembly
        Payload sizes = [1480, 1480, 1020], offsets = [0, 185, 370], MF = [True, True, False]
        Expected: success=True, payload_size=3980
        """
        result = reassemble_fragments(self.standard_fragments)
        self.assertTrue(result.success)
        self.assertEqual(result.payload_size, 3980)
        self.assertEqual(result.identification, 1001)
        self.assertEqual(result.fragment_count, 3)
        self.assertEqual(result.missing_ranges, [])
        self.assertEqual(result.overlaps, [])
        self.assertEqual(result.expected_end_offset, 3980)

    def test_2_out_of_order_fragments(self):
        """
        TEST 2 — Out-of-order fragments
        Pass the exact same fragments in a shuffled order.
        Expected: success=True, payload_size=3980
        """
        shuffled = [self.frag3, self.frag1, self.frag2]
        result = reassemble_fragments(shuffled)
        self.assertTrue(result.success)
        self.assertEqual(result.payload_size, 3980)
        self.assertEqual(result.identification, 1001)
        self.assertEqual(result.fragment_count, 3)
        self.assertEqual(result.missing_ranges, [])
        self.assertEqual(result.overlaps, [])

        # Also test reverse order [frag3, frag2, frag1]
        reverse_shuffled = [self.frag3, self.frag2, self.frag1]
        result_rev = reassemble_fragments(reverse_shuffled)
        self.assertTrue(result_rev.success)
        self.assertEqual(result_rev.payload_size, 3980)

    def test_3_missing_fragment(self):
        """
        TEST 3 — Missing fragment
        Remove the middle fragment.
        Expected: success=False, result identifies missing byte range.
        """
        incomplete = [self.frag1, self.frag3]
        result = reassemble_fragments(incomplete)
        self.assertFalse(result.success)
        self.assertEqual(result.payload_size, 0)
        # Missing range is from end of frag1 (1480) to start of frag3 (370 * 8 = 2960)
        self.assertIn((1480, 2960), result.missing_ranges)
        self.assertEqual(result.expected_end_offset, 3980)

    def test_4_overlapping_fragments(self):
        """
        TEST 4 — Overlapping fragments
        Create fragments whose byte ranges overlap.
        Expected: success=False, result identifies the overlap.
        """
        # frag1 covers [0, 1480)
        # overlapping_frag covers offset 100 -> [800, 800 + 1480 = 2280)
        # Overlap with frag1 is [800, 1480)
        overlapping_frag = Fragment(
            identification=1001,
            offset=100,
            payload_size=1480,
            total_size=1500,
            more_fragments=True,
        )
        result = reassemble_fragments([self.frag1, overlapping_frag, self.frag3])
        self.assertFalse(result.success)
        self.assertTrue(len(result.overlaps) > 0)
        self.assertIn((800, 1480), result.overlaps)

    def test_5_missing_first_fragment(self):
        """
        TEST 5 — Missing first fragment
        Provide fragments beginning at an offset greater than zero.
        Expected: success=False, identifies missing initial byte range.
        """
        no_first = [self.frag2, self.frag3]
        result = reassemble_fragments(no_first)
        self.assertFalse(result.success)
        # Missing range from byte 0 to start of frag2 (185 * 8 = 1480)
        self.assertIn((0, 1480), result.missing_ranges)

    def test_6_no_final_fragment(self):
        """
        TEST 6 — No final fragment
        Provide fragments where every fragment has MF=True.
        Expected: success=False.
        """
        all_mf_true = [self.frag1, self.frag2]
        result = reassemble_fragments(all_mf_true)
        self.assertFalse(result.success)
        self.assertIsNone(result.expected_end_offset)
        self.assertIn("Missing final fragment", result.reason)

    def test_7_different_identification_values(self):
        """
        TEST 7 — Different Identification values
        Provide fragments belonging to different datagrams.
        Expected: success=False.
        """
        mixed_id_frag = Fragment(
            identification=2002,
            offset=370,
            payload_size=1020,
            total_size=1040,
            more_fragments=False,
        )
        result = reassemble_fragments([self.frag1, self.frag2, mixed_id_frag])
        self.assertFalse(result.success)
        self.assertIsNone(result.identification)
        self.assertIn("different datagrams", result.reason)

    def test_8_single_unfragmented_packet(self):
        """
        TEST 8 — Single unfragmented packet
        One fragment: offset=0, MF=False.
        Expected: success=True.
        """
        single_frag = Fragment(
            identification=5050,
            offset=0,
            payload_size=1000,
            total_size=1020,
            more_fragments=False,
        )
        result = reassemble_fragments([single_frag])
        self.assertTrue(result.success)
        self.assertEqual(result.payload_size, 1000)
        self.assertEqual(result.identification, 5050)
        self.assertEqual(result.fragment_count, 1)
        self.assertEqual(result.missing_ranges, [])
        self.assertEqual(result.overlaps, [])
        self.assertEqual(result.expected_end_offset, 1000)

    def test_empty_fragments_list(self):
        """Empty input list returns clean failure."""
        result = reassemble_fragments([])
        self.assertFalse(result.success)
        self.assertEqual(result.fragment_count, 0)
        self.assertIsNone(result.identification)

    def test_multiple_final_fragments(self):
        """Multiple fragments with MF=False must be rejected as invalid sequence."""
        dup_final = Fragment(
            identification=1001,
            offset=370,
            payload_size=1020,
            total_size=1040,
            more_fragments=False,
        )
        result = reassemble_fragments([self.frag1, self.frag3, dup_final])
        self.assertFalse(result.success)
        self.assertIn("found 2 final fragments", result.reason)

    def test_fragment_beyond_final_fragment(self):
        """A fragment situated past the marked final fragment must be rejected."""
        beyond_frag = Fragment(
            identification=1001,
            offset=500,
            payload_size=100,
            total_size=120,
            more_fragments=True,
        )
        result = reassemble_fragments([self.frag1, self.frag2, self.frag3, beyond_frag])
        self.assertFalse(result.success)
        self.assertIn("fragments exist beyond", result.reason)

    def test_group_by_identification_utility(self):
        """Verify grouping fragments by Identification field."""
        f_a1 = Fragment(101, 0, 1480, 1500, True)
        f_a2 = Fragment(101, 185, 1000, 1020, False)
        f_b1 = Fragment(202, 0, 500, 520, False)

        grouped = group_by_identification([f_a1, f_b1, f_a2])
        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[101]), 2)
        self.assertEqual(len(grouped[202]), 1)

    def test_class_interface_parity(self):
        """Verify IPv4Reassembler class interface matches function."""
        r1 = reassemble_fragments(self.standard_fragments)
        r2 = IPv4Reassembler.reassemble(self.standard_fragments)
        self.assertEqual(r1, r2)

    def test_end_to_end_fragment_and_reassemble(self):
        """Pipeline test: fragment a packet and reassemble it in both order and random shuffle."""
        payload_size = 7500
        mtu = 1500
        identification = 9876

        frags = fragment_packet(payload_size=payload_size, mtu=mtu, identification=identification)
        self.assertEqual(len(frags), 6)

        # In-order reassembly
        res_ordered = IPv4Reassembler.reassemble(frags)
        self.assertTrue(res_ordered.success)
        self.assertEqual(res_ordered.payload_size, payload_size)

        # Shuffled out-of-order reassembly
        shuffled_frags = list(frags)
        random.seed(42)
        random.shuffle(shuffled_frags)
        res_shuffled = IPv4Reassembler.reassemble(shuffled_frags)
        self.assertTrue(res_shuffled.success)
        self.assertEqual(res_shuffled.payload_size, payload_size)


if __name__ == "__main__":
    unittest.main()
