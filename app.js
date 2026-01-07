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
  }
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

let quests = [];
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
    lastResetDate = data.lastResetDate;
  }

  // Initialize quests if empty
  if (quests.length === 0) {
    resetDailyQuests();
  }
}

// Check if daily quests should reset
function checkDailyReset() {
  const now = new Date();
  const today = now.toDateString();

  if (lastResetDate !== today) {
    resetDailyQuests();
    lastResetDate = today;
    saveGameData();
  }
}

// Reset daily quests
function resetDailyQuests() {
  quests = JSON.parse(JSON.stringify(dailyQuestsTemplate));
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

// Update quests list display
function updateQuestsList() {
  const container = document.getElementById('questsList');

  container.innerHTML = quests.map(quest => {
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
}

// Complete a quest
function completeQuest(questId) {
  const quest = quests.find(q => q.id === questId);
  if (!quest || quest.completed) return;

  // Mark as completed
  quest.completed = true;
  quest.progress = quest.target;

  // Award XP
  gainXP(quest.xpReward);

  // Award bonus skill point for run quest
  if (quest.id === 'run') {
    player.skillPoints += 1;
  }

  // Save and update
  saveGameData();
  updateUI();

  // Show completion message
  showNotification(`✓ Quête terminée: ${quest.title}`, 'success');
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
