import React from 'react';
import {
  Sliders,
  RotateCcw,
  Play,
  AlertCircle,
  Info,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { SimulationFormData, FormValidationErrors } from '../types/simulation';

interface Props {
  formData: SimulationFormData;
  errors: FormValidationErrors;
  isLoading?: boolean;
  onChange: (updated: Partial<SimulationFormData>) => void;
  onReset: () => void;
  onRunAttempt: () => void;
  runStatusMessage: string | null;
}

export const SimulationConfigPanel: React.FC<Props> = ({
  formData,
  errors,
  isLoading = false,
  onChange,
  onReset,
  onRunAttempt,
  runStatusMessage,
}) => {
  const hasErrors = Object.values(errors).some((err) => Boolean(err));

  // Quick preset test cases conforming to RFC 791 and user specification
  const applyPreset = (preset: Partial<SimulationFormData>) => {
    onChange({
      payloadSize: 3000,
      mtu: 1500,
      identification: 1001,
      headerSize: 20,
      df: false,
      reorder: false,
      dropIndicesStr: '',
      duplicateIndicesStr: '',
      corruptIndicesStr: '',
      delayMs: 50,
      seed: 42,
      ...preset,
    });
  };

  return (
    <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-6 shadow-lg flex flex-col h-full">
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyber-800 mb-4">
        <div className="flex items-center gap-2.5">
          <Sliders className="w-5 h-5 text-forge-cyan" />
          <h2 className="text-base font-semibold text-white tracking-wide">
            Simulation Parameters
          </h2>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="flex items-center gap-1.5 text-xs font-mono text-cyber-400 hover:text-cyber-200 transition-colors px-2 py-1 rounded bg-cyber-850 hover:bg-cyber-800 border border-cyber-700/50"
          title="Reset to RFC 791 baseline defaults"
        >
          <RotateCcw className="w-3 h-3" />
          Reset Defaults
        </button>
      </div>

      {/* Quick Test Presets */}
      <div className="mb-5 p-3 rounded-lg bg-cyber-950/70 border border-cyber-850 space-y-2">
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-cyber-400">
          <Sparkles className="w-3.5 h-3.5 text-forge-cyan" />
          <span className="font-semibold text-cyber-300">Quick Test Scenarios:</span>
        </div>
        <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
          <button
            type="button"
            onClick={() =>
              applyPreset({ payloadSize: 400, mtu: 1500, identification: 1001, df: false })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-cyber-700/60 hover:border-forge-cyan/50 text-cyber-300 transition-colors"
          >
            Test 1 (400B / MTU 1500)
          </button>
          <button
            type="button"
            onClick={() =>
              applyPreset({ payloadSize: 3000, mtu: 1500, identification: 1002, df: false })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-cyber-700/60 hover:border-forge-cyan/50 text-cyber-300 transition-colors"
          >
            Test 2 (3000B / MTU 1500)
          </button>
          <button
            type="button"
            onClick={() =>
              applyPreset({ payloadSize: 2500, mtu: 1000, identification: 1003, df: false })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-cyber-700/60 hover:border-forge-cyan/50 text-cyber-300 transition-colors"
          >
            Test 3 (2500B / MTU 1000)
          </button>
          <button
            type="button"
            onClick={() =>
              applyPreset({ payloadSize: 3000, mtu: 1500, identification: 1004, df: true })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-forge-amber/40 hover:border-forge-amber text-forge-amber transition-colors"
          >
            Test 4 (DF=1 / MTU 1500)
          </button>
          <button
            type="button"
            onClick={() =>
              applyPreset({
                payloadSize: 3000,
                mtu: 1500,
                identification: 1005,
                reorder: true,
                seed: 42,
              })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-cyber-700/60 hover:border-forge-cyan/50 text-cyber-300 transition-colors"
          >
            Out-of-Order
          </button>
          <button
            type="button"
            onClick={() =>
              applyPreset({
                payloadSize: 3000,
                mtu: 1500,
                identification: 1006,
                dropIndicesStr: '1',
              })
            }
            className="px-2 py-1 rounded bg-cyber-900 hover:bg-cyber-800 border border-cyber-700/60 hover:border-forge-rose/50 text-cyber-300 transition-colors"
          >
            Loss (Drop #1)
          </button>
        </div>
      </div>

      <div className="space-y-6 flex-1 overflow-y-auto pr-1">
        {/* SECTION 1: IPv4 Packet Parameters */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-forge-cyan bg-forge-cyan/10 px-2 py-0.5 rounded border border-forge-cyan/20">
              Layer 3 (IPv4) Packet
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Payload Size */}
            <div>
              <label htmlFor="payloadSize" className="block text-xs font-medium text-cyber-300 mb-1.5">
                Payload Size <span className="text-cyber-500 font-mono">(bytes)</span>
              </label>
              <input
                id="payloadSize"
                type="number"
                min="0"
                value={formData.payloadSize}
                onChange={(e) => onChange({ payloadSize: parseInt(e.target.value) || 0 })}
                className={`w-full bg-cyber-950 border ${
                  errors.payloadSize ? 'border-forge-rose' : 'border-cyber-700'
                } rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan`}
              />
              {errors.payloadSize && (
                <p className="text-xs text-forge-rose mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.payloadSize}
                </p>
              )}
            </div>

            {/* MTU */}
            <div>
              <label htmlFor="mtu" className="block text-xs font-medium text-cyber-300 mb-1.5">
                Link MTU <span className="text-cyber-500 font-mono">(bytes)</span>
              </label>
              <input
                id="mtu"
                type="number"
                min="28"
                value={formData.mtu}
                onChange={(e) => onChange({ mtu: parseInt(e.target.value) || 0 })}
                className={`w-full bg-cyber-950 border ${
                  errors.mtu ? 'border-forge-rose' : 'border-cyber-700'
                } rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan`}
              />
              {errors.mtu && (
                <p className="text-xs text-forge-rose mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.mtu}
                </p>
              )}
            </div>

            {/* Identification */}
            <div>
              <label htmlFor="identification" className="block text-xs font-medium text-cyber-300 mb-1.5">
                Identification <span className="text-cyber-500 font-mono">(16-bit ID)</span>
              </label>
              <input
                id="identification"
                type="number"
                min="0"
                max="65535"
                value={formData.identification}
                onChange={(e) => onChange({ identification: parseInt(e.target.value) || 0 })}
                className={`w-full bg-cyber-950 border ${
                  errors.identification ? 'border-forge-rose' : 'border-cyber-700'
                } rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan`}
              />
              {errors.identification && (
                <p className="text-xs text-forge-rose mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.identification}
                </p>
              )}
            </div>

            {/* Header Size */}
            <div>
              <label htmlFor="headerSize" className="block text-xs font-medium text-cyber-300 mb-1.5">
                Header Size <span className="text-cyber-500 font-mono">(default: 20)</span>
              </label>
              <input
                id="headerSize"
                type="number"
                min="20"
                value={formData.headerSize}
                onChange={(e) => onChange({ headerSize: parseInt(e.target.value) || 20 })}
                className={`w-full bg-cyber-950 border ${
                  errors.headerSize ? 'border-forge-rose' : 'border-cyber-700'
                } rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan`}
              />
              {errors.headerSize && (
                <p className="text-xs text-forge-rose mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.headerSize}
                </p>
              )}
            </div>

            {/* Don't Fragment (DF) Flag Toggle */}
            <div className="sm:col-span-2 flex items-center justify-between p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <div>
                <span className="text-sm font-medium text-cyber-200 block">
                  Don't Fragment (DF) Flag
                </span>
                <span className="text-xs text-cyber-500">
                  RFC 791 bit: DF=1 indicates datagram should not be fragmented
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.df}
                  onChange={(e) => onChange({ df: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-cyber-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-forge-cyan"></div>
              </label>
            </div>
          </div>
        </div>

        {/* SECTION 2: Transmission Network Failures */}
        <div className="pt-2 border-t border-cyber-800">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-forge-amber bg-forge-amber/10 px-2 py-0.5 rounded border border-forge-amber/20">
              Network Channel Failure Injection
            </span>
          </div>

          <div className="space-y-4">
            {/* Reorder Toggle */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-cyber-950 border border-cyber-800">
              <div>
                <span className="text-sm font-medium text-cyber-200 block">
                  Out-of-Order Delivery
                </span>
                <span className="text-xs text-cyber-500">
                  Reorder fragments during network transit
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.reorder}
                  onChange={(e) => onChange({ reorder: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-cyber-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-forge-cyan"></div>
              </label>
            </div>

            {/* Drop Indices */}
            <div>
              <label htmlFor="dropIndices" className="block text-xs font-medium text-cyber-300 mb-1">
                Drop Fragment Indices <span className="text-cyber-500 font-mono">(packet loss: e.g. 1)</span>
              </label>
              <input
                id="dropIndices"
                type="text"
                placeholder="e.g., 1, 3"
                value={formData.dropIndicesStr}
                onChange={(e) => onChange({ dropIndicesStr: e.target.value })}
                className="w-full bg-cyber-950 border border-cyber-700 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan"
              />
            </div>

            {/* Duplicate Indices */}
            <div>
              <label htmlFor="duplicateIndices" className="block text-xs font-medium text-cyber-300 mb-1">
                Duplicate Fragment Indices <span className="text-cyber-500 font-mono">(e.g. 2)</span>
              </label>
              <input
                id="duplicateIndices"
                type="text"
                placeholder="e.g., 2"
                value={formData.duplicateIndicesStr}
                onChange={(e) => onChange({ duplicateIndicesStr: e.target.value })}
                className="w-full bg-cyber-950 border border-cyber-700 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan"
              />
            </div>

            {/* Corrupt Indices */}
            <div>
              <label htmlFor="corruptIndices" className="block text-xs font-medium text-cyber-300 mb-1">
                Corrupt Fragment Indices <span className="text-cyber-500 font-mono">(altered metadata offset)</span>
              </label>
              <input
                id="corruptIndices"
                type="text"
                placeholder="e.g., 1"
                value={formData.corruptIndicesStr}
                onChange={(e) => onChange({ corruptIndicesStr: e.target.value })}
                className="w-full bg-cyber-950 border border-cyber-700 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan"
              />
            </div>

            {/* Delay & Seed */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="delayMs" className="block text-xs font-medium text-cyber-300 mb-1">
                  Latency <span className="text-cyber-500 font-mono">(delay_ms)</span>
                </label>
                <input
                  id="delayMs"
                  type="number"
                  min="0"
                  value={formData.delayMs}
                  onChange={(e) => onChange({ delayMs: parseInt(e.target.value) || 0 })}
                  className="w-full bg-cyber-950 border border-cyber-700 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan"
                />
              </div>

              <div>
                <label htmlFor="seed" className="block text-xs font-medium text-cyber-300 mb-1">
                  PRNG Seed <span className="text-cyber-500 font-mono">(determinism)</span>
                </label>
                <input
                  id="seed"
                  type="number"
                  value={formData.seed === null ? '' : formData.seed}
                  onChange={(e) =>
                    onChange({
                      seed: e.target.value === '' ? null : parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-full bg-cyber-950 border border-cyber-700 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:ring-1 focus:ring-forge-cyan"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Area */}
      <div className="mt-6 pt-4 border-t border-cyber-800">
        <button
          type="button"
          onClick={onRunAttempt}
          disabled={hasErrors || isLoading}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
            hasErrors || isLoading
              ? 'bg-cyber-800 text-cyber-500 cursor-not-allowed'
              : 'bg-forge-cyan hover:bg-cyan-400 text-cyber-950 shadow-md shadow-forge-cyan/20 active:scale-[0.99]'
          }`}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Simulation</span>
            </>
          )}
        </button>

        {runStatusMessage && (
          <div className="mt-3 p-2.5 rounded-lg bg-cyber-850 border border-cyber-700/70 text-xs text-cyber-300 flex items-start gap-2">
            <Info className="w-4 h-4 text-forge-cyan shrink-0 mt-0.5" />
            <span>{runStatusMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
};
