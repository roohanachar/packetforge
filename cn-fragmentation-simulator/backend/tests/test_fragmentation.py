"""
Tests for IPv4 Fragmentation Engine.
"""

import unittest
from backend.core.models import Fragment
from backend.core.fragmenter import fragment_packet, IPv4Fragmenter


class TestIPv4Fragmentation(unittest.TestCase):
    """Test suite for IPv4 fragmentation logic conforming to RFC 791."""

    def test_1_multifragment_standard(self):
        """
        TEST 1:
        payload_size=3980, mtu=1500, header_size=20, identification=1001
        Expected:
            3 fragments
            payload sizes = [1480, 1480, 1020]
            offsets = [0, 185, 370]
            MF = [True, True, False]
            total sizes = [1500, 1500, 1040]
        """
        payload_size = 3980
        mtu = 1500
        header_size = 20
        identification = 1001

        fragments = fragment_packet(
            payload_size=payload_size,
            mtu=mtu,
            identification=identification,
            header_size=header_size,
        )

        self.assertEqual(len(fragments), 3)

        self.assertEqual([f.payload_size for f in fragments], [1480, 1480, 1020])
        self.assertEqual([f.offset for f in fragments], [0, 185, 370])
        self.assertEqual([f.more_fragments for f in fragments], [True, True, False])
        self.assertEqual([f.total_size for f in fragments], [1500, 1500, 1040])
        self.assertTrue(all(f.identification == 1001 for f in fragments))

        # Check total reassembled payload matches original
        self.assertEqual(sum(f.payload_size for f in fragments), payload_size)

    def test_2_single_fragment_within_mtu(self):
        """
        TEST 2:
        payload_size=1000, mtu=1500, header_size=20
        Expected:
            1 fragment
            payload_size=1000
            offset=0
            MF=False
            total_size=1020
        """
        payload_size = 1000
        mtu = 1500
        header_size = 20
        identification = 1002

        fragments = fragment_packet(
            payload_size=payload_size,
            mtu=mtu,
            identification=identification,
            header_size=header_size,
        )

        self.assertEqual(len(fragments), 1)
        frag = fragments[0]
        self.assertEqual(frag.identification, identification)
        self.assertEqual(frag.payload_size, 1000)
        self.assertEqual(frag.offset, 0)
        self.assertFalse(frag.more_fragments)
        self.assertEqual(frag.total_size, 1020)

    def test_3_non_multiple_of_8_payload(self):
        """
        TEST 3:
        Use a payload size that requires fragmentation but is not itself a multiple of 8,
        and verify that only non-final fragments are aligned to 8-byte boundaries.
        """
        # 3005 is not divisible by 8 (3005 = 375 * 8 + 5)
        payload_size = 3005
        mtu = 1500
        header_size = 20
        identification = 2003

        fragments = fragment_packet(
            payload_size=payload_size,
            mtu=mtu,
            identification=identification,
            header_size=header_size,
        )

        self.assertEqual(len(fragments), 3)

        # Non-final fragments must be multiples of 8 bytes
        for i in range(len(fragments) - 1):
            frag = fragments[i]
            self.assertTrue(frag.more_fragments, f"Fragment {i} must have MF=True")
            self.assertEqual(
                frag.payload_size % 8,
                0,
                f"Non-final fragment {i} payload ({frag.payload_size}) must be multiple of 8",
            )
            self.assertLessEqual(frag.total_size, mtu)

        # Final fragment must have MF=False and in this test is NOT a multiple of 8
        final_frag = fragments[-1]
        self.assertFalse(final_frag.more_fragments, "Final fragment must have MF=False")
        self.assertEqual(final_frag.payload_size, 45)
        self.assertNotEqual(
            final_frag.payload_size % 8,
            0,
            "Final fragment payload in this test is deliberately not a multiple of 8",
        )
        self.assertEqual(final_frag.total_size, 20 + 45)
        self.assertLessEqual(final_frag.total_size, mtu)

        # Total payload preservation
        self.assertEqual(sum(f.payload_size for f in fragments), payload_size)

    def test_boundary_payload_exactly_equals_mtu(self):
        """When total packet size exactly equals MTU, no fragmentation is needed."""
        payload_size = 1480
        mtu = 1500
        header_size = 20
        fragments = fragment_packet(payload_size, mtu, identification=5000, header_size=header_size)
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0].offset, 0)
        self.assertFalse(fragments[0].more_fragments)
        self.assertEqual(fragments[0].total_size, 1500)

    def test_zero_payload(self):
        """Zero payload datagram produces one fragment with MF=False."""
        fragments = fragment_packet(payload_size=0, mtu=1500, identification=10)
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0].payload_size, 0)
        self.assertEqual(fragments[0].total_size, 20)
        self.assertFalse(fragments[0].more_fragments)

    def test_class_interface(self):
        """Verify IPv4Fragmenter class interface matches function."""
        f_func = fragment_packet(3980, 1500, 1001, 20)
        f_class = IPv4Fragmenter.fragment(3980, 1500, 1001, 20)
        self.assertEqual(f_func, f_class)

    def test_validation_errors(self):
        """Verify validation errors for invalid inputs."""
        # MTU <= header_size
        with self.assertRaises(ValueError):
            fragment_packet(100, 20, 1, header_size=20)

        # Negative payload
        with self.assertRaises(ValueError):
            fragment_packet(-10, 1500, 1)

        # Invalid identification (negative or > 65535)
        with self.assertRaises(ValueError):
            fragment_packet(100, 1500, -1)
        with self.assertRaises(ValueError):
            fragment_packet(100, 1500, 65536)

        # Header size < 20
        with self.assertRaises(ValueError):
            fragment_packet(100, 1500, 1, header_size=16)

        # MTU too small to hold at least an 8-byte aligned fragment
        with self.assertRaises(ValueError):
            fragment_packet(100, 24, 1, header_size=20)

    def test_df_packet_fits_within_mtu(self):
        """TEST: Payload=400, MTU=1500, DF=1 -> 1 fragment, total_size=420, offset=0, MF=0, DF=1."""
        fragments = fragment_packet(payload_size=400, mtu=1500, identification=1001, df=True)
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0].payload_size, 400)
        self.assertEqual(fragments[0].total_size, 420)
        self.assertEqual(fragments[0].offset, 0)
        self.assertFalse(fragments[0].more_fragments)
        self.assertTrue(fragments[0].df)

    def test_df_packet_exceeds_mtu_prevented(self):
        """TEST: Payload=3000, MTU=1500, DF=1 -> 0 fragments (fragmentation prevented)."""
        fragments = fragment_packet(payload_size=3000, mtu=1500, identification=1002, df=True)
        self.assertEqual(len(fragments), 0)
        self.assertEqual(fragments, [])

    def test_df_packet_exceeds_mtu_raise_on_df(self):
        """TEST: Payload=3000, MTU=1500, DF=1, raise_on_df=True -> raises FragmentationPreventedError."""
        from backend.core.fragmenter import FragmentationPreventedError
        with self.assertRaises(FragmentationPreventedError):
            fragment_packet(payload_size=3000, mtu=1500, identification=1003, df=True, raise_on_df=True)


if __name__ == "__main__":
    unittest.main()
