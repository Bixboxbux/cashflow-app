/**
 * SiteAuditPro - Frontend Application
 * Gestion de l'audit de site web
 */

// Configuration
const API_URL = 'http://localhost:5000/api';
let currentReport = null;

// DOM Elements
const auditForm = document.getElementById('auditForm');
const urlInput = document.getElementById('urlInput');
const submitBtn = document.getElementById('submitBtn');
const loadingState = document.getElementById('loadingState');
const resultsSection = document.getElementById('resultsSection');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
auditForm.addEventListener('submit', handleAuditSubmit);

// Tab Navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`tab-${tab}`).classList.add('active');
    });
});

/**
 * Gère la soumission du formulaire d'audit
 */
async function handleAuditSubmit(e) {
    e.preventDefault();

    const url = urlInput.value.trim();
    if (!url) return;

    // Reset states
    hideError();
    hideResults();
    showLoading();

    // Animate loading steps
    animateLoadingSteps();

    try {
        const response = await fetch(`${API_URL}/audit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erreur lors de l\'analyse');
        }

        // Store report
        currentReport = data;

        // Wait for animation to complete
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Display results
        hideLoading();
        displayResults(data);

    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

/**
 * Anime les étapes de chargement
 */
function animateLoadingSteps() {
    const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
    let currentStep = 0;

    const interval = setInterval(() => {
        if (currentStep > 0) {
            document.getElementById(steps[currentStep - 1]).classList.remove('active');
            document.getElementById(steps[currentStep - 1]).classList.add('done');
        }

        if (currentStep < steps.length) {
            document.getElementById(steps[currentStep]).classList.add('active');
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 600);
}

/**
 * Affiche les résultats de l'audit
 */
function displayResults(data) {
    // Score principal
    const score = data.global_score;
    const grade = data.grade;

    // Update score circle
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreColor = getScoreColor(score);
    scoreCircle.style.setProperty('--score', score);
    scoreCircle.style.setProperty('--score-color', scoreColor);

    // Animate score counter
    animateCounter('scoreValue', 0, score, 1000);

    // Update grade
    const gradeEl = document.getElementById('scoreGrade');
    gradeEl.textContent = grade;
    gradeEl.className = 'score-grade grade-' + grade.charAt(0);

    // Summary text
    document.getElementById('scoreSummary').textContent = getScoreSummary(score);
    document.getElementById('scoreDescription').textContent = getScoreDescription(score);
    document.getElementById('analyzedUrl').textContent = data.final_url;

    // Category scores
    displayCategoryScores(data.analyses);

    // Priority recommendations (free - limit to 3)
    displayFreeRecommendations(data.priority_recommendations);

    // Total issues count
    document.getElementById('totalIssues').textContent = data.priority_recommendations.length;

    // Detailed analysis by category
    displayDetailedAnalysis(data.analyses);

    // Show results section
    showResults();
}

/**
 * Affiche les scores par catégorie
 */
function displayCategoryScores(analyses) {
    const container = document.getElementById('categoryScores');
    container.innerHTML = '';

    const categories = {
        seo: { name: 'SEO', icon: '🔍' },
        performance: { name: 'Performance', icon: '⚡' },
        conversion: { name: 'Conversion', icon: '🎯' },
        mobile: { name: 'Mobile', icon: '📱' },
        security: { name: 'Sécurité', icon: '🔒' }
    };

    for (const [key, info] of Object.entries(categories)) {
        const analysis = analyses[key];
        const percent = Math.round((analysis.score / analysis.max_score) * 100);
        const color = getScoreColor(percent);

        const card = document.createElement('div');
        card.className = 'category-card';
        card.innerHTML = `
            <div class="category-header">
                <span class="category-name">${info.icon} ${info.name}</span>
                <span class="category-score" style="color: ${color}">${percent}%</span>
            </div>
            <div class="score-bar">
                <div class="score-bar-fill" style="width: ${percent}%; background: ${color}"></div>
            </div>
        `;
        container.appendChild(card);
    }
}

/**
 * Affiche les recommandations gratuites (limitées)
 */
function displayFreeRecommendations(recommendations) {
    const container = document.getElementById('freeRecommendations');
    container.innerHTML = '';

    // Limit to 3 for free version
    const freeRecs = recommendations.slice(0, 3);

    freeRecs.forEach(rec => {
        const item = createIssueItem(rec);
        container.appendChild(item);
    });

    if (recommendations.length > 3) {
        const moreCount = recommendations.length - 3;
        const moreDiv = document.createElement('div');
        moreDiv.style.cssText = 'text-align: center; padding: 1rem; color: var(--gray-500); font-style: italic;';
        moreDiv.innerHTML = `+ ${moreCount} autres recommandations disponibles dans la version Pro`;
        container.appendChild(moreDiv);
    }
}

/**
 * Affiche l'analyse détaillée par catégorie
 */
function displayDetailedAnalysis(analyses) {
    for (const [category, data] of Object.entries(analyses)) {
        // Successes
        const successContainer = document.getElementById(`${category}-successes`);
        if (successContainer) {
            successContainer.innerHTML = '';
            data.successes.forEach(success => {
                const item = document.createElement('div');
                item.className = 'success-item';
                item.innerHTML = `
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    ${success}
                `;
                successContainer.appendChild(item);
            });
        }

        // Issues
        const issueContainer = document.getElementById(`${category}-issues`);
        if (issueContainer) {
            issueContainer.innerHTML = '';
            data.issues.forEach(issue => {
                const item = createIssueItem({ ...issue, category });
                issueContainer.appendChild(item);
            });
        }
    }
}

/**
 * Crée un élément d'issue/recommandation
 */
function createIssueItem(issue) {
    const item = document.createElement('div');
    item.className = 'issue-item';

    const badgeClass = {
        critical: 'badge-critical',
        warning: 'badge-warning',
        info: 'badge-info'
    }[issue.type] || 'badge-info';

    const badgeText = {
        critical: 'Critique',
        warning: 'Important',
        info: 'Info'
    }[issue.type] || 'Info';

    const categoryNames = {
        seo: 'SEO',
        performance: 'Performance',
        conversion: 'Conversion',
        mobile: 'Mobile',
        security: 'Sécurité'
    };

    item.innerHTML = `
        <div class="issue-header">
            <span class="issue-badge ${badgeClass}">${badgeText}</span>
            <div class="issue-content">
                <p class="issue-message">${issue.message}</p>
                <p class="issue-recommendation">${issue.recommendation}</p>
                ${issue.category ? `<p class="issue-category">${categoryNames[issue.category] || issue.category}</p>` : ''}
            </div>
        </div>
    `;

    return item;
}

/**
 * Génère un rapport texte
 */
function generateTextReport() {
    if (!currentReport) return '';

    const data = currentReport;
    let report = '';

    report += '═══════════════════════════════════════════════════════════\n';
    report += '                    RAPPORT D\'AUDIT SEO & CONVERSION\n';
    report += '                         SiteAuditPro.com\n';
    report += '═══════════════════════════════════════════════════════════\n\n';

    report += `URL analysée: ${data.final_url}\n`;
    report += `Date: ${data.analyzed_at}\n`;
    report += `Temps de chargement: ${data.load_time}s\n\n`;

    report += '───────────────────────────────────────────────────────────\n';
    report += '                         SCORE GLOBAL\n';
    report += '───────────────────────────────────────────────────────────\n\n';

    report += `  Score: ${data.global_score}/100 (${data.grade})\n`;
    report += `  ${getScoreSummary(data.global_score)}\n\n`;

    report += '───────────────────────────────────────────────────────────\n';
    report += '                      SCORES PAR CATÉGORIE\n';
    report += '───────────────────────────────────────────────────────────\n\n';

    const categories = {
        seo: 'SEO',
        performance: 'Performance',
        conversion: 'Conversion',
        mobile: 'Mobile',
        security: 'Sécurité'
    };

    for (const [key, name] of Object.entries(categories)) {
        const analysis = data.analyses[key];
        const percent = Math.round((analysis.score / analysis.max_score) * 100);
        const bar = '█'.repeat(Math.floor(percent / 5)) + '░'.repeat(20 - Math.floor(percent / 5));
        report += `  ${name.padEnd(12)} ${bar} ${percent}%\n`;
    }

    report += '\n───────────────────────────────────────────────────────────\n';
    report += '                 RECOMMANDATIONS PRIORITAIRES\n';
    report += '───────────────────────────────────────────────────────────\n\n';

    data.priority_recommendations.slice(0, 3).forEach((rec, i) => {
        const priority = rec.type === 'critical' ? '🔴' : rec.type === 'warning' ? '🟡' : '🔵';
        report += `${i + 1}. ${priority} ${rec.message}\n`;
        report += `   → ${rec.recommendation}\n\n`;
    });

    report += '\n═══════════════════════════════════════════════════════════\n';
    report += '  Pour le rapport complet, passez à la version Pro sur\n';
    report += '                    SiteAuditPro.com\n';
    report += '═══════════════════════════════════════════════════════════\n';

    return report;
}

/**
 * Copie le rapport dans le presse-papiers
 */
function copyReport() {
    const report = generateTextReport();

    navigator.clipboard.writeText(report).then(() => {
        // Show success feedback
        const btn = event.target.closest('button');
        const originalText = btn.innerHTML;
        btn.innerHTML = `
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Copié !
        `;
        btn.style.background = 'var(--success)';
        btn.style.color = 'white';
        btn.style.borderColor = 'var(--success)';

        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.background = '';
            btn.style.color = '';
            btn.style.borderColor = '';
        }, 2000);
    }).catch(err => {
        alert('Impossible de copier le rapport');
    });
}

/**
 * Lance un nouvel audit
 */
function newAudit() {
    urlInput.value = '';
    hideResults();
    hideError();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    urlInput.focus();
}

/**
 * Cache le paywall
 */
function hidePaywall() {
    document.getElementById('paywallSection').style.display = 'none';
}

/**
 * Affiche la modal des prix
 */
function showPricingModal() {
    document.getElementById('pricingModal').style.display = 'flex';
}

/**
 * Ferme la modal des prix
 */
function closePricingModal() {
    document.getElementById('pricingModal').style.display = 'none';
}

// Utility Functions

function showLoading() {
    loadingState.classList.add('active');
    submitBtn.disabled = true;

    // Reset loading steps
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`step${i}`);
        step.classList.remove('active', 'done');
    }
}

function hideLoading() {
    loadingState.classList.remove('active');
    submitBtn.disabled = false;
}

function showResults() {
    resultsSection.classList.add('active');

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function hideResults() {
    resultsSection.classList.remove('active');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('active');
}

function hideError() {
    errorMessage.classList.remove('active');
}

function getScoreColor(score) {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--warning)';
    return 'var(--danger)';
}

function getScoreSummary(score) {
    if (score >= 90) return 'Excellent ! Votre site est très bien optimisé.';
    if (score >= 80) return 'Très bien ! Quelques optimisations possibles.';
    if (score >= 70) return 'Bien, mais des améliorations recommandées.';
    if (score >= 60) return 'Moyen. Plusieurs points à améliorer.';
    if (score >= 50) return 'Insuffisant. Optimisation urgente recommandée.';
    return 'Critique. Votre site nécessite une refonte.';
}

function getScoreDescription(score) {
    if (score >= 80) return 'Continuez ainsi et surveillez régulièrement vos performances.';
    if (score >= 60) return 'Appliquez les recommandations ci-dessous pour améliorer vos conversions.';
    return 'Priorisez les problèmes critiques pour améliorer rapidement votre site.';
}

function animateCounter(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    const range = end - start;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function
        const easeOut = 1 - Math.pow(1 - progress, 3);

        const current = Math.round(start + range * easeOut);
        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Close modal on outside click
document.getElementById('pricingModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
        closePricingModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePricingModal();
    }
});

// Demo mode - if API is not available
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_URL}/health`, { method: 'GET' });
        return response.ok;
    } catch {
        return false;
    }
}

// Initialize
console.log('SiteAuditPro initialized');
