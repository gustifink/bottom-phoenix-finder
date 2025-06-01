// API Configuration - Use relative URLs for production
const API_URL = '/api';
const API_BASE_URL = '';
const WS_URL = location.protocol === 'https:' ? 'wss://' + location.host + '/ws/updates' : 'ws://' + location.host + '/ws/updates';

// State Management
let phoenixTokens = [];
let recentAlerts = [];
let selectedToken = null;
let ws = null;
let autoRefreshInterval = null;

// DOM Elements
const phoenixTbody = document.getElementById('phoenix-tbody');
const loadingDiv = document.getElementById('loading');
const alertsContainer = document.getElementById('alerts-container');
const modal = document.getElementById('tokenDetailsModal');
const modalClose = document.querySelector('.close-modal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Bottom dashboard initialized');
    
    // Initialize Feather icons
    feather.replace();
    
    // Load initial data
    loadTopPhoenixes();
    loadRecentAlerts();
    
    // Set up WebSocket connection
    connectWebSocket();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up auto-refresh
    autoRefreshInterval = setInterval(() => {
        loadTopPhoenixes();
        loadRecentAlerts();
    }, 60000); // Refresh every minute
    
    // Update stats
    updateStats();
});

// Event Listeners
function setupEventListeners() {
    // Filters
    document.getElementById('score-filter').addEventListener('change', loadTopPhoenixes);
    document.getElementById('marketcap-filter').addEventListener('change', loadTopPhoenixes);
    document.getElementById('volume-filter').addEventListener('change', loadTopPhoenixes);
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const refreshBtn = document.getElementById('refresh-btn');
        const originalHTML = refreshBtn.innerHTML;
        
        // Show loading state
        refreshBtn.innerHTML = '<i data-feather="loader"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        // Load data
        Promise.all([
            loadTopPhoenixes(),
            loadRecentAlerts()
        ]).finally(() => {
            // Restore button state
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
            feather.replace(); // Re-initialize icons
        });
    });
    
    // Modal close - use event delegation
    document.addEventListener('click', (e) => {
        if (e.target.matches('.close-modal') || e.target === modal) {
            closeModal();
        }
    });
}

// Load Phoenix Tokens
async function loadTopPhoenixes() {
    try {
        showLoading();
        
        // Get filter values
        const minScore = document.getElementById('score-filter').value;
        const minMarketCap = document.getElementById('marketcap-filter').value;
        const minVolume = document.getElementById('volume-filter').value;
        
        // Build query params
        const params = new URLSearchParams({
            limit: 20,
            min_score: minScore,
            min_liquidity: 5000,  // Keep a minimum liquidity
            chain: 'solana'  // Always Solana
        });
        
        const response = await fetch(`${API_URL}/top-phoenixes?${params}`);
        if (!response.ok) throw new Error('Failed to load tokens');
        
        let tokens = await response.json();
        
        // Client-side filtering for market cap and volume
        tokens = tokens.filter(token => {
            const marketCap = token.market_cap || 0;
            const volume = token.volume_24h || 0;
            return marketCap >= parseFloat(minMarketCap) && volume >= parseFloat(minVolume);
        });
        
        phoenixTokens = tokens;
        renderPhoenixTable();
        updateStats();
        
    } catch (error) {
        console.error('Error loading phoenix tokens:', error);
        showError('Failed to load phoenix tokens. Make sure the backend is running.');
    } finally {
        hideLoading();
    }
}

