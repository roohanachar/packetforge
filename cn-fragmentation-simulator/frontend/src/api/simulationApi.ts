/**
 * API client module for communicating with the FastAPI IPv4 Simulator backend.
 */

import {
  SimulationRequest,
  SimulationResponse,
  HealthResponse,
} from '../types/simulation';

// Use relative API path (proxied by Vite in dev) or fallback to direct URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  status?: number;
  isBackendUnavailable?: boolean;

  constructor(message: string, status?: number, isBackendUnavailable: boolean = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.isBackendUnavailable = isBackendUnavailable;
  }
}

/**
 * Checks if the backend API is reachable and healthy.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      return false;
    }

    const data: HealthResponse = await response.json();
    return data.status === 'ok';
  } catch {
    // If proxied fetch failed, try direct connection to localhost:8000
    try {
      const directResponse = await fetch('http://127.0.0.1:8000/api/health');
      if (directResponse.ok) {
        const data: HealthResponse = await directResponse.json();
        return data.status === 'ok';
      }
      return false;
    } catch {
      return false;
    }
  }
}

/**
 * Sends packet parameters and failure configurations to the FastAPI simulator backend.
 */
export async function simulatePacket(
  request: SimulationRequest
): Promise<SimulationResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
  } catch (networkErr: unknown) {
    // Network failure / server offline
    const errMsg = networkErr instanceof Error ? networkErr.message : String(networkErr);
    throw new ApiError(
      `FastAPI backend unavailable at http://127.0.0.1:8000 (${errMsg}). Please confirm 'python -m uvicorn backend.api.main:app --reload' is running.`,
      undefined,
      true
    );
  }

  // Handle HTTP error statuses
  if (!response.ok) {
    let errorDetail = response.statusText || 'Simulation request failed';
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          // Pydantic validation error array
          errorDetail = errJson.detail
            .map((d: { loc?: (string | number)[]; msg?: string }) => {
              const field = d.loc ? d.loc.slice(1).join('.') : '';
              return field ? `${field}: ${d.msg}` : d.msg || JSON.stringify(d);
            })
            .join('; ');
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      }
    } catch {
      // Body not JSON
    }

    throw new ApiError(
      `API Error (${response.status}): ${errorDetail}`,
      response.status,
      false
    );
  }

  // Parse JSON response
  let data: SimulationResponse;
  try {
    data = await response.json();
  } catch (parseErr) {
    throw new ApiError(
      `Failed to parse response from simulator backend: ${parseErr instanceof Error ? parseErr.message : 'Invalid JSON'}`,
      response.status
    );
  }

  // Validate response integrity
  if (
    !data ||
    typeof data !== 'object' ||
    !Array.isArray(data.generated_fragments) ||
    !data.transmission_result ||
    !data.reassembly_result
  ) {
    throw new ApiError(
      'Malformed response: Missing expected simulation stages in backend response payload.',
      response.status
    );
  }

  return data;
}
