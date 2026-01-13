/**
 * IBKR Options Trading Assistant - Dashboard JavaScript
 *
 * This module handles all client-side functionality:
 * - Fetching and displaying alerts
 * - Filtering and sorting
 * - Real-time updates
 * - User interactions
 *
 * Author: IBKR Options Assistant
 * License: MIT
 */

// ═══════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = '/api';
const REFRESH_INTERVAL = 30000; // 30 seconds

// ═══════════════════════════════════════════════════════════════════════════
// State Management
// ═══════════════════════════════════════════════════════════════════════════

const state = {
    alerts: [],
    filters: {
        symbol: '',
        optionType: '',
        decision: '',
        minConfidence: 0
    },
    summary: null,
    isLoading: false,
    isConnected: false,
    lastUpdate: null,
    refreshTimer: null
};

// ═══════════════════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fetch alerts from the API with current filters
 */
async function fetchAlerts() {
    try {
        const params = new URLSearchParams();

        if (state.filters.symbol) {
            params.append('symbol', state.filters.symbol);
        }
        if (state.filters.optionType) {
            params.append('option_type', state.filters.optionType);
        }
        if (state.filters.decision) {
            params.append('decision', state.filters.decision);
        }
        if (state.filters.minConfidence > 0) {
            params.append('min_confidence', state.filters.minConfidence);
        }

        const url = `${API_BASE}/alerts?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            state.alerts = data.alerts;
            state.summary = data.summary;
            state.lastUpdate = new Date(data.timestamp);
            return data;
        } else {
            throw new Error(data.error || 'Failed to fetch alerts');
        }
    } catch (error) {
        console.error('Error fetching alerts:', error);
        throw error;
    }
}

/**
 * Fetch system status
 */
async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        state.isConnected = data.connected;
        updateConnectionStatus(data.connected);

        return data;
    } catch (error) {
        console.error('Error fetching status:', error);
        state.isConnected = false;
        updateConnectionStatus(false);
    }
}

/**
 * Fetch summary statistics
 */
async function fetchSummary() {
    try {
        const response = await fetch(`${API_BASE}/summary`);
        const data = await response.json();

        if (data.success) {
            updateStatsBar(data);
        }

        return data;
    } catch (error) {
        console.error('Error fetching summary:', error);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// UI Update Functions
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    if (statusDot) {
        statusDot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    }

    if (statusText) {
        statusText.textContent = connected ? 'Connected (Paper)' : 'Disconnected';
    }
}

/**
 * Update stats bar with summary data
 */
function updateStatsBar(summary) {
    const elements = {
        'stat-total': summary.total_alerts,
        'stat-buy': summary.by_decision?.BUY || 0,
        'stat-sell': summary.by_decision?.SELL || 0,
        'stat-wait': summary.by_decision?.WAIT || 0,
        'stat-confidence': `${summary.avg_confidence}%`,
        'stat-actionable': `${summary.actionable_pct}%`
    };

    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
}

/**
 * Render all alert cards
 */
function renderAlerts() {
    const container = document.getElementById('alerts-container');
    if (!container) return;

    if (state.alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <h3 class="empty-title">No Alerts Found</h3>
                <p class="empty-text">
                    No options alerts match your current filters.
                    Try adjusting the filters or wait for new signals.
                </p>
            </div>
        `;
        return;
    }

    const alertsHtml = state.alerts.map(alert => createAlertCard(alert)).join('');
    container.innerHTML = `<div class="alerts-grid">${alertsHtml}</div>`;
}

/**
 * Create HTML for a single alert card
 */
function createAlertCard(alert) {
    const decisionClass = alert.decision.toLowerCase();
    const optionTypeClass = alert.option_type.toLowerCase();

    // Determine confidence class
    let confidenceClass = 'low';
    if (alert.confidence >= 75) {
        confidenceClass = 'high';
    } else if (alert.confidence >= 50) {
        confidenceClass = 'medium';
    }

    // Format signals
    const signalsHtml = alert.signals.map(signal => {
        const directionClass = signal.direction;
        return `
            <span class="signal-tag ${directionClass}">
                ${formatSignalType(signal.type)}
                <span class="signal-strength">${signal.strength.toFixed(0)}%</span>
            </span>
        `;
    }).join('');

    return `
        <div class="alert-card ${decisionClass}" data-alert-id="${alert.alert_id}">
            <div class="alert-header">
                <div class="alert-symbol">
                    <span class="symbol-name">${alert.symbol}</span>
                    <span class="option-type ${optionTypeClass}">
                        ${alert.option_type === 'CALL' ? '📈' : '📉'} ${alert.option_type}
                    </span>
                </div>
                <div class="decision-badge">
                    <span class="decision-text ${decisionClass}">${alert.decision}</span>
                </div>
            </div>

            <div class="alert-body">
                <div class="strike-expiry">
                    <div>
                        <div class="strike-price">$${alert.strike.toFixed(0)}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="expiry-date">${formatDate(alert.expiration)}</div>
                        <div class="expiry-dte">${alert.days_to_expiry} DTE</div>
                    </div>
                </div>

                <div class="confidence-section">
                    <div class="confidence-header">
                        <span class="confidence-label">Confidence</span>
                        <span class="confidence-value">${alert.confidence.toFixed(1)}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill ${confidenceClass}"
                             style="width: ${alert.confidence}%"></div>
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-item">
                        <span class="metric-label">Underlying</span>
                        <span class="metric-value">$${alert.underlying_price.toFixed(2)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Option Price</span>
                        <span class="metric-value">$${alert.option_mid.toFixed(2)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Volume</span>
                        <span class="metric-value ${alert.volume_ratio >= 3 ? 'highlight' : ''}">
                            ${formatNumber(alert.volume)} (${alert.volume_ratio.toFixed(1)}x)
                        </span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Open Interest</span>
                        <span class="metric-value">${formatNumber(alert.open_interest)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">IV</span>
                        <span class="metric-value">${alert.implied_volatility.toFixed(1)}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Delta</span>
                        <span class="metric-value">${alert.delta.toFixed(3)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Bid/Ask</span>
                        <span class="metric-value">$${alert.option_bid.toFixed(2)} / $${alert.option_ask.toFixed(2)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Spread</span>
                        <span class="metric-value ${alert.spread_pct > 5 ? 'text-warning' : ''}">${alert.spread_pct.toFixed(1)}%</span>
                    </div>
                </div>

                <div class="signals-section">
                    <div class="signals-title">Signals (${alert.signal_count})</div>
                    <div class="signals-list">
                        ${signalsHtml}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Show loading state
 */
function showLoading() {
    state.isLoading = true;
    const container = document.getElementById('alerts-container');
    if (container) {
        container.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner"></div>
                <p>Loading alerts...</p>
            </div>
        `;
    }
}

