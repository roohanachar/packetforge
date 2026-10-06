"""
Core engine package for IPv4 Fragmentation & Network Failure Simulator.
"""

from .models import Fragment
from .fragmenter import FragmentationPreventedError, IPv4Fragmenter, fragment_packet
from .reassembler import (
    IPv4Reassembler,
    ReassemblyResult,
    group_by_identification,
    reassemble_fragments,
)
from .transmitter import (
    TransmissionConfig,
    TransmissionEvent,
    TransmissionResult,
    TransmissionSimulator,
    simulate_transmission,
)
from .simulator import (
    PacketSimulator,
    SimulationConfig,
    SimulationResult,
    simulate_packet,
)

__all__ = [
    "Fragment",
    "FragmentationPreventedError",
    "IPv4Fragmenter",
    "IPv4Reassembler",
    "PacketSimulator",
    "ReassemblyResult",
    "SimulationConfig",
    "SimulationResult",
    "TransmissionConfig",
    "TransmissionEvent",
    "TransmissionResult",
    "TransmissionSimulator",
    "fragment_packet",
    "group_by_identification",
    "reassemble_fragments",
    "simulate_packet",
    "simulate_transmission",
]
