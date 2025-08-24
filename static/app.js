// Global state
let currentUser = null;
let authToken = null;
let allTickets = [];
let filteredTickets = [];

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Navigation toggle for mobile
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Authentication functions
async function checkAuthStatus() {
    try {
        // Check if we have a token in session
        const response = await fetch('/api/auth/token', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.token;
            
            // Get user info
            const userResponse = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                },
                credentials: 'include'
            });
            
            if (userResponse.ok) {
                currentUser = await userResponse.json();
                showDashboard();
            } else {
                showLandingPage();
            }
        } else {
            showLandingPage();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLandingPage();
    }
}

function showLandingPage() {
    document.getElementById('landingPage').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('navMenu').style.display = 'flex';
    document.getElementById('userMenu').style.display = 'none';
}

function showDashboard() {
    document.getElementById('landingPage').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('navMenu').style.display = 'none';
    document.getElementById('userMenu').style.display = 'flex';
    
    // Update user info in nav
    document.getElementById('userName').textContent = currentUser.name;
    if (currentUser.picture) {
        document.getElementById('userAvatar').src = currentUser.picture;
    }
    
    // Load dashboard data
    loadDashboardData();
}

function logout() {
    currentUser = null;
    authToken = null;
    window.location.href = '/logout';
}

// Dashboard functions
async function loadDashboardData() {
    try {
        showLoading(true);
        
        // Load tickets and analytics
        await Promise.all([
            loadTickets(),
            loadAnalytics()
        ]);
        
        showLoading(false);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showLoading(false);
        showError('Failed to load dashboard data');
    }
}

async function loadTickets() {
    try {
        const response = await fetch('/api/tickets', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            allTickets = data.tickets;
            filteredTickets = [...allTickets];
            renderTickets();
        } else {
            throw new Error('Failed to load tickets');
        }
    } catch (error) {
        console.error('Error loading tickets:', error);
        showError('Failed to load tickets');
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics/dashboard', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateAnalyticsDisplay(data);
        } else {
            // If analytics endpoint doesn't exist, calculate from tickets
            const analytics = calculateAnalyticsFromTickets(allTickets);
            updateAnalyticsDisplay(analytics);
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        // Fallback to calculating from tickets
        const analytics = calculateAnalyticsFromTickets(allTickets);
        updateAnalyticsDisplay(analytics);
    }
}

function calculateAnalyticsFromTickets(tickets) {
    const totalTickets = tickets.length;
    const pendingTickets = tickets.filter(t => t.status === 'pending' || t.status === 'pending_human_review').length;
    const resolvedTickets = tickets.filter(t => t.status === 'resolved' || t.status === 'auto_resolved').length;
    const highRiskTickets = tickets.filter(t => t.risk_level === 'high').length;
    
    return {
        overview: {
            total_tickets: totalTickets,
            pending_tickets: pendingTickets,
            resolved_tickets: resolvedTickets,
            high_risk_tickets: highRiskTickets
        }
    };
}

function updateAnalyticsDisplay(analytics) {
    document.getElementById('totalTickets').textContent = analytics.overview.total_tickets;
    document.getElementById('pendingTickets').textContent = analytics.overview.pending_tickets;
    document.getElementById('resolvedTickets').textContent = analytics.overview.resolved_tickets;
    document.getElementById('highRiskTickets').textContent = analytics.overview.high_risk_tickets;
}

