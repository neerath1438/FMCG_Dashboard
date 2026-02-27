import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Upload, Play, CheckCircle, XCircle, Clock, Download,
    ChevronDown, ChevronUp, Zap, GitBranch, Loader,
    FileSpreadsheet, Database, BarChart3, AlertCircle,
    Terminal, ShoppingBag, RefreshCw, Square
} from 'lucide-react';
import { pipelineAPI } from '../services/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    a.remove(); window.URL.revokeObjectURL(url);
};
const formatDuration = (s) => s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
const ts = () => new Date().toLocaleTimeString('en-GB', { hour12: false });

// ─── Log Panel ────────────────────────────────────────────────────────────────
const LOG_COLORS = {
    info: 'text-slate-300',
    success: 'text-emerald-400',
    error: 'text-red-400',
    warn: 'text-yellow-400',
    stage: 'text-pink-400 font-semibold',
};
const LogPanel = ({ logs }) => {
    const bottomRef = useRef(null);
    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);
    return (
        <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-3 bg-gray-900/90 border-b border-gray-700">
                <Terminal size={14} className="text-pink-400" />
                <span className="text-xs font-semibold text-gray-300 tracking-wide">PIPELINE LOGS</span>
                <div className="ml-auto flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/70" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
                    <span className="w-3 h-3 rounded-full bg-green-500/70" />
                </div>
            </div>
            <div className="bg-gray-950/95 h-56 overflow-y-auto px-4 py-3 font-mono text-xs space-y-1 custom-scrollbar">
                {logs.length === 0
                    ? <span className="text-gray-600">Waiting for pipeline to start...</span>
                    : logs.map((e, i) => (
                        <div key={i} className="flex gap-3 leading-5">
                            <span className="text-gray-600 flex-shrink-0 select-none">[{e.time}]</span>
                            <span className={`${LOG_COLORS[e.type] || 'text-slate-300'} break-all`}>
                                {e.stage && <span className="text-pink-500 mr-1">[{e.stage}]</span>}
                                {e.msg}
                            </span>
                        </div>
                    ))
                }
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

// ─── Stage Card ───────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
    pending: { label: 'PENDING', bg: 'bg-gray-100', text: 'text-gray-500', ring: 'ring-gray-200', dot: 'bg-gray-400' },
    running: { label: 'RUNNING', bg: 'bg-blue-50', text: 'text-blue-600', ring: 'ring-blue-200', dot: 'bg-blue-500 animate-pulse' },
    success: { label: 'SUCCESS', bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200', dot: 'bg-emerald-500' },
    failed: { label: 'FAILED', bg: 'bg-red-50', text: 'text-red-700', ring: 'ring-red-200', dot: 'bg-red-500' },
};
const PipelineStageCard = ({
    index, icon: Icon, title, subtitle, status, duration,
    result, error, canRun, onRun, onStop, onExport, exportLabel, extraSlot
}) => {
    const [expanded, setExpanded] = useState(false);
    const cfg = STATUS_CONFIG[status];
    return (
        <div className={`relative flex flex-col gap-3 p-5 rounded-2xl border-2 transition-all duration-300 bg-white/70 backdrop-blur-sm
            ${status === 'running' ? 'border-blue-300 shadow-lg shadow-blue-100' : ''}
            ${status === 'success' ? 'border-emerald-300 shadow-lg shadow-emerald-50' : ''}
            ${status === 'failed' ? 'border-red-300 shadow-lg shadow-red-50' : ''}
            ${status === 'pending' ? 'border-gray-200' : ''}`}>
            <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0
                    ${status === 'success' ? 'bg-gradient-to-br from-emerald-500 to-teal-500' :
                        status === 'running' ? 'bg-gradient-to-br from-blue-500 to-indigo-500' :
                            status === 'failed' ? 'bg-gradient-to-br from-red-500 to-rose-500' :
                                'bg-gradient-to-br from-gray-300 to-gray-400'}`}>
                    {status === 'success' ? <CheckCircle className="text-white" size={20} /> :
                        status === 'running' ? <Loader className="text-white animate-spin" size={20} /> :
                            status === 'failed' ? <XCircle className="text-white" size={20} /> :
                                <Icon className="text-white" size={20} />}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                        <p className="font-bold text-gray-900 text-sm">Stage {index}</p>
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${cfg.bg} ${cfg.text} ring-1 ${cfg.ring}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />{cfg.label}
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
            {extraSlot}
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
                {status === 'running' ? (
                    <button onClick={onStop}
                        className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200 bg-red-100 text-red-600 hover:bg-red-200 shadow-sm">
                        <Square size={14} fill="currentColor" /> Stop
                    </button>
                ) : (
                    <button onClick={onRun} disabled={!canRun}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200
                        ${canRun
                                ? 'bg-gradient-to-r from-pink-500 to-rose-500 text-white hover:from-pink-600 hover:to-rose-600 shadow-sm hover:shadow-md'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}>
                        <Play size={14} /> Run
                    </button>
                )}
                {onExport && (
                    <button onClick={onExport} disabled={status !== 'success'}
                        className={`flex items-center gap-2 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200
                            ${status === 'success'
                                ? 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-sm hover:shadow-md'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}>
                        <Download size={14} />{exportLabel || 'Export'}
                    </button>
                )}
            </div>
        </div>
    );
};

