/**
 * TypeScript definitions representing the PacketForge IPv4 Simulator domain.
 * Mirrors schemas defined in backend/api/schemas.py and backend/core/models.py.
 */

// ---------------------------------------------------------------------------
// Core Fragment & Event Models
// ---------------------------------------------------------------------------

export interface Fragment {
  identification: number;
  offset: number;
  payload_size: number;
  total_size: number;
  more_fragments: boolean;
  df?: boolean;
}

export type TransmissionAction = 'delivered' | 'dropped' | 'duplicated' | 'corrupted';

export interface TransmissionEvent {
  sequence_number: number;
  original_fragment_index: number;
  action: TransmissionAction | string;
  delay_ms: number;
  detail: string;
}

export interface TransmissionResult {
  delivered_fragments: Fragment[];
  events: TransmissionEvent[];
  total_input: number;
  delivered_count: number;
  dropped_count: number;
  duplicate_count: number;
  corrupted_count: number;
}

export interface ReassemblyResult {
  success: boolean;
  identification: number | null;
  fragment_count: number;
  payload_size: number;
  missing_ranges: [number, number][];
  overlaps: [number, number][];
  reason: string;
  expected_end_offset: number | null;
}

// ---------------------------------------------------------------------------
// API Request & Response Schemas
// ---------------------------------------------------------------------------

export interface TransmissionConfig {
  reorder: boolean;
  drop_indices: number[];
  loss_indices?: number[];
  duplicate_indices: number[];
  corrupt_indices: number[];
  corruption_indices?: number[];
  delay_ms: number;
  seed: number | null;
  corruption_offset_shift: number;
}

export interface SimulationRequest {
  payload_size: number;
  mtu: number;
  identification: number;
  header_size: number;
  df?: boolean;
  transmission: TransmissionConfig;
}

export interface SimulationResponse {
  payload_size: number;
  mtu: number;
  identification: number;
  header_size: number;
  df?: boolean;
  fragmentation_prevented?: boolean;
  status?: string;
  reason?: string | null;
  fragment_count: number;
  generated_fragments: Fragment[];
  transmission_result: TransmissionResult;
  reassembly_result: ReassemblyResult;
  success: boolean;
}

export interface HealthResponse {
  status: string;
}

// ---------------------------------------------------------------------------
// UI State & Form Validation Types
// ---------------------------------------------------------------------------

export interface SimulationFormData {
  payloadSize: number;
  mtu: number;
  identification: number;
  headerSize: number;
  df: boolean;
  reorder: boolean;
  dropIndicesStr: string;
  duplicateIndicesStr: string;
  corruptIndicesStr: string;
  delayMs: number;
  seed: number | null;
}

export interface FormValidationErrors {
  payloadSize?: string;
  mtu?: string;
  identification?: string;
  headerSize?: string;
  delayMs?: string;
  dropIndices?: string;
  duplicateIndices?: string;
  corruptIndices?: string;
}
