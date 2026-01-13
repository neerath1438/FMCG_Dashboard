import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginAPI, logoutAPI, verifyAuthAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    // Check authentication on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const token = sessionStorage.getItem('session_token');

        if (!token) {
            setIsAuthenticated(false);
            setUser(null);
            setLoading(false);
            return;
        }

        try {
            const response = await verifyAuthAPI(token);
            if (response.status === 'success') {
                setIsAuthenticated(true);
                setUser(response.user);
            } else {
                // Invalid token
                sessionStorage.removeItem('session_token');
                setIsAuthenticated(false);
                setUser(null);
            }
        } catch (error) {
            // Token verification failed
            sessionStorage.removeItem('session_token');
            setIsAuthenticated(false);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            const response = await loginAPI(email, password);

            if (response.status === 'success') {
                // Store session token
                sessionStorage.setItem('session_token', response.session_token);

                // Update state
                setIsAuthenticated(true);
                setUser(response.user);

                // Navigate to dashboard
                navigate('/');

                return { success: true };
            } else {
                return { success: false, error: 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: error.response?.data?.detail || 'Invalid credentials'
            };
        }
    };

    const logout = async () => {
        const token = sessionStorage.getItem('session_token');

        try {
            if (token) {
                await logoutAPI(token);
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear session regardless of API call success
            sessionStorage.removeItem('session_token');
            setIsAuthenticated(false);
            setUser(null);
            navigate('/login');
        }
    };

    const value = {
        isAuthenticated,
        user,
        loading,
        login,
        logout,
        checkAuth
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext;
