"""
Pydantic schemas for IPv4 Fragmentation & Network Failure Simulator API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from backend.core.models import Fragment
from backend.core.transmitter import TransmissionConfig, TransmissionEvent, TransmissionResult
from backend.core.reassembler import ReassemblyResult
from backend.core.simulator import SimulationConfig, SimulationResult


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class TransmissionConfigSchema(BaseModel):
    """
    Schema for network transmission simulation options.
    """

    reorder: bool = Field(default=False, description="Whether fragments should arrive out of order.")
    drop_indices: List[int] = Field(default_factory=list, description="0-based indices of fragments to drop.")
    loss_indices: Optional[List[int]] = Field(default=None, description="Alias for drop_indices.")
    duplicate_indices: List[int] = Field(default_factory=list, description="0-based indices of fragments to duplicate.")
    corrupt_indices: List[int] = Field(default_factory=list, description="0-based indices of fragments to corrupt.")
    corruption_indices: Optional[List[int]] = Field(default=None, description="Alias for corrupt_indices.")
    delay_ms: int = Field(default=0, ge=0, description="Simulated latency in milliseconds.")
    seed: Optional[int] = Field(default=None, description="Optional PRNG seed for deterministic simulation.")
    corruption_offset_shift: int = Field(default=10, description="Offset change applied during metadata corruption.")

    def to_core(self) -> TransmissionConfig:
        """Converts to core TransmissionConfig domain object."""
        drops = list(self.drop_indices)
        if self.loss_indices is not None:
            drops.extend(self.loss_indices)

        corrupts = list(self.corrupt_indices)
        if self.corruption_indices is not None:
            corrupts.extend(self.corruption_indices)

        return TransmissionConfig(
            reorder=self.reorder,
            drop_indices=drops,
            duplicate_indices=self.duplicate_indices,
            corrupt_indices=corrupts,
            delay_ms=self.delay_ms,
            seed=self.seed,
            corruption_offset_shift=self.corruption_offset_shift,
        )


class SimulationRequest(BaseModel):
    """
    Schema for end-to-end packet simulation request.
    """

    payload_size: int = Field(..., ge=0, description="Size of unfragmented datagram payload in bytes.")
    mtu: int = Field(..., gt=20, description="Maximum Transmission Unit in bytes (must be > header_size).")
    identification: int = Field(..., ge=0, le=65535, description="16-bit IPv4 Identification (0 to 65535).")
    header_size: int = Field(default=20, ge=20, description="IPv4 header size in bytes (default: 20).")
    df: bool = Field(default=False, description="IPv4 Don't Fragment (DF) flag.")
    transmission: TransmissionConfigSchema = Field(
        default_factory=TransmissionConfigSchema,
        description="Transmission simulation options.",
    )

    @model_validator(mode="after")
    def validate_bounds(self) -> "SimulationRequest":
        if self.mtu <= self.header_size:
            raise ValueError(f"MTU ({self.mtu}) must be greater than header_size ({self.header_size}).")
        return self

    def to_core(self) -> SimulationConfig:
        """Converts to core SimulationConfig domain object."""
        return SimulationConfig(
            payload_size=self.payload_size,
            mtu=self.mtu,
            identification=self.identification,
            header_size=self.header_size,
            df=self.df,
            transmission=self.transmission.to_core(),
        )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class FragmentSchema(BaseModel):
    """Schema representing an individual IPv4 packet fragment."""

    identification: int
    offset: int
    payload_size: int
    total_size: int
    more_fragments: bool
    df: bool = False

    @classmethod
    def from_core(cls, fragment: Fragment, df: bool = False) -> "FragmentSchema":
        return cls(
            identification=fragment.identification,
            offset=fragment.offset,
            payload_size=fragment.payload_size,
            total_size=fragment.total_size,
            more_fragments=fragment.more_fragments,
            df=getattr(fragment, "df", df),
        )


class TransmissionEventSchema(BaseModel):
    """Schema representing a transmission event in the delivery timeline."""

    sequence_number: int
    original_fragment_index: int
    action: str
    delay_ms: int
    detail: str

    @classmethod
    def from_core(cls, event: TransmissionEvent) -> "TransmissionEventSchema":
        return cls(
            sequence_number=event.sequence_number,
            original_fragment_index=event.original_fragment_index,
            action=event.action,
            delay_ms=event.delay_ms,
            detail=event.detail,
        )


class TransmissionResultSchema(BaseModel):
    """Schema representing the transmission simulation result."""

    delivered_fragments: List[FragmentSchema]
    events: List[TransmissionEventSchema]
    total_input: int
    delivered_count: int
    dropped_count: int
    duplicate_count: int
    corrupted_count: int

    @classmethod
    def from_core(cls, result: TransmissionResult) -> "TransmissionResultSchema":
        return cls(
            delivered_fragments=[FragmentSchema.from_core(f) for f in result.delivered_fragments],
            events=[TransmissionEventSchema.from_core(e) for e in result.events],
            total_input=result.total_input,
            delivered_count=result.delivered_count,
            dropped_count=result.dropped_count,
            duplicate_count=result.duplicate_count,
            corrupted_count=result.corrupted_count,
        )


class ReassemblyResultSchema(BaseModel):
    """Schema representing the reassembly outcome and layout analysis."""

    success: bool
    identification: Optional[int]
    fragment_count: int
    payload_size: int
    missing_ranges: List[List[int]]
    overlaps: List[List[int]]
    reason: str
    expected_end_offset: Optional[int] = None

    @classmethod
    def from_core(cls, result: ReassemblyResult) -> "ReassemblyResultSchema":
        return cls(
            success=result.success,
            identification=result.identification,
            fragment_count=result.fragment_count,
            payload_size=result.payload_size,
            missing_ranges=[list(r) for r in result.missing_ranges],
            overlaps=[list(r) for r in result.overlaps],
            reason=result.reason,
            expected_end_offset=result.expected_end_offset,
        )


class SimulationResponse(BaseModel):
    """
    Unified response schema providing complete visibility into all simulation stages.
    """

    payload_size: int
    mtu: int
    identification: int
    header_size: int
    df: bool = False
    fragmentation_prevented: bool = False
    status: str = "success"
    reason: Optional[str] = None
    fragment_count: int
    generated_fragments: List[FragmentSchema]
    transmission_result: TransmissionResultSchema
    reassembly_result: ReassemblyResultSchema
    success: bool

    @classmethod
    def from_core(cls, result: SimulationResult, df: bool = False) -> "SimulationResponse":
        effective_df = getattr(result, "df", df)
        return cls(
            payload_size=result.payload_size,
            mtu=result.mtu,
            identification=result.identification,
            header_size=result.header_size,
            df=effective_df,
            fragmentation_prevented=getattr(result, "fragmentation_prevented", False),
            status=getattr(result, "status", "success"),
            reason=getattr(result, "reason", None),
            fragment_count=result.fragment_count,
            generated_fragments=[FragmentSchema.from_core(f, df=effective_df) for f in result.generated_fragments],
            transmission_result=TransmissionResultSchema.from_core(result.transmission_result),
            reassembly_result=ReassemblyResultSchema.from_core(result.reassembly_result),
            success=result.success,
        )


class HealthResponse(BaseModel):
    """Schema for API health status."""

    status: str = "ok"