// Render Phoenix Table
function renderPhoenixTable() {
    phoenixTbody.innerHTML = '';
    
    if (phoenixTokens.length === 0) {
        phoenixTbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px;">
                    No Solana phoenix tokens found matching your criteria.
                    <br>Try adjusting the filters or wait for the next scan.
                </td>
            </tr>
        `;
        // Hide featured card if no tokens
        document.getElementById('featured-phoenix').style.display = 'none';
        return;
    }
    
    // Find the best phoenix token (highest BRS score > 70)
    const featuredToken = phoenixTokens.find(token => token.brs_score >= 70) || 
                         phoenixTokens[0]; // Or just the first one if none qualify
    
    // Show featured card for high-scoring tokens
    if (featuredToken && featuredToken.brs_score >= 60) {
        showFeaturedPhoenix(featuredToken);
    } else {
        document.getElementById('featured-phoenix').style.display = 'none';
    }
    
    phoenixTokens.forEach(token => {
        const volumeToMcRatio = token.market_cap > 0 ? (token.volume_24h / token.market_cap * 100).toFixed(0) : 0;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="token-info">
                    <strong>${token.symbol}</strong>
                    <span class="token-name">${token.name || ''}</span>
                </div>
            </td>
            <td>
                <span class="brs-score">${token.brs_score.toFixed(1)}</span>
                <div class="score-category">${token.category}</div>
            </td>
            <td>
                <div>$${formatPrice(token.current_price)}</div>
                <div class="price-change ${token.price_change_24h >= 0 ? 'positive' : 'negative'}">
                    ${token.price_change_24h >= 0 ? '+' : ''}${token.price_change_24h.toFixed(1)}%
                </div>
            </td>
            <td>$${formatNumber(token.market_cap)}</td>
            <td>
                <div>$${formatNumber(token.volume_24h)}</div>
                ${volumeToMcRatio > 100 ? 
                    `<div class="volume-ratio-high">${volumeToMcRatio}% of MC</div>` : 
                    `<div class="volume-ratio">${volumeToMcRatio}% of MC</div>`
                }
            </td>
            <td>$${formatNumber(token.liquidity_usd)}</td>
            <td>
                <div class="actions">
                    <button class="btn-small" onclick="showTokenDetails('${token.address}')">Analysis</button>
                    <a href="https://dexscreener.com/solana/${token.address}" target="_blank" class="btn-small btn-outline">
                        Chart
                    </a>
                </div>
            </td>
        `;
        phoenixTbody.appendChild(row);
    });
}

function showFeaturedPhoenix(token) {
    const container = document.getElementById('featured-phoenix');
    const card = container.querySelector('.featured-card');
    
    // Calculate key metrics
    const volumeToMcRatio = token.market_cap > 0 ? (token.volume_24h / token.market_cap * 100).toFixed(0) : 0;
    const liqRatio = token.market_cap > 0 ? (token.liquidity_usd / token.market_cap * 100).toFixed(0) : 0;
    
    // Determine score interpretation
    let scoreInterpretation = '';
    if (token.brs_score >= 80) {
        scoreInterpretation = '🚀 Phoenix Rising - Strong buy signal!';
    } else if (token.brs_score >= 70) {
        scoreInterpretation = '🔥 Showing Life - Accumulation recommended';
    } else {
        scoreInterpretation = '👀 Potential Phoenix - Monitor closely';
    }
    
    card.innerHTML = `
        <div class="featured-header">
            <div class="featured-token-info">
                <h3>${token.symbol}</h3>
                <p class="featured-name">${token.name || 'Unknown'}</p>
                <div class="featured-score">
                    <span class="brs-score-large">${token.brs_score.toFixed(1)}</span>
                    <span class="score-label">BRS Score</span>
                </div>
            </div>
            <div class="featured-interpretation">
                <p>${scoreInterpretation}</p>
                <p class="featured-description">${token.description}</p>
            </div>
        </div>
        
        <div class="featured-metrics">
            <div class="metric-card">
                <span class="metric-label">Current Price</span>
                <span class="metric-value">$${formatPrice(token.current_price)}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Market Cap</span>
                <span class="metric-value">$${formatNumber(token.market_cap)}</span>
                ${token.fdv && token.fdv !== token.market_cap ? `<span class="metric-sub">FDV: $${formatNumber(token.fdv)}</span>` : ''}
            </div>
            <div class="metric-card">
                <span class="metric-label">24h Volume</span>
                <span class="metric-value">$${formatNumber(token.volume_24h)}</span>
                ${volumeToMcRatio > 100 ? `<span class="metric-highlight">${volumeToMcRatio}% of MC!</span>` : `<span class="metric-sub">${volumeToMcRatio}% of MC</span>`}
            </div>
            <div class="metric-card">
                <span class="metric-label">Liquidity</span>
                <span class="metric-value">$${formatNumber(token.liquidity_usd)}</span>
                <span class="metric-sub">${liqRatio}% of MC</span>
            </div>
        </div>
        
        <div class="featured-indicators">
            <div class="indicator-item ${token.crash_percentage >= 70 ? 'highlight' : ''}">
                <span class="indicator-icon">📉</span>
                <span>Crashed ${formatPercentage(token.crash_percentage)} from ATH</span>
            </div>
            <div class="indicator-item ${token.buy_sell_ratio > 1.2 ? 'highlight' : ''}">
                <span class="indicator-icon">💪</span>
                <span>Buy/Sell Ratio: ${token.buy_sell_ratio.toFixed(2)}</span>
            </div>
            <div class="indicator-item ${volumeToMcRatio > 500 ? 'highlight' : ''}">
                <span class="indicator-icon">📊</span>
                <span>Volume ${volumeToMcRatio}% of Market Cap</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-icon">📅</span>
                <span>Token Age: ${token.token_age_days || 0} days</span>
            </div>
        </div>
        
        <div class="featured-actions">
            <button class="btn-primary" onclick="showTokenDetails('${token.address}')">
                View Full Analysis
            </button>
            <a href="https://dexscreener.com/solana/${token.address}" target="_blank" class="btn-secondary">
                Open Dexscreener
            </a>
        </div>
    `;
    
    container.style.display = 'block';
}