const StageConnector = ({ active }) => (
    <div className="hidden lg:flex items-center justify-center w-12 flex-shrink-0">
        <div className={`relative w-full h-0.5 ${active ? 'bg-emerald-400' : 'bg-gray-200'} transition-colors duration-500`}>
            <div className={`absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0
                border-t-[5px] border-t-transparent border-l-[8px]
                ${active ? 'border-l-emerald-400' : 'border-l-gray-200'}
                border-b-[5px] border-b-transparent transition-colors duration-500`} />
        </div>
    </div>
);

// ─── Stage definitions ────────────────────────────────────────────────────────
const STAGES = [
    { id: 'flow1', title: 'Flow 1: UPC Merge', subtitle: 'Upload & deduplicate raw stock data', icon: FileSpreadsheet, exportLabel: 'Export CSV', exportFile: 'flow1_single_stock.csv' },
    { id: 'flow2', title: 'Flow 2: AI Mastering', subtitle: 'Extract brand, flavour, size via LLM', icon: Database, exportLabel: 'Export CSV', exportFile: 'master_stock.csv' },
    { id: 'flow3', title: 'Flow 3: Mapping Analysis', subtitle: 'Map master stock to 7-Eleven catalogue', icon: BarChart3, exportLabel: 'Export CSV', exportFile: 'mapping_analysis.csv' },
];

const STAGE_LABELS = { flow1: 'FLOW-1', flow2: 'FLOW-2', flow3: 'FLOW-3', s711: '7-ELEVEN' };
const initialStageState = () => ({
    flow1: { status: 'pending', duration: 0, result: null, error: null },
    flow2: { status: 'pending', duration: 0, result: null, error: null },
    flow3: { status: 'pending', duration: 0, result: null, error: null },
    s711: { status: 'pending', duration: 0, result: null, error: null },
});

