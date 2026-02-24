// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Navigate to audit dashboard
function navigateToAudit() {
    window.location.href = 'audit_dashboard.html';
}

// Format number with commas
function formatNumber(num) {
    return num.toLocaleString();
}

// Load dashboard data from API
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update alert message
        document.getElementById('alertMessage').textContent =
            `${data.items_need_review} items need review. Manual verification required.`;

        // Update stats cards
        document.getElementById('inputRows').textContent = formatNumber(data.input_rows);
        document.getElementById('itemsMerged').textContent = formatNumber(data.items_merged);
        document.getElementById('outputRows').textContent = formatNumber(data.output_rows);
        document.getElementById('reductionPct').textContent = `${data.reduction_percentage}% Reduction`;

        // Update products card
        document.getElementById('productsInputRows').textContent = formatNumber(data.input_rows);
        document.getElementById('productsOutputRows').textContent = formatNumber(data.output_rows);
        document.getElementById('uniqueUPCs').textContent = formatNumber(data.unique_upcs);

        // Update merge status card
        document.getElementById('mergedCount').textContent = formatNumber(data.merged);
        document.getElementById('singleCount').textContent = formatNumber(data.single);
        document.getElementById('uniqueBrands').textContent = formatNumber(data.unique_brands);

        console.log('✅ Dashboard data loaded successfully');
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);

        // Show error state
        const errorElements = [
            'alertMessage', 'inputRows', 'itemsMerged', 'outputRows',
            'productsInputRows', 'productsOutputRows', 'uniqueUPCs',
            'mergedCount', 'singleCount', 'uniqueBrands'
        ];

        errorElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Error';
                element.style.color = 'var(--danger)';
            }
        });
    }
}

// Auto-refresh data every 30 seconds
function startAutoRefresh() {
    setInterval(loadDashboardData, 30000); // 30 seconds
    console.log('🔄 Auto-refresh enabled (30s interval)');
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 FMCG Dashboard initializing...');

    // Load initial data
    loadDashboardData();

    // Start auto-refresh
    startAutoRefresh();

    console.log('✅ Dashboard initialized');
});
