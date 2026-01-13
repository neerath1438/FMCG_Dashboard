import React, { useState, useEffect } from 'react';
import { Package, Download, Trash2, TrendingUp, Zap, Bell, Users, RefreshCw, ArrowRight } from 'lucide-react';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { dashboardAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

// Circular Progress Component matching reference design
const CircularProgress = ({ percentage = 0, size = 48, strokeWidth = 4 }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size} height={size}>
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth={strokeWidth}
                />
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    className="transition-all duration-700"
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-semibold text-gray-700">{percentage}%</span>
            </div>
        </div>
    );
};

const Dashboard = () => {
    const [summary, setSummary] = useState(null);
    const [recentProducts, setRecentProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [summaryData, productsData] = await Promise.all([
                dashboardAPI.getSummary(),
                dashboardAPI.getProducts()
            ]);

            setSummary(summaryData?.data || summaryData);
            const products = productsData?.data || productsData;
            setRecentProducts(Array.isArray(products) ? products.slice(0, 10) : []);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await dashboardAPI.exportMasterStock();
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Master_Stock_Export_${new Date().toISOString().split('T')[0]}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export data. Please try again.');
        }
    };

    const handleResetDatabase = async () => {
        const confirmed = window.confirm(
            'WARNING: This will delete ALL data from the database!\n\n' +
            'This includes:\n' +
            '- All uploaded files (RAW data)\n' +
            '- All processed products (SINGLE_STOCK)\n' +
            '- All master products (MASTER_STOCK)\n' +
            '- All LLM cache\n\n' +
            'This action CANNOT be undone!\n\n' +
            'Are you sure you want to continue?'
        );

        if (!confirmed) return;

        try {
            const result = await dashboardAPI.resetDatabase();
            if (result.status === 'success') {
                alert(`Database reset successfully!\n\nDeleted ${result.total_deleted} records from ${Object.keys(result.deleted_counts).length} collections.`);
                fetchData();
            } else {
                alert(`Reset failed: ${result.message}`);
            }
        } catch (error) {
            console.error('Reset failed:', error);
            alert('Failed to reset database. Please try again.');
        }
    };

    const columns = [
        { key: 'BRAND', label: 'Brand', sortable: true },
        {
            key: 'ITEM',
            label: 'Product',
            sortable: true,
            render: (value) => (
                <span className="max-w-xs truncate block">{value || 'N/A'}</span>
            )
        },
        { key: 'UPC', label: 'UPC', sortable: true },
        {
            key: 'merged_from_docs',
            label: 'Merged Docs',
            sortable: true,
            render: (value) => (
                <Badge variant={value > 1 ? 'glass-success' : 'glass-info'} size="sm">
                    {value || 1}
                </Badge>
            )
        },
        {
            key: 'merge_level',
            label: 'Status',
            render: (value) => {
                if (!value) return <Badge variant="glass" size="sm">Unknown</Badge>;
                if (value.includes('NO_MERGE')) return <Badge variant="glass-info" size="sm">Single</Badge>;
                if (value.includes('MERGED')) return <Badge variant="glass-success" size="sm">Merged</Badge>;
                if (value.includes('LOW_CONFIDENCE')) return <Badge variant="glass-warning" size="sm">Low Conf</Badge>;
                return <Badge variant="glass" size="sm">{value}</Badge>;
            }
        },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    // Calculate percentages for circular progress
    const totalProducts = summary?.master_products || 0;
    const mergedProducts = summary?.raw_rows || 0;
    const lowConfidence = summary?.low_confidence || 0;
    const healthPercent = totalProducts > 0 ? Math.round(((totalProducts - lowConfidence) / totalProducts) * 100) : 0;
    const mergePercent = mergedProducts > 0 && totalProducts > 0 ? Math.min(Math.round((mergedProducts / (mergedProducts + totalProducts)) * 100), 100) : 0;

    return (
        <div className="space-y-6">
            {/* Top Section - Header Left + Status Card Right */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Left Side - Title, Description, Buttons */}
                <div className="lg:col-span-3 space-y-4">
                    {/* Breadcrumb */}
                    <p className="text-sm text-gray-500 uppercase tracking-wide">Dashboard / Overview</p>

                    {/* Title */}
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">FMCG Dashboard</h1>

                    {/* Description */}
                    <p className="text-gray-500 text-sm sm:text-base max-w-lg">
                        Comprehensive overview of your product portfolio, key performance metrics, and recent activity.
                    </p>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap gap-3 pt-2">
                        <Button
                            variant="primary"
                            icon={Download}
                            onClick={handleExport}
                        >
                            Export Data
                        </Button>
                        <button
                            onClick={fetchData}
                            className="p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors shadow-sm"
                        >
                            <RefreshCw size={20} className="text-gray-600" />
                        </button>
                    </div>
                </div>

                {/* Right Side - Status Card + Decorative Image */}
                <div className="lg:col-span-2 flex gap-4">
                    {/* Status Card */}
                    <div className="flex-1 bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                        <div className="flex items-start gap-3 mb-4">
                            <div className="p-2 bg-pink-100 rounded-xl">
                                <Package className="text-pink-600" size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">Product Intelligence</h3>
                                <p className="text-xs text-gray-500">Current Status</p>
                            </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-4">
                            {lowConfidence > 0
                                ? `${lowConfidence} items need review. Manual verification required.`
                                : 'All products processed successfully.'}
                        </p>
                        <button
                            onClick={() => navigate('/low-confidence')}
                            className="text-sm text-pink-600 hover:text-pink-700 font-medium flex items-center gap-1"
                        >
                            View Details <ArrowRight size={14} />
                        </button>
                    </div>

                    {/* Decorative Image Placeholder */}
                    <div className="hidden xl:block w-32 h-full rounded-2xl overflow-hidden bg-gradient-to-br from-indigo-400 to-purple-500 relative">
                        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                        <div className="absolute bottom-3 left-3 right-3">
                            <div className="h-1 bg-white/30 rounded mb-1" />
                            <div className="h-1 bg-white/20 rounded w-2/3" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Row - 3 Cards with Circular Progress */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Data Health */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-4">
                        <CircularProgress percentage={healthPercent} />
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Data Health</p>
                            <p className="text-2xl font-bold text-gray-900">{totalProducts}</p>
                        </div>
                    </div>
                </div>

                {/* Merge Status */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-4">
                        <CircularProgress percentage={mergePercent} />
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Merge Status</p>
                            <p className="text-2xl font-bold text-gray-900">{mergedProducts}</p>
                            <p className="text-xs text-gray-400">Total Rows</p>
                        </div>
                    </div>
                </div>

                {/* UPC Coverage */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-4">
                        <CircularProgress percentage={totalProducts > 0 ? Math.min(Math.round(((summary?.unique_upcs || 0) / totalProducts) * 100), 100) : 0} />
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">UPC Coverage</p>
                            <p className="text-2xl font-bold text-gray-900">{summary?.unique_upcs || 0}</p>
                            <p className="text-xs text-gray-400">Unique UPCs</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Grid - 4 Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Products Card */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <TrendingUp size={18} className="text-emerald-500" />
                            <span className="font-semibold text-gray-900">Products</span>
                        </div>
                        <Badge variant="glass-success" size="sm">Overview</Badge>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Total Products</span>
                            <span className="text-sm font-semibold text-blue-600">{totalProducts}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Master Items</span>
                            <span className="text-sm font-semibold text-blue-600">{summary?.master_products || 0}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Growth Rate</span>
                            <span className="text-sm font-semibold text-emerald-600">+0%</span>
                        </div>
                    </div>
                </div>

                {/* Merge Status Card */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <Zap size={18} className="text-blue-500" />
                            <span className="font-semibold text-gray-900">Merge Status</span>
                        </div>
                        <Badge variant="glass-info" size="sm">Health Check</Badge>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Merged</span>
                            <span className="text-sm font-semibold text-blue-600">{recentProducts.filter(p => p.merged_from_docs > 1).length}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Single</span>
                            <span className="text-sm font-semibold text-blue-600">{recentProducts.filter(p => !p.merged_from_docs || p.merged_from_docs === 1).length}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">Low Confidence</span>
                            <span className="text-sm font-semibold text-amber-600">{lowConfidence}</span>
                        </div>
                    </div>
                </div>

                {/* Alerts Card */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <Bell size={18} className="text-amber-500" />
                            <span className="font-semibold text-gray-900">Alerts</span>
                        </div>
                        <Badge variant="glass-warning" size="sm">Attention</Badge>
                    </div>
                    {lowConfidence > 0 ? (
                        <div className="bg-red-50 rounded-xl p-3">
                            <div className="flex items-center gap-2 mb-1">
                                <div className="w-2 h-2 bg-red-500 rounded-full" />
                                <span className="text-sm font-medium text-red-700">Low Confidence</span>
                            </div>
                            <p className="text-xs text-red-600">{lowConfidence} items need review</p>
                        </div>
                    ) : (
                        <div className="bg-emerald-50 rounded-xl p-3">
                            <div className="flex items-center gap-2 mb-1">
                                <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                                <span className="text-sm font-medium text-emerald-700">All Clear</span>
                            </div>
                            <p className="text-xs text-emerald-600">No issues detected</p>
                        </div>
                    )}
                </div>

                {/* Quick Actions Card */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <Users size={18} className="text-purple-500" />
                            <span className="font-semibold text-gray-900">Quick Actions</span>
                        </div>
                        <Badge variant="glass-pink" size="sm">Tools</Badge>
                    </div>
                    <div className="space-y-3">
                        <button
                            onClick={() => navigate('/upload')}
                            className="w-full flex justify-between items-center text-sm text-gray-500 hover:text-pink-600 transition-colors"
                        >
                            <span>Upload Data</span>
                            <ArrowRight size={14} />
                        </button>
                        <button
                            onClick={() => navigate('/products')}
                            className="w-full flex justify-between items-center text-sm text-gray-500 hover:text-pink-600 transition-colors"
                        >
                            <span>View Products</span>
                            <ArrowRight size={14} />
                        </button>
                        <button
                            onClick={handleResetDatabase}
                            className="w-full flex justify-between items-center text-sm text-red-500 hover:text-red-600 transition-colors"
                        >
                            <span>Reset Database</span>
                            <Trash2 size={14} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Recent Products Table */}
            <Card title="Recent Products" subtitle="Latest processed products">
                <Table
                    columns={columns}
                    data={recentProducts}
                    onRowClick={(row) => navigate(`/products/${row.merge_id}`)}
                />
            </Card>
        </div>
    );
};

export default Dashboard;
