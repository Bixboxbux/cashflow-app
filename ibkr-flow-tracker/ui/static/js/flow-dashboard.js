/**
 * Institutional Flow Tracker - Dashboard JavaScript
 *
 * Real-time flow signal display with WebSocket updates.
 *
 * Features:
 * - WebSocket connection for live updates
 * - Filtering and sorting
 * - Auto-refresh fallback
 * - Responsive design
 */

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
    WS_URL: `ws://${window.location.host}/ws`,
    API_BASE: '/api',
    REFRESH_INTERVAL: 5000,
    MAX_SIGNALS: 100,
    RECONNECT_DELAY: 3000,
};


// ═══════════════════════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════════════════════

const state = {
    signals: [],
    ws: null,
    wsConnected: false,
    filters: {
        symbol: '',
        direction: '',
        signalType: '',
        minPremium: 0,
    },
    stats: {
        total: 0,
        bullish: 0,
        bearish: 0,
        sweeps: 0,
        whales: 0,
        totalPremium: 0,
    },
    isDemo: true,
    refreshTimer: null,
};


// ═══════════════════════════════════════════════════════════════════════════
// WebSocket
// ═══════════════════════════════════════════════════════════════════════════

function connectWebSocket() {
    try {
        state.ws = new WebSocket(CONFIG.WS_URL);

        state.ws.onopen = () => {
            console.log('WebSocket connected');
            state.wsConnected = true;
            updateConnectionStatus(true);
        };

        state.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        state.ws.onclose = () => {
            console.log('WebSocket disconnected');
            state.wsConnected = false;
            updateConnectionStatus(false);

            // Reconnect after delay
            setTimeout(connectWebSocket, CONFIG.RECONNECT_DELAY);
        };

        state.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

    } catch (e) {
        console.error('Failed to connect WebSocket:', e);
        // Fall back to polling
        startPolling();
    }
}

function handleWebSocketMessage(data) {
    if (data.type === 'new_signal') {
        addSignal(data.signal);
    } else if (data.type === 'update_stats') {
        updateStats(data.stats);
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════════════════

async function fetchSignals() {
    try {
        const params = new URLSearchParams();
        if (state.filters.symbol) params.append('symbol', state.filters.symbol);
        if (state.filters.direction) params.append('direction', state.filters.direction);
        if (state.filters.signalType) params.append('signal_type', state.filters.signalType);
        if (state.filters.minPremium > 0) params.append('min_premium', state.filters.minPremium);

        const response = await fetch(`${CONFIG.API_BASE}/signals?${params}`);
        const data = await response.json();

        if (data.success) {
            state.signals = data.signals;
            renderSignals();
        }
    } catch (e) {
        console.error('Error fetching signals:', e);
    }
}

async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();

        if (data.success) {
            state.isDemo = data.demo_mode;
            updateConnectionStatus(data.connected || data.demo_mode);
            if (data.stats) {
                updateStats(data.stats);
            }
        }
    } catch (e) {
        console.error('Error fetching status:', e);
    }
}

