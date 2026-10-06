"""
IPv4 Transmission Simulator for Intelligent IPv4 Fragmentation & Network Failure Simulator.

Simulates transmission of IPv4 fragments over an unreliable network link:
- Out-of-order arrival (reordering via local PRNG).
- Packet loss (dropped fragments).
- Packet duplication (duplicate fragments).
- Network latency (simulated delay_ms recorded in events).
- Metadata-level fragment corruption (altered offset without mutating original Fragment).

Pure logical simulation:
- No network sockets or real I/O.
- Deterministic behavior via configurable random seeds.
- Independent of any web framework.
"""

from dataclasses import dataclass, field, replace
import random
from typing import Collection, Iterable, List, Optional
from .models import Fragment


@dataclass
class TransmissionConfig:
    """
    Configuration for simulating IPv4 fragment transmission over an unreliable network.

    Attributes:
        reorder (bool): Whether fragments should arrive out of order.
        drop_indices (Collection[int]): 0-based indices of fragments to drop (packet loss).
        duplicate_indices (Collection[int]): 0-based indices of fragments to duplicate.
        corrupt_indices (Collection[int]): 0-based indices of fragments whose metadata should be corrupted.
        delay_ms (int): Simulated transmission latency in milliseconds.
        seed (Optional[int]): Random seed for deterministic simulation.
        corruption_offset_shift (int): Offset change applied when simulating metadata corruption (default 10).
    """

    reorder: bool = False
    drop_indices: Collection[int] = field(default_factory=list)
    duplicate_indices: Collection[int] = field(default_factory=list)
    corrupt_indices: Collection[int] = field(default_factory=list)
    delay_ms: int = 0
    seed: Optional[int] = None
    corruption_offset_shift: int = 10


@dataclass
class TransmissionEvent:
    """
    Represents an event that occurred to an IPv4 fragment during transmission.

    Attributes:
        sequence_number (int): Chronological sequence number of this event.
        original_fragment_index (int): 0-based index of the original fragment in the input list.
        action (str): Action taken ("delivered", "dropped", "duplicated", "corrupted").
        delay_ms (int): Simulated transmission latency in milliseconds.
        detail (str): Descriptive detail / explanation of the event.
    """

    sequence_number: int
    original_fragment_index: int
    action: str
    delay_ms: int
    detail: str

    @property
    def fragment_index(self) -> int:
        """Alias for original_fragment_index for convenience."""
        return self.original_fragment_index


@dataclass
class TransmissionResult:
    """
    Result of a transmission simulation run.

    Attributes:
        delivered_fragments (List[Fragment]): Fragments that reached the destination.
        events (List[TransmissionEvent]): Chronological event log of the transmission.
        total_input (int): Total number of input fragments passed into simulator.
        delivered_count (int): Number of fragments successfully delivered (including duplicates/corrupted).
        dropped_count (int): Number of fragments dropped due to simulated packet loss.
        duplicate_count (int): Number of duplicate fragment events generated.
        corrupted_count (int): Number of fragment metadata corruption events generated.
    """

    delivered_fragments: List[Fragment]
    events: List[TransmissionEvent]
    total_input: int
    delivered_count: int
    dropped_count: int
    duplicate_count: int
    corrupted_count: int


