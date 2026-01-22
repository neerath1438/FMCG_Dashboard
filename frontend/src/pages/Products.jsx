import React, { useState, useEffect } from 'react';
import { Search, Filter, X, LayoutGrid, List } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import Table from '../components/ui/Table';
import Badge from '../components/ui/Badge';
import { dashboardAPI } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';

const Products = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const confidenceStatusParam = searchParams.get('confidence_status') || 'all';
    const brandParam = searchParams.get('brand');

    const [products, setProducts] = useState([]);
    const [brands, setBrands] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterBrand, setFilterBrand] = useState(brandParam || 'all');
    const [hasMore, setHasMore] = useState(true);
    const [skip, setSkip] = useState(0);
    const [viewMode, setViewMode] = useState('grid');
    const limit = 100;
    const navigate = useNavigate();

    // Update filter when URL parameter changes
    useEffect(() => {
        if (brandParam && brandParam !== filterBrand) {
            setFilterBrand(brandParam);
        }
    }, [brandParam]);

    useEffect(() => {
        fetchInitialData();
    }, [confidenceStatusParam]);

    // Re-fetch products when filters change after a small delay
    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            fetchProducts(true);
        }, 500);

        return () => clearTimeout(delayDebounceFn);
    }, [searchTerm, filterBrand]);

    const fetchInitialData = async () => {
        try {
            setLoading(true);
            const [productsData, brandsData] = await Promise.all([
                dashboardAPI.getProducts(limit, 0, searchTerm, filterBrand, confidenceStatusParam),
                dashboardAPI.getBrands()
            ]);

            // Products
            const pResponse = productsData?.data || productsData;
            setProducts(pResponse?.products || pResponse);
            setHasMore(pResponse?.total > limit);
            setSkip(limit);

            // Brands
            setBrands(brandsData?.brands || []);
        } catch (error) {
            console.error('Error fetching initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchProducts = async (reset = false) => {
        try {
            if (reset) {
                // For debounced search/filter reset
                const data = await dashboardAPI.getProducts(limit, 0, searchTerm, filterBrand, confidenceStatusParam);
                const response = data?.data || data;
                const newProducts = response?.products || response;
                setProducts(newProducts);
                setHasMore(response?.total > limit);
                setSkip(limit);
            } else {
                setLoadingMore(true);
                const currentSkip = skip;
                const data = await dashboardAPI.getProducts(limit, currentSkip, searchTerm, filterBrand, confidenceStatusParam);
                const response = data?.data || data;
                const newProducts = response?.products || response;

                if (Array.isArray(newProducts)) {
                    setProducts(prev => [...prev, ...newProducts]);
                    setHasMore((currentSkip + limit) < response?.total);
                    setSkip(currentSkip + limit);
                }
            }
        } catch (error) {
            console.error('Error fetching products:', error);
        } finally {
            setLoadingMore(false);
        }
    };

    const handleClearFilters = () => {
        setSearchTerm('');
        setFilterBrand('all');
        setSearchParams({});
    };

    const columns = [
        { key: 'BRAND', label: 'Brand', sortable: true },
        {
            key: 'ITEM',
            label: 'Product',
            sortable: true,
            render: (value) => <span className="font-medium text-gray-900">{value}</span>
        },
        { key: 'UPC', label: 'UPC', sortable: true },
        {
            key: 'merged_from_docs',
            label: 'Merged Docs',
            sortable: true,
            render: (value) => (
                <Badge variant={(value || 1) > 1 ? 'glass-success' : 'glass-info'} size="sm">
                    {value || 1}
                </Badge>
            )
        },
        {
            key: 'MARKETS',
            label: 'Market',
            render: (value, row) => value || row.MARKET || 'N/A'
        }
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
            {/* Confidence Status Banner */}
            {confidenceStatusParam === 'na' && (
                <div className="bg-pink-50 border border-pink-100 p-4 rounded-2xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-pink-100 rounded-lg">
                            <Filter size={18} className="text-pink-600" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-pink-900">Filtering: N/A Confidence Items</p>
                            <p className="text-xs text-pink-700">Showing products that have not been scored by the AI agent yet.</p>
                        </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={handleClearFilters} className="bg-white">
                        Show All Products
                    </Button>
                </div>
            )}
            {/* Filters - Glass styling */}
            <div className="flex flex-col xl:flex-row gap-4">
                <div className="flex-1 flex flex-col md:flex-row gap-4">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search by product, brand, or UPC..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5
                                       bg-white/50 backdrop-blur-sm
                                       border border-white/40 rounded-xl
                                       focus:ring-2 focus:ring-pink-500/30 focus:border-pink-500/50
                                       focus:bg-white/70 placeholder-gray-400 text-gray-700
                                       transition-all duration-200"
                        />
                    </div>

                    {/* Brand Filter */}
                    <div className="flex items-center gap-2">
                        <Filter size={20} className="text-gray-400" />
                        <select
                            value={filterBrand}
                            onChange={(e) => setFilterBrand(e.target.value)}
                            className="px-4 py-2.5
                                       bg-white/50 backdrop-blur-sm
                                       border border-white/40 rounded-xl
                                       focus:ring-2 focus:ring-pink-500/30 focus:border-pink-500/50
                                       text-gray-700 transition-all duration-200 min-w-[180px]"
                        >
                            <option value="all">All Brands ({brands.length})</option>
                            {brands.map(brand => (
                                <option key={brand} value={brand}>{brand}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center bg-white/40 backdrop-blur-sm border border-white/40 rounded-xl p-1">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`p-2 rounded-lg transition-all ${viewMode === 'grid'
                                ? 'bg-white text-pink-600 shadow-sm'
                                : 'text-gray-400 hover:text-gray-600'}`}
                            title="Grid View"
                        >
                            <LayoutGrid size={20} />
                        </button>
                        <button
                            onClick={() => setViewMode('table')}
                            className={`p-2 rounded-lg transition-all ${viewMode === 'table'
                                ? 'bg-white text-pink-600 shadow-sm'
                                : 'text-gray-400 hover:text-gray-600'}`}
                            title="Table View"
                        >
                            <List size={20} />
                        </button>
                    </div>

                    <Button
                        variant="outline"
                        icon={X}
                        onClick={handleClearFilters}
                    >
                        Clear
                    </Button>
                </div>
            </div>

            {/* Results Count */}
            <div className="text-sm text-gray-600">
                Found <span className="font-semibold text-pink-600">{products.length}</span> results
            </div>

            {/* Products View */}
            {products.length === 0 ? (
                <div className="text-center py-12 glass rounded-2xl">
                    <p className="text-gray-500">No products found matching your filters</p>
                </div>
            ) : (
                <>
                    {viewMode === 'grid' ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {products.map((product, index) => (
                                <ProductCard key={product.merge_id || index} product={product} />
                            ))}
                        </div>
                    ) : (
                        <div className="bg-white/40 backdrop-blur-sm border border-white/40 rounded-2xl overflow-hidden">
                            <Table
                                columns={columns}
                                data={products}
                                onRowClick={(row) => navigate(`/products/${row.merge_id}`)}
                            />
                        </div>
                    )}

                    {/* Load More Button */}
                    {hasMore && (
                        <div className="flex justify-center mt-8">
                            <Button
                                variant="outline"
                                onClick={() => fetchProducts(false)}
                                loading={loadingMore}
                                disabled={loadingMore}
                            >
                                {loadingMore ? 'Loading...' : 'Load More Products'}
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Products;