async function fetchSummary() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/summary`);
        const data = await response.json();

        if (data.success) {
            updateStatsBar(data);
        }
    } catch (e) {
        console.error('Error fetching summary:', e);
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// UI Updates
// ═══════════════════════════════════════════════════════════════════════════

function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    if (statusDot) {
        statusDot.className = `status-dot ${connected ? (state.isDemo ? 'demo' : 'connected') : 'disconnected'}`;
    }
    if (statusText) {
        statusText.textContent = connected
            ? (state.isDemo ? 'Demo Mode' : 'Connected')
            : 'Disconnected';
    }
}

function updateStatsBar(summary) {
    setElementText('stat-total', summary.total || 0);
    setElementText('stat-bullish', summary.by_direction?.BULLISH || 0);
    setElementText('stat-bearish', summary.by_direction?.BEARISH || 0);
    setElementText('stat-sweeps', summary.by_type?.SWEEP || 0);
    setElementText('stat-whales', summary.stats?.whales_detected || 0);
    setElementText('stat-premium', formatPremium(summary.total_premium || 0));
}

function updateStats(stats) {
    state.stats = { ...state.stats, ...stats };
    updateStatsBar({ stats: state.stats, ...state.stats });
}

function setElementText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}


// ═══════════════════════════════════════════════════════════════════════════
// Signal Rendering
// ═══════════════════════════════════════════════════════════════════════════

function addSignal(signal) {
    // Add to beginning
    state.signals.unshift(signal);

    // Trim to max
    if (state.signals.length > CONFIG.MAX_SIGNALS) {
        state.signals = state.signals.slice(0, CONFIG.MAX_SIGNALS);
    }

    // Re-render
    renderSignals();

    // Update stats
    fetchSummary();
}

function renderSignals() {
    const container = document.getElementById('flow-feed');
    if (!container) return;

    // Apply filters
    let filtered = state.signals;

    if (state.filters.symbol) {
        filtered = filtered.filter(s => s.symbol.toUpperCase() === state.filters.symbol.toUpperCase());
    }
    if (state.filters.direction) {
        filtered = filtered.filter(s => s.direction === state.filters.direction);
    }
    if (state.filters.signalType) {
        filtered = filtered.filter(s => s.signal_type === state.filters.signalType);
    }
    if (state.filters.minPremium > 0) {
        filtered = filtered.filter(s => s.metrics.premium >= state.filters.minPremium);
    }

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <h3 class="empty-title">No Flow Signals</h3>
                <p class="empty-text">
                    Waiting for institutional flow activity...
                    Signals will appear here in real-time.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map((signal, index) => createFlowCard(signal, index === 0)).join('');
}

function createFlowCard(signal, isNew = false) {
    const direction = signal.direction.toLowerCase();
    const signalType = formatSignalType(signal.signal_type);
    const signalTypeClass = signal.signal_type.toLowerCase().replace('_', '-');

    const convictionClass = signal.conviction_level.toLowerCase();
    const positioningClass = signal.positioning.toLowerCase();

    return `
        <div class="flow-card ${direction} ${isNew ? 'new' : ''}" data-signal-id="${signal.signal_id}">
            <!-- Header -->
            <div class="flow-card-header">
                <div>
                    <span class="flow-type-badge ${signalTypeClass}">${signalType}</span>
                    <div class="flow-symbol">${signal.symbol}</div>
                    <div class="flow-target">
                        <span class="target-arrow">→</span>
                        <span class="target-price">$${signal.price_target.toFixed(0)}</span>
                        <span class="target-label">Target</span>
                        <span class="target-date">by ${formatDate(signal.target_date)}</span>
                    </div>
                </div>
                <div class="flow-direction-badge ${direction}">
                    ${direction === 'bullish' ? '📈' : direction === 'bearish' ? '📉' : '➡️'} ${signal.direction}
                </div>
            </div>

            <!-- Subtitle -->
            <div class="flow-card-subtitle">
                ${signal.subtitle}
            </div>

            <!-- Body: Positioning & Technicals -->
            <div class="flow-card-body">
                <div class="info-box">
                    <div class="info-box-label">Positioning</div>
                    <div class="info-box-value ${positioningClass}">${signal.positioning}</div>
                </div>
                <div class="info-box">
                    <div class="info-box-label">Levels / Technicals</div>
                    <div class="levels-display">
                        <div class="level-item">
                            <span class="level-price floor">$${signal.technical_levels.floor.toFixed(0)}</span>
                            <span class="level-label">Floor</span>
                        </div>
                        <span style="color: var(--text-muted);">•</span>
                        <div class="level-item">
                            <span class="level-price resistance">$${signal.technical_levels.resistance.toFixed(0)}</span>
                            <span class="level-label">Major Resistance</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Details -->
            ${signal.positioning_details ? `
            <div class="flow-card-details">
                <div class="details-row">
                    <span class="details-icon">+</span>
                    <span>${signal.positioning_details}</span>
                </div>
            </div>
            ` : ''}

            <!-- Metrics -->
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value ${signal.metrics.volume_ratio >= 3 ? 'highlight' : ''}">${formatPremium(signal.metrics.premium)}</div>
                    <div class="metric-label">Premium</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${formatNumber(signal.metrics.contracts)}</div>
                    <div class="metric-label">Contracts</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value ${signal.metrics.volume_ratio >= 3 ? 'highlight' : ''}">${signal.metrics.volume_ratio.toFixed(1)}x</div>
                    <div class="metric-label">Vol Ratio</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${signal.conviction_score.toFixed(0)}%</div>
                    <div class="metric-label">Conviction</div>
                </div>
            </div>

            <!-- Conviction Bar -->
            <div class="conviction-bar-container">
                <div class="conviction-bar">
                    <div class="conviction-fill ${convictionClass}" style="width: ${signal.conviction_score}%"></div>
                </div>
            </div>

            <!-- Footer -->
            <div class="flow-card-footer">
                ${signal.option ? `
                <span style="color: var(--text-secondary);">
                    ${signal.option.type} $${signal.option.strike} • ${signal.option.dte} DTE
                </span>
                ` : '<span></span>'}
                <span class="flow-timestamp">${formatTime(signal.timestamp)}</span>
            </div>
        </div>
    `;
}


// ═══════════════════════════════════════════════════════════════════════════
// Formatting Utilities
// ═══════════════════════════════════════════════════════════════════════════

function formatPremium(value) {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
}

function formatNumber(value) {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return value.toString();
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function formatSignalType(type) {
    const types = {
        'INSTITUTIONAL_FLOW': 'Institutional Flow',
        'SWEEP': 'Sweep',
        'BLOCK': 'Block Trade',
        'DARK_POOL': 'Dark Pool',
        'UNUSUAL_VOLUME': 'Unusual Volume',
        'UNUSUAL_OI': 'Unusual OI',
        'GOLDEN_SWEEP': 'Golden Sweep',
    };
    return types[type] || type;
}


// ═══════════════════════════════════════════════════════════════════════════
// Filters
// ═══════════════════════════════════════════════════════════════════════════

function applyFilters() {
    state.filters.symbol = document.getElementById('filter-symbol')?.value || '';
    state.filters.direction = document.getElementById('filter-direction')?.value || '';
    state.filters.signalType = document.getElementById('filter-type')?.value || '';
    state.filters.minPremium = parseFloat(document.getElementById('filter-premium')?.value || 0);

    fetchSignals();
}

function resetFilters() {
    state.filters = { symbol: '', direction: '', signalType: '', minPremium: 0 };

    const els = ['filter-symbol', 'filter-direction', 'filter-type', 'filter-premium'];
    els.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = el.tagName === 'SELECT' ? '' : '0';
    });

    renderSignals();
}


// ═══════════════════════════════════════════════════════════════════════════
// Polling Fallback
// ═══════════════════════════════════════════════════════════════════════════

function startPolling() {
    if (state.refreshTimer) clearInterval(state.refreshTimer);

    state.refreshTimer = setInterval(() => {
        fetchSignals();
        fetchSummary();
    }, CONFIG.REFRESH_INTERVAL);
}

function stopPolling() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════════════════════

async function initDashboard() {
    console.log('Initializing Institutional Flow Tracker...');

    // Set up event listeners
    document.getElementById('btn-apply-filters')?.addEventListener('click', applyFilters);
    document.getElementById('btn-reset-filters')?.addEventListener('click', resetFilters);
    document.getElementById('btn-refresh')?.addEventListener('click', () => {
        fetchSignals();
        fetchSummary();
    });

    // Enter key applies filters
    document.querySelectorAll('.filter-input, .filter-select').forEach(el => {
        el.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') applyFilters();
        });
    });

    // Initial data load
    await fetchStatus();
    await fetchSignals();
    await fetchSummary();

    // Connect WebSocket
    connectWebSocket();

    // Start polling as fallback
    startPolling();

    console.log('Dashboard initialized');
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initDashboard);

// Pause/resume on visibility change
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        fetchSignals();
        fetchSummary();
        startPolling();
    }
});
