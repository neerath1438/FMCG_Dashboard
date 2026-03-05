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
    Table,
    Box,
    Share2,
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

const MasteringQA = () => {
    const [file, setFile] = useState(null);
    const [pipelineStatus, setPipelineStatus] = useState('pending'); // pending, running, success, failed
    const [activeStage, setActiveStage] = useState(0);
    const [logs, setLogs] = useState([]);
    const [results, setResults] = useState([]);
    const [brand, setBrand] = useState("");
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const [isDiagnosticLoading, setIsDiagnosticLoading] = useState(false);
    const [diagnosticReport, setDiagnosticReport] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [isTranslating, setIsTranslating] = useState(false);
    const [translatedReport, setTranslatedReport] = useState(null);
    const [showTamil, setShowTamil] = useState(false);
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
        if (f && (f.name.endsWith('.csv') || f.name.endsWith('.xlsx'))) {
            setFile(f);
            addLog(`Ready to audit mastering: ${f.name}`, 'success');
        } else {
            alert("Please upload a valid .csv or .xlsx file.");
        }
    };

    const startAudit = async () => {
        if (!file) return;

        setPipelineStatus('running');
        setLogs([]);
        setResults([]);
        setActiveStage(1); // Stage 1: Reading Master Data
        addLog("Initializing Mastering QA Pipeline...", 'info');
        addLog(`Processing Master Stock Data: ${file.name}`, 'info');

        try {
            const data = await qaAPI.uploadMasteringAudit(file);

            if (data.status === 'success') {
                setBrand(data.brand);

                // Process logs with stage tracking
                for (const log of data.logs) {
                    await new Promise(r => setTimeout(r, 60));

                    if (log.includes("Analyzing Bucket")) {
                        setActiveStage(2); // Stage 2: AI Semantic Grouping
                    } else if (log.includes("Mastering QA completed")) {
                        setActiveStage(3); // Stage 3: Scoring / Summary
                    }

                    const type = log.includes('✅') ? 'success' : log.includes('❌') ? 'error' : log.includes('⚠️') ? 'warn' : 'info';
                    addLog(log, type);
                }

                setResults(data.results);
                setPipelineStatus('success');
                setActiveStage(3);
                addLog("✨ Mastering QA Analysis Complete.", 'success');
            }
        } catch (err) {
            const msg = err.response?.data?.detail || err.message;
            addLog(`❌ Mastering Error: ${msg}`, 'error');
            setPipelineStatus('failed');
            setActiveStage(0);
        }
    };

    const handleStop = async () => {
        const targetBrand = brand || file?.name?.split('.')[0] || "Unknown";
        try {
            await qaAPI.stopAudit(targetBrand);
            addLog(`🛑 Stop signal sent for ${targetBrand}. Processing will halt shortly...`, 'warn');
        } catch (err) {
            addLog(`⚠️ Failed to send stop signal: ${err.message}`, 'error');
        }
    };

    const handleAcceptMerge = async (group) => {
        setSelectedGroup(group);
        setIsDiagnosticLoading(true);
        setDiagnosticReport(null);
        setTranslatedReport(null);
        setShowTamil(false);
        setShowModal(true);

        try {
            const data = await qaAPI.getMasteringDiagnostic(group.matched_items);
            if (data.status === 'success') {
                setDiagnosticReport(data.report);
            } else {
                setDiagnosticReport("Failed to fetch diagnostic report.");
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

            const res = await qaAPI.translateText(textToTranslate);
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
        <div className="max-w-5xl mx-auto space-y-6 pb-12 relative">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl shadow-lg">
                    <Share2 className="text-white" size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Mastering QA Module</h1>
                    <p className="text-sm text-gray-500">Flow 2: Automated grouping audit for single-item records</p>
                </div>
                {pipelineStatus === 'success' && (
                    <span className="ml-auto inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold ring-1 ring-blue-200">
                        <CheckCircle size={16} /> Audit Complete
                    </span>
                )}
            </div>

            {/* Initialization Card */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <Upload size={16} className="text-blue-500" />
                    Step 1 — Upload Master Stock Report
                </h2>
                <div
                    onClick={() => fileInputRef.current?.click()}
                    onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    className={`relative flex flex-col items-center justify-center gap-3 py-10 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200
                        ${dragOver ? 'border-blue-400 bg-blue-50' :
                            file ? 'border-emerald-300 bg-emerald-50/60' :
                                'border-gray-200 bg-gray-50/60 hover:border-blue-300 hover:bg-blue-50/40'}`}>
                    <input ref={fileInputRef} type="file" accept=".csv,.xlsx" className="hidden"
                        onChange={(e) => handleFileSelect(e.target.files[0])} />
                    {file ? (
                        <>
                            <FileText size={40} className="text-emerald-500" />
                            <div className="text-center px-4">
                                <p className="font-semibold text-emerald-800 break-all">{file.name}</p>
                                <p className="text-xs text-emerald-600 mt-0.5">Ready for semantic grouping audit</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="p-4 bg-blue-100 rounded-2xl"><Upload size={28} className="text-blue-500" /></div>
                            <div className="text-center">
                                <p className="font-semibold text-gray-700">Drop Master Stock file here</p>
                                <p className="text-xs text-gray-400 mt-0.5">supports .csv or .xlsx</p>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Pipeline Stage Cards */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-6 flex items-center gap-2">
                    <Zap size={16} className="text-blue-500" /> Mastering Process Flow
                </h2>
                <div className="flex flex-col lg:flex-row items-stretch gap-2 lg:gap-4">
                    {[
                        { id: 1, title: 'Stage 1', icon: FileText, label: 'Single-Item Bucketing', desc: 'Filtering merged_from: 1 items by strict rules' },
                        { id: 2, title: 'Stage 2', icon: Cpu, label: 'Semantic Grouping', desc: 'AI analysis of potential ITEM synonyms' },
                        { id: 3, title: 'Stage 3', icon: Layers, label: 'Grouping Summary', desc: 'Finalizing suggested merge clusters' }
                    ].map((stage, idx) => {
                        const isDone = (pipelineStatus === 'success' || activeStage > stage.id);
                        const isCurrent = (pipelineStatus === 'running' && activeStage === stage.id);
                        const statusColor = isDone ? 'bg-emerald-500 shadow-emerald-200' : isCurrent ? 'bg-blue-600 animate-pulse shadow-blue-200' : 'bg-gray-300 shadow-transparent';

                        return (
                            <React.Fragment key={stage.id}>
                                <div className={`flex-1 transition-all duration-300 rounded-2xl p-4 flex flex-col gap-3 border
                                    ${isCurrent ? 'bg-white ring-2 ring-blue-100 border-blue-200 shadow-lg' :
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
                                                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm hover:shadow-md active:scale-95'}`}
                                        >
                                            {pipelineStatus === 'running' ? <RefreshCw className="animate-spin size-3" /> : <Play size={12} />}
                                            {pipelineStatus === 'running' ? 'Auditing...' : 'Run Mastering Audit'}
                                        </button>
                                    )}

                                    {stage.id === 1 && pipelineStatus === 'running' && (
                                        <button
                                            onClick={handleStop}
                                            className="mt-1 py-1.5 rounded-xl text-[10px] font-bold bg-white border border-red-200 text-red-500 hover:bg-red-50 transition-all flex items-center justify-center gap-2 shadow-sm"
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
                <div className="flex items-center gap-2 px-5 py-3 bg-gray-900 border-b border-gray-700">
                    <Terminal size={14} className="text-blue-400" />
                    <span className="text-xs font-semibold text-gray-300 tracking-wide uppercase">Mastering Audit Logs</span>
                    <div className="ml-auto flex gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-400/50" />
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-400/50" />
                        <span className="w-2.5 h-2.5 rounded-full bg-green-400/50" />
                    </div>
                </div>
                <div
                    ref={logContainerRef}
                    className="bg-black/90 h-60 overflow-y-auto px-4 py-3 font-mono text-[11px] space-y-1 custom-scrollbar"
                >
                    {logs.length === 0
                        ? <span className="text-gray-600 italic">Waiting for mastering pipeline initialization...</span>
                        : logs.map((log, i) => (
                            <div key={i} className="flex gap-3 leading-5 animate-in fade-in slide-in-from-left-1 duration-200">
                                <span className="text-gray-600 flex-shrink-0 select-none">[{log.time}]</span>
                                <span className={`${LOG_COLORS[log.type] || 'text-slate-300'} break-all`}>
                                    <span className="text-blue-500 mr-2">❯</span>
                                    {log.msg}
                                </span>
                            </div>
                        ))
                    }
                </div>
            </div>

            {/* Proposed Groups Section */}
            {results.length > 0 && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                            <span className="w-1.5 h-7 bg-blue-600 rounded-full shadow-lg shadow-blue-200" />
                            AI Suggested Group Merges ({results.length})
                        </h2>
                        <div className="text-xs bg-white/50 px-3 py-1.5 rounded-lg border border-white/80 text-gray-500 font-medium">
                            Source: {brand}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {results.map((res, i) => (
                            <div key={i} className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-5 hover:shadow-md transition-all group border-l-4 border-l-blue-500">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-1">Potential Group</p>
                                        <h3 className="text-lg font-extrabold text-gray-900 group-hover:text-blue-700 transition-colors uppercase tracking-tight">{res.group_name}</h3>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded-full">
                                            {res.confidence}% Confidence
                                        </span>
                                        <span className="text-[9px] text-gray-400 mt-1 font-mono uppercase">
                                            {res.bucket_info.market} | {res.bucket_info.size}g
                                        </span>
                                    </div>
                                </div>

                                <div className="space-y-2 mb-4 bg-gray-50/50 p-3 rounded-xl border border-gray-100">
                                    <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Items in Group</p>
                                    {res.matched_items.map((item, idx) => (
                                        <div key={idx} className="flex items-center gap-2 text-xs text-gray-700 py-1">
                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                                            <span className="font-semibold">{item}</span>
                                        </div>
                                    ))}
                                </div>

                                <div className="bg-white/80 p-3 rounded-xl border border-white shadow-inner">
                                    <div className="flex items-start gap-2">
                                        <AlertCircle size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
                                        <p className="text-xs text-gray-600 italic leading-relaxed">"{res.reason}"</p>
                                    </div>
                                </div>

                                <div className="mt-4 flex gap-2">
                                    <button
                                        onClick={() => handleAcceptMerge(res)}
                                        className="flex-1 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-100 transition-all active:scale-95"
                                    >
                                        Accept Merge
                                    </button>
                                    <button className="px-4 py-2 border border-gray-200 text-gray-500 text-xs font-bold rounded-xl hover:bg-white hover:text-gray-700 transition-all">
                                        Ignore
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Diagnostic Modal */}
            {showModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-md" onClick={() => setShowModal(false)} />
                    <div className="relative bg-white w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-600 rounded-xl text-white">
                                    <Cpu size={18} />
                                </div>
                                <div>
                                    <h3 className="text-base font-bold text-gray-900 uppercase tracking-tight">Merge Diagnostic Report</h3>
                                    <p className="text-[10px] text-gray-500 font-medium">Root Cause Analysis for: {selectedGroup?.group_name}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setShowModal(false)}
                                className="p-2 hover:bg-white hover:shadow-sm rounded-xl text-gray-400 hover:text-gray-600 transition-all"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            {isDiagnosticLoading ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-4">
                                    <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
                                    <div className="text-center">
                                        <p className="text-sm font-bold text-gray-700">Analyzing decision gates...</p>
                                        <p className="text-xs text-gray-400 mt-1">Comparing attributes across processor rules</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="bg-blue-50/50 p-6 rounded-2xl border border-blue-100 border-l-4 border-l-blue-600">
                                        <div className="flex items-start gap-3">
                                            <AlertCircle className="text-blue-600 mt-1 flex-shrink-0" size={20} />
                                            <div>
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="text-sm font-bold text-blue-900">
                                                        AI Diagnostic Summary ({showTamil ? 'Tamil' : 'English'})
                                                    </h4>
                                                    <button
                                                        onClick={handleTranslate}
                                                        disabled={isTranslating}
                                                        className="text-[10px] font-bold px-3 py-1 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-all disabled:opacity-50"
                                                    >
                                                        {isTranslating ? 'Translating...' : (showTamil ? 'Show English' : 'Translate to Tamil')}
                                                    </button>
                                                </div>
                                                <div className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap font-medium italic">
                                                    {showTamil ? translatedReport : (typeof diagnosticReport === 'string' ? diagnosticReport : (diagnosticReport?.diagnosis || "No diagnosis available."))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Diagnostic Status</p>
                                            <div className="flex items-center gap-2">
                                                <CheckCircle className="text-emerald-500" size={16} />
                                                <span className="text-xs font-bold text-gray-700 uppercase">Analysis Success</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Rule Reference</p>
                                            <div className="flex items-center gap-2">
                                                <GitBranch className="text-blue-500" size={16} />
                                                <span className="text-xs font-bold text-gray-700 uppercase">
                                                    {diagnosticReport?.rule_reference || "Analyzing Logic..."}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-gray-900 rounded-2xl p-4">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Terminal size={14} className="text-emerald-400" />
                                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Actionable Solution</span>
                                        </div>
                                        <div className="font-mono text-[11px] text-emerald-300 leading-relaxed">
                                            {typeof diagnosticReport === 'string' ? (
                                                <>
                                                    // Recommendation: Review brand synonym normalization and confidence thresholds.
                                                    <br />
                                                    // Target: normalize_item_llm() or apply_llm_rule_guards()
                                                </>
                                            ) : (
                                                <>
                                                    // Recommendation: {diagnosticReport?.actionable_solution}
                                                    <br />
                                                    // Target: {diagnosticReport?.rule_reference}
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

export default MasteringQA;
