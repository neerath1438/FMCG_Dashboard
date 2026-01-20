import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import UploadZone from '../components/UploadZone';
import Badge from '../components/ui/Badge';
import { uploadAPI } from '../services/api';

const Upload = () => {
    const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
    const [uploadResult, setUploadResult] = useState(null);
    const [error, setError] = useState(null);
    const [processingLLM, setProcessingLLM] = useState(false);
    const [llmResult, setLlmResult] = useState(null);
    const [uploadController, setUploadController] = useState(null); // For cancellation

    const handleUpload = async (file) => {
        // Create abort controller for cancellation
        const controller = new AbortController();
        setUploadController(controller);

        try {
            setUploadStatus('uploading');
            setError(null);

            const result = await uploadAPI.uploadExcel(file, controller.signal);

            setUploadStatus('success');
            setUploadResult(result.data);
        } catch (err) {
            if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
                setUploadStatus('idle');
                setError('Upload cancelled by user');
            } else {
                setUploadStatus('error');
                setError(err.response?.data?.message || err.message || 'Upload failed');
            }
        } finally {
            setUploadController(null);
        }
    };

    const handleCancelUpload = () => {
        if (uploadController) {
            uploadController.abort();
            setUploadStatus('idle');
            setError(null);
        }
    };

    const handleTriggerLLM = async (sheetName) => {
        try {
            setProcessingLLM(true);
            const response = await uploadAPI.triggerLLMMastering(sheetName);
            setLlmResult(response.data);
        } catch (err) {
            setError(err.response?.data?.message || err.message || 'LLM processing failed');
        } finally {
            setProcessingLLM(false);
        }
    };

    const resetUpload = () => {
        setUploadStatus('idle');
        setUploadResult(null);
        setError(null);
        setLlmResult(null);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
            {/* Upload Section */}
            <Card title="Upload Excel File" subtitle="Upload FMCG product data for processing">
                {uploadStatus === 'idle' && (
                    <UploadZone
                        key={Date.now()}
                        onUpload={handleUpload}
                    />
                )}

                {uploadStatus === 'uploading' && (
                    <div className="text-center py-12 space-y-4">
                        <Loader className="animate-spin mx-auto text-pink-600 mb-4" size={48} />
                        <div>
                            <p className="text-lg font-medium text-gray-900">Uploading and processing...</p>
                            <p className="text-sm text-gray-500 mt-1">This may take 5-10 minutes for large files</p>
                        </div>

                        {/* Progress Tips */}
                        <div className="max-w-md mx-auto mt-6 p-4 bg-blue-50/70 backdrop-blur-sm border border-blue-200/50 rounded-xl text-left">
                            <p className="text-sm font-medium text-blue-900 mb-2">Please wait:</p>
                            <ul className="text-xs text-blue-700 space-y-1">
                                <li>✓ Keep this tab open</li>
                                <li>✓ Don't refresh the page</li>
                                <li>✓ Large files (100MB) may take up to 10 minutes</li>
                                <li>✓ Backend is processing your data</li>
                            </ul>
                        </div>

                        {/* Cancel Button */}
                        <Button
                            variant="outline"
                            onClick={handleCancelUpload}
                            className="mt-4"
                        >
                            Cancel Upload
                        </Button>
                    </div>
                )}

                {uploadStatus === 'success' && uploadResult && (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 p-4 bg-emerald-50/70 backdrop-blur-sm border border-emerald-200/50 rounded-xl">
                            <CheckCircle className="text-emerald-600" size={24} />
                            <div>
                                <p className="font-medium text-emerald-900">Upload Successful!</p>
                                <p className="text-sm text-emerald-700">Flow 1 (UPC Merging) completed</p>
                            </div>
                        </div>

                        {/* Results */}
                        <div className="space-y-3">
                            {Object.entries(uploadResult.data || uploadResult || {}).map(([sheetName, stats]) => (
                                <Card key={sheetName} variant="glass">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h4 className="font-semibold text-gray-900">{sheetName}</h4>
                                            <div className="flex gap-4 mt-2 text-sm text-gray-600">
                                                <span>Raw: {stats.raw_count}</span>
                                                <span>•</span>
                                                <span>Single Stock: {stats.single_stock_count}</span>
                                            </div>
                                        </div>
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={() => handleTriggerLLM(sheetName)}
                                            loading={processingLLM}
                                            disabled={processingLLM}
                                        >
                                            Run Wersel AI Agent Mastering
                                        </Button>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        {/* LLM Results */}
                        {llmResult && (
                            <div className="p-4 bg-blue-50/70 backdrop-blur-sm border border-blue-200/50 rounded-xl">
                                <h4 className="font-semibold text-blue-900 mb-2">LLM Mastering Complete</h4>
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <p className="text-blue-600">Processed</p>
                                        <p className="text-lg font-bold text-blue-900">{llmResult?.total_processed || 0}</p>
                                    </div>
                                    <div>
                                        <p className="text-blue-600">Groups Created</p>
                                        <p className="text-lg font-bold text-blue-900">{llmResult?.groups_created || 0}</p>
                                    </div>
                                    <div>
                                        <p className="text-blue-600">Low Confidence</p>
                                        <p className="text-lg font-bold text-blue-900">{llmResult?.low_confidence_items || 0}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* LLM Trigger Button - Show if upload successful but LLM not run yet */}
                        {/* {!llmResult && (uploadResult.data || uploadResult) && (
                            <div className="space-y-3">
                                <p className="text-sm text-gray-600">
                                    Flow 1 (UPC Merging) completed. Run AI mastering to extract product attributes.
                                </p>
                                {Object.keys(uploadResult.data || uploadResult || {}).map(sheetName => (
                                    <Button
                                        key={sheetName}
                                        onClick={() => handleTriggerLLM(sheetName)}
                                        loading={processingLLM}
                                        disabled={processingLLM}
                                        className="w-full"
                                    >
                                        {processingLLM ? 'Running AI Mastering...' : `Run AI Mastering for ${sheetName}`}
                                    </Button>
                                ))}
                            </div>
                        )} */}

                        <Button variant="outline" onClick={resetUpload} className="w-full">
                            Upload Another File
                        </Button>
                    </div>
                )}

                {uploadStatus === 'error' && (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 p-4 bg-red-50/70 backdrop-blur-sm border border-red-200/50 rounded-xl">
                            <AlertCircle className="text-red-600" size={24} />
                            <div>
                                <p className="font-medium text-red-900">Upload Failed</p>
                                <p className="text-sm text-red-700">{error}</p>
                            </div>
                        </div>
                        <Button variant="outline" onClick={resetUpload} className="w-full">
                            Try Again
                        </Button>
                    </div>
                )}
            </Card>

            {/* Instructions - Glass card */}
            <Card title="Processing Flow" variant="glass">
                <div className="space-y-4">
                    <div className="flex items-start gap-3">
                        <Badge variant="glass-pink">1</Badge>
                        <div>
                            <h4 className="font-semibold text-gray-900">Upload Excel File</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                Upload your FMCG product data. The system will perform UPC-based merging (Flow 1).
                            </p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <Badge variant="glass-pink">2</Badge>
                        <div>
                            <h4 className="font-semibold text-gray-900">Trigger Wersel AI Agent Mastering</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                Run AI-powered product mastering to extract brand, flavour, and size attributes (Flow 2).
                            </p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <Badge variant="glass-pink">3</Badge>
                        <div>
                            <h4 className="font-semibold text-gray-900">View Results</h4>
                            <p className="text-sm text-gray-600 mt-1">
                                Navigate to the Products page to view all processed and mastered products.
                            </p>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default Upload;
