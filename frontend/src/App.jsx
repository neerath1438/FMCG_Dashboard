import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Upload from './pages/Upload';
import LowConfidence from './pages/LowConfidence';
import Analytics from './pages/Analytics';
import Chatbot from './pages/Chatbot';
import Login from './pages/Login';

import { Toaster } from 'react-hot-toast';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-600">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-white text-lg font-medium">Loading...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return children;
};

// Public Route Component (redirect to dashboard if already logged in)
const PublicRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-600">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-white text-lg font-medium">Loading...</p>
                </div>
            </div>
        );
    }

    if (isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    return children;
};

function AppRoutes() {
    return (
        <Routes>
            {/* Public Route - Login */}
            <Route path="/login" element={
                <PublicRoute>
                    <Login />
                </PublicRoute>
            } />

            {/* Protected Routes */}
            <Route path="/" element={
                <ProtectedRoute>
                    <Layout>
                        <Dashboard />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/products" element={
                <ProtectedRoute>
                    <Layout>
                        <Products />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/products/:mergeId" element={
                <ProtectedRoute>
                    <Layout>
                        <ProductDetail />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/upload" element={
                <ProtectedRoute>
                    <Layout>
                        <Upload />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/low-confidence" element={
                <ProtectedRoute>
                    <Layout>
                        <LowConfidence />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/analytics" element={
                <ProtectedRoute>
                    <Layout>
                        <Analytics />
                    </Layout>
                </ProtectedRoute>
            } />
            <Route path="/chatbot" element={
                <ProtectedRoute>
                    <Layout>
                        <Chatbot />
                    </Layout>
                </ProtectedRoute>
            } />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}

function App() {
    return (
        <Router>
            <AuthProvider>
                <Toaster position="top-right" reverseOrder={false} />
                <AppRoutes />
            </AuthProvider>
        </Router>
    );
}

export default App;
