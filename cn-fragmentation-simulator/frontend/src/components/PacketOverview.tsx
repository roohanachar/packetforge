import React from 'react';
import { FileText, ArrowRight, ShieldAlert } from 'lucide-react';
import { SimulationResponse } from '../types/simulation';

interface Props {
  data: SimulationResponse | null;
  dfFlag?: boolean;
}

export const PacketOverview: React.FC<Props> = ({ data, dfFlag }) => {
  const requiresFragmentation = data ? data.payload_size + data.header_size > data.mtu : false;
  const effectiveDf = data ? (data.df !== undefined ? data.df : Boolean(dfFlag)) : Boolean(dfFlag);

  return (
    <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-cyber-800 mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-forge-cyan" />
          <h3 className="text-sm font-semibold text-white tracking-wide">
            1. Packet Overview
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {data && (
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                data.fragmentation_prevented
                  ? 'bg-forge-rose/15 border-forge-rose/40 text-forge-rose font-bold'
                  : requiresFragmentation
                  ? 'bg-forge-amber/10 border-forge-amber/30 text-forge-amber'
                  : 'bg-forge-emerald/10 border-forge-emerald/30 text-forge-emerald'
              }`}
            >
              {data.fragmentation_prevented
                ? 'Fragmentation Prevented (DF=1)'
                : requiresFragmentation
                ? 'Fragmentation Required'
                : 'Fits in Single Packet'}
            </span>
          )}
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyber-800 text-cyber-400">
            Source Datagram
          </span>
        </div>
      </div>

      {!data ? (
        <div className="p-6 rounded-lg bg-cyber-950/60 border border-cyber-850 border-dashed text-center">
          <p className="text-xs text-cyber-400">
            Initial packet telemetry and MTU constraint analysis will display here.
          </p>
          <div className="flex items-center justify-center gap-2 text-xs font-mono text-cyber-500 mt-2">
            <span>Payload Size</span>
            <ArrowRight className="w-3 h-3" />
            <span>Header Size</span>
            <ArrowRight className="w-3 h-3" />
            <span>Link MTU</span>
          </div>
        </div>
      ) : (
        <div className="space-y-3 font-mono text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <span className="text-cyber-500 block text-[10px]">PAYLOAD</span>
              <span className="text-white text-base font-bold">{data.payload_size} B</span>
            </div>
            <div className="p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <span className="text-cyber-500 block text-[10px]">HEADER</span>
              <span className="text-white text-base font-bold">{data.header_size} B</span>
            </div>
            <div className="p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <span className="text-cyber-500 block text-[10px]">LINK MTU</span>
              <span className="text-white text-base font-bold">{data.mtu} B</span>
            </div>
            <div className="p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <span className="text-cyber-500 block text-[10px]">TOTAL SIZE</span>
              <span className="text-white text-base font-bold">
                {data.payload_size + data.header_size} B
              </span>
            </div>
          </div>

          {/* Secondary Header Metadata Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
            <div className="p-2 rounded bg-cyber-950/80 border border-cyber-850 flex items-center justify-between">
              <span className="text-cyber-500">IDENTIFICATION:</span>
              <span className="text-cyber-200 font-semibold">{data.identification}</span>
            </div>
            <div className="p-2 rounded bg-cyber-950/80 border border-cyber-850 flex items-center justify-between">
              <span className="text-cyber-500">DF FLAG:</span>
              <span
                className={`font-semibold px-1.5 py-0.2 rounded text-[10px] ${
                  effectiveDf
                    ? 'bg-forge-amber/15 text-forge-amber border border-forge-amber/30'
                    : 'bg-cyber-800 text-cyber-300'
                }`}
              >
                DF={effectiveDf ? '1' : '0'}
              </span>
            </div>
            <div className="p-2 rounded bg-cyber-950/80 border border-cyber-850 flex items-center justify-between">
              <span className="text-cyber-500">MAX FRAG PAYLOAD:</span>
              <span className="text-forge-cyan font-semibold">
                {Math.floor((data.mtu - data.header_size) / 8) * 8} B
              </span>
            </div>
            <div className="p-2 rounded bg-cyber-950/80 border border-cyber-850 flex items-center justify-between">
              <span className="text-cyber-500">FRAGMENTS:</span>
              <span className="text-white font-semibold">{data.fragment_count} generated</span>
            </div>
          </div>

          {/* Status Note on DF / MTU Comparison */}
          {data.fragmentation_prevented ? (
            <div className="p-3 rounded-lg bg-forge-rose/15 border border-forge-rose/40 text-forge-rose text-xs space-y-1">
              <div className="flex items-center gap-2 font-bold text-sm">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>RFC 791 DF Enforcement: Fragmentation Prevented</span>
              </div>
              <p className="text-cyber-200 pl-6">
                <strong>DF = 1</strong> | Datagram size ({data.payload_size + data.header_size} B) exceeds Link MTU ({data.mtu} B).
              </p>
              <p className="text-forge-rose pl-6 font-semibold">
                Reason: {data.reason || "Fragmentation required, but DF flag is set."}
              </p>
            </div>
          ) : (
            effectiveDf && requiresFragmentation && (
              <div className="p-2.5 rounded-lg bg-forge-amber/10 border border-forge-amber/25 text-forge-amber text-xs flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>
                  <strong>RFC 791 Notice:</strong> Datagram size ({data.payload_size + data.header_size}B) exceeds MTU ({data.mtu}B) with Don't Fragment (DF=1) configured.
                </span>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};
