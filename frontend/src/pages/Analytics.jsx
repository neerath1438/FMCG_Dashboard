import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/ui/Card';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Badge from '../components/ui/Badge';
import { dashboardAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

const Analytics = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const res = await dashboardAPI.getAnalyticsData();
            const analyticsData = res?.data || res;
            setData(analyticsData);
        } catch (error) {
            console.error('Error fetching analytics data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Pink-themed color palette
    const COLORS = ['#f43f5e', '#ec4899', '#a855f7', '#8b5cf6', '#6366f1', '#3b82f6', '#10b981', '#f59e0b'];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="space-y-6">
            {/* Summary Stats - Glass cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Total Products</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{data.totalProducts?.toLocaleString()}</p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Unique Brands</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{data.uniqueBrands?.toLocaleString()}</p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Merged Products</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{data.mergedProducts?.toLocaleString()}</p>
                </Card>
                <Card>
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Avg Confidence</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                        {data.avgConfidence ? (data.avgConfidence * 100).toFixed(1) + '%' : 'N/A'}
                    </p>
                </Card>
            </div>

            {/* Charts - Glass cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Brand Distribution */}
                <Card title="Top 10 Brands" subtitle="Product count by brand">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data.brandDistribution || []}>
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

                {/* Confidence Distribution */}
                <Card title="Confidence Distribution" subtitle="LLM confidence scores - Click bar to view items">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                            data={data.confidenceDistribution || []}
                            onClick={(data) => {
                                if (data && data.activePayload && data.activePayload[0]) {
                                    const entry = data.activePayload[0].payload;
                                    const status = entry.isNA ? 'na' : 'scored';
                                    navigate(`/products?confidence_status=${status}`);
                                }
                            }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip
                                cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                                contentStyle={{
                                    background: 'rgba(255,255,255,0.9)',
                                    backdropFilter: 'blur(8px)',
                                    border: '1px solid rgba(255,255,255,0.3)',
                                    borderRadius: '12px'
                                }}
                            />
                            <Bar dataKey="value" fill="#ec4899" radius={[4, 4, 0, 0]} className="cursor-pointer" />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>


            </div>
        </div>
    );
};

export default Analytics;
