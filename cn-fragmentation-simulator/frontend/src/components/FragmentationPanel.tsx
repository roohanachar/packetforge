import React from 'react';
import { Scissors, Box, Check, ShieldAlert } from 'lucide-react';
import { SimulationResponse } from '../types/simulation';

interface Props {
  data: SimulationResponse | null;
  dfFlag?: boolean;
}

export const FragmentationPanel: React.FC<Props> = ({ data, dfFlag }) => {
  const effectiveDf = data ? (data.df !== undefined ? data.df : Boolean(dfFlag)) : Boolean(dfFlag);

  return (
    <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-cyber-800 mb-4">
        <div className="flex items-center gap-2">
          <Scissors className="w-4 h-4 text-forge-cyan" />
          <h3 className="text-sm font-semibold text-white tracking-wide">
            2. Fragmentation Stage (RFC 791)
          </h3>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyber-800 text-cyber-400">
          Sender Partitioning
        </span>
      </div>

      {!data ? (
        <div className="p-8 rounded-lg bg-cyber-950/60 border border-cyber-850 border-dashed text-center flex flex-col items-center justify-center">
          <Box className="w-8 h-8 text-cyber-700 mb-2 stroke-[1.5]" />
          <p className="text-xs text-cyber-400 font-medium">
            Generated fragments will appear here once simulation is initiated.
          </p>
          <p className="text-[11px] text-cyber-500 mt-1">
            Calculates 8-byte boundary alignment, fragment offsets, payload splits, and MF flags.
          </p>
        </div>
      ) : data.fragmentation_prevented ? (
        <div className="space-y-4 font-mono text-xs">
          <div className="p-5 rounded-lg bg-cyber-950 border border-forge-rose/30 space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded bg-forge-rose/15 text-forge-rose border border-forge-rose/30 mt-0.5 shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="text-white font-bold text-sm">
                    0 Fragments Generated — Fragmentation Prevented
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-forge-rose/15 text-forge-rose border border-forge-rose/30 font-semibold">
                    DF=1 ENFORCED
                  </span>
                </div>
                <p className="text-cyber-300 text-xs mt-1">
                  Datagram payload size ({data.payload_size}B + {data.header_size}B header = {data.payload_size + data.header_size}B) exceeds the link MTU ({data.mtu}B), but the IPv4 Don't Fragment flag is active (<span className="text-forge-amber font-mono font-semibold">DF=1</span>).
                </p>
                <p className="text-forge-rose text-xs font-semibold mt-1.5">
                  RFC 791 Verdict: {data.reason || 'Fragmentation required, but DF flag is set.'}
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded bg-cyber-900/80 border border-cyber-800 text-[11px] text-cyber-400 space-y-1.5">
              <div className="font-semibold text-cyber-300">RFC 791 Protocol Specification Rule:</div>
              <p className="italic text-cyber-300 leading-relaxed">
                "An internet datagram can be marked 'don't fragment'. Any internet datagram so marked is not to be internet fragmented under any circumstances. If internet datagram marked 'don't fragment' cannot be delivered to its destination without being internet fragmented, it is to be discarded."
              </p>
              <p className="text-cyber-500 pt-1 border-t border-cyber-850">
                Simulation Note: Zero fragments were generated. No fake or partial fragments are sent into the pipeline.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4 font-mono text-xs">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="text-cyber-400">
              Total Generated Fragments:{' '}
              <strong className="text-forge-cyan text-sm">{data.fragment_count}</strong>
            </span>
            <div className="flex items-center gap-3 text-[11px] text-cyber-500">
              <span>Datagram ID: #{data.identification}</span>
              <span>•</span>
              <span>Header: {data.header_size}B</span>
              <span>•</span>
              <span>Link MTU: {data.mtu}B</span>
            </div>
          </div>

          {/* Visual byte layout progress bar */}
          {data.payload_size > 0 && (
            <div className="space-y-1.5">
              <div className="text-[10px] text-cyber-500 flex justify-between font-mono">
                <span>Byte 0</span>
                <span>Payload Span ({data.payload_size} bytes)</span>
                <span>Byte {data.payload_size}</span>
              </div>
              <div className="h-4 w-full bg-cyber-950 rounded border border-cyber-800 flex overflow-hidden">
                {data.generated_fragments.map((frag, idx) => {
                  const widthPercent =
                    data.payload_size > 0
                      ? (frag.payload_size / data.payload_size) * 100
                      : 100;
                  const colors = [
                    'bg-forge-cyan/20 border-r border-forge-cyan/40 text-forge-cyan',
                    'bg-forge-emerald/20 border-r border-forge-emerald/40 text-forge-emerald',
                    'bg-forge-amber/20 border-r border-forge-amber/40 text-forge-amber',
                    'bg-purple-500/20 border-r border-purple-500/40 text-purple-400',
                  ];
                  const colorClass = colors[idx % colors.length];

                  return (
                    <div
                      key={idx}
                      style={{ width: `${Math.max(widthPercent, 5)}%` }}
                      className={`h-full flex items-center justify-center text-[10px] truncate px-1 transition-all ${colorClass}`}
                      title={`Fragment #${idx}: ${frag.payload_size}B [${frag.offset * 8}, ${frag.offset * 8 + frag.payload_size})`}
                    >
                      #{idx} ({frag.payload_size}B)
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Fragment Detail Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-cyber-800 text-cyber-400 text-[11px]">
                  <th className="py-2 px-2">Frag #</th>
                  <th className="py-2 px-2">ID</th>
                  <th className="py-2 px-2">Total Length</th>
                  <th className="py-2 px-2">Payload</th>
                  <th className="py-2 px-2">Offset (8B)</th>
                  <th className="py-2 px-2">Byte Range</th>
                  <th className="py-2 px-2">DF Flag</th>
                  <th className="py-2 px-2">MF Flag</th>
                  <th className="py-2 px-2">8B Aligned</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-850">
                {data.generated_fragments.map((frag, idx) => {
                  const fragDf = frag.df !== undefined ? frag.df : effectiveDf;
                  const isAligned = frag.payload_size % 8 === 0;

                  return (
                    <tr key={idx} className="hover:bg-cyber-850/50 transition-colors">
                      <td className="py-2.5 px-2 text-cyber-300 font-semibold">#{idx}</td>
                      <td className="py-2.5 px-2 text-cyber-300">{frag.identification}</td>
                      <td className="py-2.5 px-2 text-white font-medium">{frag.total_size} B</td>
                      <td className="py-2.5 px-2 text-white font-medium">{frag.payload_size} B</td>
                      <td className="py-2.5 px-2 text-cyber-300">
                        <span className="bg-cyber-950 px-1.5 py-0.5 rounded border border-cyber-800">
                          {frag.offset}
                        </span>
                      </td>
                      <td className="py-2.5 px-2 text-cyber-400">
                        [{frag.offset * 8}, {frag.offset * 8 + frag.payload_size})
                      </td>
                      <td className="py-2.5 px-2">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] ${
                            fragDf
                              ? 'bg-forge-amber/15 text-forge-amber border border-forge-amber/30'
                              : 'bg-cyber-800 text-cyber-300'
                          }`}
                        >
                          DF={fragDf ? '1' : '0'}
                        </span>
                      </td>
                      <td className="py-2.5 px-2">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            frag.more_fragments
                              ? 'bg-forge-amber/15 text-forge-amber border border-forge-amber/30'
                              : 'bg-forge-cyan/15 text-forge-cyan border border-forge-cyan/30'
                          }`}
                        >
                          MF={frag.more_fragments ? '1' : '0'}
                        </span>
                      </td>
                      <td className="py-2.5 px-2">
                        {frag.more_fragments ? (
                          isAligned ? (
                            <span className="text-forge-emerald text-[11px] flex items-center gap-1">
                              <Check className="w-3 h-3" /> Yes (div 8)
                            </span>
                          ) : (
                            <span className="text-forge-rose text-[11px]">No (RFC violation)</span>
                          )
                        ) : (
                          <span className="text-cyber-500 text-[11px]">Final (Any)</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
