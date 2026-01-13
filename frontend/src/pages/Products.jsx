import React, { useState, useEffect } from 'react';
import { Search, Filter, X } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import { dashboardAPI } from '../services/api';

const Products = () => {
    const [products, setProducts] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterBrand, setFilterBrand] = useState('all');

    useEffect(() => {
        fetchProducts();
    }, []);

    useEffect(() => {
        filterProducts();
    }, [searchTerm, filterBrand, products]);

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const data = await dashboardAPI.getProducts();
            const products = data?.data || data;
            setProducts(Array.isArray(products) ? products : []);
            setFilteredProducts(Array.isArray(products) ? products : []);
        } catch (error) {
            console.error('Error fetching products:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterProducts = () => {
        let filtered = [...products];

        // Search filter
        if (searchTerm) {
            filtered = filtered.filter(p =>
                p.ITEM?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                p.BRAND?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                p.UPC?.toString().includes(searchTerm)
            );
        }

        // Brand filter
        if (filterBrand !== 'all') {
            filtered = filtered.filter(p => p.BRAND === filterBrand);
        }

        setFilteredProducts(filtered);
    };

    const uniqueBrands = [...new Set(products.map(p => p.BRAND).filter(Boolean))].sort();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Filters - Glass styling */}
            <div className="flex flex-col md:flex-row gap-4">
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
                                   text-gray-700 transition-all duration-200"
                    >
                        <option value="all">All Brands</option>
                        {uniqueBrands.map(brand => (
                            <option key={brand} value={brand}>{brand}</option>
                        ))}
                    </select>
                </div>

                <Button
                    variant="outline"
                    icon={X}
                    onClick={() => { setSearchTerm(''); setFilterBrand('all'); }}
                >
                    Clear Filters
                </Button>
            </div>

            {/* Results Count */}
            <div className="text-sm text-gray-600">
                Showing <span className="font-semibold text-pink-600">{filteredProducts.length}</span> of {products.length} products
            </div>

            {/* Products Grid */}
            {filteredProducts.length === 0 ? (
                <div className="text-center py-12 glass rounded-2xl">
                    <p className="text-gray-500">No products found</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredProducts.map((product, index) => (
                        <ProductCard key={product.merge_id || index} product={product} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default Products;