/**
 * Hide loading state
 */
function hideLoading() {
    state.isLoading = false;
}

// ═══════════════════════════════════════════════════════════════════════════
// Filter Handlers
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Apply filters and refresh display
 */
async function applyFilters() {
    // Get filter values
    state.filters.symbol = document.getElementById('filter-symbol')?.value || '';
    state.filters.optionType = document.getElementById('filter-type')?.value || '';
    state.filters.decision = document.getElementById('filter-decision')?.value || '';
    state.filters.minConfidence = parseFloat(document.getElementById('filter-confidence')?.value || 0);

    await refreshData();
}

/**
 * Reset all filters
 */
function resetFilters() {
    state.filters = {
        symbol: '',
        optionType: '',
        decision: '',
        minConfidence: 0
    };

    // Reset form elements
    const filterSymbol = document.getElementById('filter-symbol');
    const filterType = document.getElementById('filter-type');
    const filterDecision = document.getElementById('filter-decision');
    const filterConfidence = document.getElementById('filter-confidence');

    if (filterSymbol) filterSymbol.value = '';
    if (filterType) filterType.value = '';
    if (filterDecision) filterDecision.value = '';
    if (filterConfidence) filterConfidence.value = 0;

    refreshData();
}

// ═══════════════════════════════════════════════════════════════════════════
// Utility Functions
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Format signal type for display
 */
function formatSignalType(type) {
    const types = {
        'unusual_volume': '📊 Vol',
        'oi_acceleration': '📈 OI',
        'iv_spike': '⚡ IV',
        'delta_momentum': '🎯 Delta'
    };
    return types[type] || type;
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

/**
 * Format large numbers
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Update last update timestamp
 */
function updateTimestamp() {
    const element = document.getElementById('last-update');
    if (element && state.lastUpdate) {
        element.textContent = `Last updated: ${state.lastUpdate.toLocaleTimeString()}`;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Functions
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Refresh all data
 */
async function refreshData() {
    showLoading();

    try {
        await Promise.all([
            fetchAlerts(),
            fetchStatus(),
            fetchSummary()
        ]);

        renderAlerts();
        updateTimestamp();
    } catch (error) {
        console.error('Error refreshing data:', error);
        const container = document.getElementById('alerts-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <h3 class="empty-title">Error Loading Data</h3>
                    <p class="empty-text">${error.message}</p>
                    <button class="btn btn-primary" onclick="refreshData()">Retry</button>
                </div>
            `;
        }
    } finally {
        hideLoading();
    }
}

/**
 * Start auto-refresh timer
 */
function startAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
    }

    state.refreshTimer = setInterval(() => {
        refreshData();
    }, REFRESH_INTERVAL);
}

/**
 * Stop auto-refresh timer
 */
function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

/**
 * Initialize the dashboard
 */
async function initDashboard() {
    console.log('Initializing IBKR Options Assistant Dashboard...');

    // Set up event listeners
    const applyBtn = document.getElementById('btn-apply-filters');
    const resetBtn = document.getElementById('btn-reset-filters');
    const refreshBtn = document.getElementById('btn-refresh');

    if (applyBtn) {
        applyBtn.addEventListener('click', applyFilters);
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshData);
    }

    // Enter key applies filters
    document.querySelectorAll('.filter-input, .filter-select').forEach(el => {
        el.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });
    });

    // Initial data load
    await refreshData();

    // Start auto-refresh
    startAutoRefresh();

    console.log('Dashboard initialized');
}

// ═══════════════════════════════════════════════════════════════════════════
// Initialize on DOM ready
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', initDashboard);

// Pause refresh when tab is hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        refreshData();
        startAutoRefresh();
    }
});
