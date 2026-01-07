// Solo Leveling - Player Development System

// Player state
const player = {
  name: 'Hunter',
  level: 1,
  xp: 0,
  xpToNextLevel: 100,
  hp: 100,
  maxHp: 100,
  mp: 50,
  maxMp: 50,
  skillPoints: 0,
  stats: {
    strength: 10,
    agility: 10,
    intelligence: 10,
    vitality: 10
  },
  penalties: 0 // Track number of penalties received
};

// Daily quests template
const dailyQuestsTemplate = [
  {
    id: 'pushups',
    icon: '💪',
    title: 'Pompes',
    description: 'Effectuer 100 pompes',
    progress: 0,
    target: 100,
    xpReward: 50,
    completed: false
  },
  {
    id: 'situps',
    icon: '🏋️',
    title: 'Abdominaux',
    description: 'Effectuer 100 abdominaux',
    progress: 0,
    target: 100,
    xpReward: 50,
    completed: false
  },
  {
    id: 'squats',
    icon: '🦵',
    title: 'Squats',
    description: 'Effectuer 100 squats',
    progress: 0,
    target: 100,
    xpReward: 50,
    completed: false
  },
  {
    id: 'run',
    icon: '🏃',
    title: 'Course',
    description: 'Courir 10 kilomètres',
    progress: 0,
    target: 10,
    xpReward: 100,
    completed: false
  },
  {
    id: 'meditation',
    icon: '🧘',
    title: 'Méditation',
    description: 'Méditer pendant 30 minutes',
    progress: 0,
    target: 30,
    xpReward: 75,
    completed: false
  }
];

// Mandatory daily quest (like in Solo Leveling)
const mandatoryQuestTemplate = {
  id: 'mandatory',
  icon: '⚠️',
  title: 'QUÊTE QUOTIDIENNE OBLIGATOIRE',
  description: 'Compléter l\'entraînement du jour - ÉCHEC = PÉNALITÉ',
  progress: 0,
  target: 1,
  xpReward: 200,
  completed: false,
  isMandatory: true
};

let quests = [];
let mandatoryQuest = null;
let lastResetDate = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadGameData();
  checkDailyReset();
  updateUI();
  startResetTimer();
});

// Save game data to localStorage
function saveGameData() {
  const gameData = {
    player,
    quests,
    mandatoryQuest,
    lastResetDate
  };
  localStorage.setItem('solo-leveling-data', JSON.stringify(gameData));
}

// Load game data from localStorage
function loadGameData() {
  const saved = localStorage.getItem('solo-leveling-data');
  if (saved) {
    const data = JSON.parse(saved);
    Object.assign(player, data.player);
    quests = data.quests || [];
    mandatoryQuest = data.mandatoryQuest || null;
    lastResetDate = data.lastResetDate;
  }

  // Initialize quests if empty
  if (quests.length === 0) {
    resetDailyQuests();
  }

  // Initialize mandatory quest if null
  if (!mandatoryQuest) {
    mandatoryQuest = JSON.parse(JSON.stringify(mandatoryQuestTemplate));
  }
}

// Check if daily quests should reset
function checkDailyReset() {
  const now = new Date();
  const today = now.toDateString();

  if (lastResetDate !== today) {
    // Check if mandatory quest was completed before applying penalty
    if (mandatoryQuest && !mandatoryQuest.completed && lastResetDate !== null) {
      applyPenalty();
    }

    resetDailyQuests();
    lastResetDate = today;
    saveGameData();
  }
}

// Reset daily quests
function resetDailyQuests() {
  quests = JSON.parse(JSON.stringify(dailyQuestsTemplate));
  mandatoryQuest = JSON.parse(JSON.stringify(mandatoryQuestTemplate));
  saveGameData();
}

// Update all UI elements
function updateUI() {
  updatePlayerInfo();
  updateStats();
  updateQuestsList();
  updateSkillPointButtons();
}

// Update player information display
function updatePlayerInfo() {
  // Player level
  document.getElementById('playerLevel').textContent = `Nv. ${player.level}`;

  // XP bar
  const xpPercent = (player.xp / player.xpToNextLevel) * 100;
  document.getElementById('xpBar').style.width = `${xpPercent}%`;
  document.getElementById('xpLabel').textContent = `${player.xp} / ${player.xpToNextLevel}`;

  // HP bar
  const hpPercent = (player.hp / player.maxHp) * 100;
  document.getElementById('hpBar').style.width = `${hpPercent}%`;
  document.getElementById('hpLabel').textContent = `${player.hp} / ${player.maxHp}`;

  // MP bar
  const mpPercent = (player.mp / player.maxMp) * 100;
  document.getElementById('mpBar').style.width = `${mpPercent}%`;
  document.getElementById('mpLabel').textContent = `${player.mp} / ${player.maxMp}`;
}