// Load Recent Alerts
async function loadRecentAlerts() {
    try {
        const response = await fetch(`${API_URL}/alerts/recent?limit=5`);
        if (!response.ok) throw new Error('Failed to load alerts');
        
        recentAlerts = await response.json();
        renderAlerts();
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Render Alerts
function renderAlerts() {
    alertsContainer.innerHTML = '';
    
    if (recentAlerts.length === 0) {
        alertsContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                No recent alerts. Phoenixes will appear here when found.
            </div>
        `;
        return;
    }
    
    recentAlerts.forEach(alert => {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert-item';
        alertDiv.innerHTML = `
            <div class="alert-content">
                <div class="alert-title">${alert.message}</div>
                <div class="alert-time">${formatTime(alert.timestamp)}</div>
            </div>
            <button class="action-btn view-alert" data-address="${alert.token_address}">View</button>
        `;
        
        // Add click event listener
        alertDiv.querySelector('.view-alert').addEventListener('click', () => {
            showTokenDetails(alert.token_address);
        });
        
        alertsContainer.appendChild(alertDiv);
    });
}

// Show Token Details
async function showTokenDetails(address) {
    // Show loading state
    document.getElementById('modalContent').innerHTML = '<div class="loading">Loading detailed analysis...</div>';
    document.getElementById('tokenDetailsModal').classList.add('active');
    
    try {
        const response = await fetch(`${API_URL}/token/${address}/analysis`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const analysis = await response.json();
        
        const modalContent = document.getElementById('modalContent');
        modalContent.innerHTML = `
            <div class="analysis-container">
                <div class="analysis-header">
                    <h2>${analysis.token_info.symbol} - Detailed Phoenix Analysis</h2>
                    <p class="token-age">Token Age: ${analysis.token_info.token_age_days} days (Created: ${new Date(analysis.token_info.first_seen).toLocaleDateString()})</p>
                    <a href="${analysis.token_info.dexscreener_url}" target="_blank" class="dex-link">View on Dexscreener →</a>
                </div>
                
                <div class="market-metrics">
                    <h3>Market Metrics</h3>
                    <div class="metrics-grid">
                        <div class="metric">
                            <span class="label">Current Price:</span>
                            <span class="value">$${analysis.market_metrics.current_price.toFixed(8)}</span>
                        </div>
                        <div class="metric">
                            <span class="label">Market Cap:</span>
                            <span class="value">${formatVolume(analysis.market_metrics.market_cap)}</span>
                        </div>
                        <div class="metric">
                            <span class="label">Liquidity:</span>
                            <span class="value">${formatVolume(analysis.market_metrics.liquidity_usd)}</span>
                        </div>
                        <div class="metric">
                            <span class="label">24h Volume:</span>
                            <span class="value">${formatVolume(analysis.market_metrics.volume_24h)}</span>
                        </div>
                        <div class="metric">
                            <span class="label">Liquidity/MCap Ratio:</span>
                            <span class="value">${analysis.market_metrics.liquidity_to_mcap_ratio.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="volume-chart-section">
                    <h3>30-Day Volume History</h3>
                    <div class="chart-container">
                        <canvas id="volumeChart"></canvas>
                    </div>
                </div>
                
                <div class="large-transactions">
                    <h4>Large Buy Transactions (>$3,000)</h4>
                    ${analysis.large_transactions.total_count > 0 ? `
                        <div class="transaction-summary">
                            <p>Total: ${analysis.large_transactions.total_count} large buys</p>
                            <p>Total Volume: $${formatNumber(analysis.large_transactions.total_volume)}</p>
                            <p class="disclaimer">Note: These are simulated transactions for demonstration purposes. In production, real transaction data would be shown from the blockchain.</p>
                        </div>
                        <div class="transaction-list">
                            ${analysis.large_transactions.transactions.slice(0, 10).map(tx => `
                                <div class="transaction-item">
                                    <div class="tx-info">
                                        <span class="tx-type ${tx.type}">${tx.type.toUpperCase()}</span>
                                        <span class="tx-amount">$${formatNumber(tx.usd_amount)}</span>
                                        <span class="tx-tokens">${formatNumber(tx.token_amount)} tokens</span>
                                    </div>
                                    <div class="tx-details">
                                        <span class="tx-wallet">${tx.wallet}</span>
                                        <span class="tx-time">${new Date(tx.timestamp).toLocaleString()}</span>
                                        <a href="https://solscan.io/tx/${generateTxHash()}" target="_blank" class="tx-link">View on Solscan</a>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p>No large transactions found in the last 30 days.</p>'}
                </div>
                
                <div class="phoenix-indicators">
                    <h3>Phoenix Indicators</h3>
                    <div class="indicators-grid">
                        <div class="indicator">
                            <span class="label">Crash from ATH:</span>
                            <span class="value crash">${analysis.phoenix_indicators.crash_from_ath.toFixed(1)}%</span>
                        </div>
                        <div class="indicator">
                            <span class="label">24h Change:</span>
                            <span class="value ${analysis.phoenix_indicators.price_change_24h >= 0 ? 'positive' : 'negative'}">
                                ${analysis.phoenix_indicators.price_change_24h >= 0 ? '+' : ''}${analysis.phoenix_indicators.price_change_24h.toFixed(1)}%
                            </span>
                        </div>
                        <div class="indicator">
                            <span class="label">6h Change:</span>
                            <span class="value ${analysis.phoenix_indicators.price_change_6h >= 0 ? 'positive' : 'negative'}">
                                ${analysis.phoenix_indicators.price_change_6h >= 0 ? '+' : ''}${analysis.phoenix_indicators.price_change_6h.toFixed(1)}%
                            </span>
                        </div>
                        <div class="indicator">
                            <span class="label">1h Change:</span>
                            <span class="value ${analysis.phoenix_indicators.price_change_1h >= 0 ? 'positive' : 'negative'}">
                                ${analysis.phoenix_indicators.price_change_1h >= 0 ? '+' : ''}${analysis.phoenix_indicators.price_change_1h.toFixed(1)}%
                            </span>
                        </div>
                        <div class="indicator">
                            <span class="label">Buy/Sell Ratio:</span>
                            <span class="value ${analysis.phoenix_indicators.buy_sell_ratio >= 1 ? 'positive' : 'negative'}">
                                ${analysis.phoenix_indicators.buy_sell_ratio.toFixed(2)}
                            </span>
                        </div>
                        <div class="indicator">
                            <span class="label">24h Buys/Sells:</span>
                            <span class="value">${analysis.phoenix_indicators.buys_24h}/${analysis.phoenix_indicators.sells_24h}</span>
                        </div>
                    </div>
                </div>
                
                <div class="brs-analysis">
                    <h3>BRS Analysis - Total Score: ${analysis.brs_analysis.total_score.toFixed(1)}/100</h3>
                    <p class="brs-category">${analysis.brs_analysis.category}: ${analysis.brs_analysis.interpretation}</p>
                    
                    <div class="score-breakdown">
                        ${Object.entries(analysis.brs_analysis.score_breakdown).map(([key, component]) => `
                            <div class="score-component">
                                <div class="component-header">
                                    <h4>${formatComponentName(key)}</h4>
                                    <span class="score">${component.score}/${component.max_score} (${component.percentage.toFixed(0)}%)</span>
                                </div>
                                <div class="score-bar">
                                    <div class="score-fill" style="width: ${component.percentage}%"></div>
                                </div>
                                <p class="explanation">${component.explanation}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="selection-reasons">
                    <h3>Why This Token Was Selected</h3>
                    <ul>
                        ${analysis.selection_reasons.map(reason => `<li>${reason}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="risk-factors">
                    <h3>Risk Factors</h3>
                    <ul>
                        ${analysis.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
        
        // Create the volume chart after DOM is updated
        setTimeout(() => {
            createVolumeChart(analysis.volume_history);
        }, 100);
        
    } catch (error) {
        console.error('Error fetching token analysis:', error);
        document.getElementById('modalContent').innerHTML = `<div class="error">Failed to load token analysis: ${error.message}</div>`;
    }
}

function formatComponentName(key) {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

// Add to Watchlist
async function addToWatchlist(address) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/watchlist/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                token_address: address,
                alert_threshold: 80
            })
        });
        
        if (!response.ok) throw new Error('Failed to add to watchlist');
        
        const result = await response.json();
        showSuccess(result.message);
        
    } catch (error) {
        console.error('Error adding to watchlist:', error);
        showError('Failed to add to watchlist');
    }
}

// WebSocket Connection - Disabled in production, use polling instead
function connectWebSocket() {
    // WebSockets not supported in Vercel serverless
    // Use polling instead for production
    if (location.hostname.includes('vercel.app') || location.hostname !== 'localhost') {
        console.log('Production environment detected - using polling instead of WebSocket');
        return;
    }
    
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'phoenix_update') {
            handlePhoenixUpdate(data.data);
        }
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle Phoenix Update
function handlePhoenixUpdate(tokens) {
    // Update tokens if on the main view
    if (modal.classList.contains('active')) return;
    
    // Filter for our criteria
    const minMarketCap = document.getElementById('marketcap-filter').value;
    const minVolume = document.getElementById('volume-filter').value;
    
    tokens = tokens.filter(token => {
        const marketCap = token.market_cap || 0;
        const volume = token.volume_24h || 0;
        return marketCap >= parseFloat(minMarketCap) && volume >= parseFloat(minVolume);
    });
    
    // Check for new high-scoring tokens
    tokens.forEach(token => {
        if (token.brs_score >= 70) {
            const existing = phoenixTokens.find(t => t.address === token.address);
            if (!existing || existing.brs_score < token.brs_score) {
                showNotification(`🚀 New Phoenix Found: ${token.symbol} (BRS: ${token.brs_score.toFixed(1)})`);
            }
        }
    });
    
    // Merge updates with existing tokens
    tokens.forEach(updatedToken => {
        const index = phoenixTokens.findIndex(t => t.address === updatedToken.address);
        if (index >= 0) {
            phoenixTokens[index] = updatedToken;
        } else {
            phoenixTokens.unshift(updatedToken);
            phoenixTokens = phoenixTokens.slice(0, 20);
        }
    });
    
    renderPhoenixTable();
}

// Notification System
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <p>${message}</p>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Update Stats
function updateStats() {
    document.getElementById('total-tracked').textContent = phoenixTokens.length;
    document.getElementById('phoenixes-found').textContent = phoenixTokens.filter(t => t.brs_score >= 80).length;
    document.getElementById('alerts-sent').textContent = recentAlerts.length;
}

// Utility Functions
function showLoading() {
    loadingDiv.classList.add('active');
    phoenixTbody.style.display = 'none';
}

function hideLoading() {
    loadingDiv.classList.remove('active');
    phoenixTbody.style.display = '';
}

function closeModal() {
    document.getElementById('tokenDetailsModal').classList.remove('active');
}

function showError(message) {
    // Simple error notification - in production use a proper notification library
    console.error(message);
    // You could also show a toast notification here
}

function showSuccess(message) {
    // Simple success notification - in production use a proper notification library
    console.log(message);
    alert(message);
}

function formatChain(chain) {
    const chainMap = {
        'ethereum': 'ETH',
        'bsc': 'BSC',
        'polygon': 'POLY',
        'arbitrum': 'ARB',
        'solana': 'SOL'
    };
    return chainMap[chain] || chain.toUpperCase();
}

function formatPrice(price) {
    if (!price || price === 0) return '0';
    if (price < 0.00001) return price.toExponential(2);
    if (price < 0.01) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    return price.toFixed(2);
}

function formatPercentage(value) {
    if (!value && value !== 0) return '0%';
    // If value is already in percentage form (>= 1), just format it
    if (Math.abs(value) >= 1) {
        return `${value.toFixed(1)}%`;
    }
    // If value is in decimal form (< 1), multiply by 100
    const sign = value > 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(2)}%`;
}

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

function formatVolume(volume) {
    return volume ? `$${volume.toLocaleString()}` : 'N/A';
}

// Create Volume Chart
function createVolumeChart(volumeHistory) {
    const ctx = document.getElementById('volumeChart');
    if (!ctx) return;
    
    const labels = volumeHistory.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    const data = volumeHistory.map(d => d.volume);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '24h Volume ($)',
                data: data,
                backgroundColor: 'rgba(0, 212, 255, 0.6)',
                borderColor: 'rgba(0, 212, 255, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Volume: ' + formatVolume(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        callback: function(value) {
                            return formatVolume(value);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Generate Transaction Hash (for demo)
function generateTxHash() {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let hash = '';
    for (let i = 0; i < 64; i++) {
        hash += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return hash;
}

// Make showTokenDetails available globally
window.showTokenDetails = showTokenDetails; 