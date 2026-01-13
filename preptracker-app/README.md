# PrepTracker - Application Mobile de Gestion de Commandes B2B

Application mobile React Native pour préparateurs de commandes chez Guillemot Corporation.

## 📱 Description

PrepTracker est une application mobile personnelle conçue pour les préparateurs de commandes en entrepôt. Elle permet d'organiser et de suivre les commandes B2B de manière efficace avec une interface optimisée pour une utilisation en conditions d'entrepôt.

### Fonctionnalités principales

- ✅ **Gestion des clients** : Ajout, modification et suppression de clients B2B
- ✅ **Gestion des commandes** : Création et suivi des commandes avec référence, statut et priorité
- ✅ **Tableau de bord** : Vue d'ensemble des commandes du jour avec statistiques en temps réel
- ✅ **Changement de statut rapide** : Interface tactile avec haptic feedback
- ✅ **Notes journalières** : Ajout de notes pour chaque commande
- ✅ **Recherche et filtres** : Recherche par référence, client ou code
- ✅ **Mode sombre** : Interface optimisée pour réduire la fatigue visuelle
- ✅ **Fonctionnement hors-ligne** : Stockage local avec SQLite

### Statuts des commandes

- **À faire** (gris) : Commandes en attente
- **En cours** (bleu) : Commandes en préparation
- **Terminé** (vert) : Commandes complétées
- **Problème** (rouge) : Commandes avec problèmes

## 🛠️ Technologies utilisées

- **React Native** avec **Expo**
- **TypeScript**
- **SQLite** (expo-sqlite) pour le stockage local
- **React Navigation** pour la navigation
- **Expo Haptics** pour le retour tactile
- **React Native Gesture Handler** pour les interactions tactiles

## 📦 Installation

### Prérequis

- Node.js 18+
- npm ou yarn
- Expo CLI (optionnel, mais recommandé)
- Un appareil Android/iOS ou un émulateur

### Étapes d'installation

1. **Cloner le projet et accéder au dossier**
   ```bash
   cd preptracker-app
   ```

2. **Installer les dépendances**
   ```bash
   npm install
   ```

3. **Lancer l'application en mode développement**
   ```bash
   npm start
   ```

   Ou directement sur Android :
   ```bash
   npm run android
   ```

   Ou sur iOS (macOS uniquement) :
   ```bash
   npm run ios
   ```

4. **Scanner le QR code** avec l'application Expo Go sur votre téléphone

## 📱 Utilisation

### Premier lancement

1. **Créer des clients** : Accédez à "Gérer les clients" depuis le dashboard et ajoutez vos clients B2B
2. **Créer une commande** : Appuyez sur le bouton "+" et remplissez le formulaire
3. **Suivre vos commandes** : Utilisez le dashboard pour voir l'état de vos commandes

### Interface optimisée entrepôt

- **Taille des polices** : Minimum 16px pour une lisibilité avec des gants
- **Zone de tap** : Boutons minimum 48x48px
- **Swipe gestures** : Changement rapide de statut
- **Haptic feedback** : Retour tactile sur les actions importantes
- **Mode sombre** : Activé par défaut

## 🏗️ Structure du projet

```
preptracker-app/
├── src/
│   ├── components/          # Composants réutilisables
│   │   ├── StatusBadge.tsx
│   │   ├── OrderCard.tsx
│   │   ├── QuickStatusBar.tsx
│   │   ├── SearchBar.tsx
│   │   └── EmptyState.tsx
│   ├── screens/            # Écrans de l'application
│   │   ├── DashboardScreen.tsx
│   │   ├── OrdersListScreen.tsx
│   │   ├── OrderDetailScreen.tsx
│   │   ├── ClientsScreen.tsx
│   │   └── AddOrderScreen.tsx
│   ├── database/           # Base de données SQLite
│   │   ├── schema.ts       # Schéma des tables
│   │   └── queries.ts      # Fonctions CRUD
│   ├── hooks/              # Hooks personnalisés
│   │   ├── useClients.ts
│   │   ├── useOrders.ts
│   │   └── useDailyStats.ts
│   └── utils/              # Fonctions utilitaires
│       ├── dateHelpers.ts
│       └── statusHelpers.ts
├── App.tsx                 # Point d'entrée de l'application
├── package.json
└── README.md
```

## 🗄️ Schéma de base de données

### Table `clients`
- `id` : Identifiant unique
- `name` : Nom du client
- `code` : Code client interne
- `notes` : Notes additionnelles
- `created_at` : Date de création

### Table `orders`
- `id` : Identifiant unique
- `client_id` : Référence au client
- `reference` : Numéro de commande
- `status` : Statut (todo, in_progress, done, problem)
- `priority` : Priorité (0=normal, 1=urgent)
- `due_date` : Date d'échéance
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### Table `daily_notes`
- `id` : Identifiant unique
- `order_id` : Référence à la commande
- `client_id` : Référence au client
- `content` : Contenu de la note
- `note_date` : Date de la note
- `created_at` : Date de création

## 🚀 Build pour production

### Android (APK)

```bash
# Build de développement
npx expo build:android

# Build de production (EAS)
npx eas build --platform android
```

### iOS (IPA)

```bash
# Build de développement (nécessite macOS)
npx expo build:ios

# Build de production (EAS)
npx eas build --platform ios
```

## 🔮 Fonctionnalités futures (Phase 2)

- [ ] Export des données en CSV
- [ ] Scan de code-barres pour ajout rapide
- [ ] Statistiques hebdomadaires
- [ ] Backup/restore en JSON
- [ ] Widget Android pour vue rapide

## 📄 Licence

Usage personnel - Guillemot Corporation

## 👨‍💻 Développé pour

Préparateurs de commandes B2B chez Guillemot Corporation

---

**Note** : Application optimisée pour un usage en entrepôt avec interface tactile adaptée (gros boutons, mode sombre, haptic feedback).
