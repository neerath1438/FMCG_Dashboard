import React, { useState, useRef, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  Play, 
  Upload, 
  Terminal, 
  FileText, 
  Cpu, 
  Layers, 
  ArrowRight,
  RefreshCw,
  ExternalLink,
  Zap,
  Clock,
  GitBranch,
  X
} from 'lucide-react';
import { qaAPI } from '../services/api';

// --- Helpers ---
const ts = () => new Date().toLocaleTimeString('en-GB', { hour12: false });

const LOG_COLORS = {
    info: 'text-slate-300',
    success: 'text-emerald-400',
    error: 'text-red-400',
    warn: 'text-yellow-400',
    stage: 'text-pink-400 font-semibold',
};

const AuditDashboard = () => {
    const [file, setFile] = useState(null);
    const [pipelineStatus, setPipelineStatus] = useState('pending'); // pending, running, success, failed
    const [activeStage, setActiveStage] = useState(0); // 0 (none), 1, 2, 3
    const [logs, setLogs] = useState([]);
    const [results, setResults] = useState([]);
    const [brand, setBrand] = useState("");
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    // Diagnostic Stats
    const [isDiagnosticLoading, setIsDiagnosticLoading] = useState(false);
    const [diagnosticReport, setDiagnosticReport] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [isTranslating, setIsTranslating] = useState(false);
    const [translatedReport, setTranslatedReport] = useState(null);
    const [showTamil, setShowTamil] = useState(false);
    const [selectedAuditItem, setSelectedAuditItem] = useState(null);
    const logContainerRef = useRef(null);

    const addLog = (msg, type = 'info') => {
        setLogs(prev => [...prev, { msg, type, time: ts() }]);
    };

    useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs]);

    const handleFileSelect = (f) => {
        if (f && f.name.endsWith('.csv')) {
            setFile(f);
            addLog(`Ready to audit: ${f.name}`, 'success');
        } else {
            alert("Please upload a valid .csv file.");
        }
    };

    const startAudit = async () => {
        if (!file) return;

        setPipelineStatus('running');
        setLogs([]);
        setResults([]);
        setActiveStage(1); // Start with Stage 1: Parsing
        addLog("Initializing Processing Pipeline...", 'info');
        addLog(`Uploading mapping data: ${file.name}`, 'info');

        try {
            const data = await qaAPI.uploadAudit(file);

            if (data.status === 'success') {
                setBrand(data.brand);
                
                // Process logs with stage tracking
                for (const log of data.logs) {
                    await new Promise(r => setTimeout(r, 60));
                    
                    // Logic to update active stage based on log content
                    if (log.includes("Analyzing GAP")) {
                        setActiveStage(2); // Move to Stage 2: Semantic AI
                    } else if (log.includes("AI Audit completed")) {
                        setActiveStage(3); // Move to Stage 3: Finalizing
                    }

                    const type = log.includes('✅') ? 'success' : log.includes('❌') ? 'error' : log.includes('⚠️') ? 'warn' : 'info';
                    addLog(log, type);
                }
                
                setResults(data.results);
                setPipelineStatus('success');
                setActiveStage(3); // Ensure stage 3 is complete
                addLog("✨ Pipeline Execution Successful.", 'success');
            }
        } catch (err) {
            const msg = err.response?.data?.detail || err.message;
            addLog(`❌ Pipeline Error: ${msg}`, 'error');
            setPipelineStatus('failed');
            setActiveStage(0);
        }
    };

    const handleStop = async () => {
        const targetBrand = brand || file?.name?.split('.')[0] || "Unknown";
        try {
            await qaAPI.stopAudit(targetBrand);
            addLog("🛑 User requested Audit Stop. Signaling backend...", 'warn');
        } catch (err) {
            addLog(`❌ Stop Failed: ${err.message}`, 'error');
        }
    };

    const handleOpenDiagnostic = async (item) => {
        setSelectedAuditItem(item);
        setIsDiagnosticLoading(true);
        setDiagnosticReport(null);
        setTranslatedReport(null);
        setShowTamil(false);
        setShowModal(true);

        try {
            // Use the candidates pre-fetched by the backend search
            const heroCandidates = item.candidates || [];

            const res = await qaAPI.getAuditDiagnostic(item.gap_item, item.gap_size, heroCandidates);
            if (res.status === 'success') {
                setDiagnosticReport(res.report);
            } else {
                setDiagnosticReport("Failed to generate audit diagnostic.");
            }
        } catch (err) {
            setDiagnosticReport(`Error: ${err.message}`);
        } finally {
            setIsDiagnosticLoading(false);
        }
    };

    const handleTranslate = async () => {
        if (!diagnosticReport || translatedReport) {
            setShowTamil(!showTamil);
            return;
        }

        setIsTranslating(true);
        try {
            const textToTranslate = typeof diagnosticReport === 'string' 
                ? diagnosticReport 
                : diagnosticReport.diagnosis;
            
            const res = await qaAPI.translateAudit(textToTranslate);
            if (res.status === 'success') {
                setTranslatedReport(res.translatedText);
                setShowTamil(true);
            }
        } catch (error) {
            console.error("Translation failed:", error);
        } finally {
            setIsTranslating(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-pink-500 to-rose-500 rounded-2xl shadow-lg">
                    <GitBranch className="text-white" size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">AI Audit QA Pipeline</h1>
                    <p className="text-sm text-gray-500">Run FMCG mapping verification stages sequentially</p>
                </div>
                {pipelineStatus === 'success' && (
                    <span className="ml-auto inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-full text-sm font-semibold ring-1 ring-emerald-200">
                        <CheckCircle size={16} /> Audit Complete
                    </span>
                )}
            </div>

            {/* Initialization Card */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <Upload size={16} className="text-pink-500" />
                    Step 1 — Initialize Audit (Mapping CSV)
                </h2>
                <div
                    onClick={() => fileInputRef.current?.click()}
                    onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    className={`relative flex flex-col items-center justify-center gap-3 py-10 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200
                        ${dragOver ? 'border-pink-400 bg-pink-50' :
                            file ? 'border-emerald-300 bg-emerald-50/60' :
                                'border-gray-200 bg-gray-50/60 hover:border-pink-300 hover:bg-pink-50/40'}`}>
                    <input ref={fileInputRef} type="file" accept=".csv" className="hidden"
                        onChange={(e) => handleFileSelect(e.target.files[0])} />
                    {file ? (
                        <>
                            <FileText size={36} className="text-emerald-500" />
                            <div className="text-center px-4">
                                <p className="font-semibold text-emerald-800 break-all">{file.name}</p>
                                <p className="text-xs text-emerald-600 mt-0.5">Ready for semantic audit</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="p-4 bg-pink-100 rounded-2xl"><Upload size={28} className="text-pink-500" /></div>
                            <div className="text-center">
                                <p className="font-semibold text-gray-700">Drop Mapping CSV file here</p>
                                <p className="text-xs text-gray-400 mt-0.5">or click to browse — .csv</p>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Pipeline Stage Cards */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-6 flex items-center gap-2">
                    <Zap size={16} className="text-pink-500" /> AI Audit Progress Stages
                </h2>
                <div className="flex flex-col lg:flex-row items-stretch gap-2 lg:gap-4">
                    {[
                        { id: 1, title: 'Stage 1', icon: FileText, label: 'Data Parsing', desc: 'Validating and parsing mapping CSV' },
                        { id: 2, title: 'Stage 2', icon: Cpu, label: 'Semantic Audit', desc: 'GAP vs Market Hero analysis' },
                        { id: 3, title: 'Stage 3', icon: Layers, label: 'Quality Scoring', desc: 'Finalizing accuracy report' }
                    ].map((stage, idx) => {
                        const isDone = (pipelineStatus === 'success' || activeStage > stage.id);
                        const isCurrent = (pipelineStatus === 'running' && activeStage === stage.id);
                        const statusColor = isDone ? 'bg-emerald-500 shadow-emerald-200' : isCurrent ? 'bg-blue-500 animate-pulse shadow-blue-200' : 'bg-gray-300 shadow-transparent';

                        return (
                            <React.Fragment key={stage.id}>
                                <div className={`flex-1 transition-all duration-300 rounded-2xl p-4 flex flex-col gap-3 border
                                    ${isCurrent ? 'bg-white ring-2 ring-blue-100 border-blue-200' : 
                                      isDone ? 'bg-emerald-50/50 border-emerald-100' : 'bg-white/50 border-white/80'}`}>
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg transition-colors duration-500 ${statusColor}`}>
                                            {isDone ? <CheckCircle size={20} /> : <stage.icon size={20} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{stage.title}</p>
                                            <p className={`text-sm font-bold truncate ${isDone ? 'text-emerald-700' : 'text-gray-800'}`}>{stage.label}</p>
                                        </div>
                                    </div>
                                    <p className="text-xs text-gray-500 leading-tight">{stage.desc}</p>
                                    
                                    {stage.id === 1 && (
                                        <button 
                                            onClick={startAudit}
                                            disabled={!file || pipelineStatus === 'running'}
                                            className={`mt-2 py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2
                                                ${!file || pipelineStatus === 'running' 
                                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                                                    : 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-sm hover:shadow-md active:scale-95'}`}
                                        >
                                            {pipelineStatus === 'running' ? <RefreshCw className="animate-spin size-3" /> : <Play size={12} />}
                                            {pipelineStatus === 'running' ? 'Processing...' : 'Run Audit'}
                                        </button>
                                    )}

                                    {stage.id === 1 && pipelineStatus === 'running' && (
                                        <button 
                                            onClick={handleStop}
                                            className="mt-1 py-1.5 rounded-xl text-[10px] font-bold bg-white border border-red-100 text-red-500 hover:bg-red-50 transition-all flex items-center justify-center gap-2 shadow-sm"
                                        >
                                            <AlertCircle size={10} /> Stop Audit
                                        </button>
                                    )}
                                </div>
                                {idx < 2 && (
                                    <div className={`hidden lg:flex items-center transition-colors duration-500 ${isDone ? 'text-emerald-300' : 'text-gray-200'}`}>
                                        <ArrowRight size={20} />
                                    </div>
                                )}
                            </React.Fragment>
                        );
                    })}
                </div>
            </div>

            {/* Log Panel */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm overflow-hidden">
                <div className="flex items-center gap-2 px-5 py-3 bg-gray-900/90 border-b border-gray-700">
                    <Terminal size={14} className="text-pink-400" />
                    <span className="text-xs font-semibold text-gray-300 tracking-wide uppercase">Audit Pipeline Logs</span>
                    <div className="ml-auto flex gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
                    </div>
                </div>
                <div 
                    ref={logContainerRef}
                    className="bg-gray-950/95 h-56 overflow-y-auto px-4 py-3 font-mono text-[11px] space-y-1 custom-scrollbar"
                >
                    {logs.length === 0
                        ? <span className="text-gray-600 italic">Waiting for pipeline to start...</span>
                        : logs.map((log, i) => (
                            <div key={i} className="flex gap-3 leading-5 animate-in slide-in-from-left-1 duration-200">
                                <span className="text-gray-600 flex-shrink-0 select-none">[{log.time}]</span>
                                <span className={`${LOG_COLORS[log.type] || 'text-slate-300'} break-all`}>
                                    <span className="text-pink-500 mr-2">❯</span>
                                    {log.msg}
                                </span>
                            </div>
                        ))
                    }
                </div>
            </div>

            {/* Final Results */}
            {results.length > 0 && (
                <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-3">
                        <span className="w-1.5 h-6 bg-pink-500 rounded-full" />
                        AI Recommended Level 2 Matches ({brand})
                    </h2>
                    <div className="overflow-hidden border border-gray-100 rounded-xl bg-white/50">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-gray-50/80 text-gray-500 text-[10px] uppercase font-bold tracking-widest border-b border-gray-100">
                                    <tr>
                                        <th className="px-6 py-4">GAP Item (7-Eleven)</th>
                                        <th className="px-6 py-4">AI Recommended Match (Master)</th>
                                        <th className="px-6 py-4">Confidence Reasoning</th>
                                        <th className="px-6 py-4 text-center">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {results.map((m, i) => (
                                        <tr key={i} className="hover:bg-white/80 transition-colors group">
                                            <td className="px-6 py-5">
                                                <div className="text-gray-900 font-bold text-sm tracking-tight">{m.gap_item}</div>
                                                <div className="text-[10px] text-gray-400 font-medium uppercase mt-0.5">{m.gap_size}g</div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="text-pink-600 font-bold text-sm tracking-tight">{m.matched_name}</div>
                                                <div className="text-[9px] text-gray-400 font-mono mt-0.5">UPC: {m.matched_with}</div>
                                            </td>
                                            <td className="px-6 py-5 max-w-sm">
                                                <div className="text-xs text-gray-600 italic leading-relaxed">"{m.reason}"</div>
                                            </td>
                                            <td className="px-6 py-5 text-center">
                                                <button 
                                                    onClick={() => handleOpenDiagnostic(m)}
                                                    className="p-2 bg-gray-100 rounded-lg text-gray-500 hover:text-white hover:bg-pink-500 transition-all shadow-sm group-hover:scale-110"
                                                >
                                                    <Zap className="size-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* Diagnostic Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div 
                        className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm animate-in fade-in duration-300"
                        onClick={() => setShowModal(false)}
                    />
                    
                    <div className="relative bg-white w-full max-w-2xl rounded-[32px] shadow-2xl overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-8 duration-500 border border-white/20">
                        {/* Modal Header */}
                        <div className="p-6 bg-white border-b border-gray-100 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-pink-100 rounded-2xl">
                                    <Cpu className="text-pink-600" size={24} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 tracking-tight">AUDIT DIAGNOSTIC REPORT</h3>
                                    <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mt-0.5">
                                        Root Cause Analysis for: {selectedAuditItem?.gap_item}
                                    </p>
                                </div>
                            </div>
                            <button 
                                onClick={() => setShowModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
                            >
                                <X className="text-gray-400" size={20} />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            {isDiagnosticLoading ? (
                                <div className="flex flex-col items-center justify-center py-20 gap-4">
                                    <div className="w-12 h-12 border-4 border-pink-100 border-t-pink-500 rounded-full animate-spin" />
                                    <p className="text-sm font-bold text-gray-400 uppercase tracking-widest animate-pulse">Running Deep Diagnostic...</p>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="bg-pink-50/50 p-6 rounded-2xl border border-pink-100 border-l-4 border-l-pink-600">
                                        <div className="flex items-start gap-3">
                                            <AlertCircle className="text-pink-600 mt-1 flex-shrink-0" size={20} />
                                            <div>
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="text-sm font-bold text-pink-900">
                                                        AI Audit Summary ({showTamil ? 'Tamil' : 'English'})
                                                    </h4>
                                                    <button 
                                                        onClick={handleTranslate}
                                                        disabled={isTranslating}
                                                        className="text-[10px] font-bold px-3 py-1 bg-pink-600 text-white rounded-full hover:bg-pink-700 transition-all disabled:opacity-50"
                                                    >
                                                        {isTranslating ? 'Translating...' : (showTamil ? 'Show English' : 'Translate to Tamil')}
                                                    </button>
                                                </div>
                                                <div className="text-sm text-pink-800 leading-relaxed whitespace-pre-wrap font-medium italic">
                                                    {showTamil ? translatedReport : (typeof diagnosticReport === 'string' ? diagnosticReport : (diagnosticReport?.diagnosis || "No audit diagnosis available."))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Audit Status</p>
                                            <div className="flex items-center gap-2">
                                                <CheckCircle className="text-emerald-500" size={16} />
                                                <span className="text-xs font-bold text-gray-700 uppercase">Analysis Success</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Rule Reference</p>
                                            <div className="flex items-center gap-2">
                                                <GitBranch className="text-pink-500" size={16} />
                                                <span className="text-xs font-bold text-gray-700 uppercase">
                                                    {diagnosticReport?.rule_reference || "mapping_analysis.py:L90"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-gray-900 rounded-2xl p-4 shadow-inner">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Terminal size={14} className="text-emerald-400" />
                                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Actionable Solution</span>
                                        </div>
                                        <div className="font-mono text-[11px] text-emerald-300 leading-relaxed">
                                            {typeof diagnosticReport === 'string' ? (
                                                <>
                                                    // Recommendation: Review mapping rules and flavor conflicts.
                                                    <br />
                                                    // Target: mapping_analysis.py -> validate_match()
                                                </>
                                            ) : (
                                                <>
                                                    // Recommendation: {diagnosticReport?.actionable_solution}
                                                    <br />
                                                    // Target: mapping_analysis.py specific rules
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="p-6 bg-gray-50/50 border-t border-gray-100 flex justify-end">
                            <button 
                                onClick={() => setShowModal(false)}
                                className="px-6 py-2 bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-xl hover:bg-white hover:shadow-md transition-all active:scale-95"
                            >
                                Close Report
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AuditDashboard;
