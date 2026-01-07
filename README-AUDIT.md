# SiteAuditPro - Outil d'Audit SEO & Conversion

Application web micro-SaaS permettant d'analyser automatiquement un site web pour le SEO, la conversion, la performance et le mobile.

## Fonctionnalités

### Version Gratuite
- ✅ Audit complet d'une page
- ✅ Score global sur 100 + note (A à F)
- ✅ 5 catégories d'analyse (SEO, Performance, Conversion, Mobile, Sécurité)
- ✅ 3 recommandations prioritaires
- ✅ Copie du rapport en texte
- ❌ Limité à 3 audits/jour (à implémenter)

### Version Pro (29€/mois)
- ✅ Toutes les recommandations
- ✅ Export PDF
- ✅ Audit de 10 pages internes
- ✅ Suivi historique
- ✅ Audits illimités

### Version Agence (99€/mois)
- ✅ Tout Pro +
- ✅ White label
- ✅ Accès API
- ✅ Multi-utilisateurs

---

## 🚀 Lancement Rapide

### Prérequis
- Python 3.8+
- Un navigateur web moderne

### Installation

```bash
# 1. Cloner ou aller dans le répertoire
cd /home/user/cashflow-app

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r backend/requirements.txt

# 4. Lancer le serveur backend
python backend/app.py
```

Le serveur démarre sur `http://localhost:5000`

### Lancer le Frontend

```bash
# Option 1: Ouvrir directement dans le navigateur
# Ouvrez frontend/index.html dans votre navigateur

# Option 2: Serveur HTTP simple (recommandé)
cd frontend
python -m http.server 8080
# Puis ouvrez http://localhost:8080
```

---

## 📁 Structure du Projet

```
cashflow-app/
├── backend/
│   ├── app.py              # API Flask principale
│   └── requirements.txt    # Dépendances Python
├── frontend/
│   ├── index.html          # Interface utilisateur
│   └── app.js              # Logique JavaScript
└── README-AUDIT.md         # Ce fichier
```

---

## 🔧 API Endpoints

### POST /api/audit
Analyse une URL et retourne un rapport complet.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "global_score": 72,
  "grade": "B",
  "analyses": {
    "seo": { "score": 65, "max_score": 100, "issues": [...], "successes": [...] },
    "performance": { ... },
    "conversion": { ... },
    "mobile": { ... },
    "security": { ... }
  },
  "priority_recommendations": [...]
}
```

### GET /api/health
Health check endpoint.

---

## 💰 Stratégies de Monétisation

### 1. Freemium (Implémenté)
- Version gratuite limitée (3 recommandations visibles)
- Paywall visuel pour débloquer le rapport complet
- Modal de pricing avec 3 plans

### 2. Upsells Suggérés
- **Export PDF** : Générer un rapport PDF professionnel
- **Audit multi-pages** : Analyser 10+ pages d'un site
- **Suivi mensuel** : Alertes quand le score change
- **White label** : Rapport aux couleurs du client (pour agences)
- **API** : Accès programmatique pour intégrations

### 3. Lead Generation
- Capturer l'email avant de montrer les résultats
- Proposer un "audit approfondi gratuit" par un expert
- Newsletter avec tips SEO hebdomadaires

### 4. Affiliation
- Recommander des outils (hébergeurs, CDN, outils SEO)
- Toucher une commission sur les inscriptions

---

## 🌐 Déploiement

### Option 1: Railway (Recommandé - Gratuit pour commencer)

1. Créer un compte sur [railway.app](https://railway.app)
2. Connecter votre repo GitHub
3. Créer un nouveau projet depuis GitHub
4. Railway détecte automatiquement Python/Flask
5. Ajouter les variables d'environnement si nécessaire

```bash
# Fichier Procfile (à créer)
web: cd backend && python app.py
```

### Option 2: Render

1. Créer un compte sur [render.com](https://render.com)
2. New > Web Service
3. Connecter le repo
4. Build Command: `pip install -r backend/requirements.txt`
5. Start Command: `cd backend && python app.py`

### Option 3: Vercel (Frontend) + Railway (Backend)

**Frontend sur Vercel:**
```bash
# vercel.json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/frontend/index.html" }]
}
```

**Backend sur Railway:**
- Déployer le dossier `backend/` séparément
- Mettre à jour `API_URL` dans `frontend/app.js`

### Option 4: VPS (DigitalOcean, Hetzner)

```bash
# Sur le serveur
sudo apt update
sudo apt install python3-pip nginx

# Cloner le projet
git clone <repo> /var/www/siteauditpro
cd /var/www/siteauditpro

# Installer
pip3 install -r backend/requirements.txt

# Lancer avec Gunicorn
pip3 install gunicorn
gunicorn --chdir backend -w 4 -b 0.0.0.0:5000 app:app

# Configurer Nginx pour servir le frontend
# et proxy vers le backend
```

---

## 🔒 Améliorations pour la Production

### Sécurité
- [ ] Ajouter rate limiting (Flask-Limiter)
- [ ] Valider/sanitizer les URLs
- [ ] Ajouter CORS restrictif
- [ ] Implémenter authentification JWT

### Performance
- [ ] Cache Redis pour les audits récents
- [ ] Queue avec Celery pour audits longs
- [ ] CDN pour les assets statiques

### Fonctionnalités
- [ ] Base de données (PostgreSQL) pour historique
- [ ] Intégration Stripe pour paiements
- [ ] Export PDF avec WeasyPrint
- [ ] Lighthouse API pour métriques avancées
- [ ] Screenshots avec Playwright

### Monitoring
- [ ] Sentry pour les erreurs
- [ ] Analytics (Plausible, Simple Analytics)
- [ ] Uptime monitoring

---

## 📊 Analyses Effectuées

### SEO (30% du score)
- Balise title (présence, longueur)
- Meta description
- Structure H1/H2/H3
- Attributs alt des images
- Balise canonical
- Open Graph
- Schema.org

### Performance (20% du score)
- Temps de réponse serveur
- Taille de la page HTML
- Compression GZIP
- Headers de cache

### Conversion (25% du score)
- Présence de CTAs
- Formulaires
- Signaux de confiance
- Coordonnées visibles
- Information tarifaire

### Mobile (15% du score)
- Viewport meta tag
- CSS responsive
- Pas de Flash
- Taille des polices

### Sécurité (10% du score)
- HTTPS
- Headers de sécurité
- Content Security Policy

---

## 🛠️ Personnalisation

### Changer les couleurs
Modifiez les variables CSS dans `frontend/index.html` :

```css
:root {
    --primary: #4F46E5;      /* Couleur principale */
    --primary-dark: #4338CA;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
}
```

### Changer les prix
Modifiez la modal pricing dans `frontend/index.html` (recherchez "pricingModal")

### Ajouter des analyses
Ajoutez de nouvelles fonctions dans `backend/app.py` et intégrez-les dans l'endpoint `/api/audit`

---

## 📝 License

MIT - Libre d'utilisation commerciale

---

## 🤝 Support

Pour toute question : contact@siteauditpro.com

---

*Créé avec ❤️ pour les entrepreneurs et PME qui veulent booster leur présence en ligne.*
