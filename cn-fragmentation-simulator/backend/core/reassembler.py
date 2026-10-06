"""
IPv4 Fragment Reassembly Engine for Intelligent IPv4 Fragmentation & Network Failure Simulator.

Reassembles IPv4 fragments logically according to RFC 791 specifications:
- Validates fragments belong to the same datagram (same Identification).
- Handles out-of-order delivery by sorting on byte offset.
- Verifies full coverage from byte 0 to the end of the final fragment (MF=False).
- Detects missing ranges (gaps) and overlapping fragments.
- Calculates reconstructed payload size.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from .models import Fragment


@dataclass
class ReassemblyResult:
    """
    Represents the result of an IPv4 fragment reassembly attempt.

    Attributes:
        success (bool): True if reassembly succeeded without gaps or overlaps.
        identification (Optional[int]): IPv4 Identification shared by the fragments.
        fragment_count (int): Total number of fragments analyzed.
        payload_size (int): Reconstructed payload size in bytes (0 on failure).
        missing_ranges (List[Tuple[int, int]]): Detected gap intervals [start_byte, end_byte).
        overlaps (List[Tuple[int, int]]): Detected overlapping intervals [start_byte, end_byte).
        reason (str): Descriptive reason for success or specific failure mode.
        expected_end_offset (Optional[int]): Expected total payload end offset from final fragment.
    """

    success: bool
    identification: Optional[int]
    fragment_count: int
    payload_size: int
    missing_ranges: List[Tuple[int, int]]
    overlaps: List[Tuple[int, int]]
    reason: str
    expected_end_offset: Optional[int] = None


def group_by_identification(fragments: Iterable[Fragment]) -> Dict[int, List[Fragment]]:
    """
    Groups a collection of fragments by their IPv4 Identification field.

    Args:
        fragments (Iterable[Fragment]): Collection of IPv4 fragments.

    Returns:
        Dict[int, List[Fragment]]: Dictionary mapping identification to its fragments.
    """
    grouped: Dict[int, List[Fragment]] = {}
    for frag in fragments:
        grouped.setdefault(frag.identification, []).append(frag)
    return grouped


def reassemble_fragments(fragments: Iterable[Fragment]) -> ReassemblyResult:
    """
    Logically reassembles a collection of fragments belonging to an IPv4 datagram.

    Args:
        fragments (Iterable[Fragment]): Fragments to reassemble (can arrive in any order).

    Returns:
        ReassemblyResult: Detailed reassembly status including missing ranges and overlaps.
    """
    frag_list = list(fragments)

    # 1. Handle empty input
    if not frag_list:
        return ReassemblyResult(
            success=False,
            identification=None,
            fragment_count=0,
            payload_size=0,
            missing_ranges=[],
            overlaps=[],
            reason="No fragments provided for reassembly.",
            expected_end_offset=None,
        )

    # 2. Verify all fragments share the exact same Identification
    identifications = {f.identification for f in frag_list}
    if len(identifications) > 1:
        return ReassemblyResult(
            success=False,
            identification=None,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=[],
            overlaps=[],
            reason=(
                f"Fragments belong to different datagrams: found multiple identifications "
                f"{sorted(identifications)}."
            ),
            expected_end_offset=None,
        )

    ident = frag_list[0].identification

    # 3. Inspect final fragments (MF=False)
    final_fragments = [f for f in frag_list if not f.more_fragments]
    if len(final_fragments) == 0:
        has_final = False
        expected_end_offset = None
    elif len(final_fragments) > 1:
        return ReassemblyResult(
            success=False,
            identification=ident,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=[],
            overlaps=[],
            reason=(
                f"Invalid fragment sequence: found {len(final_fragments)} final fragments "
                f"(MF=False), exactly 1 required."
            ),
            expected_end_offset=None,
        )
    else:
        has_final = True
        final_frag = final_fragments[0]
        expected_end_offset = (final_frag.offset * 8) + final_frag.payload_size

    # 4. Sort fragments by byte_start (offset * 8), then by payload_size to handle out-of-order delivery
    sorted_frags = sorted(frag_list, key=lambda f: (f.offset * 8, f.payload_size))

    # 5. Check if any fragment extends past the final fragment
    if has_final:
        final_end = (final_frag.offset * 8) + final_frag.payload_size
        fragments_beyond = [
            f for f in sorted_frags if (f.offset * 8 + f.payload_size) > final_end
        ]
        if fragments_beyond:
            return ReassemblyResult(
                success=False,
                identification=ident,
                fragment_count=len(frag_list),
                payload_size=0,
                missing_ranges=[],
                overlaps=[],
                reason="Invalid fragment sequence: fragments exist beyond the final fragment (MF=False).",
                expected_end_offset=expected_end_offset,
            )

    # 6. Analyze contiguous byte ranges, gaps, and overlaps
    missing_ranges: List[Tuple[int, int]] = []
    overlaps: List[Tuple[int, int]] = []

    # First fragment must start at byte offset 0
    first_byte_start = sorted_frags[0].offset * 8
    if first_byte_start > 0:
        missing_ranges.append((0, first_byte_start))
        covered_end = first_byte_start
    else:
        covered_end = 0

    for frag in sorted_frags:
        byte_start = frag.offset * 8
        byte_end = byte_start + frag.payload_size

        if frag.payload_size < 0:
            return ReassemblyResult(
                success=False,
                identification=ident,
                fragment_count=len(frag_list),
                payload_size=0,
                missing_ranges=[],
                overlaps=[],
                reason=f"Invalid fragment payload size: {frag.payload_size}.",
                expected_end_offset=expected_end_offset,
            )

        if byte_start < covered_end:
            # Overlapping byte range detected
            overlap_end = min(covered_end, byte_end)
            if overlap_end > byte_start:
                overlaps.append((byte_start, overlap_end))
            elif byte_start == byte_end:
                # Duplicate or zero-length fragment at or before covered_end
                overlaps.append((byte_start, byte_start))
            covered_end = max(covered_end, byte_end)
        elif byte_start > covered_end:
            # Gap (missing bytes) detected
            missing_ranges.append((covered_end, byte_start))
            covered_end = byte_end
        else:
            # Contiguous progression: byte_start == covered_end
            covered_end = byte_end

    # 7. Check if final fragment was missing
    if not has_final:
        return ReassemblyResult(
            success=False,
            identification=ident,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=missing_ranges,
            overlaps=overlaps,
            reason="Missing final fragment (no fragment with MF=False found).",
            expected_end_offset=None,
        )

    # 8. Check for overlaps
    if overlaps:
        return ReassemblyResult(
            success=False,
            identification=ident,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=missing_ranges,
            overlaps=overlaps,
            reason=f"Overlapping fragment byte ranges detected: {overlaps}.",
            expected_end_offset=expected_end_offset,
        )

    # 9. Check for missing ranges (gaps)
    if missing_ranges:
        return ReassemblyResult(
            success=False,
            identification=ident,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=missing_ranges,
            overlaps=overlaps,
            reason=f"Missing fragment byte ranges (gaps) detected: {missing_ranges}.",
            expected_end_offset=expected_end_offset,
        )

    # 10. Verify total coverage equals expected end offset
    if covered_end != expected_end_offset:
        return ReassemblyResult(
            success=False,
            identification=ident,
            fragment_count=len(frag_list),
            payload_size=0,
            missing_ranges=[(covered_end, expected_end_offset)],
            overlaps=overlaps,
            reason=f"Incomplete payload: covered {covered_end} bytes, expected {expected_end_offset} bytes.",
            expected_end_offset=expected_end_offset,
        )

    # 11. Successful reassembly
    return ReassemblyResult(
        success=True,
        identification=ident,
        fragment_count=len(frag_list),
        payload_size=covered_end,
        missing_ranges=[],
        overlaps=[],
        reason="Reassembly successful.",
        expected_end_offset=expected_end_offset,
    )


class IPv4Reassembler:
    """Component interface for IPv4 fragment reassembly."""

    @staticmethod
    def reassemble(fragments: Iterable[Fragment]) -> ReassemblyResult:
        """Reassembles a collection of fragments belonging to the same IPv4 datagram."""
        return reassemble_fragments(fragments)

    @staticmethod
    def group_by_identification(fragments: Iterable[Fragment]) -> Dict[int, List[Fragment]]:
        """Groups fragments by their IPv4 Identification field."""
        return group_by_identification(fragments)