// Update stats display
function updateStats() {
  // Skill points
  document.getElementById('skillPoints').textContent = player.skillPoints;

  // Individual stats
  document.getElementById('strengthValue').textContent = player.stats.strength;
  document.getElementById('agilityValue').textContent = player.stats.agility;
  document.getElementById('intelligenceValue').textContent = player.stats.intelligence;
  document.getElementById('vitalityValue').textContent = player.stats.vitality;
}

// Update skill point buttons state
function updateSkillPointButtons() {
  const hasPoints = player.skillPoints > 0;
  const buttons = ['strengthBtn', 'agilityBtn', 'intelligenceBtn', 'vitalityBtn'];

  buttons.forEach(btnId => {
    const btn = document.getElementById(btnId);
    btn.disabled = !hasPoints;
  });
}

// Apply penalty for not completing mandatory quest
function applyPenalty() {
  player.penalties += 1;

  // Penalty effects:
  // 1. Lose 30% of max HP
  const hpLoss = Math.floor(player.maxHp * 0.3);
  player.maxHp = Math.max(50, player.maxHp - hpLoss);
  player.hp = Math.min(player.hp, player.maxHp);

  // 2. Lose 100 XP (can't go below 0)
  player.xp = Math.max(0, player.xp - 100);

  // 3. Lose 1 point from a random stat (can't go below 5)
  const stats = ['strength', 'agility', 'intelligence', 'vitality'];
  const randomStat = stats[Math.floor(Math.random() * stats.length)];
  player.stats[randomStat] = Math.max(5, player.stats[randomStat] - 1);

  saveGameData();

  // Show dramatic penalty notification
  showPenaltyNotification(hpLoss, randomStat);
}

// Update quests list display
function updateQuestsList() {
  const container = document.getElementById('questsList');

  // Build mandatory quest HTML (always shown first)
  let mandatoryQuestHTML = '';
  if (mandatoryQuest) {
    const isCompleted = mandatoryQuest.completed;
    mandatoryQuestHTML = `
      <div class="quest-item ${isCompleted ? 'completed' : ''}" style="border: 3px solid ${isCompleted ? '#10b981' : '#ef4444'}; background: ${isCompleted ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.15)'}; margin-bottom: 1.5rem;">
        <div class="quest-header">
          <span class="quest-icon" style="font-size: 2.5rem;">${mandatoryQuest.icon}</span>
          <div style="flex: 1;">
            <div class="quest-title" style="color: ${isCompleted ? '#10b981' : '#ef4444'}; font-size: 1.3rem;">${mandatoryQuest.title}</div>
          </div>
          ${isCompleted ? '<span style="color: #10b981; font-size: 2rem;">✓</span>' : '<span style="color: #ef4444; font-size: 1.2rem; animation: pulse 2s infinite;">⚠️</span>'}
        </div>

        <div class="quest-desc" style="color: ${isCompleted ? 'rgba(255, 255, 255, 0.7)' : '#fca5a5'}; font-weight: 600;">${mandatoryQuest.description}</div>

        <div class="quest-rewards" style="margin-left: 3.5rem; margin-top: 0.75rem;">
          <span class="reward xp">+${mandatoryQuest.xpReward} XP</span>
          <span class="reward sp">+2 Points de Compétence</span>
        </div>

        ${!isCompleted ? `
          <div style="margin: 1rem 0 0 3.5rem; padding: 1rem; background: rgba(239, 68, 68, 0.2); border-radius: 0.5rem; border: 1px solid #ef4444;">
            <div style="color: #fca5a5; font-weight: 700; margin-bottom: 0.5rem;">⚠️ PÉNALITÉ SI NON COMPLÉTÉE :</div>
            <ul style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; margin-left: 1.5rem;">
              <li>- 30% HP Maximum</li>
              <li>- 100 Points d'Expérience</li>
              <li>- 1 Point de Statistique aléatoire</li>
            </ul>
          </div>
          <button class="btn btn-small" style="margin: 1rem 0 0 3.5rem; background: linear-gradient(135deg, #ef4444, #dc2626);" onclick="completeQuest('mandatory')">
            ⚡ COMPLÉTER LA QUÊTE OBLIGATOIRE
          </button>
        ` : ''}
      </div>

      <style>
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      </style>
    `;
  }

  // Build regular quests HTML
  const regularQuestsHTML = quests.map(quest => {
    const progressPercent = (quest.progress / quest.target) * 100;
    const isCompleted = quest.completed;

    return `
      <div class="quest-item ${isCompleted ? 'completed' : ''}">
        <div class="quest-header">
          <span class="quest-icon">${quest.icon}</span>
          <div style="flex: 1;">
            <div class="quest-title">${quest.title}</div>
          </div>
          ${isCompleted ? '<span style="color: #10b981; font-size: 1.5rem;">✓</span>' : ''}
        </div>

        <div class="quest-desc">${quest.description}</div>

        <div style="margin: 0.75rem 0 0.75rem 3.5rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.85rem;">
            <span>Progression</span>
            <span class="orbitron">${quest.progress} / ${quest.target}</span>
          </div>
          <div class="progress-bar-bg" style="height: 0.5rem;">
            <div class="progress-bar xp" style="width: ${progressPercent}%"></div>
          </div>
        </div>

        <div class="quest-rewards">
          <span class="reward xp">+${quest.xpReward} XP</span>
          ${quest.id === 'run' ? '<span class="reward sp">+1 Point de Compétence</span>' : ''}
        </div>

        ${!isCompleted ? `
          <button class="btn btn-small" style="margin: 1rem 0 0 3.5rem;" onclick="completeQuest('${quest.id}')">
            ✓ Terminer la quête
          </button>
        ` : ''}
      </div>
    `;
  }).join('');

  // Combine mandatory quest + regular quests
  container.innerHTML = mandatoryQuestHTML + (regularQuestsHTML ? '<div style="margin-top: 2rem;"><h3 style="color: #00d4ff; margin-bottom: 1rem; font-size: 1.2rem;">📋 Quêtes Optionnelles</h3>' + regularQuestsHTML + '</div>' : '');
}

