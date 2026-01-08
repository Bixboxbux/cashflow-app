# 🎯 X Profile Analyzer

**Outil local d'analyse sémantique de profils X/Twitter**

Identifiez facilement les comptes pertinents à suivre et les prospects potentiels pour votre produit (swipe file d'accroches, formations copywriting, etc.).

---

## 📋 Table des matières

- [Caractéristiques](#-caractéristiques)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Comment ça marche](#-comment-ça-marche)
- [Exemples](#-exemples)
- [Export des résultats](#-export-des-résultats)
- [FAQ](#-faq)

---

## ✨ Caractéristiques

✅ **100% Local** - Aucune donnée envoyée sur internet, tout fonctionne sur votre machine
✅ **Pas de scraping** - Vous copiez-collez manuellement les données depuis X
✅ **Pas d'API requise** - Aucune clé API Twitter nécessaire
✅ **Analyse sémantique** - Détection intelligente des thématiques et intentions
✅ **Scoring automatique** - Classement des profils par pertinence (0-100)
✅ **Export CSV/JSON** - Exportez vos résultats pour analyse ultérieure
✅ **Interface simple** - Application web locale intuitive

---

## 🚀 Installation

### Prérequis

- Python 3.8+ installé sur votre machine
- Navigateur web moderne (Chrome, Firefox, Safari, Edge)

### Étapes

1. **Ouvrez un terminal** dans le dossier `x-profile-analyzer`

2. **Installez les dépendances :**

```bash
pip install -r requirements.txt
```

3. **Lancez l'application :**

```bash
python app.py
```

4. **Ouvrez votre navigateur** à l'adresse :

```
http://localhost:5000
```

Et voilà ! L'outil est prêt à l'emploi 🎉

---

## 📖 Utilisation

### Étape 1 : Configuration

Dans la section "⚙️ Configuration" :

1. **Ajoutez vos mots-clés personnalisés** (séparés par des virgules)
   - Exemple : `copywriting, accroche, conversion, marketing, vente`
   - Ces mots-clés permettent d'affiner la recherche selon votre niche

2. **Langue** : Français (fr) par défaut

3. **Nombre minimum de tweets** : Définissez le niveau d'activité minimum souhaité

### Étape 2 : Ajouter des profils

Dans la section "👥 Profils à analyser" :

1. **Username** : Entrez le nom d'utilisateur (ex: @marie_copy)

2. **Bio** : Copiez-collez la bio du profil depuis X/Twitter

3. **Tweets récents** : Copiez-collez les tweets récents (un par ligne)

**Astuce :** Cliquez sur "📝 Charger exemple" pour voir un exemple pré-rempli !

### Étape 3 : Analyser

Cliquez sur le gros bouton **"🚀 ANALYSER LES PROFILS"**

L'analyse se lance et vous obtenez :
- Un **score de pertinence** (0-100) pour chaque profil
- Les **thématiques détectées** (copywriting, marketing, business...)
- Les **signaux d'intention** (recherche d'aide, vente, optimisation...)
- Une **explication claire** du score
- Un **classement automatique** du plus au moins pertinent

---

## 🧠 Comment ça marche ?

### Système de scoring (0-100 points)

L'algorithme analyse le texte (bio + tweets) et attribue des points selon :

| Critère | Points max | Description |
|---------|-----------|-------------|
| **Thématiques** | 40 pts | Copywriting, marketing, business, création de contenu, e-commerce |
| **Signaux d'intention** | 25 pts | Recherche d'aide, vente, optimisation, lancement de projet |
| **Mots-clés personnalisés** | 20 pts | Correspondance avec vos mots-clés spécifiques |
| **Mots-clés accroches** | 10 pts | Mentions d'accroches, headlines, hooks, swipe files |
| **Niveau d'activité** | 5 pts | Nombre de tweets analysés |

### Interprétation des scores

- **70-100** : 🎯 **TRÈS PERTINENT** - Prospect idéal pour votre produit
- **50-69** : ✅ **PERTINENT** - Bon prospect potentiel
- **30-49** : ⚠️ **MOYENNEMENT PERTINENT** - À suivre mais pas prioritaire
- **0-29** : ❌ **PEU PERTINENT** - Hors cible

### Thématiques détectées

L'outil détecte automatiquement ces thématiques :

- **Copywriting** : rédaction, accroches, storytelling, persuasion
- **Marketing** : acquisition, conversion, funnel, leads
- **Business** : entrepreneuriat, vente, revenus
- **Création de contenu** : audience, newsletter, blog
- **E-commerce** : boutique, produits, vente en ligne

### Signaux d'intention

L'outil repère les intentions suivantes :

- **Recherche d'aide** : "besoin", "cherche", "comment", "galère"
- **Vente active** : "vendre", "offre", "lancement", "disponible"
- **Optimisation** : "améliorer", "booster", "doubler", "augmenter"
- **Création** : "créer", "lancer", "nouveau projet", "démarrer"

---

## 📊 Exemples

### Exemple 1 : Copywriter freelance

**Profil :**
```
Username: @marie_copywriter
Bio: Copywriter freelance 🇫🇷 | J'aide les entrepreneurs à créer
      du contenu qui convertit | Accroches & storytelling

Tweets:
- Comment écrire une accroche qui capte l'attention en 3 secondes ?
- Je cherche des exemples d'accroches percutantes pour mes clients
- La règle d'or du copywriting : partir du problème du client
```

**Résultat attendu :**
- Score : **85-95**
- Thématiques : Copywriting, Marketing, Création de contenu
- Signaux : Recherche d'aide, Optimisation
- **Verdict : 🎯 TRÈS PERTINENT**

### Exemple 2 : Growth Marketer

**Profil :**
```
Username: @julien_growth
Bio: Growth Marketer | Expert acquisition & conversion |
     Je booste les ventes des e-commerces 📈

Tweets:
- Mon funnel ne convertit pas assez... Besoin d'optimiser
- Lancement de ma formation sur l'acquisition client
- 3 techniques pour doubler votre taux de conversion
```

**Résultat attendu :**
- Score : **80-90**
- Thématiques : Marketing, Business, E-commerce
- Signaux : Recherche d'aide, Optimisation, Vente active
- **Verdict : 🎯 TRÈS PERTINENT**

### Exemple 3 : Développeur (hors cible)

**Profil :**
```
Username: @thomas_dev
Bio: Développeur Full Stack | React & Node.js | Tech enthusiast 💻

Tweets:
- Nouveau projet en TypeScript avec Next.js 14
- Debug session du dimanche...
- Code review time !
```

**Résultat attendu :**
- Score : **5-15**
- Thématiques : Aucune pertinente
- Signaux : Aucun
- **Verdict : ❌ PEU PERTINENT**

---

## 💾 Export des résultats

Une fois l'analyse terminée, vous pouvez exporter les résultats :

### Export CSV
- Idéal pour Excel / Google Sheets
- Contient toutes les données tabulées
- Encodage UTF-8 avec BOM (compatible Excel)

### Export JSON
- Format structuré pour développeurs
- Facile à réimporter dans d'autres outils
- Contient tous les détails de l'analyse

**Nom des fichiers :**
- `x_profile_analysis_YYYYMMDD_HHMMSS.csv`
- `x_profile_analysis_YYYYMMDD_HHMMSS.json`

---

## ❓ FAQ

### Puis-je analyser des profils en anglais ?

Actuellement, l'outil est optimisé pour le français. L'analyse en anglais est possible mais moins précise. Une version multilingue est prévue.

### Combien de profils puis-je analyser en une fois ?

Il n'y a pas de limite technique, mais pour des performances optimales, nous recommandons 10-20 profils par analyse.

### Est-ce que l'outil stocke mes données ?

Non. Toutes les données sont traitées localement et en mémoire. Rien n'est sauvegardé sauf si vous exportez volontairement les résultats.

### Comment améliorer la précision des résultats ?

1. Ajoutez des **mots-clés spécifiques** à votre niche
2. Copiez **plusieurs tweets récents** (5-10 minimum)
3. Incluez la **bio complète** du profil

### L'outil peut-il scraper automatiquement X/Twitter ?

Non, et c'est volontaire. Le scraping automatique violerait les conditions d'utilisation de X/Twitter. Cet outil nécessite une saisie manuelle pour rester dans le cadre légal et éthique.

### Puis-je personnaliser les critères de scoring ?

Oui ! Le code est open source. Vous pouvez modifier le fichier `analyzer.py` pour ajuster :
- Les mots-clés par thématique
- Les pondérations du scoring
- Les seuils d'interprétation

### Comment contribuer au projet ?

Le code est ouvert et documenté. N'hésitez pas à :
- Proposer des améliorations
- Ajouter de nouvelles thématiques
- Améliorer l'algorithme de scoring
- Traduire dans d'autres langues

---

## 🛠️ Structure du projet

```
x-profile-analyzer/
│
├── app.py                 # Application Flask (serveur web)
├── analyzer.py            # Moteur d'analyse sémantique
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation (ce fichier)
│
├── templates/
│   └── index.html        # Interface web
│
├── data/
│   └── example_profiles.json  # Exemples de profils
│
└── exports/              # Dossier pour les exports (créé auto)
```

---

## 📝 Notes importantes

⚠️ **Usage personnel uniquement**
- Cet outil est conçu pour votre usage personnel
- Ne l'utilisez pas pour du scraping massif
- Respectez les conditions d'utilisation de X/Twitter

⚠️ **Aucune garantie**
- Les scores sont indicatifs et basés sur une analyse sémantique simple
- L'outil ne remplace pas votre jugement humain
- Vérifiez toujours manuellement les profils avant de les contacter

✅ **Légal et éthique**
- Pas de scraping automatique
- Pas d'accès non autorisé aux données
- Traitement local des données
- Respect de la vie privée

---

## 🎉 Bon usage !

Vous avez maintenant tout ce qu'il faut pour identifier les profils pertinents et développer votre audience sur X/Twitter.

**Questions ? Suggestions ?**
N'hésitez pas à améliorer le code ou à l'adapter à vos besoins spécifiques !

---

**Version :** 1.0.0
**Dernière mise à jour :** Janvier 2026
**Licence :** Usage personnel uniquement
