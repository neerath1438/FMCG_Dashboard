import React, { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { dashboardAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

const LowConfidence = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchLowConfidence();
    }, []);

    const fetchLowConfidence = async () => {
        try {
            setLoading(true);
            const data = await dashboardAPI.getLowConfidence();
            setProducts(data);
        } catch (error) {
            console.error('Error fetching low confidence items:', error);
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        { key: 'BRAND', label: 'Brand', sortable: true },
        {
            key: 'ITEM',
            label: 'Product',
            sortable: true,
            render: (value) => (
                <span className="max-w-md truncate block">{value || 'N/A'}</span>
            )
        },
        { key: 'UPC', label: 'UPC', sortable: true },
        {
            key: 'llm_confidence_min',
            label: 'Confidence',
            sortable: true,
            render: (value) => {
                if (!value) return <Badge variant="glass" size="sm">N/A</Badge>;
                const percent = (value * 100).toFixed(1);
                const variant = value >= 0.8 ? 'glass-info' : value >= 0.6 ? 'glass-warning' : 'error';
                return <Badge variant={variant} size="sm">{percent}%</Badge>;
            }
        },
        {
            key: 'merged_from_docs',
            label: 'Merged Docs',
            sortable: true,
            render: (value) => value || 1
        },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header - Glass warning card */}
            <Card variant="warning">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-amber-100/70 backdrop-blur-sm rounded-xl">
                        <AlertTriangle className="text-amber-600" size={32} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 mb-1">Low Confidence Items</h2>
                        <p className="text-gray-600">
                            These products have low LLM confidence scores and may require manual review.
                        </p>
                        <p className="text-sm text-gray-500 mt-2">
                            Total items: <span className="font-semibold text-amber-600">{products.length}</span>
                        </p>
                    </div>
                </div>
            </Card>

            {/* Table */}
            {products.length === 0 ? (
                <Card>
                    <div className="text-center py-12 text-gray-500">
                        <AlertTriangle size={48} className="mx-auto mb-4 text-gray-300" />
                        <p>No low confidence items found</p>
                    </div>
                </Card>
            ) : (
                <Card>
                    <Table
                        columns={columns}
                        data={products}
                        onRowClick={(row) => navigate(`/products/${row.merge_id}`)}
                    />
                </Card>
            )}
        </div>
    );
};

export default LowConfidence;
