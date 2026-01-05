// CashFlow App - Pure JavaScript
// État de l'application
const state = {
  transactions: [],
  isPro: false,
  savingsGoal: { target: 1000, current: 0 },
  budgets: {},
  currentType: 'expense',
  editingId: null,
  activeTab: 'dashboard'
};

const FREE_LIMIT = 20;

const categories = {
  expense: ['🍔 Alimentation', '🏠 Logement', '🚗 Transport', '🎮 Loisirs', '🛍️ Shopping', '💊 Santé', '📱 Abonnements', '💰 Autre'],
  income: ['💼 Salaire', '🎁 Cadeau', '📈 Investissement', '💵 Autre']
};

// Chargement initial
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  setupEventListeners();
  updateUI();
  updateProStatus();
});

// Setup event listeners
function setupEventListeners() {
  // Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      if (btn.classList.contains('pro-tab') && !state.isPro) {
        showUpgradeModal();
      } else {
        switchTab(tab);
      }
    });
  });

  // Type buttons
  document.getElementById('typeExpense').addEventListener('click', () => setType('expense'));
  document.getElementById('typeIncome').addEventListener('click', () => setType('income'));

  // Form
  document.getElementById('addTransactionBtn').addEventListener('click', () => showForm());
  document.getElementById('closeForm').addEventListener('click', () => hideForm());
  document.getElementById('submitBtn').addEventListener('click', handleSubmit);

  // Modal
  document.getElementById('upgradeBtn')?.addEventListener('click', showUpgradeModal);
  document.getElementById('closeModal').addEventListener('click', hideUpgradeModal);
  document.getElementById('activateProBtn').addEventListener('click', activatePro);
  document.getElementById('upgradeFromAccounts')?.addEventListener('click', showUpgradeModal);
  document.getElementById('upgradeFromBudgets')?.addEventListener('click', showUpgradeModal);
  document.getElementById('upgradeFromReports')?.addEventListener('click', showUpgradeModal);

  // Close insight
  document.getElementById('closeInsight')?.addEventListener('click', () => {
    document.getElementById('aiInsightCard').classList.add('hidden');
  });
}

// Data persistence
function saveData() {
  localStorage.setItem('cashflow-data', JSON.stringify(state));
}

function loadData() {
  const saved = localStorage.getItem('cashflow-data');
  if (saved) {
    Object.assign(state, JSON.parse(saved));
  }
}

// UI Updates
function updateUI() {
  updateStats();
  updateTransactionsList();
  updateSavingsGoal();
  updateTransactionCounter();
  updateCategoryOptions();
}

function updateProStatus() {
  const proBadge = document.getElementById('proBadge');
  const upgradeBtn = document.getElementById('upgradeBtn');
  const accountSelect = document.getElementById('account');
  const categorySelect = document.getElementById('category');
  
  if (state.isPro) {
    proBadge?.classList.remove('hidden');
    upgradeBtn?.classList.add('hidden');
    accountSelect?.classList.remove('hidden');
    
    // Update category placeholder
    if (categorySelect) {
      categorySelect.options[0].text = '🤖 Auto-détection IA';
    }
    
    // Hide PRO badges on tabs
    document.querySelectorAll('.pro-badge').forEach(badge => badge.classList.add('hidden'));
  } else {
    proBadge?.classList.add('hidden');
    upgradeBtn?.classList.remove('hidden');
    accountSelect?.classList.add('hidden');
    
    if (categorySelect) {
      categorySelect.options[0].text = 'Choisir une catégorie';
    }
    
    // Show PRO badges on tabs
    document.querySelectorAll('.pro-badge').forEach(badge => badge.classList.remove('hidden'));
  }
}

function updateStats() {
  const totalIncome = state.transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);
  
  const totalExpense = state.transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);
  
  const balance = totalIncome - totalExpense;

  document.getElementById('totalIncome').textContent = `+${totalIncome.toFixed(2)}€`;
  document.getElementById('totalExpense').textContent = `-${totalExpense.toFixed(2)}€`;
  
  const balanceEl = document.getElementById('totalBalance');
  balanceEl.textContent = `${balance >= 0 ? '+' : ''}${balance.toFixed(2)}€`;
  balanceEl.style.color = balance >= 0 ? '#10b981' : '#ef4444';
}

