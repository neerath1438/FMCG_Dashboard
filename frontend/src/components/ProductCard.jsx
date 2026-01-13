import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from './ui/Card';
import Badge from './ui/Badge';

const ProductCard = ({ product }) => {
    const navigate = useNavigate();

    const getMergeLevelBadge = (level) => {
        if (!level) return { variant: 'default', text: 'Unknown' };

        if (level.includes('NO_MERGE')) {
            return { variant: 'glass-info', text: 'Single Item' };
        } else if (level.includes('MERGED')) {
            const count = level.match(/\d+/)?.[0] || '?';
            return { variant: 'glass-success', text: `Merged (${count})` };
        } else if (level.includes('LOW_CONFIDENCE')) {
            return { variant: 'glass-warning', text: 'Low Confidence' };
        }
        return { variant: 'glass', text: level };
    };

    const getConfidenceBadge = (confidence) => {
        if (!confidence) return null;
        if (confidence >= 0.9) return { variant: 'glass-success', text: `${(confidence * 100).toFixed(0)}%` };
        if (confidence >= 0.8) return { variant: 'glass-info', text: `${(confidence * 100).toFixed(0)}%` };
        return { variant: 'glass-warning', text: `${(confidence * 100).toFixed(0)}%` };
    };

    const mergeBadge = getMergeLevelBadge(product.merge_level);
    const confidenceBadge = product.llm_confidence_min ? getConfidenceBadge(product.llm_confidence_min) : null;

    return (
        <Card
            hoverable
            onClick={() => navigate(`/products/${product.merge_id}`)}
            className="h-full"
        >
            <div className="space-y-3">
                {/* Brand */}
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Brand</p>
                    <p className="text-lg font-semibold text-gray-900">{product.BRAND || 'Unknown'}</p>
                </div>

                {/* Item */}
                <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Product</p>
                    <p className="text-sm text-gray-700 line-clamp-2">{product.ITEM || product.normalized_item || 'N/A'}</p>
                </div>

                {/* UPC */}
                {product.UPC && (
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide">UPC</p>
                        <p className="text-sm font-mono text-gray-700">{product.UPC}</p>
                    </div>
                )}

                {/* Badges */}
                <div className="flex flex-wrap gap-2 pt-2">
                    <Badge variant={mergeBadge.variant} size="sm">
                        {mergeBadge.text}
                    </Badge>
                    {confidenceBadge && (
                        <Badge variant={confidenceBadge.variant} size="sm">
                            Confidence: {confidenceBadge.text}
                        </Badge>
                    )}
                    {product.merged_from_docs > 1 && (
                        <Badge variant="glass-pink" size="sm">
                            {product.merged_from_docs} docs
                        </Badge>
                    )}
                </div>
            </div>
        </Card>
    );
};

export default ProductCard;
