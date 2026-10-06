import React from 'react';
import { Terminal, Shield, CheckCircle, Radio, WifiOff } from 'lucide-react';

interface Props {
  backendOnline?: boolean | null;
  isSimulating?: boolean;
}

export const StatusBar: React.FC<Props> = ({
  backendOnline = null,
  isSimulating = false,
}) => {
  return (
    <footer className="border-t border-cyber-800 bg-cyber-900/95 px-6 py-2.5 text-xs font-mono text-cyber-400">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-cyber-300">
            {backendOnline === false ? (
              <WifiOff className="w-3.5 h-3.5 text-forge-rose" />
            ) : (
              <Radio
                className={`w-3.5 h-3.5 ${
                  backendOnline ? 'text-forge-emerald animate-pulse' : 'text-forge-amber'
                }`}
              />
            )}
            <span className="font-semibold text-white">Backend:</span>
            {backendOnline === true && (
              <span className="text-forge-emerald">
                {isSimulating ? 'Processing Simulation...' : 'Connected (FastAPI :8000)'}
              </span>
            )}
            {backendOnline === false && (
              <span className="text-forge-rose">Disconnected / Offline</span>
            )}
            {backendOnline === null && (
              <span className="text-forge-amber">Checking connectivity...</span>
            )}
          </div>
          <span className="text-cyber-700 hidden sm:inline">|</span>
          <div className="hidden md:flex items-center gap-1.5 text-cyber-400">
            <Shield className="w-3.5 h-3.5 text-cyber-500" />
            <span>Mode: Connected Simulation</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-cyber-400">
            <Terminal className="w-3.5 h-3.5 text-cyber-500" />
            <span>Pipeline: FastAPI + React + Vite</span>
          </div>
          <span className="text-cyber-700 hidden sm:inline">|</span>
          <div className="flex items-center gap-1 text-cyber-400">
            <CheckCircle className="w-3.5 h-3.5 text-forge-cyan" />
            <span>RFC 791 Standard</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
