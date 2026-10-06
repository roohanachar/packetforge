import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SimulationConfigPanel } from './components/SimulationConfig';
import { PacketOverview } from './components/PacketOverview';
import { FragmentationPanel } from './components/FragmentationPanel';
import { TransmissionPanel } from './components/TransmissionPanel';
import { ReassemblyPanel } from './components/ReassemblyPanel';
import { StatusBar } from './components/StatusBar';
import {
  SimulationFormData,
  FormValidationErrors,
  SimulationResponse,
  SimulationRequest,
} from './types/simulation';
import { simulatePacket, checkBackendHealth, ApiError } from './api/simulationApi';
import { Info, Terminal, AlertTriangle, RefreshCw } from 'lucide-react';

const INITIAL_FORM_DATA: SimulationFormData = {
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
};

export const App: React.FC = () => {
  const [formData, setFormData] = useState<SimulationFormData>(INITIAL_FORM_DATA);
  const [errors, setErrors] = useState<FormValidationErrors>({});
  const [runStatusMessage, setRunStatusMessage] = useState<string | null>(null);

  // Real backend simulation state
  const [simulationData, setSimulationData] = useState<SimulationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Initial check on API availability
  useEffect(() => {
    let isMounted = true;
    checkBackendHealth().then((isHealthy) => {
      if (isMounted) {
        setBackendOnline(isHealthy);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  // Safe parsing helper for comma-separated indices string
  const parseIndices = (str: string): number[] => {
    if (!str || !str.trim()) return [];
    return str
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s !== '' && !isNaN(Number(s)))
      .map((s) => parseInt(s, 10))
      .filter((n) => n >= 0);
  };

  // Validation function
  const validateForm = (data: SimulationFormData): FormValidationErrors => {
    const errs: FormValidationErrors = {};

    if (isNaN(data.payloadSize) || data.payloadSize < 0) {
      errs.payloadSize = 'Payload size must be a non-negative integer.';
    }

    if (isNaN(data.headerSize) || data.headerSize < 20) {
      errs.headerSize = 'IPv4 header size must be at least 20 bytes.';
    }

    if (isNaN(data.mtu) || data.mtu <= data.headerSize) {
      errs.mtu = `MTU must be strictly greater than header size (${data.headerSize}B).`;
    }

    if (isNaN(data.identification) || data.identification < 0 || data.identification > 65535) {
      errs.identification = 'Identification must be a 16-bit integer (0 to 65535).';
    }

    if (isNaN(data.delayMs) || data.delayMs < 0) {
      errs.delayMs = 'Latency delay must be non-negative.';
    }

    return errs;
  };

  const handleFieldChange = (updated: Partial<SimulationFormData>) => {
    const nextData = { ...formData, ...updated };
    setFormData(nextData);
    setErrors(validateForm(nextData));
    setRunStatusMessage(null);
  };

  const handleReset = () => {
    setFormData(INITIAL_FORM_DATA);
    setErrors({});
    setRunStatusMessage(null);
    setApiError(null);
    setSimulationData(null);
  };

  const handleRunSimulation = async () => {
    const currentErrors = validateForm(formData);
    setErrors(currentErrors);

    if (Object.keys(currentErrors).length > 0) {
      setRunStatusMessage('Please correct the validation errors before simulating.');
      return;
    }

    setRunStatusMessage(null);
    setApiError(null);
    setIsLoading(true);

    const requestPayload: SimulationRequest = {
      payload_size: formData.payloadSize,
      mtu: formData.mtu,
      identification: formData.identification,
      header_size: formData.headerSize,
      df: formData.df,
      transmission: {
        reorder: formData.reorder,
        drop_indices: parseIndices(formData.dropIndicesStr),
        duplicate_indices: parseIndices(formData.duplicateIndicesStr),
        corrupt_indices: parseIndices(formData.corruptIndicesStr),
        delay_ms: formData.delayMs,
        seed: formData.seed,
        corruption_offset_shift: 10,
      },
    };

    try {
      const response = await simulatePacket(requestPayload);
      setSimulationData(response);
      setBackendOnline(true);
      setApiError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setApiError(message);
      if (err instanceof ApiError && err.isBackendUnavailable) {
        setBackendOnline(false);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-cyber-950 text-cyber-200">
      {/* 1. Header */}
      <Header />

      {/* 2. Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Simulation Configuration Panel */}
        <section className="lg:col-span-5 h-full">
          <SimulationConfigPanel
            formData={formData}
            errors={errors}
            isLoading={isLoading}
            onChange={handleFieldChange}
            onReset={handleReset}
            onRunAttempt={handleRunSimulation}
            runStatusMessage={runStatusMessage}
          />
        </section>

        {/* RIGHT COLUMN: Results Workspace / Dynamic Visualizations */}
        <section className="lg:col-span-7 space-y-5">
          {/* Informative Workspace Header Banner */}
          <div className="bg-cyber-900 border border-cyber-800 rounded-xl p-4 flex items-start gap-3 shadow-sm">
            <div className="p-2 rounded bg-forge-cyan/10 text-forge-cyan shrink-0 mt-0.5 border border-forge-cyan/20">
              <Info className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">
                  Simulation Results Workspace
                </h2>
                {simulationData && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyber-800 text-forge-cyan border border-cyber-700">
                    Live Backend Data
                  </span>
                )}
              </div>
              <p className="text-xs text-cyber-400 mt-0.5">
                {simulationData
                  ? simulationData.fragmentation_prevented
                    ? `Simulation evaluated: Fragmentation prevented due to Don't Fragment (DF=1) flag on oversized datagram.`
                    : `Simulation executed successfully via FastAPI PacketSimulator. ${simulationData.fragment_count} fragment(s) generated, transmitted, and evaluated for reassembly.`
                  : 'Configure simulation parameters on the left and click "Run Simulation" to execute the IPv4 RFC 791 pipeline.'}
              </p>
            </div>
          </div>

          {/* Backend API Error Banner */}
          {apiError && (
            <div className="p-4 rounded-xl bg-forge-rose/10 border border-forge-rose/30 text-forge-rose flex items-start gap-3 shadow-sm animate-fadeIn">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1 text-xs">
                <strong className="block font-semibold text-sm">Simulation Request Failed</strong>
                <p className="mt-1 text-cyber-200 font-mono break-all">{apiError}</p>
                <button
                  type="button"
                  onClick={handleRunSimulation}
                  className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-forge-rose/20 hover:bg-forge-rose/30 border border-forge-rose/40 text-white font-medium transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Retry Simulation
                </button>
              </div>
            </div>
          )}

          {/* Dynamic Stage Panels Connected to Real Backend Simulation Response */}
          <PacketOverview data={simulationData} dfFlag={formData.df} />
          <FragmentationPanel data={simulationData} dfFlag={formData.df} />
          <TransmissionPanel data={simulationData} />
          <ReassemblyPanel data={simulationData} />

          {/* Developer Telemetry Note */}
          <div className="p-3 rounded-lg bg-cyber-900/60 border border-cyber-800 text-[11px] font-mono text-cyber-500 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-cyber-600" />
              <span>Pipeline: Fragmentation → Transmission Channel → Reassembly Engine</span>
            </div>
            <span className="text-forge-cyan">RFC 791 Logical Simulator</span>
          </div>
        </section>
      </main>

      {/* 3. Status Bar */}
      <StatusBar backendOnline={backendOnline} isSimulating={isLoading} />
    </div>
  );
};

export default App;
