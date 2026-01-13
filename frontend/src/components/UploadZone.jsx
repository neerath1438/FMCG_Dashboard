import React, { useState, useCallback, useRef } from 'react';
import { Upload as UploadIcon, X, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';
import Button from './ui/Button';

const UploadZone = ({ onUpload, accept = '.xlsx,.xls', maxSize = 100 * 1024 * 1024 }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState(null);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const validateFile = (file) => {
        if (file.size > maxSize) {
            setError(`File size must be less than ${maxSize / 1024 / 1024}MB`);
            return false;
        }

        const extension = file.name.split('.').pop().toLowerCase();
        const acceptedExtensions = accept.split(',').map(ext => ext.replace('.', '').trim());

        if (!acceptedExtensions.includes(extension)) {
            setError(`Only ${accept} files are allowed`);
            return false;
        }

        return true;
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        setError(null);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && validateFile(droppedFile)) {
            setFile(droppedFile);
        }
    }, [maxSize, accept]);

    const handleFileSelect = (e) => {
        setError(null);
        const selectedFile = e.target.files[0];
        if (selectedFile && validateFile(selectedFile)) {
            setFile(selectedFile);
        }
    };

    const handleRemove = () => {
        setFile(null);
        setError(null);
    };

    const handleUpload = () => {
        if (file) {
            onUpload(file);
        }
    };

    return (
        <div className="space-y-4">
            {/* Drop Zone - Glass styling */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                    border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300
                    ${isDragging
                        ? 'border-pink-500 bg-pink-50/50 backdrop-blur-sm'
                        : 'border-white/50 glass hover:border-pink-400 hover:bg-white/60'
                    }
                `}
            >
                <div className="flex flex-col items-center gap-4">
                    <div className={`p-4 rounded-full transition-colors ${isDragging ? 'bg-pink-100' : 'bg-white/60'}`}>
                        <UploadIcon size={32} className={isDragging ? 'text-pink-600' : 'text-gray-400'} />
                    </div>

                    <div>
                        <p className="text-lg font-medium text-gray-900">
                            {isDragging ? 'Drop file here' : 'Drag & drop your file here'}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">or</p>
                    </div>

                    <Button
                        variant="primary"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Browse Files
                    </Button>

                    <p className="text-xs text-gray-500">
                        Supported: {accept} • Max size: {maxSize / 1024 / 1024}MB
                    </p>
                </div>

                {/* Hidden File Input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={accept}
                    onChange={handleFileSelect}
                    className="hidden"
                />
            </div>

            {/* Error Message - Glass styling */}
            {error && (
                <div className="flex items-center gap-2 p-4 bg-red-50/70 backdrop-blur-sm border border-red-200/50 rounded-xl">
                    <AlertCircle size={20} className="text-red-600" />
                    <p className="text-sm text-red-700">{error}</p>
                </div>
            )}

            {/* Selected File - Glass styling */}
            {file && !error && (
                <div className="flex items-center justify-between p-4 bg-emerald-50/70 backdrop-blur-sm border border-emerald-200/50 rounded-xl">
                    <div className="flex items-center gap-3">
                        <FileSpreadsheet size={24} className="text-emerald-600" />
                        <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <CheckCircle size={20} className="text-emerald-600" />
                        <button
                            onClick={handleRemove}
                            className="p-1 rounded-lg hover:bg-emerald-100/50 transition-colors"
                        >
                            <X size={18} className="text-gray-500" />
                        </button>
                    </div>
                </div>
            )}

            {/* Upload Button */}
            {file && !error && (
                <Button
                    variant="primary"
                    size="lg"
                    onClick={handleUpload}
                    className="w-full"
                >
                    Upload & Process
                </Button>
            )}
        </div>
    );
};

export default UploadZone;