function renderTickets() {
    const ticketsGrid = document.getElementById('ticketsGrid');
    
    if (filteredTickets.length === 0) {
        ticketsGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox fa-3x" style="color: #cbd5e1; margin-bottom: 1rem;"></i>
                <h3 style="color: #64748b; margin-bottom: 0.5rem;">No tickets found</h3>
                <p style="color: #94a3b8;">Try adjusting your filters or check back later.</p>
            </div>
        `;
        return;
    }
    
    ticketsGrid.innerHTML = filteredTickets.map(ticket => createTicketCard(ticket)).join('');
}

function createTicketCard(ticket) {
    const statusClass = `status-${ticket.status.replace(/ /g, '_')}`;
    const riskClass = `risk-${ticket.risk_level || 'medium'}`;
    
    let aiAnalysisHtml = '';
    if (ticket.ai_proposal) {
        const proposal = ticket.ai_proposal;
        const ethicalScore = proposal.ethical_score || 0;
        const scoreClass = getScoreClass(ethicalScore);
        
        // Format reasoning for better display
        const formattedReasoning = proposal.reasoning 
            ? proposal.reasoning.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '<br><br>')
            : 'AI analysis completed';
        
        aiAnalysisHtml = `
            <div class="ai-analysis">
                <h4><i class="fas fa-robot"></i> AI Analysis</h4>
                <div class="ethical-score">
                    <span>Refund Score:</span>
                    <div class="score-bar">
                        <div class="score-fill ${scoreClass}" style="width: ${ethicalScore}%"></div>
                    </div>
                    <span>${ethicalScore}%</span>
                </div>
                <div class="analysis-details">
                    <div class="proposal-decision">
                        <strong>Decision:</strong> ${proposal.resolution_type}
                        ${proposal.proposed_amount > 0 ? ` - $${proposal.proposed_amount.toFixed(2)}` : ''}
                    </div>
                    <div class="reasoning-text" style="margin-top: 0.75rem; font-size: 0.8rem; line-height: 1.4; color: #64748b;">
                        ${formattedReasoning}
                    </div>
                </div>
            </div>
        `;
    }
    
    
    let actionsHtml = '';
    if (ticket.status === 'pending') {
        actionsHtml = `
            <div class="ticket-actions">
                <button class="btn-small btn-process" onclick="processTicket('${ticket.id}')">
                    <i class="fas fa-brain"></i> Process with AI
                </button>
            </div>
        `;
    } else if (ticket.status === 'pending_human_review' && ticket.ai_proposal) {
        actionsHtml = `
            <div class="ticket-actions">
                <button class="btn-small btn-approve" onclick="approveTicket('${ticket.id}')">
                    <i class="fas fa-check"></i> Approve AI
                </button>
                <button class="btn-small btn-override" onclick="overrideTicket('${ticket.id}')">
                    <i class="fas fa-edit"></i> Override
                </button>
            </div>
        `;
    }
    
    return `
        <div class="ticket-card">
            <div class="ticket-header">
                <div>
                    <div class="ticket-title">${ticket.title}</div>
                    <div class="ticket-meta">
                        <span class="status-badge ${statusClass}">${ticket.status.replace(/_/g, ' ')}</span>
                        <span class="risk-badge ${riskClass}">${ticket.risk_level || 'medium'} risk</span>
                        <span class="value-badge">$${ticket.dispute_value.toFixed(2)}</span>
                    </div>
                </div>
            </div>
            <div class="ticket-description">${ticket.description}</div>
            ${aiAnalysisHtml}
            ${actionsHtml}
            <div style="margin-top: 1rem; font-size: 0.75rem; color: #94a3b8;">
                <i class="fas fa-envelope"></i> ${ticket.customer_email} • 
                <i class="fas fa-clock"></i> ${formatDate(ticket.created_at)}
            </div>
        </div>
    `;
}

function getScoreClass(score) {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-fair';
    return 'score-poor';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Filter tickets
function filterTickets() {
    const statusFilter = document.getElementById('statusFilter').value;
    const riskFilter = document.getElementById('riskFilter').value;
    
    filteredTickets = allTickets.filter(ticket => {
        const statusMatch = statusFilter === 'all' || ticket.status === statusFilter;
        const riskMatch = riskFilter === 'all' || ticket.risk_level === riskFilter;
        return statusMatch && riskMatch;
    });
    
    renderTickets();
}

// Auto-refresh dashboard data
async function refreshDashboard() {
    await loadDashboardData();
    showSuccess('Dashboard refreshed!');
}

// Ticket actions with auto-refresh
async function processTicket(ticketId) {
    try {
        showLoading(true, 'Processing ticket with AI...');
        
        const response = await fetch(`/api/tickets/${ticketId}/process`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess('Ticket processed successfully!');
            // Auto-refresh the dashboard
            await loadDashboardData();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to process ticket');
        }
    } catch (error) {
        console.error('Error processing ticket:', error);
        showError('Failed to process ticket: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function approveTicket(ticketId) {
    try {
        showLoading(true, 'Approving AI decision...');
        
        const response = await fetch(`/api/tickets/${ticketId}/human-decision`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                decision: 'approve',
                comments: 'AI proposal approved by human reviewer'
            })
        });
        
        if (response.ok) {
            showSuccess('AI decision approved successfully!');
            // Auto-refresh the dashboard
            await loadDashboardData();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to approve ticket');
        }
    } catch (error) {
        console.error('Error approving ticket:', error);
        showError('Failed to approve ticket: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function overrideTicket(ticketId) {
    const newResolution = prompt('Enter your override resolution:');
    if (!newResolution) return;
    
    const comments = prompt('Comments (optional):') || '';
    
    try {
        showLoading(true, 'Processing override...');
        
        const response = await fetch(`/api/tickets/${ticketId}/human-decision`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                decision: 'override',
                override_resolution: {
                    type: 'human_override',
                    description: newResolution,
                    amount: 0
                },
                comments: comments
            })
        });
        
        if (response.ok) {
            showSuccess('Ticket override successful!');
            // Auto-refresh the dashboard
            await loadDashboardData();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to override ticket');
        }
    } catch (error) {
        console.error('Error overriding ticket:', error);
        showError('Failed to override ticket: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function processAllTickets() {
    const pendingTickets = allTickets.filter(t => t.status === 'pending');
    
    if (pendingTickets.length === 0) {
        showError('No pending tickets to process');
        return;
    }
    
    if (!confirm(`Process ${pendingTickets.length} pending tickets with AI?`)) {
        return;
    }
    
    try {
        showLoading(true, 'Processing all tickets...');
        
        // Process tickets one by one to avoid overwhelming the server
        for (const ticket of pendingTickets) {
            await fetch(`/api/tickets/${ticket.id}/process`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });
        }
        
        showSuccess(`Successfully processed ${pendingTickets.length} tickets!`);
        // Auto-refresh the dashboard
        await loadDashboardData();
    } catch (error) {
        console.error('Error processing all tickets:', error);
        showError('Failed to process some tickets');
    } finally {
        showLoading(false);
    }
}

// Utility functions
function showLoading(show, message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const messageElement = overlay.querySelector('p');
    
    if (show) {
        messageElement.textContent = message;
        overlay.style.display = 'flex';
    } else {
        overlay.style.display = 'none';
    }
}

function showSuccess(message) {
    // Simple success notification
    const notification = document.createElement('div');
    notification.className = 'notification success';
    notification.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #22c55e;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function showError(message) {
    // Simple error notification
    const notification = document.createElement('div');
    notification.className = 'notification error';
    notification.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}