import React from 'react';
import Card from './ui/Card';
import Badge from './ui/Badge';

const MergeMetadata = ({ product }) => {
    const getMergeLevelInfo = (level) => {
        if (!level) return { variant: 'default', label: 'Unknown' };

        if (level.includes('NO_MERGE')) {
            return { variant: 'glass-info', label: 'No Merge - Single Item' };
        } else if (level.includes('MERGED')) {
            const count = level.match(/\d+/)?.[0] || '?';
            return { variant: 'glass-success', label: `Merged from ${count} items` };
        } else if (level.includes('LOW_CONFIDENCE')) {
            return { variant: 'glass-warning', label: 'Low Confidence - No Merge' };
        } else if (level.includes('MASTER')) {
            return { variant: 'glass-pink', label: 'Master Product Merge' };
        }
        return { variant: 'glass', label: level };
    };

    const levelInfo = getMergeLevelInfo(product.merge_level);

    return (
        <Card title="Merge Information">
            <div className="space-y-4">
                {/* Merge Level */}
                <div>
                    <p className="text-sm text-gray-500 mb-2">Merge Level</p>
                    <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
                </div>

                {/* Merge ID */}
                {product.merge_id && (
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Merge ID</p>
                        <p className="text-sm font-mono text-gray-700 bg-white/50 backdrop-blur-sm px-3 py-2 rounded-lg border border-white/30">
                            {product.merge_id}
                        </p>
                    </div>
                )}

                {/* Merged From */}
                {product.merged_from_docs && (
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Documents Merged</p>
                        <p className="text-lg font-semibold text-gray-900">{product.merged_from_docs}</p>
                    </div>
                )}

                {/* Merge Rule */}
                {product.merge_rule && (
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Merge Rule</p>
                        <p className="text-sm text-gray-700 bg-white/50 backdrop-blur-sm px-3 py-2 rounded-lg border border-white/30">
                            {product.merge_rule}
                        </p>
                    </div>
                )}

                {/* Merged Items */}
                {product.merge_items && product.merge_items.length > 0 && (
                    <div>
                        <p className="text-sm text-gray-500 mb-2">Merged Items ({product.merge_items.length})</p>
                        <div className="space-y-1 max-h-48 overflow-y-auto custom-scrollbar">
                            {product.merge_items.map((item, index) => (
                                <div key={index} className="text-sm text-gray-700 bg-white/50 backdrop-blur-sm px-3 py-2 rounded-lg border border-white/30">
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Merged UPCs */}
                {product.merged_upcs && product.merged_upcs.length > 0 && (
                    <div>
                        <p className="text-sm text-gray-500 mb-2">Merged UPCs ({product.merged_upcs.length})</p>
                        <div className="flex flex-wrap gap-2">
                            {product.merged_upcs.map((upc, index) => (
                                <Badge key={index} variant="glass" size="sm">
                                    {upc}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                {/* LLM Confidence */}
                {product.llm_confidence_min !== undefined && (
                    <div>
                        <p className="text-sm text-gray-500 mb-1">LLM Confidence (Min)</p>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 bg-white/30 backdrop-blur-sm rounded-full h-2.5 border border-white/20">
                                <div
                                    className={`h-2.5 rounded-full transition-all duration-500 ${product.llm_confidence_min >= 0.9 ? 'bg-emerald-500' :
                                            product.llm_confidence_min >= 0.8 ? 'bg-blue-500' : 'bg-amber-500'
                                        }`}
                                    style={{ width: `${product.llm_confidence_min * 100}%` }}
                                />
                            </div>
                            <span className="text-sm font-medium text-gray-900">
                                {(product.llm_confidence_min * 100).toFixed(1)}%
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </Card>
    );
};

export default MergeMetadata;