function updateTransactionsList() {
  const list = document.getElementById('transactionsList');
  
  if (state.transactions.length === 0) {
    list.innerHTML = '<p style="color: rgba(255, 255, 255, 0.5); text-align: center; padding: 2rem;">Aucune transaction pour le moment</p>';
    return;
  }

  list.innerHTML = state.transactions.map(t => `
    <div class="glass" style="border-radius: 0.75rem; padding: 1rem; transition: all 0.3s; cursor: pointer;" onmouseenter="this.style.background='rgba(255,255,255,0.08)'" onmouseleave="this.style.background='rgba(255,255,255,0.05)'">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
            <span style="font-size: 1.125rem;">${t.category.split(' ')[0]}</span>
            <p style="color: white; font-weight: 600;">${t.description}</p>
          </div>
          <p style="color: rgba(255, 255, 255, 0.5); font-size: 0.875rem;">${t.category}</p>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <p class="mono" style="font-size: 1.25rem; font-weight: 900; color: ${t.type === 'income' ? '#10b981' : '#ef4444'};">
            ${t.type === 'income' ? '+' : '-'}${t.amount.toFixed(2)}€
          </p>
          <button onclick="deleteTransaction(${t.id})" style="background: none; padding: 0.5rem; color: #ef4444; opacity: 0.6; transition: opacity 0.3s;" onmouseenter="this.style.opacity='1'" onmouseleave="this.style.opacity='0.6'">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function updateSavingsGoal() {
  const progress = Math.min((state.savingsGoal.current / state.savingsGoal.target) * 100, 100);
  document.getElementById('savingsBar').style.width = `${progress}%`;
  document.getElementById('savingsProgress').textContent = 
    `${state.savingsGoal.current.toFixed(0)}€ / ${state.savingsGoal.target}€`;
  
  const message = state.savingsGoal.current >= state.savingsGoal.target
    ? '🎉 Objectif atteint !'
    : `Plus que ${(state.savingsGoal.target - state.savingsGoal.current).toFixed(2)}€`;
  document.getElementById('savingsMessage').textContent = message;
}

function updateTransactionCounter() {
  if (state.isPro) {
    document.getElementById('transactionCounter').classList.add('hidden');
    return;
  }

  document.getElementById('transactionCounter').classList.remove('hidden');
  const counterText = document.getElementById('counterText');
  const warningText = document.getElementById('warningText');
  
  counterText.textContent = `${state.transactions.length}/${FREE_LIMIT} transactions utilisées`;
  counterText.style.color = state.transactions.length >= FREE_LIMIT ? '#ef4444' : '#c4b5fd';
  
  if (state.transactions.length >= FREE_LIMIT - 5 && state.transactions.length < FREE_LIMIT) {
    warningText.classList.remove('hidden');
  } else {
    warningText.classList.add('hidden');
  }
}

function updateCategoryOptions() {
  const select = document.getElementById('category');
  const options = categories[state.currentType];
  
  select.innerHTML = `<option value="">${state.isPro ? '🤖 Auto-détection IA' : 'Choisir une catégorie'}</option>` +
    options.map(cat => `<option value="${cat}">${cat}</option>`).join('');
}

// Tab switching
function switchTab(tabName) {
  state.activeTab = tabName;
  
  // Update buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabName) {
      btn.style.background = 'linear-gradient(to right, #9333ea, #ec4899)';
      btn.style.color = 'white';
    } else {
      btn.style.background = 'rgba(255, 255, 255, 0.05)';
      btn.style.color = 'rgba(255, 255, 255, 0.6)';
    }
  });
  
  // Show/hide content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.add('hidden');
  });
  document.getElementById(`${tabName}-tab`).classList.remove('hidden');
}

// Form handling
function showForm() {
  document.getElementById('addTransactionBtn').classList.add('hidden');
  document.getElementById('addForm').classList.remove('hidden');
}

function hideForm() {
  document.getElementById('addForm').classList.add('hidden');
  document.getElementById('addTransactionBtn').classList.remove('hidden');
  resetForm();
}

function resetForm() {
  document.getElementById('amount').value = '';
  document.getElementById('description').value = '';
  document.getElementById('category').value = '';
  state.editingId = null;
  document.getElementById('formTitle').textContent = 'Nouvelle transaction';
}

function setType(type) {
  state.currentType = type;
  
  const expenseBtn = document.getElementById('typeExpense');
  const incomeBtn = document.getElementById('typeIncome');
  
  if (type === 'expense') {
    expenseBtn.style.background = '#ef4444';
    expenseBtn.style.color = 'white';
    incomeBtn.style.background = 'rgba(71, 85, 105, 0.5)';
    incomeBtn.style.color = 'rgba(255, 255, 255, 0.6)';
  } else {
    incomeBtn.style.background = '#10b981';
    incomeBtn.style.color = 'white';
    expenseBtn.style.background = 'rgba(71, 85, 105, 0.5)';
    expenseBtn.style.color = 'rgba(255, 255, 255, 0.6)';
  }
  
  updateCategoryOptions();
}

async function handleSubmit() {
  const amount = parseFloat(document.getElementById('amount').value);
  const description = document.getElementById('description').value;
  let category = document.getElementById('category').value;
  const account = state.isPro ? document.getElementById('account').value : 'personal';

  if (!amount || !description) {
    alert('Montant et description requis');
    return;
  }

  // Check limit for free users
  if (!state.isPro && state.transactions.length >= FREE_LIMIT) {
    showUpgradeModal();
    return;
  }

  const submitBtn = document.getElementById('submitBtn');
  submitBtn.disabled = true;
  submitBtn.textContent = '⏳ Ajout en cours...';

  // AI category suggestion for PRO users
  if (state.isPro && !category && state.currentType === 'expense' && description.length > 2) {
    category = await suggestCategory(description);
  }

  const transaction = {
    id: state.editingId || Date.now(),
    amount,
    description,
    category: category || (state.currentType === 'expense' ? '💰 Autre' : '💵 Autre'),
    type: state.currentType,
    account,
    date: new Date().toISOString()
  };

  if (state.editingId) {
    state.transactions = state.transactions.map(t => 
      t.id === state.editingId ? transaction : t
    );
  } else {
    state.transactions.unshift(transaction);
  }

  // Update savings
  if (state.currentType === 'income') {
    state.savingsGoal.current += amount;
  } else {
    state.savingsGoal.current = Math.max(0, state.savingsGoal.current - amount);
  }

  saveData();
  updateUI();
  hideForm();
  
  submitBtn.disabled = false;
  submitBtn.textContent = 'Ajouter';

  // Generate AI insight for PRO users
  if (state.isPro && state.transactions.length >= 5) {
    setTimeout(() => generateInsight(), 1000);
  }
}

async function suggestCategory(description) {
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 50,
        messages: [{
          role: 'user',
          content: `Catégorise cette transaction en UN seul mot parmi ces options EXACTES:
- Alimentation (restaurants, courses alimentaires, supermarchés, boulangerie, café)
- Logement (loyer, électricité, eau, gaz, internet, meubles)
- Transport (essence, péage, uber, taxi, train, bus, parking)
- Loisirs (cinéma, sport, jeux, concerts, sorties)
- Shopping (vêtements, électronique, accessoires, cadeaux non-alimentaires)
- Santé (médecin, pharmacie, mutuelle, sport santé)
- Abonnements (Netflix, Spotify, salles de sport, magazines)
- Autre (tout le reste)

Transaction: "${description}"

Réponds UNIQUEMENT avec le nom de la catégorie, sans emoji ni explication.`
        }]
      })
    });

    if (!response.ok) return null;
    const data = await response.json();
    const suggested = data.content[0].text.trim();
    
    const emojiMap = {
      'Alimentation': '🍔 Alimentation',
      'Logement': '🏠 Logement',
      'Transport': '🚗 Transport',
      'Loisirs': '🎮 Loisirs',
      'Shopping': '🛍️ Shopping',
      'Santé': '💊 Santé',
      'Abonnements': '📱 Abonnements',
      'Autre': '💰 Autre'
    };
    
    return emojiMap[suggested] || null;
  } catch (error) {
    console.log('AI categorization unavailable');
    return null;
  }
}

async function generateInsight() {
  const expenses = state.transactions.filter(t => t.type === 'expense');
  if (expenses.length < 5) return;

  const totalExpenses = expenses.reduce((sum, t) => sum + t.amount, 0);
  const categorySums = expenses.reduce((acc, t) => {
    const cat = t.category.split(' ')[1] || t.category;
    acc[cat] = (acc[cat] || 0) + t.amount;
    return acc;
  }, {});

  const topCategory = Object.entries(categorySums).sort((a, b) => b[1] - a[1])[0];

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 150,
        messages: [{
          role: 'user',
          content: `Analyse rapide de dépenses: ${totalExpenses.toFixed(0)}€ dépensés, dont ${topCategory[1].toFixed(0)}€ en ${topCategory[0]}. Donne UN conseil court et actionnable en 1-2 phrases max.`
        }]
      })
    });

    if (response.ok) {
      const data = await response.json();
      document.getElementById('aiInsightText').textContent = data.content[0].text.trim();
      document.getElementById('aiInsightCard').classList.remove('hidden');
    }
  } catch (error) {
    console.log('Insight generation unavailable');
  }
}

function deleteTransaction(id) {
  if (!confirm('Supprimer cette transaction ?')) return;
  
  const transaction = state.transactions.find(t => t.id === id);
  if (transaction) {
    if (transaction.type === 'income') {
      state.savingsGoal.current = Math.max(0, state.savingsGoal.current - transaction.amount);
    } else {
      state.savingsGoal.current += transaction.amount;
    }
    state.transactions = state.transactions.filter(t => t.id !== id);
    saveData();
    updateUI();
  }
}

// Modal handling
function showUpgradeModal() {
  const modal = document.getElementById('upgradeModal');
  const subtext = document.getElementById('modalSubtext');
  
  if (!state.isPro && state.transactions.length >= FREE_LIMIT) {
    subtext.textContent = "Tu as atteint la limite gratuite. Passe PRO pour continuer !";
  } else {
    subtext.textContent = "Prends le contrôle total de tes finances";
  }
  
  modal.classList.remove('hidden');
}

function hideUpgradeModal() {
  document.getElementById('upgradeModal').classList.add('hidden');
}

function activatePro() {
  alert('🎉 Bienvenue dans CashFlow PRO !\n\nToutes les fonctionnalités sont maintenant débloquées.\n\n(Intégration Stripe à venir pour les vrais paiements)');
  state.isPro = true;
  saveData();
  updateProStatus();
  updateUI();
  hideUpgradeModal();
}

// Global functions for inline handlers
window.deleteTransaction = deleteTransaction;