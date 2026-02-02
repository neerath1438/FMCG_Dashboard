import axios from 'axios';

// API base URL - Use environment variable or server IP
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://20.0.161.242:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 18000000, // 5 hours (18,000,000ms) for large file processing
});

// Request interceptor to add session token
api.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('session_token');
        if (token) {
            config.headers['X-Session-Token'] = token;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        const message = error.response?.data?.message || error.message || 'An error occurred';
        console.error('API Error:', message);
        return Promise.reject(error);
    }
);

// Authentication API methods
export const loginAPI = (email, password) => api.post('/auth/login', { email, password });

export const logoutAPI = (token) => api.post('/auth/logout', {}, {
    headers: { 'X-Session-Token': token }
});

export const verifyAuthAPI = (token) => api.get('/auth/verify', {
    headers: { 'X-Session-Token': token }
});

// API methods
export const dashboardAPI = {
    getSummary: () => api.get('/dashboard/summary'),
    getBrands: () => api.get('/dashboard/brands'),
    getProducts: (limit = 100, skip = 0, search = '', brand = '', confidenceStatus = 'all') =>
        api.get(`/dashboard/products?limit=${limit}&skip=${skip}&search=${search}&brand=${brand}&confidence_status=${confidenceStatus}`),
    getProduct: (mergeId) => api.get(`/dashboard/product/${mergeId}`),
    getLowConfidence: () => api.get('/dashboard/low-confidence'),
    getAnalyticsData: () => api.get('/dashboard/analytics-data'),
    exportMasterStock: (reportType = 'all') => api.get(`/export/master-stock?report_type=${reportType}`, { responseType: 'blob' }),
    resetDatabase: (clearCache = false) => api.post(`/database/reset?clear_cache=${clearCache}`),
};

export const uploadAPI = {
    uploadExcel: (file, signal) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/upload/excel', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 18000000, // 5 hours timeout for large uploads
            signal: signal, // Support for cancellation
        });
    },
    triggerLLMMastering: (sheetName) => api.post(`/process/llm-mastering/${sheetName}`),
};

export const chatbotAPI = {
    sendQuery: (question, sessionId) => api.post('/chatbot/query', { question, session_id: sessionId }),
};

export default api;
