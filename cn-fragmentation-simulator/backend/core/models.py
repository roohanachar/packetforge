"""
IPv4 Fragment Data Model for Intelligent IPv4 Fragmentation & Network Failure Simulator.

Represents an individual IPv4 packet fragment and its header metadata
as specified in RFC 791.
"""

from dataclasses import dataclass


@dataclass
class Fragment:
    """
    Represents an IPv4 packet fragment.

    Attributes:
        identification (int): IPv4 Identification field (16-bit). Uniquely identifies
            the original datagram to which this fragment belongs, allowing the
            destination to group fragments for reassembly.
        offset (int): Fragment Offset field. Indicates the position of this fragment's
            payload relative to the start of the original datagram payload,
            measured in 8-byte (64-bit) blocks as per RFC 791 (i.e., byte offset / 8).
        payload_size (int): The amount of data/payload (in bytes) carried by this
            specific fragment, excluding the IPv4 header.
        total_size (int): Complete fragment size in bytes, including the IPv4 header
            (e.g., 20 bytes standard header) plus payload_size. Must not exceed link MTU.
        more_fragments (bool): More Fragments (MF) control flag (1-bit). Set to True (MF=1)
            if more fragments follow; set to False (MF=0) if this is the final fragment.
        df (bool): Don't Fragment (DF) control flag (1-bit). Default False.
    """

    identification: int
    offset: int
    payload_size: int
    total_size: int
    more_fragments: bool
    df: bool = False
