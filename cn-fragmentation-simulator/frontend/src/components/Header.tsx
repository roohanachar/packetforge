import React from 'react';
import { Layers, Network, ShieldCheck, Cpu } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-cyber-800 bg-cyber-900/90 backdrop-blur sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyber-850 border border-cyber-700/60 text-forge-cyan shadow-sm">
            <Network className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-mono">
                Packet<span className="text-forge-cyan">Forge</span>
              </h1>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-cyber-800 border border-cyber-700 text-cyber-300">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-cyber-400 mt-0.5">
              Intelligent IPv4 Fragmentation &amp; Network Failure Simulator
            </p>
          </div>
        </div>

        {/* Technical Telemetry Badges */}
        <div className="flex items-center flex-wrap gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-cyber-850 border border-cyber-800 text-cyber-300">
            <Layers className="w-3.5 h-3.5 text-forge-cyan" />
            <span className="text-cyber-500">SPEC:</span>
            <span className="font-semibold text-cyber-200">RFC 791</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-cyber-850 border border-cyber-800 text-cyber-300">
            <ShieldCheck className="w-3.5 h-3.5 text-forge-emerald" />
            <span className="text-cyber-500">LAYER:</span>
            <span className="font-semibold text-cyber-200">IPv4 (L3)</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-cyber-850 border border-cyber-800 text-cyber-300">
            <Cpu className="w-3.5 h-3.5 text-forge-amber" />
            <span className="text-cyber-500">ENGINE:</span>
            <span className="font-semibold text-forge-emerald">Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
};
