# WebAudit Pro - Audit SEO & Conversion

Application web pour auditer automatiquement les sites web sur les critères SEO, conversion, performance et mobile.

## Fonctionnalités

### Version Gratuite
- 3 audits par mois
- Score global avec grade (A-F)
- Analyse SEO (title, meta, H1, Open Graph)
- Analyse de conversion (CTA, formulaires, preuves sociales)
- Analyse de performance (temps de chargement, poids de page)
- Analyse mobile (viewport, responsive)
- Analyse sécurité (HTTPS)
- Export du rapport en texte

### Version Pro (simulée)
- Audits illimités
- Analyse des backlinks
- Benchmark concurrentiel
- Historique 12 mois
- Rapports PDF personnalisés

## Installation

### Prérequis
- Python 3.8+
- pip

### Installation locale

```bash
# Cloner le projet
cd cashflow-app

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app.py
```

L'application sera accessible sur http://localhost:5000

## Déploiement

### Option 1: Railway (Recommandé - Gratuit)

1. Créer un compte sur [Railway](https://railway.app)
2. Connecter votre repo GitHub
3. Railway détectera automatiquement Flask
4. Ajouter un `Procfile`:

```
web: gunicorn app:app
```

### Option 2: Render (Gratuit)

1. Créer un compte sur [Render](https://render.com)
2. New > Web Service
3. Connecter votre repo GitHub
4. Configuration:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### Option 3: Heroku

```bash
# Installer Heroku CLI
heroku login
heroku create webaudit-pro
git push heroku main
```

### Option 4: VPS (DigitalOcean, OVH, etc.)

```bash
# Sur le serveur
git clone <repo>
cd cashflow-app
pip install -r requirements.txt
gunicorn app:app -b 0.0.0.0:8000 --daemon

# Configurer Nginx comme reverse proxy
```

## Structure du Projet

```
cashflow-app/
├── app.py              # Backend Flask + logique d'analyse
├── requirements.txt    # Dépendances Python
├── static/
│   ├── css/
│   │   └── style.css   # Styles professionnels
│   └── js/
│       └── app.js      # Logique frontend
├── templates/
│   └── index.html      # Template HTML principal
└── README.md
```

## Idées de Monétisation

### 1. Freemium (Implémenté)
- **Gratuit**: 3 audits/mois, fonctionnalités de base
- **Pro (29€/mois)**: Audits illimités, analyses avancées
- **Agence (99€/mois)**: White-label, multi-projets, API

### 2. Génération de Leads
- Collecter les emails pour débloquer le rapport complet
- Vendre des services de consulting SEO
- Affiliation vers des outils comme SEMrush, Ahrefs

### 3. Upsells
- Rapport PDF personnalisé: 9€
- Audit manuel par un expert: 149€
- Suivi mensuel automatisé: 19€/mois

### 4. API
- 100 requêtes/mois: 49€
- 1000 requêtes/mois: 199€
- Enterprise: Sur devis

### 5. White-Label
- Agences SEO/marketing peuvent revendre l'outil
- Intégration dans leurs services existants

## Améliorations Possibles

### Court terme
- [ ] Intégration Stripe pour paiements réels
- [ ] Système d'authentification
- [ ] Historique des audits par utilisateur
- [ ] Export PDF avec charts

### Moyen terme
- [ ] Analyse des backlinks via API tierce
- [ ] Comparaison avec concurrents
- [ ] Monitoring automatique (alertes)
- [ ] API REST publique

### Long terme
- [ ] Machine learning pour recommandations personnalisées
- [ ] Intégration Google Search Console
- [ ] Plugin WordPress/Shopify
- [ ] App mobile

## API Endpoints

### POST /api/analyze
Analyse une URL et retourne les résultats.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "global_score": 75,
  "grade": "C",
  "scores": {
    "seo": 80,
    "conversion": 65,
    "speed": 70,
    "mobile": 85,
    "security": 100
  },
  "details": {...},
  "recommendations": [...]
}
```

### POST /api/export
Génère un rapport texte structuré.

**Request:**
```json
{
  "results": {...}
}
```

**Response:**
```json
{
  "report": "..."
}
```

## Technologies

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Analyse**: BeautifulSoup, Requests
- **Design**: Custom CSS (pas de framework)

## Licence

MIT - Libre pour usage commercial et personnel.

---

Développé comme MVP micro-SaaS. Prêt pour la monétisation et le scaling.
