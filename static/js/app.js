/**
 * WebAudit Pro - Frontend JavaScript
 * Handles website analysis, UI interactions, and report generation
 */

// State management
const state = {
    analysisCount: parseInt(localStorage.getItem('analysisCount') || '0'),
    maxFreeAnalyses: 3,
    currentResults: null,
    isAnalyzing: false
};

// DOM Elements
const elements = {
    urlInput: () => document.getElementById('url-input'),
    analyzeBtn: () => document.getElementById('analyze-btn'),
    resultsSection: () => document.getElementById('results-section'),
    scoreCircle: () => document.getElementById('score-circle'),
    scoreProgress: () => document.getElementById('score-progress'),
    scoreNumber: () => document.getElementById('score-number'),
    scoreGrade: () => document.getElementById('score-grade'),
    scoreItems: () => document.getElementById('score-items'),
    analyzedUrl: () => document.getElementById('analyzed-url'),
    issuesList: () => document.getElementById('issues-list'),
    recommendationsList: () => document.getElementById('recommendations-list'),
    premiumFeatures: () => document.getElementById('premium-features'),
    pricingModal: () => document.getElementById('pricing-modal'),
    contactModal: () => document.getElementById('contact-modal'),
    toast: () => document.getElementById('toast'),
    toastMessage: () => document.getElementById('toast-message')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Add enter key listener to URL input
    elements.urlInput().addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeWebsite();
        }
    });

    // Check remaining free analyses
    updateFreeAnalysesUI();
    
    // Create contact modal if it doesn't exist
    createContactModal();
});

/**
 * Create contact modal for Agency plan
 */
