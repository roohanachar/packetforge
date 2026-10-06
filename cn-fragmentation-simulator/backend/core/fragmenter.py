"""
IPv4 Fragmentation Engine for Intelligent IPv4 Fragmentation & Network Failure Simulator.

Implements standard IPv4 packet fragmentation according to RFC 791 rules:
- Fragment payload for non-final fragments must align to 8-byte boundaries.
- Total size of each fragment (header + payload) must not exceed link MTU.
- Fragment offset is expressed in 8-byte (64-bit) units.
- MF (More Fragments) flag is True for all fragments except the final one.
- DF (Don't Fragment) flag enforcement: if DF is set and datagram exceeds MTU,
  fragmentation is prevented.
"""

from typing import List
from .models import Fragment


class FragmentationPreventedError(ValueError):
    """
    Raised or referenced when an IPv4 datagram exceeds the link MTU but the
    Don't Fragment (DF) flag is set to 1.
    """
    pass


def fragment_packet(
    payload_size: int,
    mtu: int,
    identification: int,
    header_size: int = 20,
    df: bool = False,
    raise_on_df: bool = False,
) -> List[Fragment]:
    """
    Fragments an IPv4 packet into standard-compliant fragments based on the link MTU.

    Args:
        payload_size (int): Size of the original packet payload in bytes (must be >= 0).
        mtu (int): Maximum Transmission Unit of the network link in bytes.
        identification (int): 16-bit IPv4 Identification value (0 to 65535).
        header_size (int): Size of the IPv4 header in bytes (default 20 bytes).
        df (bool): IPv4 Don't Fragment flag (1-bit). Default False.
        raise_on_df (bool): If True and packet exceeds MTU with DF=1, raises
            FragmentationPreventedError instead of returning an empty list.

    Returns:
        List[Fragment]: Ordered list of Fragment objects. Returns an empty list
            if packet exceeds MTU and DF=1 (when raise_on_df=False).

    Raises:
        ValueError: If MTU <= header_size, payload_size < 0, identification is outside
            the 16-bit range [0, 65535], or MTU is too small to carry an 8-byte aligned payload.
        FragmentationPreventedError: If packet exceeds MTU and DF=1 and raise_on_df=True.
    """
    # 1. Validation
    if header_size < 20:
        raise ValueError(f"header_size ({header_size}) must be at least 20 bytes for IPv4.")

    if mtu <= header_size:
        raise ValueError(f"MTU ({mtu}) must be greater than IPv4 header size ({header_size}).")

    if payload_size < 0:
        raise ValueError(f"payload_size ({payload_size}) must be non-negative.")

    if not (0 <= identification <= 0xFFFF):
        raise ValueError(
            f"identification ({identification}) must be a valid 16-bit integer (0 to 65535)."
        )

    packet_size = header_size + payload_size

    # 2. Case: Payload fits within MTU without fragmentation (RFC 791 Case A)
    if packet_size <= mtu:
        return [
            Fragment(
                identification=identification,
                offset=0,
                payload_size=payload_size,
                total_size=packet_size,
                more_fragments=False,
                df=df,
            )
        ]

    # 3. Case: Packet exceeds MTU with DF=1 (RFC 791 Case C: Fragmentation Prevented)
    if df:
        if raise_on_df:
            raise FragmentationPreventedError(
                f"Datagram size ({packet_size}B) exceeds link MTU ({mtu}B), "
                f"but Don't Fragment (DF) flag is set."
            )
        return []

    # 4. Case: Packet exceeds MTU with DF=0 (RFC 791 Case B: Standard Fragmentation)
    # Calculate max fragment payload (must be a multiple of 8 bytes per RFC 791)
    max_payload = ((mtu - header_size) // 8) * 8
    if max_payload < 8:
        raise ValueError(
            f"Available payload per fragment ({mtu - header_size} bytes) is too small "
            f"to carry an 8-byte aligned fragment payload."
        )

    fragments: List[Fragment] = []
    current_byte_offset = 0
    remaining_payload = payload_size

    while remaining_payload > 0:
        # Check if the remaining payload fits entirely in one last fragment
        if remaining_payload <= (mtu - header_size):
            frag_payload = remaining_payload
            mf = False
        else:
            frag_payload = max_payload
            mf = True

        fragment = Fragment(
            identification=identification,
            offset=current_byte_offset // 8,
            payload_size=frag_payload,
            total_size=header_size + frag_payload,
            more_fragments=mf,
            df=False,
        )

        # Sanity validation on generated fragment
        if mf and (frag_payload % 8 != 0):
            raise ValueError(
                f"Non-final fragment payload ({frag_payload}) must be a multiple of 8 bytes."
            )
        if fragment.total_size > mtu:
            raise ValueError(
                f"Fragment total size ({fragment.total_size}) exceeds MTU ({mtu})."
            )

        fragments.append(fragment)
        current_byte_offset += frag_payload
        remaining_payload -= frag_payload

    return fragments


class IPv4Fragmenter:
    """Utility class interface for IPv4 packet fragmentation."""

    @staticmethod
    def fragment(
        payload_size: int,
        mtu: int,
        identification: int,
        header_size: int = 20,
        df: bool = False,
        raise_on_df: bool = False,
    ) -> List[Fragment]:
        """Delegate to fragment_packet function."""
        return fragment_packet(
            payload_size,
            mtu,
            identification,
            header_size,
            df=df,
            raise_on_df=raise_on_df,
        )