// ─── Main Pipeline Page ───────────────────────────────────────────────────────
const Pipeline = () => {
    const [stageStates, setStageStates] = useState(initialStageState());
    const [file, setFile] = useState(null);           // Nielsen Excel
    const [file711, setFile711] = useState(null);           // 7-Eleven Excel
    const [uploadedSheetName, setUploadedSheetName] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [dragOver711, setDragOver711] = useState(false);
    const [isRunningAll, setIsRunningAll] = useState(false);
    const [logs, setLogs] = useState([]);
    const [cacheStats, setCacheStats] = useState(null);
    const fileInputRef = useRef(null);
    const file711Ref = useRef(null);
    const timerRefs = useRef({});
    const abortControllers = useRef({});

    // ── Log helpers ──────────────────────────────────────────────────────
    const addLog = useCallback((msg, type = 'info', stage = null) => {
        setLogs(prev => [...prev, { msg, type, stage, time: ts() }]);
    }, []);

    // ── Stage helpers ────────────────────────────────────────────────────
    const setStage = useCallback((id, patch) =>
        setStageStates(prev => ({ ...prev, [id]: { ...prev[id], ...patch } })), []);
    const startTimer = useCallback((id) => {
        let sec = 0;
        timerRefs.current[id] = setInterval(() => { sec++; setStage(id, { duration: sec }); }, 1000);
    }, [setStage]);
    const stopTimer = useCallback((id) => clearInterval(timerRefs.current[id]), []);

    const stopStage = useCallback((id) => {
        if (abortControllers.current[id]) {
            abortControllers.current[id].abort();
            delete abortControllers.current[id];
            stopTimer(id);
            setStage(id, { status: 'pending' });
            addLog(`Stage ${STAGE_LABELS[id]} stopped by user.`, 'warn', STAGE_LABELS[id]);
        }
    }, [stopTimer, setStage, addLog]);

    useEffect(() => () => {
        Object.values(timerRefs.current).forEach(clearInterval);
        Object.values(abortControllers.current).forEach(ac => ac.abort());
    }, []);

    // ── File handlers ────────────────────────────────────────────────────
    const handleFileSelect = (f) => {
        if (f && (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))) {
            setFile(f);
            addLog(`Nielsen file selected: ${f.name} (${(f.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
        }
    };
    const handleDrop = (e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); };

    const handleFile711Select = (f) => {
        if (f && (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))) {
            setFile711(f);
            addLog(`7-Eleven file selected: ${f.name} (${(f.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
        }
    };
    const handleDrop711 = (e) => { e.preventDefault(); setDragOver711(false); handleFile711Select(e.dataTransfer.files[0]); };

    // ── Run Flow 1 ───────────────────────────────────────────────────────
    const runFlow1 = async () => {
        if (!file) return;
        setStage('flow1', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow1');
        addLog('Starting Flow 1: UPC Merge...', 'stage', STAGE_LABELS.flow1);
        addLog(`Uploading "${file.name}"...`, 'info', STAGE_LABELS.flow1);
        const controller = new AbortController();
        abortControllers.current.flow1 = controller;
        try {
            const res = await pipelineAPI.uploadExcel(file, controller.signal);
            delete abortControllers.current.flow1;
            stopTimer('flow1');
            const sheetName = res?.sheets_processed?.[0] || (res?.data ? Object.keys(res.data || {})[0] : null);
            setUploadedSheetName(sheetName);
            const data = res?.data || {};
            const summary = {};
            Object.entries(data).forEach(([sheet, stats]) => {
                if (typeof stats === 'object') {
                    summary[`${sheet} raw`] = stats.raw_count ?? '-';
                    summary[`${sheet} single_stock`] = stats.single_stock_count ?? '-';
                    addLog(`Sheet "${sheet}": ${stats.raw_count} raw → ${stats.single_stock_count} items`, 'info', STAGE_LABELS.flow1);
                }
            });
            if (sheetName) addLog(`Sheet name: ${sheetName}`, 'info', STAGE_LABELS.flow1);
            setStage('flow1', { status: 'success', result: Object.keys(summary).length ? summary : { message: 'Flow 1 complete' } });
            addLog('Flow 1 completed ✓', 'success', STAGE_LABELS.flow1);
        } catch (err) {
            delete abortControllers.current.flow1;
            stopTimer('flow1');
            if (err.name === 'AbortError' || err.code === 'ERR_CANCELED' || err.name === 'CanceledError' || err.message === 'canceled') return;
            const msg = err.response?.data?.message || err.message;
            setStage('flow1', { status: 'failed', error: msg });
            addLog(`Flow 1 failed: ${msg}`, 'error', STAGE_LABELS.flow1);
        }
    };

    // ── Run Flow 2 ───────────────────────────────────────────────────────
    const runFlow2 = async () => {
        const sheet = uploadedSheetName;
        if (!sheet) { addLog('Cannot start Flow 2: no sheet name from Flow 1', 'warn', STAGE_LABELS.flow2); return; }
        setStage('flow2', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow2');
        addLog('Starting Flow 2: AI Mastering...', 'stage', STAGE_LABELS.flow2);
        addLog(`Sheet "${sheet}" → LLM mastering...`, 'info', STAGE_LABELS.flow2);
        addLog('This may take several minutes.', 'warn', STAGE_LABELS.flow2);
        const controller = new AbortController();
        abortControllers.current.flow2 = controller;
        try {
            const res = await pipelineAPI.runLLMMastering(sheet, controller.signal);
            delete abortControllers.current.flow2;
            stopTimer('flow2');
            const result = {
                items_processed: res?.total_processed ?? '-',
                master_stock_count: res?.clusters_created ?? '-',
            };
            setStage('flow2', { status: 'success', result });
            addLog(`Processed: ${result.items_processed} | Master Stock: ${result.master_stock_count}`, 'info', STAGE_LABELS.flow2);
            addLog('Flow 2 completed ✓', 'success', STAGE_LABELS.flow2);
        } catch (err) {
            delete abortControllers.current.flow2;
            stopTimer('flow2');
            if (err.name === 'AbortError' || err.code === 'ERR_CANCELED' || err.name === 'CanceledError' || err.message === 'canceled') return;
            const msg = err.response?.data?.message || err.message;
            setStage('flow2', { status: 'failed', error: msg });
            addLog(`Flow 2 failed: ${msg}`, 'error', STAGE_LABELS.flow2);
        }
    };

    // ── Run Flow 3 ───────────────────────────────────────────────────────
    const runFlow3 = async () => {
        setStage('flow3', { status: 'running', duration: 0, result: null, error: null });
        startTimer('flow3');
        addLog('Starting Flow 3: Mapping Analysis...', 'stage', STAGE_LABELS.flow3);
        const controller = new AbortController();
        abortControllers.current.flow3 = controller;
        try {
            const res = await pipelineAPI.runMapping(controller.signal);
            delete abortControllers.current.flow3;
            stopTimer('flow3');
            const result = {
                total_mapped: res?.total_mapped ?? '-',
                level_1_matches: res?.level1_matches ?? '-',
                level_2_matches: res?.level2_matches ?? '-',
                gaps: res?.gaps ?? '-',
            };
            setStage('flow3', { status: 'success', result });
            addLog(`Mapped: ${result.total_mapped} | L1: ${result.level_1_matches} | L2: ${result.level_2_matches} | Gaps: ${result.gaps}`, 'info', STAGE_LABELS.flow3);
            addLog('Flow 3 completed ✓', 'success', STAGE_LABELS.flow3);
        } catch (err) {
            delete abortControllers.current.flow3;
            stopTimer('flow3');
            if (err.name === 'AbortError' || err.code === 'ERR_CANCELED' || err.name === 'CanceledError' || err.message === 'canceled') return;
            const msg = err.response?.data?.message || err.message;
            setStage('flow3', { status: 'failed', error: msg });
            addLog(`Flow 3 failed: ${msg}`, 'error', STAGE_LABELS.flow3);
        }
    };

    // ── Run Stage 4: 7-Eleven Import ──────────────────────────────────────
    const run711 = async () => {
        if (!file711) return;
        setStage('s711', { status: 'running', duration: 0, result: null, error: null });
        startTimer('s711');
        addLog('Starting 7-Eleven Import...', 'stage', STAGE_LABELS.s711);
        addLog(`Uploading "${file711.name}"...`, 'info', STAGE_LABELS.s711);
        addLog('Checking LLM cache per ArticleDescription...', 'info', STAGE_LABELS.s711);
        const controller = new AbortController();
        abortControllers.current.s711 = controller;
        try {
            const res = await pipelineAPI.upload7Eleven(file711, controller.signal);
            delete abortControllers.current.s711;
            stopTimer('s711');
            const result = {
                total_rows: res?.total_rows ?? '-',
                saved: res?.saved ?? '-',
                cache_hits: res?.cache_hits ?? '-',
                llm_calls_made: res?.llm_calls_made ?? '-',
                errors: res?.errors ?? '-',
            };
            setStage('s711', { status: 'success', result });
            addLog(`Total rows: ${result.total_rows} | Saved: ${result.saved}`, 'info', STAGE_LABELS.s711);
            addLog(`Cache hits: ${result.cache_hits} | New LLM calls: ${result.llm_calls_made}`, 'success', STAGE_LABELS.s711);
            if (result.errors > 0) addLog(`LLM errors: ${result.errors} (used fallback)`, 'warn', STAGE_LABELS.s711);
            addLog('7-Eleven Import completed ✓', 'success', STAGE_LABELS.s711);
            // Refresh cache stats after import
            loadCacheStats();
        } catch (err) {
            delete abortControllers.current.s711;
            stopTimer('s711');
            if (err.name === 'AbortError' || err.code === 'ERR_CANCELED' || err.name === 'CanceledError' || err.message === 'canceled') return;
            const msg = err.response?.data?.message || err.message;
            setStage('s711', { status: 'failed', error: msg });
            addLog(`7-Eleven Import failed: ${msg}`, 'error', STAGE_LABELS.s711);
        }
    };

    // ── Cache stats ──────────────────────────────────────────────────────
    const loadCacheStats = async () => {
        try {
            const res = await pipelineAPI.get711CacheStats();
            setCacheStats(res);
        } catch (_) { }
    };
    useEffect(() => { loadCacheStats(); }, []);

    const clearCache = async () => {
        await pipelineAPI.clear711Cache();
        addLog('7-Eleven LLM cache cleared.', 'warn', STAGE_LABELS.s711);
        loadCacheStats();
    };

    // ── Exports ──────────────────────────────────────────────────────────
    const handleExport = async (stageId) => {
        addLog(`Exporting ${STAGE_LABELS[stageId]} results...`, 'info', STAGE_LABELS[stageId]);
        try {
            let blob;
            if (stageId === 'flow1') blob = await pipelineAPI.exportFlow1();
            else if (stageId === 'flow2') blob = await pipelineAPI.exportFlow2();
            else if (stageId === 'flow3') blob = await pipelineAPI.exportFlow3();
            const filename = STAGES.find(s => s.id === stageId)?.exportFile || 'export.csv';
            downloadBlob(blob, filename);
            addLog(`Downloaded: ${filename} ✓`, 'success', STAGE_LABELS[stageId]);
        } catch (err) {
            addLog(`Export failed: ${err.message}`, 'error', STAGE_LABELS[stageId]);
        }
    };

    // ── Stage eligibility ────────────────────────────────────────────────
    const canRun = {
        flow1: !!file,
        flow2: stageStates.flow1.status === 'success' && !!uploadedSheetName,
        flow3: stageStates.flow2.status === 'success',
        s711: !!file711,
    };
    const allDone = ['flow1', 'flow2', 'flow3'].every(id => stageStates[id].status === 'success');

    return (
        <div className="max-w-5xl mx-auto space-y-6">

            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-3 bg-gradient-to-br from-pink-500 to-rose-500 rounded-2xl shadow-lg">
                    <GitBranch className="text-white" size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Processing Pipeline</h1>
                    <p className="text-sm text-gray-500">Run FMCG processing stages sequentially or individually</p>
                </div>
                {allDone && (
                    <span className="ml-auto inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-full text-sm font-semibold ring-1 ring-emerald-200">
                        <CheckCircle size={16} /> All Stages Complete
                    </span>
                )}
            </div>

            {/* Initialize: Nielsen file */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <Upload size={16} className="text-pink-500" />
                    Step 1 — Initialize Pipeline (Nielsen Excel)
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
                                <p className="text-xs text-emerald-600 mt-0.5">{(file.size / 1024 / 1024).toFixed(1)} MB — Ready</p>
                            </div>
                            <button onClick={(e) => { e.stopPropagation(); setFile(null); addLog('Nielsen file removed.', 'warn'); }}
                                className="text-xs text-gray-400 hover:text-gray-600 underline">Remove</button>
                        </>
                    ) : (
                        <>
                            <div className="p-4 bg-pink-100 rounded-2xl"><Upload size={28} className="text-pink-500" /></div>
                            <div className="text-center">
                                <p className="font-semibold text-gray-700">Drop Nielsen Excel file here</p>
                                <p className="text-xs text-gray-400 mt-0.5">or click to browse — .xlsx, .xls</p>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Pipeline Track: Flow 1 → 2 → 3 */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-6 flex items-center gap-2">
                    <Zap size={16} className="text-pink-500" /> Nielsen Pipeline Stages (Flow 1 → 2 → 3)
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
                                    onStop={() => stopStage(stage.id)}
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

            {/* Stage 4: 7-Eleven Import */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-6 space-y-5">
                <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <ShoppingBag size={16} className="text-pink-500" />
                    Stage 4 — 7-Eleven Import (Independent)
                </h2>

                {/* 7-Eleven file picker */}
                <div
                    onClick={() => file711Ref.current?.click()}
                    onDrop={handleDrop711}
                    onDragOver={(e) => { e.preventDefault(); setDragOver711(true); }}
                    onDragLeave={() => setDragOver711(false)}
                    className={`relative flex flex-col items-center justify-center gap-3 py-8 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200
                        ${dragOver711 ? 'border-pink-400 bg-pink-50 scale-[1.01]' :
                            file711 ? 'border-emerald-300 bg-emerald-50/60' :
                                'border-gray-200 bg-gray-50/60 hover:border-pink-300 hover:bg-pink-50/40'}`}>
                    <input ref={file711Ref} type="file" accept=".xlsx,.xls" className="hidden"
                        onChange={(e) => handleFile711Select(e.target.files[0])} />
                    {file711 ? (
                        <>
                            <FileSpreadsheet size={32} className="text-emerald-500" />
                            <div className="text-center">
                                <p className="font-semibold text-emerald-800 text-sm">{file711.name}</p>
                                <p className="text-xs text-emerald-600 mt-0.5">{(file711.size / 1024 / 1024).toFixed(1)} MB — Ready</p>
                            </div>
                            <button onClick={(e) => { e.stopPropagation(); setFile711(null); addLog('7-Eleven file removed.', 'warn'); }}
                                className="text-xs text-gray-400 hover:text-gray-600 underline">Remove</button>
                        </>
                    ) : (
                        <>
                            <div className="p-3 bg-pink-100 rounded-2xl"><ShoppingBag size={24} className="text-pink-500" /></div>
                            <div className="text-center">
                                <p className="font-semibold text-gray-700 text-sm">Drop 7-Eleven Excel file here</p>
                                <p className="text-xs text-gray-400 mt-0.5">Must have ArticleDescription column</p>
                            </div>
                        </>
                    )}
                </div>

                {/* Stage 4 Card */}
                <PipelineStageCard
                    index={4}
                    icon={ShoppingBag}
                    title="7-Eleven Import"
                    subtitle="LLM-enrich ArticleDescription → save to 7-eleven_data"
                    status={stageStates.s711.status}
                    duration={stageStates.s711.duration}
                    result={stageStates.s711.result}
                    error={stageStates.s711.error}
                    canRun={canRun.s711}
                    onRun={run711}
                    onStop={() => stopStage('s711')}
                    onExport={null}
                    exportLabel={null}
                    extraSlot={
                        stageStates.s711.status === 'success' && stageStates.s711.result ? (
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    { label: 'Cache Hits', value: stageStates.s711.result.cache_hits, color: 'text-emerald-600' },
                                    { label: 'LLM Calls', value: stageStates.s711.result.llm_calls_made, color: 'text-blue-600' },
                                    { label: 'Errors', value: stageStates.s711.result.errors, color: 'text-red-500' },
                                ].map(({ label, value, color }) => (
                                    <div key={label} className="bg-gray-50 rounded-xl p-2 text-center border border-gray-100">
                                        <p className={`text-lg font-bold ${color}`}>{value}</p>
                                        <p className="text-[10px] text-gray-500">{label}</p>
                                    </div>
                                ))}
                            </div>
                        ) : null
                    }
                />

                {/* Cache Info Bar */}
                <div className="flex items-center gap-4 px-4 py-3 bg-gray-50/80 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                        <Database size={14} className="text-pink-400" />
                        <span className="font-semibold">7-Eleven LLM Cache:</span>
                        <span className="text-gray-800 font-bold">{cacheStats?.total_cached ?? '—'} entries</span>
                    </div>
                    <button onClick={loadCacheStats}
                        className="ml-auto p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
                        <RefreshCw size={13} />
                    </button>
                    <button onClick={clearCache}
                        className="text-xs text-red-400 hover:text-red-600 font-medium underline">
                        Clear Cache
                    </button>
                </div>
            </div>

            {/* Log Panel */}
            <LogPanel logs={logs} />

            {/* Run All Bar */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm p-5">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div>
                        <p className="font-semibold text-gray-800">Run All Nielsen Stages</p>
                        <p className="text-xs text-gray-500">Flow 1 → Flow 2 → Flow 3 sequentially</p>
                    </div>
                    <button
                        onClick={async () => {
                            setIsRunningAll(true);
                            addLog('═══ RUN ALL STAGES INITIATED ═══', 'stage');
                            await runFlow1();
                            await new Promise(r => setTimeout(r, 200));
                            setStageStates(prev => { if (prev.flow1.status !== 'success') { setIsRunningAll(false); return prev; } return prev; });
                            await runFlow2();
                            await new Promise(r => setTimeout(r, 200));
                            await runFlow3();
                            setIsRunningAll(false);
                            addLog('═══ ALL STAGES COMPLETE ═══', 'success');
                        }}
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
