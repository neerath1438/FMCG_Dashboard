import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/ui/Card';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Badge from '../components/ui/Badge';
import { dashboardAPI } from '../services/api';

const Analytics = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const data = await dashboardAPI.getProducts();
            setProducts(data);
        } catch (error) {
            console.error('Error fetching products:', error);
        } finally {
            setLoading(false);
        }
    };

    // Brand distribution
    const brandData = React.useMemo(() => {
        const brandCounts = {};
        products.forEach(p => {
            const brand = p.BRAND || 'Unknown';
            brandCounts[brand] = (brandCounts[brand] || 0) + 1;
        });
        return Object.entries(brandCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);
    }, [products]);

    // Merge level distribution
    const mergeLevelData = React.useMemo(() => {
        const levels = {
            'Single Item': 0,
            'Merged (2-5)': 0,
            'Merged (6-10)': 0,
            'Merged (10+)': 0,
            'Low Confidence': 0,
        };

        products.forEach(p => {
            const level = p.merge_level || '';
            const mergedDocs = p.merged_from_docs || 1;

            if (level.includes('LOW_CONFIDENCE')) {
                levels['Low Confidence']++;
            } else if (level.includes('NO_MERGE')) {
                levels['Single Item']++;
            } else if (mergedDocs >= 10) {
                levels['Merged (10+)']++;
            } else if (mergedDocs >= 6) {
                levels['Merged (6-10)']++;
            } else if (mergedDocs >= 2) {
                levels['Merged (2-5)']++;
            }
        });

        return Object.entries(levels).map(([name, value]) => ({ name, value }));
    }, [products]);

    // Confidence distribution
    const confidenceData = React.useMemo(() => {
        const ranges = {
            '90-100%': 0,
            '80-90%': 0,
            '70-80%': 0,
            '60-70%': 0,
            'Below 60%': 0,
            'N/A': 0,
        };

        products.forEach(p => {
            const conf = p.llm_confidence_min;
            if (!conf) {
                ranges['N/A']++;
            } else if (conf >= 0.9) {
                ranges['90-100%']++;
            } else if (conf >= 0.8) {
                ranges['80-90%']++;
            } else if (conf >= 0.7) {
                ranges['70-80%']++;
            } else if (conf >= 0.6) {
                ranges['60-70%']++;
            } else {
                ranges['Below 60%']++;
            }
        });

        return Object.entries(ranges).map(([name, value]) => ({ name, value }));
    }, [products]);

    // Pink-themed color palette
    const COLORS = ['#f43f5e', '#ec4899', '#a855f7', '#8b5cf6', '#6366f1', '#3b82f6', '#10b981', '#f59e0b'];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Summary Stats - Glass cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Total Products</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{products.length}</p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Unique Brands</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{brandData.length}</p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Merged Products</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                        {products.filter(p => (p.merged_from_docs || 1) > 1).length}
                    </p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Avg Confidence</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                        {products.filter(p => p.llm_confidence_min).length > 0
                            ? (products.reduce((sum, p) => sum + (p.llm_confidence_min || 0), 0) /
                                products.filter(p => p.llm_confidence_min).length * 100).toFixed(1) + '%'
                            : 'N/A'}
                    </p>
                </Card>
            </div>

            {/* Charts - Glass cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Brand Distribution */}
                <Card title="Top 10 Brands" subtitle="Product count by brand">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={brandData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(255,255,255,0.9)',
                                    backdropFilter: 'blur(8px)',
                                    border: '1px solid rgba(255,255,255,0.3)',
                                    borderRadius: '12px'
                                }}
                            />
                            <Bar dataKey="value" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>

                {/* Merge Level Distribution */}
                <Card title="Merge Level Distribution" subtitle="Products by merge status">
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={mergeLevelData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {mergeLevelData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(255,255,255,0.9)',
                                    backdropFilter: 'blur(8px)',
                                    border: '1px solid rgba(255,255,255,0.3)',
                                    borderRadius: '12px'
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </Card>

                {/* Confidence Distribution */}
                <Card title="Confidence Distribution" subtitle="LLM confidence scores">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={confidenceData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(255,255,255,0.9)',
                                    backdropFilter: 'blur(8px)',
                                    border: '1px solid rgba(255,255,255,0.3)',
                                    borderRadius: '12px'
                                }}
                            />
                            <Bar dataKey="value" fill="#ec4899" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>

                {/* Top Merged Products - Glass styling */}
                <Card title="Most Merged Products" subtitle="Products with highest merge count">
                    <div className="space-y-3">
                        {products
                            .sort((a, b) => (b.merged_from_docs || 0) - (a.merged_from_docs || 0))
                            .slice(0, 5)
                            .map((product, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-white/30">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate">{product.BRAND}</p>
                                        <p className="text-xs text-gray-500 truncate">{product.ITEM || 'N/A'}</p>
                                    </div>
                                    <Badge variant="glass-success">{product.merged_from_docs || 1} docs</Badge>
                                </div>
                            ))}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Analytics;