// Complete a quest
function completeQuest(questId) {
  let quest;
  let isMandatory = false;

  // Check if it's the mandatory quest
  if (questId === 'mandatory') {
    quest = mandatoryQuest;
    isMandatory = true;
  } else {
    quest = quests.find(q => q.id === questId);
  }

  if (!quest || quest.completed) return;

  // Mark as completed
  quest.completed = true;
  quest.progress = quest.target;

  // Award XP
  gainXP(quest.xpReward);

  // Award bonus skill points
  if (isMandatory) {
    player.skillPoints += 2; // Mandatory quest gives 2 skill points
    showNotification(`🎉 QUÊTE OBLIGATOIRE COMPLÉTÉE ! +${quest.xpReward} XP +2 Points`, 'success');
  } else if (quest.id === 'run') {
    player.skillPoints += 1;
    showNotification(`✓ Quête terminée: ${quest.title}`, 'success');
  } else {
    showNotification(`✓ Quête terminée: ${quest.title}`, 'success');
  }

  // Save and update
  saveGameData();
  updateUI();
}

// Gain experience points
function gainXP(amount) {
  player.xp += amount;

  // Check for level up
  while (player.xp >= player.xpToNextLevel) {
    levelUp();
  }

  saveGameData();
  updateUI();
}

// Level up the player
function levelUp() {
  player.xp -= player.xpToNextLevel;
  player.level += 1;
  player.skillPoints += 3;

  // Increase XP requirement for next level
  player.xpToNextLevel = Math.floor(player.xpToNextLevel * 1.5);

  // Increase max HP and MP
  player.maxHp += 10;
  player.hp = player.maxHp; // Restore HP on level up
  player.maxMp += 5;
  player.mp = player.maxMp; // Restore MP on level up

  // Show level up notification
  showLevelUpNotification();

  saveGameData();
  updateUI();
}

// Show level up notification
function showLevelUpNotification() {
  const notif = document.getElementById('levelUpNotif');
  const levelElement = document.getElementById('newLevel');
  const playerLevelElement = document.getElementById('playerLevel');

  levelElement.textContent = player.level;
  notif.classList.remove('hidden');
  playerLevelElement.classList.add('level-up-animation');

  setTimeout(() => {
    playerLevelElement.classList.remove('level-up-animation');
  }, 500);
}

// Close level up notification
function closeLevelUpNotif() {
  document.getElementById('levelUpNotif').classList.add('hidden');
}

