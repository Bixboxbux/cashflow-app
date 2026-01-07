# Solo Leveling - Système de Développement du Joueur

Application mobile gamifiée inspirée du webtoon **Solo Leveling**, permettant de progresser comme un Hunter à travers un système de quêtes journalières, d'expérience et de points de compétences.

## 🎮 Fonctionnalités

### 📊 Système de Progression
- **Niveaux** : Gagnez de l'expérience pour monter de niveau
- **Points de Vie (HP)** : Augmentent automatiquement avec le niveau et la vitalité
- **Points de Mana (MP)** : Augmentent automatiquement avec le niveau et l'intelligence
- **Barre d'Expérience** : Visualisez votre progression vers le prochain niveau

### ⭐ Points de Compétence
- Gagnez **3 points de compétence** à chaque montée de niveau
- Répartissez vos points entre 4 statistiques :
  - 💪 **Force** : Augmente les dégâts physiques
  - ⚡ **Agilité** : Augmente la vitesse et l'esquive
  - 🧠 **Intelligence** : Augmente les MP et les dégâts magiques
  - 🛡️ **Vitalité** : Augmente les HP et la défense

### 📜 Quêtes Journalières

#### ⚠️ QUÊTE OBLIGATOIRE (Nouveau !)
Une quête spéciale qui **DOIT** être complétée chaque jour :
- **⚠️ Quête Quotidienne Obligatoire** : +200 XP + 2 Points de Compétence

**ATTENTION :** Si cette quête n'est pas complétée avant minuit, vous recevrez une **PÉNALITÉ SÉVÈRE** :
- 💔 Perte de 30% des HP Maximum
- ⬇️ Perte de 100 Points d'Expérience
- 📉 Perte d'1 point dans une statistique aléatoire

#### Quêtes Optionnelles
5 quêtes bonus qui se réinitialisent chaque jour à minuit :

1. **💪 Pompes** : 100 répétitions - +50 XP
2. **🏋️ Abdominaux** : 100 répétitions - +50 XP
3. **🦵 Squats** : 100 répétitions - +50 XP
4. **🏃 Course** : 10 kilomètres - +100 XP + 1 Point de Compétence bonus
5. **🧘 Méditation** : 30 minutes - +75 XP

### ⏰ Timer de Réinitialisation
Un compte à rebours affiche le temps restant avant la réinitialisation des quêtes journalières.

### 💾 Sauvegarde Automatique
Toutes vos données sont sauvegardées automatiquement dans le localStorage de votre navigateur.

## 🚀 Utilisation

1. Ouvrez `app.html` dans votre navigateur
2. Complétez des quêtes journalières pour gagner de l'XP
3. Montez de niveau pour obtenir des points de compétence
4. Répartissez vos points pour améliorer vos statistiques
5. Revenez chaque jour pour de nouvelles quêtes !

## 🎨 Design

- Interface sombre inspirée de Solo Leveling
- Animations fluides et effets lumineux
- Design responsive adapté aux mobiles
- Barres de progression avec effets shimmer
- Notifications de niveau supérieur

## 🛠️ Technologies

- HTML5
- CSS3 (Gradients, Animations)
- JavaScript Vanilla
- LocalStorage pour la persistance
- Google Fonts (Orbitron, Rajdhani)

## 📱 Mobile-First

L'application est optimisée pour une utilisation sur smartphone, avec des contrôles tactiles et un design adaptatif.

---

*Inspiré par le webtoon Solo Leveling de Chugong*
