import React from 'react';
import { CheckCircle2, XCircle, Puzzle, AlertTriangle, Layers } from 'lucide-react';
import { SimulationResponse } from '../types/simulation';

interface Props {
  data: SimulationResponse | null;
}

export const ReassemblyPanel: React.FC<Props> = ({ data }) => {
  return (
    <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-cyber-800 mb-4">
        <div className="flex items-center gap-2">
          <Puzzle className="w-4 h-4 text-forge-emerald" />
          <h3 className="text-sm font-semibold text-white tracking-wide">
            4. Logical Reassembly &amp; Verdict
          </h3>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyber-800 text-cyber-400">
          Receiver Verification
        </span>
      </div>

      {!data ? (
        <div className="p-8 rounded-lg bg-cyber-950/60 border border-cyber-850 border-dashed text-center flex flex-col items-center justify-center">
          <Puzzle className="w-8 h-8 text-cyber-700 mb-2 stroke-[1.5]" />
          <p className="text-xs text-cyber-400 font-medium">
            Fragment layout evaluation and payload reconstruction will appear here.
          </p>
          <p className="text-[11px] text-cyber-500 mt-1">
            Detects missing byte gaps, overlapping intervals, out-of-order reordering, and final completion.
          </p>
        </div>
      ) : (
        <div className="space-y-4 font-mono text-xs">
          {/* Verdict Banner */}
          <div
            className={`p-4 rounded-lg border flex items-start gap-3 transition-colors ${
              data.fragmentation_prevented
                ? 'bg-forge-amber/10 border-forge-amber/30 text-forge-amber'
                : data.reassembly_result.success
                ? 'bg-forge-emerald/10 border-forge-emerald/30 text-forge-emerald'
                : 'bg-forge-rose/10 border-forge-rose/30 text-forge-rose'
            }`}
          >
            {data.fragmentation_prevented ? (
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-forge-amber" />
            ) : data.reassembly_result.success ? (
              <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-bold text-sm block">
                {data.fragmentation_prevented
                  ? "Reassembly Prevented — Don't Fragment (DF) Enforced"
                  : data.reassembly_result.success
                  ? 'Reassembly Successful'
                  : 'Reassembly Incomplete / Failed'}
              </span>
              <p className="text-xs text-cyber-200 mt-1 font-mono">
                {data.reassembly_result.reason}
              </p>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Reconstructed payload size */}
            <div className="p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <span className="text-cyber-500 block text-[10px] uppercase">
                Reconstructed Payload
              </span>
              <span className="text-white text-base font-bold">
                {data.reassembly_result.payload_size} B
              </span>
              <span className="text-[10px] text-cyber-500 block mt-0.5">
                Expected: {data.payload_size} B
              </span>
            </div>

            {/* Missing Ranges / Gaps */}
            <div
              className={`p-3 rounded-lg bg-cyber-950 border ${
                data.reassembly_result.missing_ranges.length > 0
                  ? 'border-forge-rose/50 bg-forge-rose/5'
                  : 'border-cyber-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-cyber-500 block text-[10px] uppercase">
                  Detected Gaps (Missing)
                </span>
                {data.reassembly_result.missing_ranges.length > 0 && (
                  <span className="text-[10px] font-bold text-forge-rose px-1.5 py-0.2 rounded bg-forge-rose/15 border border-forge-rose/30">
                    GAP DETECTED
                  </span>
                )}
              </div>
              {data.reassembly_result.missing_ranges.length === 0 ? (
                <span className="text-cyber-300 text-sm font-semibold block mt-1">
                  None (Contiguous)
                </span>
              ) : (
                <div className="space-y-1 mt-1">
                  {data.reassembly_result.missing_ranges.map(([start, end], idx) => (
                    <div
                      key={idx}
                      className="text-xs text-forge-rose font-bold flex items-center gap-1"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>
                        [{start}, {end}) ({end - start} B missing)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Overlapping Ranges */}
            <div
              className={`p-3 rounded-lg bg-cyber-950 border ${
                data.reassembly_result.overlaps.length > 0
                  ? 'border-forge-amber/50 bg-forge-amber/5'
                  : 'border-cyber-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-cyber-500 block text-[10px] uppercase">
                  Collisions / Overlaps
                </span>
                {data.reassembly_result.overlaps.length > 0 && (
                  <span className="text-[10px] font-bold text-forge-amber px-1.5 py-0.2 rounded bg-forge-amber/15 border border-forge-amber/30">
                    OVERLAP
                  </span>
                )}
              </div>
              {data.reassembly_result.overlaps.length === 0 ? (
                <span className="text-cyber-300 text-sm font-semibold block mt-1">
                  None (Clean)
                </span>
              ) : (
                <div className="space-y-1 mt-1">
                  {data.reassembly_result.overlaps.map(([start, end], idx) => (
                    <div
                      key={idx}
                      className="text-xs text-forge-amber font-bold flex items-center gap-1"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>
                        [{start}, {end}) ({end - start} B overlap)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Receiver Analysis Details */}
          <div className="p-3 rounded-lg bg-cyber-950/80 border border-cyber-850 flex flex-wrap items-center justify-between gap-3 text-[11px] text-cyber-400">
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-forge-cyan shrink-0" />
              <span>
                Receiver Buffer:{' '}
                <strong className="text-white">
                  {data.reassembly_result.fragment_count} fragments analyzed
                </strong>
              </span>
            </div>
            <div>
              <span>RFC 791 Offset Ordering: </span>
              <span className="text-forge-emerald font-semibold">
                Sorted by Fragment Offset × 8B
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