function createContactModal() {
    if (document.getElementById('contact-modal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'contact-modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="closeContactModal()">&times;</button>
            <div class="modal-header">
                <h2>Plan Agence - 99€/mois</h2>
                <p>Contactez notre équipe commerciale pour une démonstration personnalisée</p>
            </div>
            <form onsubmit="handleContactForm(event)">
                <div class="form-group">
                    <label for="contact-name">Nom complet</label>
                    <input type="text" id="contact-name" placeholder="Jean Dupont" required>
                </div>
                <div class="form-group">
                    <label for="contact-email">Email professionnel</label>
                    <input type="email" id="contact-email" placeholder="jean@agence.com" required>
                </div>
                <div class="form-group">
                    <label for="contact-company">Nom de l'agence</label>
                    <input type="text" id="contact-company" placeholder="Mon Agence Digital" required>
                </div>
                <div class="form-group">
                    <label for="contact-clients">Nombre de clients</label>
                    <select id="contact-clients" required>
                        <option value="">Sélectionnez...</option>
                        <option value="1-10">1-10 clients</option>
                        <option value="11-25">11-25 clients</option>
                        <option value="26-50">26-50 clients</option>
                        <option value="50+">Plus de 50 clients</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="contact-message">Message (optionnel)</label>
                    <textarea id="contact-message" rows="3" placeholder="Parlez-nous de vos besoins..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">
                    Demander une démo
                </button>
            </form>
            <div class="modal-footer">
                <p>Ou contactez-nous directement : <a href="mailto:contact@webauditpro.com">contact@webauditpro.com</a></p>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Show contact modal for Agency plan
 */
function contactSales() {
    const modal = document.getElementById('contact-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close contact modal
 */
function closeContactModal() {
    const modal = document.getElementById('contact-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Handle contact form submission
 */
function handleContactForm(event) {
    event.preventDefault();
    
    const name = document.getElementById('contact-name').value;
    const email = document.getElementById('contact-email').value;
    const company = document.getElementById('contact-company').value;
    const clients = document.getElementById('contact-clients').value;
    const message = document.getElementById('contact-message').value;
    
    // In a real app, send this to your backend
    console.log('Agency contact request:', { name, email, company, clients, message });
    
    // Show success message
    showToast('Merci ! Notre équipe vous contactera sous 24h.');
    closeContactModal();
    
    // Reset form
    event.target.reset();
}

/**
 * Update UI to show remaining free analyses
 */
function updateFreeAnalysesUI() {
    const remaining = state.maxFreeAnalyses - state.analysisCount;
    const hint = document.querySelector('.form-hint');
    if (hint && remaining <= state.maxFreeAnalyses) {
        const badge = remaining > 0 ? 'GRATUIT' : 'LIMITE ATTEINTE';
        const badgeClass = remaining > 0 ? '' : 'style="background: var(--warning)"';
        hint.innerHTML = `
            <span class="free-badge" ${badgeClass}>${badge}</span>
            ${remaining} analyse${remaining !== 1 ? 's' : ''} gratuite${remaining !== 1 ? 's' : ''} restante${remaining !== 1 ? 's' : ''}
        `;
    }
}

/**
 * Main analysis function
 */
async function analyzeWebsite() {
    const url = elements.urlInput().value.trim();

    // Validation
    if (!url) {
        showToast('Veuillez entrer une URL');
        elements.urlInput().focus();
        return;
    }

    // Check free tier limit
    if (state.analysisCount >= state.maxFreeAnalyses) {
        showPricingModal();
        showToast('Limite gratuite atteinte. Passez à Pro pour continuer.');
        return;
    }

    // Prevent double submission
    if (state.isAnalyzing) return;
    state.isAnalyzing = true;

    // Update UI
    setLoadingState(true);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.error) {
            showToast(data.error);
            return;
        }

        // Increment analysis count
        state.analysisCount++;
        localStorage.setItem('analysisCount', state.analysisCount.toString());
        updateFreeAnalysesUI();

        // Store results and render
        state.currentResults = data;
        renderResults(data);

    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Erreur lors de l\'analyse. Veuillez réessayer.');
    } finally {
        setLoadingState(false);
        state.isAnalyzing = false;
    }
}

/**
 * Set loading state on analyze button
 */
function setLoadingState(loading) {
    const btn = elements.analyzeBtn();
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');

    if (loading) {
        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-flex';
    } else {
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

/**
 * Render analysis results
 */
function renderResults(data) {
    // Show results section
    elements.resultsSection().style.display = 'block';

    // Scroll to results
    elements.resultsSection().scrollIntoView({ behavior: 'smooth' });

    // Set analyzed URL
    elements.analyzedUrl().textContent = data.url;

    // Animate score
    animateScore(data.global_score, data.grade);

    // Render score breakdown
    renderScoreBreakdown(data.scores);

    // Render issues
    renderIssues(data.details);

    // Render recommendations
    renderRecommendations(data.recommendations);

    // Render premium features
    renderPremiumFeatures(data.recommendations);
}

/**
 * Animate the global score circle
 */
function animateScore(score, grade) {
    const scoreProgress = elements.scoreProgress();
    const scoreNumber = elements.scoreNumber();
    const scoreGrade = elements.scoreGrade();

    // Calculate stroke offset (circumference = 2 * PI * 45 = ~283)
    const circumference = 283;
    const offset = circumference - (score / 100) * circumference;

    // Reset and animate
    scoreProgress.style.strokeDashoffset = circumference;
    scoreProgress.className = 'score-progress';

    // Add grade class for color
    const gradeClass = `grade-${grade.toLowerCase()}`;
    scoreProgress.classList.add(gradeClass);

    // Trigger animation
    setTimeout(() => {
        scoreProgress.style.strokeDashoffset = offset;
    }, 100);

    // Animate number
    animateNumber(scoreNumber, 0, score, 1000);

    // Set grade
    scoreGrade.textContent = `Grade ${grade}`;
    scoreGrade.className = `score-grade ${gradeClass}`;
}

/**
 * Animate a number from start to end
 */
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (end - start) * eased);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Render score breakdown bars
 */
function renderScoreBreakdown(scores) {
    const container = elements.scoreItems();
    const categories = {
        seo: { label: 'SEO', icon: '🔍' },
        conversion: { label: 'Conversion', icon: '🎯' },
        speed: { label: 'Vitesse', icon: '⚡' },
        mobile: { label: 'Mobile', icon: '📱' },
        security: { label: 'Sécurité', icon: '🛡️' }
    };

    container.innerHTML = Object.entries(categories).map(([key, { label }]) => {
        const score = scores[key] || 0;
        const fillClass = score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'average' : 'poor';

        return `
            <div class="score-item">
                <span class="score-item-label">${label}</span>
                <div class="score-item-bar">
                    <div class="score-item-fill ${fillClass}" style="width: 0%;" data-width="${score}%"></div>
                </div>
                <span class="score-item-value">${score}/100</span>
            </div>
        `;
    }).join('');

    // Animate bars
    setTimeout(() => {
        container.querySelectorAll('.score-item-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    }, 200);
}

/**
 * Render detected issues
 */
function renderIssues(details) {
    const container = elements.issuesList();
    const allIssues = [];

    const categoryNames = {
        seo: 'SEO',
        conversion: 'Conversion',
        speed: 'Vitesse',
        mobile: 'Mobile',
        security: 'Sécurité'
    };

    Object.entries(details).forEach(([category, data]) => {
        if (data.issues && data.issues.length > 0) {
            data.issues.forEach(issue => {
                allIssues.push({
                    category: categoryNames[category] || category,
                    text: issue
                });
            });
        }
    });

    if (allIssues.length === 0) {
        container.innerHTML = `
            <div class="issue-item" style="background: #DCFCE7;">
                <span class="issue-icon" style="background: #DCFCE7; color: #15803D;">✓</span>
                <div>
                    <div class="issue-text">Aucun problème critique détecté</div>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = allIssues.slice(0, 6).map(issue => `
        <div class="issue-item">
            <span class="issue-icon">!</span>
            <div>
                <div class="issue-category">${issue.category}</div>
                <div class="issue-text">${issue.text}</div>
            </div>
        </div>
    `).join('');

    // Show "more issues" indicator if needed
    if (allIssues.length > 6) {
        container.innerHTML += `
            <div class="issue-item" style="background: #FEF3C7; cursor: pointer;" onclick="showPricingModal()">
                <span class="issue-icon" style="background: #FEF3C7; color: #B45309;">🔒</span>
                <div>
                    <div class="issue-text">+${allIssues.length - 6} autres problèmes (version Pro)</div>
                </div>
            </div>
        `;
    }
}

/**
 * Render recommendations
 */
function renderRecommendations(recommendations) {
    const container = elements.recommendationsList();
    const freeRecs = recommendations.filter(r => !r.premium);

    if (freeRecs.length === 0) {
        container.innerHTML = `
            <div class="recommendation-item">
                <span class="recommendation-icon">✅</span>
                <div class="recommendation-content">
                    <div class="recommendation-title">Excellent travail !</div>
                    <div class="recommendation-action">Votre site est bien optimisé sur les critères de base.</div>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = freeRecs.map(rec => `
        <div class="recommendation-item priority-${rec.priority}">
            <span class="recommendation-icon">${rec.priority === 'haute' ? '🔴' : rec.priority === 'moyenne' ? '🟡' : '🟢'}</span>
            <div class="recommendation-content">
                <div class="recommendation-title">
                    ${rec.category}
                    <span class="priority-badge ${rec.priority}">${rec.priority}</span>
                </div>
                <div class="recommendation-action">${rec.action}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Render premium features teaser
 */
function renderPremiumFeatures(recommendations) {
    const container = elements.premiumFeatures();
    const premiumRecs = recommendations.filter(r => r.premium);

    container.innerHTML = premiumRecs.map(rec => `
        <div class="premium-feature">
            <span class="premium-feature-icon">🔒</span>
            <span class="premium-feature-text">${rec.issue}</span>
        </div>
    `).join('');
}

/**
 * Export report as text
 */
async function exportReport() {
    if (!state.currentResults) {
        showToast('Aucun résultat à exporter');
        return;
    }

    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ results: state.currentResults })
        });

        const data = await response.json();

        if (data.error) {
            showToast(data.error);
            return;
        }

        // Create and download file
        const blob = new Blob([data.report], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showToast('Rapport téléchargé !');

    } catch (error) {
        console.error('Export error:', error);
        showToast('Erreur lors de l\'export');
    }
}

/**
 * Start a new audit
 */
function newAudit() {
    // Hide results
    elements.resultsSection().style.display = 'none';

    // Clear input
    elements.urlInput().value = '';
    elements.urlInput().focus();

    // Clear results
    state.currentResults = null;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Scroll to audit form
 */
function scrollToAudit() {
    document.getElementById('audit-form').scrollIntoView({ behavior: 'smooth' });
    elements.urlInput().focus();
}

/**
 * Show pricing modal
 */
function showPricingModal() {
    elements.pricingModal().classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close pricing modal
 */
function closePricingModal() {
    elements.pricingModal().classList.remove('active');
    document.body.style.overflow = '';
}

/**
 * Handle payment form submission (simulated)
 */
function handlePayment(event) {
    event.preventDefault();
    const email = event.target.querySelector('input').value;

    // Simulate payment processing
    showToast('Merci ! Vous allez recevoir un email de confirmation.');
    closePricingModal();

    // In a real app, this would redirect to Stripe/payment processor
    console.log('Payment initiated for:', email);
}

/**
 * Show contact sales modal (Agency plan)
 */
function contactSales() {
    elements.contactModal().classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close contact sales modal
 */
function closeContactModal() {
    elements.contactModal().classList.remove('active');
    document.body.style.overflow = '';
}

/**
 * Handle contact form submission (Agency plan)
 */
function handleContactForm(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        agency: formData.get('agency'),
        clients: formData.get('clients'),
        message: formData.get('message') || ''
    };

    // Simulate form submission
    console.log('Contact form submitted:', data);

    // Show success message
    showToast('Demande envoyée ! Notre équipe vous contactera sous 24h.');

    // Close modal
    closeContactModal();

    // Reset form
    event.target.reset();

    // In a real app, this would send data to an API endpoint
    // fetch('/api/contact', { method: 'POST', body: JSON.stringify(data), ... })
}

/**
 * Show toast notification
 */
function showToast(message, duration = 3000) {
    const toast = elements.toast();
    const toastMessage = elements.toastMessage();

    toastMessage.textContent = message;
    toast.classList.add('active');

    setTimeout(() => {
        toast.classList.remove('active');
    }, duration);
}

// Close modals on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePricingModal();
        closeContactModal();
    }
});