def simulate_transmission(
    fragments: Iterable[Fragment],
    config: Optional[TransmissionConfig] = None,
) -> TransmissionResult:
    """
    Simulates the transmission of IPv4 fragments through an unreliable network.

    Args:
        fragments (Iterable[Fragment]): Input fragments in sender creation order.
        config (Optional[TransmissionConfig]): Simulation parameters and failure conditions.

    Returns:
        TransmissionResult: Delivered fragments and event timeline.
    """
    if config is None:
        config = TransmissionConfig()

    if config.delay_ms < 0:
        raise ValueError(f"delay_ms ({config.delay_ms}) must be non-negative.")

    frag_list = list(fragments)
    total_input = len(frag_list)

    if total_input == 0:
        return TransmissionResult(
            delivered_fragments=[],
            events=[],
            total_input=0,
            delivered_count=0,
            dropped_count=0,
            duplicate_count=0,
            corrupted_count=0,
        )

    drop_set = set(config.drop_indices)
    duplicate_set = set(config.duplicate_indices)
    corrupt_set = set(config.corrupt_indices)

    # Temporary storage for events and delivered items
    dropped_events: List[TransmissionEvent] = []
    delivered_items: List[tuple[Fragment, TransmissionEvent]] = []

    dropped_count = 0
    duplicate_count = 0
    corrupted_count = 0

    shift = config.corruption_offset_shift if config.corruption_offset_shift != 0 else 10

    # 1. Process each fragment according to configured conditions
    for idx, frag in enumerate(frag_list):
        # Case A: Fragment Loss (Dropped)
        if idx in drop_set:
            dropped_count += 1
            event = TransmissionEvent(
                sequence_number=0,  # Will be assigned chronologically below
                original_fragment_index=idx,
                action="dropped",
                delay_ms=config.delay_ms,
                detail=f"Fragment {idx} (ID={frag.identification}, Offset={frag.offset}) dropped (packet loss).",
            )
            dropped_events.append(event)
            # Dropped fragments are not delivered and cannot be duplicated/corrupted
            continue

        # Case B: Metadata Corruption (Altered copy without mutating original)
        if idx in corrupt_set:
            corrupted_count += 1
            new_offset = frag.offset + shift
            corrupted_frag = replace(frag, offset=new_offset)
            event = TransmissionEvent(
                sequence_number=0,
                original_fragment_index=idx,
                action="corrupted",
                delay_ms=config.delay_ms,
                detail=(
                    f"Fragment {idx} metadata corrupted: offset modified from "
                    f"{frag.offset} to {corrupted_frag.offset} (logical simulation)."
                ),
            )
            delivered_items.append((corrupted_frag, event))
            primary_frag = corrupted_frag
        else:
            # Normal delivery
            event = TransmissionEvent(
                sequence_number=0,
                original_fragment_index=idx,
                action="delivered",
                delay_ms=config.delay_ms,
                detail=f"Fragment {idx} (ID={frag.identification}, Offset={frag.offset}) delivered.",
            )
            delivered_items.append((frag, event))
            primary_frag = frag

        # Case C: Duplication (Fragment appears an additional time)
        if idx in duplicate_set:
            duplicate_count += 1
            dup_frag = replace(primary_frag)
            dup_event = TransmissionEvent(
                sequence_number=0,
                original_fragment_index=idx,
                action="duplicated",
                delay_ms=config.delay_ms,
                detail=f"Fragment {idx} duplicated during transmission.",
            )
            delivered_items.append((dup_frag, dup_event))

    # 2. Out-of-order reordering (if configured)
    if config.reorder and len(delivered_items) > 1:
        rng = random.Random(config.seed)
        shuffled_items = list(delivered_items)
        rng.shuffle(shuffled_items)
        # Guarantee that reorder=True alters order even if random permutation matches original
        if [item[0] for item in shuffled_items] == [item[0] for item in delivered_items]:
            shuffled_items = shuffled_items[1:] + shuffled_items[:1]
        delivered_items = shuffled_items

    delivered_fragments = [item[0] for item in delivered_items]

    # 3. Assemble timeline of events with sequential sequence numbers
    # Dropped events occur during transit; delivered events follow arrival order
    all_events = dropped_events + [item[1] for item in delivered_items]
    for seq_num, event in enumerate(all_events, start=1):
        event.sequence_number = seq_num

    return TransmissionResult(
        delivered_fragments=delivered_fragments,
        events=all_events,
        total_input=total_input,
        delivered_count=len(delivered_fragments),
        dropped_count=dropped_count,
        duplicate_count=duplicate_count,
        corrupted_count=corrupted_count,
    )


class TransmissionSimulator:
    """Simulator component for IPv4 fragment transmission."""

    @staticmethod
    def simulate(
        fragments: Iterable[Fragment],
        config: Optional[TransmissionConfig] = None,
    ) -> TransmissionResult:
        """Simulates transmission of IPv4 fragments under configured network conditions."""
        return simulate_transmission(fragments, config)
