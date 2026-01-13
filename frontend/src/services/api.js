import axios from 'axios';

const api = axios.create({
    baseURL: 'https://retail-5465-api',
    headers: {
        'Content-Type': 'application/json',
    },
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
    getProducts: () => api.get('/dashboard/products'),
    getProduct: (mergeId) => api.get(`/dashboard/product/${mergeId}`),
    getLowConfidence: () => api.get('/dashboard/low-confidence'),
    exportMasterStock: () => api.get('/export/master-stock', { responseType: 'blob' }),
    resetDatabase: () => api.post('/database/reset'),
};

export const uploadAPI = {
    uploadExcel: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return axios.post('/api/upload/excel', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    triggerLLMMastering: (sheetName) => api.post(`/process/llm-mastering/${sheetName}`),
};

export const chatbotAPI = {
    sendQuery: (question, sessionId) => api.post('/chatbot/query', { question, session_id: sessionId }),
};

export default api;
