import React from 'react';
import { Send, Activity, ArrowRight } from 'lucide-react';
import { SimulationResponse } from '../types/simulation';

interface Props {
  data: SimulationResponse | null;
}

export const TransmissionPanel: React.FC<Props> = ({ data }) => {
  const isOutOfOrder = React.useMemo(() => {
    if (!data || data.transmission_result.delivered_fragments.length <= 1) return false;
    const deliveredOffsets = data.transmission_result.delivered_fragments.map((f) => f.offset);
    for (let i = 1; i < deliveredOffsets.length; i++) {
      if (deliveredOffsets[i] < deliveredOffsets[i - 1]) return true;
    }
    return false;
  }, [data]);

  const displayedDroppedCount = React.useMemo(() => {
    if (!data) return 0;
    return (
      data.transmission_result.dropped_count +
      (data.fragmentation_prevented ? 1 : 0)
    );
  }, [data]);

  return (
    <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-cyber-800 mb-4">
        <div className="flex items-center gap-2">
          <Send className="w-4 h-4 text-forge-amber" />
          <h3 className="text-sm font-semibold text-white tracking-wide">
            3. Transmission Channel &amp; Network Events
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {data && isOutOfOrder && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-forge-amber/15 border border-forge-amber/30 text-forge-amber">
              Out-of-Order Delivery
            </span>
          )}
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyber-800 text-cyber-400">
            Network Dynamics
          </span>
        </div>
      </div>

      {!data ? (
        <div className="p-8 rounded-lg bg-cyber-950/60 border border-cyber-850 border-dashed text-center flex flex-col items-center justify-center">
          <Activity className="w-8 h-8 text-cyber-700 mb-2 stroke-[1.5]" />
          <p className="text-xs text-cyber-400 font-medium">
            Transmission timeline and failure event telemetry will display here.
          </p>
          <p className="text-[11px] text-cyber-500 mt-1">
            Tracks packet drops, duplicates, metadata alterations, and latency logs.
          </p>
        </div>
      ) : (
        <div className="space-y-4 font-mono text-xs">
          {/* Counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="p-2.5 rounded bg-cyber-950 border border-cyber-800 text-center">
              <span className="text-cyber-500 block text-[10px]">DELIVERED</span>
              <span className="text-forge-emerald text-sm font-bold">
                {data.transmission_result.delivered_count}
              </span>
            </div>
            <div className="p-2.5 rounded bg-cyber-950 border border-cyber-800 text-center">
              <span className="text-cyber-500 block text-[10px]">DROPPED</span>
              <span
                className={`text-sm font-bold ${
                  displayedDroppedCount > 0
                    ? 'text-forge-rose'
                    : 'text-cyber-400'
                }`}
              >
                {displayedDroppedCount}
              </span>
            </div>
            <div className="p-2.5 rounded bg-cyber-950 border border-cyber-800 text-center">
              <span className="text-cyber-500 block text-[10px]">DUPLICATED</span>
              <span
                className={`text-sm font-bold ${
                  data.transmission_result.duplicate_count > 0
                    ? 'text-forge-amber'
                    : 'text-cyber-400'
                }`}
              >
                {data.transmission_result.duplicate_count}
              </span>
            </div>
            <div className="p-2.5 rounded bg-cyber-950 border border-cyber-800 text-center">
              <span className="text-cyber-500 block text-[10px]">CORRUPTED</span>
              <span
                className={`text-sm font-bold ${
                  data.transmission_result.corrupted_count > 0
                    ? 'text-forge-rose'
                    : 'text-cyber-400'
                }`}
              >
                {data.transmission_result.corrupted_count}
              </span>
            </div>
          </div>

          {/* Delivery Sequence Flow */}
          <div className="p-2.5 rounded bg-cyber-950 border border-cyber-850">
            <span className="text-cyber-500 text-[10px] block mb-1.5 uppercase tracking-wide">
              Receiver Arrival Sequence:
            </span>
            {data.fragmentation_prevented ? (
              <span className="text-forge-amber text-xs">
                Transmission bypassed: Datagram was discarded prior to transmission because Don't Fragment (DF=1) was set on an oversized datagram.
              </span>
            ) : data.transmission_result.delivered_fragments.length === 0 ? (
              <span className="text-forge-rose text-xs">
                No fragments arrived at the receiver (100% loss).
              </span>
            ) : (
              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                {data.transmission_result.delivered_fragments.map((frag, idx) => (
                  <React.Fragment key={idx}>
                    <div
                      className="px-2 py-1 rounded bg-cyber-900 border border-cyber-750 text-cyber-200 flex items-center gap-1.5"
                      title={`Delivered #${idx + 1}: Offset ${frag.offset} (${frag.payload_size}B)`}
                    >
                      <span className="text-cyber-500 text-[10px]">Arr#{idx + 1}</span>
                      <span className="text-forge-cyan font-bold">Offset {frag.offset}</span>
                      <span className="text-cyber-400 text-[10px]">({frag.payload_size}B)</span>
                    </div>
                    {idx < data.transmission_result.delivered_fragments.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-cyber-600 shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          {/* Chronological Event Log */}
          <div>
            <span className="text-cyber-500 text-[10px] block mb-1.5 uppercase tracking-wide">
              Chronological Transmission Log ({data.transmission_result.events.length} events):
            </span>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {data.transmission_result.events.map((evt) => (
                <div
                  key={evt.sequence_number}
                  className="flex items-center justify-between p-2 rounded bg-cyber-950 border border-cyber-850 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-cyber-500 text-[11px]">#{evt.sequence_number}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        evt.action === 'delivered'
                          ? 'bg-forge-emerald/15 text-forge-emerald border border-forge-emerald/30'
                          : evt.action === 'dropped'
                          ? 'bg-forge-rose/15 text-forge-rose border border-forge-rose/30'
                          : evt.action === 'duplicated'
                          ? 'bg-forge-amber/15 text-forge-amber border border-forge-amber/30'
                          : 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                      }`}
                    >
                      {evt.action}
                    </span>
                    <span className="text-cyber-300">{evt.detail}</span>
                  </div>
                  <span className="text-cyber-500 text-[11px] shrink-0">{evt.delay_ms}ms</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