// Increase a stat
function increaseStat(statName) {
  if (player.skillPoints <= 0) return;

  player.stats[statName] += 1;
  player.skillPoints -= 1;

  // Update derived stats based on stat increase
  if (statName === 'vitality') {
    player.maxHp += 5;
    player.hp += 5;
  } else if (statName === 'intelligence') {
    player.maxMp += 3;
    player.mp += 3;
  }

  saveGameData();
  updateUI();

  // Show stat increase effect
  const valueElement = document.getElementById(`${statName}Value`);
  valueElement.style.transform = 'scale(1.3)';
  valueElement.style.color = '#fbbf24';

  setTimeout(() => {
    valueElement.style.transform = 'scale(1)';
    valueElement.style.color = '#00d4ff';
  }, 300);
}

// Show notification
function showNotification(message, type = 'info') {
  // Create notification element
  const notif = document.createElement('div');
  notif.style.cssText = `
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: ${type === 'success' ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #a855f7, #ec4899)'};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 0.75rem;
    font-weight: 700;
    box-shadow: 0 0 30px rgba(168, 85, 247, 0.5);
    z-index: 1000;
    animation: fadeIn 0.3s ease;
  `;
  notif.textContent = message;

  document.body.appendChild(notif);

  // Remove after 3 seconds
  setTimeout(() => {
    notif.style.opacity = '0';
    notif.style.transition = 'opacity 0.3s';
    setTimeout(() => notif.remove(), 300);
  }, 3000);
}

// Show penalty notification (dramatic style)
function showPenaltyNotification(hpLoss, statLost) {
  const statNames = {
    strength: 'Force',
    agility: 'Agilité',
    intelligence: 'Intelligence',
    vitality: 'Vitalité'
  };

  // Create full-screen penalty overlay
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.95);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.5s ease;
  `;

  overlay.innerHTML = `
    <div style="text-align: center; padding: 2rem; max-width: 500px;">
      <div style="font-size: 5rem; margin-bottom: 1rem; animation: pulse 1s infinite;">💀</div>
      <div style="font-family: 'Orbitron', sans-serif; font-size: 2.5rem; font-weight: 900; color: #ef4444; text-shadow: 0 0 20px #ef4444; margin-bottom: 1rem;">
        PÉNALITÉ APPLIQUÉE
      </div>
      <div style="color: #fca5a5; font-size: 1.2rem; margin-bottom: 2rem; line-height: 1.8;">
        Vous n'avez pas complété la quête obligatoire !<br>
        Le Système vous impose une sanction.
      </div>
      <div style="background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 1rem; padding: 1.5rem; margin-bottom: 2rem;">
        <div style="color: white; font-weight: 700; margin-bottom: 1rem; font-size: 1.1rem;">Effets de la Pénalité :</div>
        <div style="color: #fca5a5; line-height: 2;">
          ⚠️ -${hpLoss} HP Maximum<br>
          ⚠️ -100 Points d'Expérience<br>
          ⚠️ -1 ${statNames[statLost]}
        </div>
      </div>
      <button onclick="closePenaltyNotif()" style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; font-weight: 700; padding: 1rem 2rem; border-radius: 0.75rem; border: none; cursor: pointer; font-size: 1.1rem; box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);">
        Accepter la Pénalité
      </button>
    </div>
  `;

  document.body.appendChild(overlay);

  // Also store reference for global close function
  window.currentPenaltyOverlay = overlay;
}

// Close penalty notification
function closePenaltyNotif() {
  if (window.currentPenaltyOverlay) {
    window.currentPenaltyOverlay.style.opacity = '0';
    window.currentPenaltyOverlay.style.transition = 'opacity 0.3s';
    setTimeout(() => {
      window.currentPenaltyOverlay.remove();
      window.currentPenaltyOverlay = null;
    }, 300);
  }
  updateUI();
}

// Global function for inline handler
window.closePenaltyNotif = closePenaltyNotif;

// Reset timer for daily quests
function startResetTimer() {
  updateResetTimer();
  setInterval(updateResetTimer, 1000);
}

function updateResetTimer() {
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(0, 0, 0, 0);

  const diff = tomorrow - now;
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);

  const timerElement = document.getElementById('resetTimer');
  timerElement.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  // Check if we need to reset quests
  if (hours === 23 && minutes === 59 && seconds === 59) {
    setTimeout(() => {
      checkDailyReset();
      updateUI();
      showNotification('📜 Nouvelles quêtes journalières disponibles !', 'info');
    }, 1000);
  }
}

// Global functions for inline handlers
window.completeQuest = completeQuest;
window.increaseStat = increaseStat;
window.closeLevelUpNotif = closeLevelUpNotif;
