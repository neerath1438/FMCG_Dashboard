import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Upload, Play, CheckCircle, XCircle, Clock, Download,
    ChevronDown, ChevronUp, Zap, GitBranch, Loader,
    FileSpreadsheet, Database, BarChart3, AlertCircle, Terminal
} from 'lucide-react';
import { pipelineAPI } from '../services/api';

// ─── Helper: Download blob ────────────────────────────────────────────────────
const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    a.remove(); window.URL.revokeObjectURL(url);
};

// ─── Helper: Format seconds ───────────────────────────────────────────────────
const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
};

// ─── Helper: Timestamp prefix ────────────────────────────────────────────────
const ts = () => new Date().toLocaleTimeString('en-GB', { hour12: false });

// ─────────────────────────────────────────────────────────────────────────────
//  Log Panel (Terminal-style)
// ─────────────────────────────────────────────────────────────────────────────
const LOG_COLORS = {
    info: 'text-slate-300',
    success: 'text-emerald-400',
    error: 'text-red-400',
    warn: 'text-yellow-400',
    stage: 'text-pink-400 font-semibold',
};

const LogPanel = ({ logs }) => {
    const bottomRef = useRef(null);
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-2 px-5 py-3 bg-gray-900/90 border-b border-gray-700">
                <Terminal size={14} className="text-pink-400" />
                <span className="text-xs font-semibold text-gray-300 tracking-wide">PIPELINE LOGS</span>
                <div className="ml-auto flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/70" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
                    <span className="w-3 h-3 rounded-full bg-green-500/70" />
                </div>
            </div>

            {/* Log body */}
            <div className="bg-gray-950/95 h-56 overflow-y-auto px-4 py-3 font-mono text-xs space-y-1 custom-scrollbar">
                {logs.length === 0 ? (
                    <span className="text-gray-600">Waiting for pipeline to start...</span>
                ) : (
                    logs.map((entry, i) => (
                        <div key={i} className="flex gap-3 leading-5">
                            <span className="text-gray-600 flex-shrink-0 select-none">[{entry.time}]</span>
                            <span className={`${LOG_COLORS[entry.type] || 'text-slate-300'} break-all`}>
                                {entry.stage && (
                                    <span className="text-pink-500 mr-1">[{entry.stage}]</span>
                                )}
                                {entry.msg}
                            </span>
                        </div>
                    ))
                )}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

// ─────────────────────────────────────────────────────────────────────────────
//  PipelineStageCard
// ─────────────────────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
    pending: { label: 'PENDING', bg: 'bg-gray-100', text: 'text-gray-500', ring: 'ring-gray-200', dot: 'bg-gray-400' },
    running: { label: 'RUNNING', bg: 'bg-blue-50', text: 'text-blue-600', ring: 'ring-blue-200', dot: 'bg-blue-500 animate-pulse' },
    success: { label: 'SUCCESS', bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200', dot: 'bg-emerald-500' },
    failed: { label: 'FAILED', bg: 'bg-red-50', text: 'text-red-700', ring: 'ring-red-200', dot: 'bg-red-500' },
};

const PipelineStageCard = ({
    index, icon: Icon, title, subtitle, status, duration,
    result, error, canRun, onRun, onExport, exportLabel,
}) => {
    const [expanded, setExpanded] = useState(false);
    const cfg = STATUS_CONFIG[status];

    return (
        <div className={`
            relative flex flex-col gap-3 p-5 rounded-2xl border-2 transition-all duration-300
            bg-white/70 backdrop-blur-sm
            ${status === 'running' ? 'border-blue-300 shadow-lg shadow-blue-100' : ''}
            ${status === 'success' ? 'border-emerald-300 shadow-lg shadow-emerald-50' : ''}
            ${status === 'failed' ? 'border-red-300 shadow-lg shadow-red-50' : ''}
            ${status === 'pending' ? 'border-gray-200' : ''}
        `}>
            <div className="flex items-center gap-3">
                <div className={`
                    w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0
                    ${status === 'success' ? 'bg-gradient-to-br from-emerald-500 to-teal-500' :
                        status === 'running' ? 'bg-gradient-to-br from-blue-500 to-indigo-500' :
                            status === 'failed' ? 'bg-gradient-to-br from-red-500 to-rose-500' :
                                'bg-gradient-to-br from-gray-300 to-gray-400'}
                `}>
                    {status === 'success' ? <CheckCircle className="text-white" size={20} /> :
                        status === 'running' ? <Loader className="text-white animate-spin" size={20} /> :
                            status === 'failed' ? <XCircle className="text-white" size={20} /> :
                                <Icon className="text-white" size={20} />}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                        <p className="font-bold text-gray-900 text-sm">Stage {index}</p>
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${cfg.bg} ${cfg.text} ring-1 ${cfg.ring}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                            {cfg.label}
                        </span>
                    </div>
                    <p className="text-sm font-semibold text-gray-700 truncate">{title}</p>
                    <p className="text-xs text-gray-500">{subtitle}</p>
                </div>
            </div>

            {duration > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Clock size={12} /><span>{formatDuration(duration)}</span>
                </div>
            )}

            {result && (
                <div>
                    <button onClick={() => setExpanded(e => !e)}
                        className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900 font-medium">
                        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />} View Summary
                    </button>
                    {expanded && (
                        <div className="mt-2 p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs text-gray-700 space-y-1">
                            {Object.entries(result).map(([k, v]) => (
                                <div key={k} className="flex justify-between gap-2">
                                    <span className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</span>
                                    <span className="font-semibold text-gray-800">{String(v)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 rounded-xl border border-red-100">
                    <AlertCircle size={14} className="text-red-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-red-700">{error}</p>
                </div>
            )}

            <div className="flex gap-2 mt-auto">
                <button onClick={onRun} disabled={!canRun || status === 'running'}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200
                        ${canRun && status !== 'running'
                            ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white hover:from-pink-600 hover:to-rose-600 shadow-sm hover:shadow-md'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}>
                    {status === 'running' ? <><Loader size={14} className="animate-spin" /> Running...</> : <><Play size={14} /> Run</>}
                </button>
                <button onClick={onExport} disabled={status !== 'success'}
                    className={`flex items-center gap-2 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200
                        ${status === 'success'
                            ? 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-sm hover:shadow-md'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}>
                    <Download size={14} />{exportLabel || 'Export'}
                </button>
            </div>
        </div>
    );
};

// ─── Animated connector ───────────────────────────────────────────────────────
const StageConnector = ({ active }) => (
    <div className="hidden lg:flex items-center justify-center w-12 flex-shrink-0">
        <div className={`relative w-full h-0.5 ${active ? 'bg-emerald-400' : 'bg-gray-200'} transition-colors duration-500`}>
            <div className={`absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0
                border-t-[5px] border-t-transparent border-l-[8px]
                ${active ? 'border-l-emerald-400' : 'border-l-gray-200'}
                border-b-[5px] border-b-transparent transition-colors duration-500`} />
            {active && (
                <div className="absolute inset-0 overflow-hidden">
                    <div className="h-full w-1/2 bg-gradient-to-r from-transparent to-emerald-300 animate-pulse" />
                </div>
            )}
        </div>
    </div>
);

// ─────────────────────────────────────────────────────────────────────────────
//  Main Pipeline Page
// ─────────────────────────────────────────────────────────────────────────────
const STAGES = [
    { id: 'flow1', title: 'Flow 1: UPC Merge', subtitle: 'Upload & deduplicate raw stock data', icon: FileSpreadsheet, exportLabel: 'Export CSV', exportFile: 'flow1_single_stock.csv' },
    { id: 'flow2', title: 'Flow 2: AI Mastering', subtitle: 'Extract brand, flavour, size via LLM', icon: Database, exportLabel: 'Export CSV', exportFile: 'master_stock.csv' },
    { id: 'flow3', title: 'Flow 3: Mapping Analysis', subtitle: 'Map master stock to 7-Eleven catalogue', icon: BarChart3, exportLabel: 'Export CSV', exportFile: 'mapping_analysis.csv' },
];

const STAGE_LABELS = { flow1: 'FLOW-1', flow2: 'FLOW-2', flow3: 'FLOW-3' };

const initialStageState = () => STAGES.reduce((acc, s) => ({
    ...acc, [s.id]: { status: 'pending', duration: 0, result: null, error: null }
}), {});

const Pipeline = () => {
    const [stageStates, setStageStates] = useState(initialStageState());
    const [file, setFile] = useState(null);
    const [uploadedSheetName, setUploadedSheetName] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [isRunningAll, setIsRunningAll] = useState(false);
    const [logs, setLogs] = useState([]);
    const fileInputRef = useRef(null);
    const timerRefs = useRef({});

    // ─── Log helpers ──────────────────────────────────────────────────────
    const addLog = useCallback((msg, type = 'info', stage = null) => {
        setLogs(prev => [...prev, { msg, type, stage, time: ts() }]);
    }, []);

    // ─── Stage helpers ────────────────────────────────────────────────────
    const setStage = useCallback((id, patch) =>
        setStageStates(prev => ({ ...prev, [id]: { ...prev[id], ...patch } })), []);

    const startTimer = useCallback((id) => {
        let sec = 0;
        timerRefs.current[id] = setInterval(() => { sec++; setStage(id, { duration: sec }); }, 1000);
    }, [setStage]);

    const stopTimer = useCallback((id) => clearInterval(timerRefs.current[id]), []);
    useEffect(() => () => Object.values(timerRefs.current).forEach(clearInterval), []);

    // ─── File handling ────────────────────────────────────────────────────
    const handleFileSelect = (f) => {
        if (f && (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))) {
            setFile(f);
            addLog(`File selected: ${f.name} (${(f.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
        }
    };
    const handleDrop = (e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); };

    // ─── Run Flow 1 ───────────────────────────────────────────────────────
    const runFlow1 = async () => {
        if (!file) return;
        setStage('flow1', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow1');
        addLog('Starting Flow 1: UPC Merge...', 'stage', STAGE_LABELS.flow1);
        addLog(`Uploading file "${file.name}" to backend...`, 'info', STAGE_LABELS.flow1);
        try {
            const res = await pipelineAPI.uploadExcel(file);
            stopTimer('flow1');
            const sheetName = res?.sheets_processed?.[0] || (res?.data ? Object.keys(res.data || {})[0] : null);
            setUploadedSheetName(sheetName);
            const data = res?.data || res || {};
            const summary = {};
            Object.entries(data).forEach(([sheet, stats]) => {
                if (typeof stats === 'object') {
                    summary[`${sheet} raw`] = stats.raw_count ?? '-';
                    summary[`${sheet} single_stock`] = stats.single_stock_count ?? '-';
                    addLog(`Sheet "${sheet}": ${stats.raw_count} raw rows → ${stats.single_stock_count} single stock items`, 'info', STAGE_LABELS.flow1);
                }
            });
            if (sheetName) addLog(`Sheet name detected: ${sheetName}`, 'info', STAGE_LABELS.flow1);
            setStage('flow1', { status: 'success', result: Object.keys(summary).length ? summary : { message: 'Flow 1 complete' } });
            addLog('Flow 1 completed successfully ✓', 'success', STAGE_LABELS.flow1);
        } catch (err) {
            stopTimer('flow1');
            const msg = err.response?.data?.message || err.message;
            setStage('flow1', { status: 'failed', error: msg });
            addLog(`Flow 1 failed: ${msg}`, 'error', STAGE_LABELS.flow1);
        }
    };

    // ─── Run Flow 2 ───────────────────────────────────────────────────────
    const runFlow2 = async () => {
        const sheet = uploadedSheetName;
        if (!sheet) { addLog('Cannot start Flow 2: no sheet name from Flow 1', 'warn', STAGE_LABELS.flow2); return; }
        setStage('flow2', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow2');
        addLog('Starting Flow 2: AI Mastering...', 'stage', STAGE_LABELS.flow2);
        addLog(`Sending sheet "${sheet}" to LLM mastering endpoint...`, 'info', STAGE_LABELS.flow2);
        addLog('This may take several minutes for large datasets.', 'warn', STAGE_LABELS.flow2);
        try {
            const res = await pipelineAPI.runLLMMastering(sheet);
            stopTimer('flow2');
            const result = {
                total_processed: res?.total_processed ?? '-',
                groups_created: res?.groups_created ?? '-',
                low_confidence: res?.low_confidence_items ?? '-',
            };
            setStage('flow2', { status: 'success', result });
            addLog(`Processed: ${result.total_processed} items`, 'info', STAGE_LABELS.flow2);
            addLog(`Groups created: ${result.groups_created}`, 'info', STAGE_LABELS.flow2);
            addLog(`Low confidence items: ${result.low_confidence}`, result.low_confidence > 0 ? 'warn' : 'info', STAGE_LABELS.flow2);
            addLog('Flow 2 AI Mastering completed successfully ✓', 'success', STAGE_LABELS.flow2);
        } catch (err) {
            stopTimer('flow2');
            const msg = err.response?.data?.message || err.message;
            setStage('flow2', { status: 'failed', error: msg });
            addLog(`Flow 2 failed: ${msg}`, 'error', STAGE_LABELS.flow2);
        }
    };

    // ─── Run Flow 3 ───────────────────────────────────────────────────────
    const runFlow3 = async () => {
        setStage('flow3', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow3');
        addLog('Starting Flow 3: Mapping Analysis...', 'stage', STAGE_LABELS.flow3);
        addLog('Building 7-Eleven lookup dictionary...', 'info', STAGE_LABELS.flow3);
        addLog('Running Level 1 (UPC) and Level 2 (Attribute) matching...', 'info', STAGE_LABELS.flow3);
        try {
            const res = await pipelineAPI.runMapping();
            stopTimer('flow3');
            const result = {
                total_mapped: res?.total_mapped ?? '-',
                level1_UPC_matches: res?.level1_matches ?? '-',
                level2_attr_matches: res?.level2_matches ?? '-',
                gaps: res?.gaps ?? '-',
            };
            setStage('flow3', { status: 'success', result });
            addLog(`Total master stock items mapped: ${result.total_mapped}`, 'info', STAGE_LABELS.flow3);
            addLog(`Level 1 (UPC exact match): ${result.level1_UPC_matches}`, 'success', STAGE_LABELS.flow3);
            addLog(`Level 2 (Attribute match): ${result.level2_attr_matches}`, 'info', STAGE_LABELS.flow3);
            addLog(`Gaps (no match found): ${result.gaps}`, result.gaps > 0 ? 'warn' : 'success', STAGE_LABELS.flow3);
            addLog('Flow 3 Mapping Analysis completed successfully ✓', 'success', STAGE_LABELS.flow3);
        } catch (err) {
            stopTimer('flow3');
            const msg = err.response?.data?.message || err.message;
            setStage('flow3', { status: 'failed', error: msg });
            addLog(`Flow 3 failed: ${msg}`, 'error', STAGE_LABELS.flow3);
        }
    };

    // ─── Run All ──────────────────────────────────────────────────────────
    const runAll = async () => {
        setIsRunningAll(true);
        addLog('═══ RUN ALL STAGES INITIATED ═══', 'stage');
        await runFlow1();
        // Check latest state via ref pattern
        await new Promise(r => setTimeout(r, 100)); // flush state
        setStageStates(prev => {
            if (prev.flow1.status === 'success') {
                Promise.resolve().then(async () => {
                    await runFlow2();
                    await new Promise(r => setTimeout(r, 100));
                    setStageStates(prev2 => {
                        if (prev2.flow2.status === 'success') {
                            Promise.resolve().then(async () => {
                                await runFlow3();
                                setIsRunningAll(false);
                                addLog('═══ ALL STAGES COMPLETE ═══', 'success');
                            });
                        } else {
                            setIsRunningAll(false);
                            addLog('Pipeline stopped due to Flow 2 failure.', 'error');
                        }
                        return prev2;
                    });
                });
            } else {
                setIsRunningAll(false);
                addLog('Pipeline stopped due to Flow 1 failure.', 'error');
            }
            return prev;
        });
    };

    // ─── Exports ──────────────────────────────────────────────────────────
    const handleExport = async (stageId) => {
        addLog(`Exporting ${STAGE_LABELS[stageId]} results...`, 'info', STAGE_LABELS[stageId]);
        try {
            let blob;
            if (stageId === 'flow1') blob = await pipelineAPI.exportFlow1();
            else if (stageId === 'flow2') blob = await pipelineAPI.exportFlow2();
            else blob = await pipelineAPI.exportFlow3();
            const filename = STAGES.find(s => s.id === stageId)?.exportFile || 'export.csv';
            downloadBlob(blob, filename);
            addLog(`Export downloaded: ${filename} ✓`, 'success', STAGE_LABELS[stageId]);
        } catch (err) {
            addLog(`Export failed: ${err.message}`, 'error', STAGE_LABELS[stageId]);
        }
    };

    // ─── Stage eligibility ────────────────────────────────────────────────
    const canRun = {
        flow1: !!file,
        flow2: stageStates.flow1.status === 'success' && !!uploadedSheetName,
        flow3: stageStates.flow2.status === 'success',
    };
    const allDone = STAGES.every(s => stageStates[s.id].status === 'success');

    return (
        <div className="max-w-5xl mx-auto space-y-6">

            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-pink-500 to-rose-500 rounded-2xl shadow-lg">
                    <GitBranch className="text-white" size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Processing Pipeline</h1>
                    <p className="text-sm text-gray-500">Run all FMCG processing stages sequentially or individually</p>
                </div>
                {allDone && (
                    <span className="ml-auto inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-full text-sm font-semibold ring-1 ring-emerald-200">
                        <CheckCircle size={16} /> All Stages Complete
                    </span>
                )}
            </div>

            {/* Initialize Panel */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <Upload size={16} className="text-pink-500" />
                    Step 1 — Initialize Pipeline
                </h2>
                <div
                    onClick={() => fileInputRef.current?.click()}
                    onDrop={handleDrop}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    className={`relative flex flex-col items-center justify-center gap-3 py-10 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200
                        ${dragOver ? 'border-pink-400 bg-pink-50 scale-[1.01]' :
                            file ? 'border-emerald-300 bg-emerald-50/60' :
                                'border-gray-200 bg-gray-50/60 hover:border-pink-300 hover:bg-pink-50/40'}`}>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" className="hidden"
                        onChange={(e) => handleFileSelect(e.target.files[0])} />
                    {file ? (
                        <>
                            <FileSpreadsheet size={36} className="text-emerald-500" />
                            <div className="text-center">
                                <p className="font-semibold text-emerald-800">{file.name}</p>
                                <p className="text-xs text-emerald-600 mt-0.5">{(file.size / 1024 / 1024).toFixed(1)} MB — Ready to process</p>
                            </div>
                            <button onClick={(e) => { e.stopPropagation(); setFile(null); addLog('File removed.', 'warn'); }}
                                className="text-xs text-gray-400 hover:text-gray-600 underline">Remove</button>
                        </>
                    ) : (
                        <>
                            <div className="p-4 bg-pink-100 rounded-2xl"><Upload size={28} className="text-pink-500" /></div>
                            <div className="text-center">
                                <p className="font-semibold text-gray-700">Drop your Excel file here</p>
                                <p className="text-xs text-gray-400 mt-0.5">or click to browse — .xlsx, .xls supported</p>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Pipeline Track */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-6 flex items-center gap-2">
                    <Zap size={16} className="text-pink-500" /> Pipeline Stages
                </h2>
                <div className="flex flex-col lg:flex-row items-stretch gap-2 lg:gap-0">
                    {STAGES.map((stage, idx) => (
                        <React.Fragment key={stage.id}>
                            <div className="flex-1 min-w-0">
                                <PipelineStageCard
                                    index={idx + 1}
                                    icon={stage.icon}
                                    title={stage.title}
                                    subtitle={stage.subtitle}
                                    status={stageStates[stage.id].status}
                                    duration={stageStates[stage.id].duration}
                                    result={stageStates[stage.id].result}
                                    error={stageStates[stage.id].error}
                                    canRun={canRun[stage.id]}
                                    onRun={idx === 0 ? runFlow1 : idx === 1 ? runFlow2 : runFlow3}
                                    onExport={() => handleExport(stage.id)}
                                    exportLabel={stage.exportLabel}
                                />
                            </div>
                            {idx < STAGES.length - 1 && (
                                <StageConnector active={stageStates[STAGES[idx].id].status === 'success'} />
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </div>

            {/* Live Log Panel */}
            <LogPanel logs={logs} />

            {/* Actions Bar */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-5">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div>
                        <p className="font-semibold text-gray-800">Run All Stages</p>
                        <p className="text-xs text-gray-500">Runs Flow 1 → Flow 2 → Flow 3 sequentially</p>
                    </div>
                    <button
                        onClick={runAll}
                        disabled={!file || isRunningAll}
                        className={`flex items-center gap-3 px-8 py-3 rounded-xl font-semibold text-sm transition-all duration-200
                            ${file && !isRunningAll
                                ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-lg hover:from-pink-600 hover:to-rose-600 hover:shadow-xl hover:-translate-y-0.5'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}>
                        {isRunningAll ? <><Loader size={16} className="animate-spin" /> Running All...</> : <><Play size={16} /> Run All Stages</>}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Pipeline;
