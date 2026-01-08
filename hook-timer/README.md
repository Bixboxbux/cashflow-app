# Hook Timer - Application Mobile Android de Productivité Gamifiée

Application mobile React Native combinant un timer Pomodoro avec un système de gamification où l'utilisateur débloque des "hooks" (phrases motivantes) à chaque session complétée.

## 🚀 Fonctionnalités

### Timer Pomodoro
- Sessions de focus personnalisables (15-60 min)
- Pauses courtes et longues
- 4 cycles de travail avec progression visuelle
- Notifications et sons de fin de session
- Retour haptique

### Système de Hooks
- 50 hooks gratuits
- 450 hooks premium (via achat in-app)
- 5 catégories: Motivation, Productivity, Mindset, Success, Discipline
- Déblocage aléatoire à chaque session complétée
- Système de favoris
- Partage de hooks

### Statistiques
- Suivi du streak quotidien
- Graphiques hebdomadaires
- Statistiques avancées (Premium)
- Objectifs personnalisables

### Premium
- 450 hooks supplémentaires
- Statistiques avancées
- 5 thèmes de couleur
- Widget Android
- Paiement unique (4.99€)

## 📱 Stack Technique

- **Framework**: React Native avec Expo SDK 50+
- **Navigation**: @react-navigation/native avec bottom-tabs et native-stack
- **State Management**: Zustand
- **Persistance**: @react-native-async-storage/async-storage
- **Notifications**: expo-notifications
- **Animations**: react-native-reanimated + lottie-react-native
- **Achats in-app**: expo-in-app-purchases
- **Graphiques**: react-native-chart-kit

## 🛠️ Installation

```bash
# Installer les dépendances
npm install

# ou avec yarn
yarn install

# Lancer le projet
npx expo start

# Lancer sur Android
npx expo start --android
```

## 📂 Structure du Projet

```
hook-timer/
├── App.tsx                 # Point d'entrée
├── app.json               # Configuration Expo
├── src/
│   ├── components/        # Composants réutilisables
│   ├── screens/          # Écrans de l'app
│   ├── navigation/       # Configuration navigation
│   ├── store/           # Stores Zustand
│   ├── hooks/           # Custom hooks
│   ├── data/            # Données (hooks)
│   ├── utils/           # Utilitaires
│   ├── theme/           # Système de thème
│   └── types/           # Types TypeScript
└── assets/              # Images, sons, animations
```

## 🎨 Design System

### Couleurs
- Primary: #6366F1 (Indigo)
- Secondary: #22D3EE (Cyan)
- Success: #10B981
- Warning: #F59E0B
- Error: #EF4444

### Thèmes
- Dark (par défaut)
- Light
- 5 thèmes de couleur premium

## 🔧 Configuration

### Google Play License Key
Remplacer `YOUR_GOOGLE_PLAY_LICENSE_KEY` dans `app.json` avec votre clé de licence Google Play.

### EAS Project ID
Remplacer `YOUR_EAS_PROJECT_ID` dans `app.json` avec votre ID de projet EAS.

## 📝 Développement

### Ajouter des Hooks
Les hooks sont définis dans:
- `src/data/hooks-free.ts` (50 hooks gratuits)
- `src/data/hooks-premium.ts` (120 hooks premium, 330 à compléter)

Format d'un hook:
```typescript
{
  id: 'unique-id',
  text: 'Texte du hook (max 150 caractères)',
  category: 'motivation' | 'productivity' | 'mindset' | 'success' | 'discipline',
  isPremium: boolean,
}
```

### Tester les Achats In-App
1. Configurer un compte développeur Google Play
2. Créer un produit in-app avec l'ID: `hook_timer_premium`
3. Ajouter des testeurs
4. Utiliser la Google Play Console pour tester

## 🚢 Déploiement

### Build Android (APK)
```bash
eas build --platform android --profile preview
```

### Build Production
```bash
eas build --platform android --profile production
```

### Soumettre au Play Store
```bash
eas submit --platform android
```

## 📄 Licence

Projet privé - Tous droits réservés

## 👤 Auteur

Créé pour le Google Play Store

## 🎯 TODO

- [ ] Ajouter 330 hooks premium supplémentaires
- [ ] Créer les assets (icône, splash screen, sons, animations)
- [ ] Configurer les clés Google Play
- [ ] Tester les achats in-app
- [ ] Implémenter le widget Android
- [ ] Ajouter les 4 thèmes de couleur premium supplémentaires
- [ ] Tests end-to-end
- [ ] Optimisation des performances

## 📞 Support

Pour toute question ou suggestion, contactez [votre email]
