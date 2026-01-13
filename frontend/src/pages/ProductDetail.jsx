import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Package } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import MergeMetadata from '../components/MergeMetadata';
import { dashboardAPI } from '../services/api';

const ProductDetail = () => {
    const { mergeId } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProduct();
    }, [mergeId]);

    const fetchProduct = async () => {
        try {
            setLoading(true);
            const data = await dashboardAPI.getProduct(mergeId);
            setProduct(data);
        } catch (error) {
            console.error('Error fetching product:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    if (!product) {
        return (
            <div className="text-center py-12 glass rounded-2xl">
                <p className="text-gray-500">Product not found</p>
                <Button variant="primary" onClick={() => navigate('/products')} className="mt-4">
                    Back to Products
                </Button>
            </div>
        );
    }

    // Get all monthly columns
    const monthlyColumns = Object.keys(product).filter(key =>
        key.toLowerCase().includes('w/e') || key.toLowerCase().includes('mat')
    );

    // Get descriptive columns (exclude system fields and monthly data)
    const systemFields = ['_id', 'merge_id', 'merge_items', 'merged_from_docs', 'merge_rule',
        'merge_level', 'merged_upcs', 'normalized_item', 'llm_confidence_min'];
    const descriptiveColumns = Object.keys(product).filter(key =>
        !systemFields.includes(key) && !monthlyColumns.includes(key) && !key.startsWith('_')
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/products')}>
                    Back
                </Button>
            </div>

            {/* Product Info - Pink gradient card */}
            <Card variant="gradient">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                        <Package className="text-white" size={32} />
                    </div>
                    <div className="flex-1">
                        <h2 className="text-2xl font-bold text-white mb-2">
                            {product.ITEM || product.normalized_item || 'Unknown Product'}
                        </h2>
                        <p className="text-white/80 text-lg">{product.BRAND || 'Unknown Brand'}</p>
                        {product.UPC && (
                            <p className="text-white/60 text-sm mt-1 font-mono">UPC: {product.UPC}</p>
                        )}
                    </div>
                </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Product Attributes */}
                <div className="lg:col-span-2 space-y-6">
                    <Card title="Product Attributes">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {descriptiveColumns.map(key => (
                                <div key={key} className="bg-white/50 backdrop-blur-sm p-3 rounded-xl border border-white/30">
                                    <p className="text-sm text-gray-500 mb-1">{key}</p>
                                    <p className="text-sm font-medium text-gray-900">
                                        {product[key]?.toString() || 'N/A'}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </Card>

                    {/* Monthly Data */}
                    {monthlyColumns.length > 0 && (
                        <Card title="Monthly Data">
                            <div className="overflow-x-auto custom-scrollbar">
                                <table className="w-full text-sm">
                                    <thead className="bg-white/40 backdrop-blur-sm border-b border-white/30">
                                        <tr>
                                            {monthlyColumns.map(col => (
                                                <th key={col} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                                    {col}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="bg-white/20 backdrop-blur-sm">
                                            {monthlyColumns.map(col => (
                                                <td key={col} className="px-4 py-2 text-gray-900 font-medium">
                                                    {typeof product[col] === 'number'
                                                        ? product[col].toLocaleString()
                                                        : product[col] || '0'}
                                                </td>
                                            ))}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </Card>
                    )}
                </div>

                {/* Merge Metadata */}
                <div>
                    <MergeMetadata product={product} />
                </div>
            </div>
        </div>
    );
};

export default ProductDetail;
