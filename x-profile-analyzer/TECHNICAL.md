# 🔧 Documentation Technique

## Architecture

### Stack technique
- **Backend :** Python 3.8+ avec Flask
- **Frontend :** HTML5 + CSS3 + JavaScript (vanilla)
- **Analyse :** Traitement de texte basé sur regex et correspondance de mots-clés

### Structure du code

```
x-profile-analyzer/
│
├── analyzer.py              # Moteur d'analyse (logique métier)
│   ├── Profile              # Dataclass pour les profils
│   ├── AnalysisResult       # Dataclass pour les résultats
│   └── ProfileAnalyzer      # Classe principale d'analyse
│
├── app.py                   # Application Flask (API REST)
│   ├── /                    # Route principale (interface)
│   ├── /analyze             # POST - Analyse des profils
│   ├── /export/csv          # GET - Export CSV
│   └── /export/json         # GET - Export JSON
│
└── templates/index.html     # Interface utilisateur (SPA)
```

---

## Algorithme de scoring

### Pondération (total 100 points)

| Critère | Points | Formule |
|---------|--------|---------|
| Thématiques | 0-40 | `min(nb_themes * 8, 40)` |
| Signaux | 0-25 | `min(nb_signals * 8, 25)` |
| Mots-clés custom | 0-20 | `min(sum(count * 3), 20)` |
| Mots-clés hooks | 0-10 | `min(nb_hook_keywords * 3, 10)` |
| Activité | 0-5 | Selon nb de tweets |

### Thématiques détectées

```python
THEMES = {
    'copywriting': ['copy', 'copywriting', 'rédaction', 'écriture', ...],
    'marketing': ['marketing', 'growth', 'acquisition', 'conversion', ...],
    'business': ['business', 'entrepreneur', 'startup', 'vente', ...],
    'content_creation': ['créateur', 'contenu', 'audience', ...],
    'ecommerce': ['ecommerce', 'boutique', 'shopify', ...]
}
```

### Signaux d'intention

```python
INTENT_SIGNALS = {
    'needs_help': ['besoin', 'cherche', 'recherche', 'galère', ...],
    'selling': ['vendre', 'vente', 'offre', 'promo', ...],
    'improving': ['améliorer', 'optimiser', 'booster', ...],
    'creating': ['créer', 'lancer', 'démarrer', 'nouveau', ...]
}
```

---

## API Endpoints

### POST /analyze

Analyse un lot de profils.

**Request body :**
```json
{
  "profiles": [
    {
      "username": "@username",
      "bio": "Bio text...",
      "tweets": "Tweet 1\nTweet 2\nTweet 3"
    }
  ],
  "keywords": ["keyword1", "keyword2"],
  "language": "fr",
  "min_activity": 1
}
```

**Response :**
```json
{
  "success": true,
  "results": [
    {
      "username": "@username",
      "score": 85.5,
      "themes": ["copywriting (3 mentions)", ...],
      "signals": ["Recherche d'aide (2 mentions)", ...],
      "keyword_matches": {"keyword1": 2},
      "activity_level": "Actif (5 tweets)",
      "explanation": "🎯 TRÈS PERTINENT | ..."
    }
  ],
  "total_analyzed": 1
}
```

### GET /export/csv

Exporte les résultats en CSV.

**Response :** Fichier CSV avec colonnes :
- Username
- Score
- Niveau
- Thématiques
- Signaux
- Mots-clés trouvés
- Activité
- Explication

### GET /export/json

Exporte les résultats en JSON structuré.

---

## Classes principales

### Profile

```python
@dataclass
class Profile:
    username: str
    bio: str
    tweets: List[str]

    def get_all_text(self) -> str:
        """Retourne tout le texte du profil concaténé"""
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    username: str
    score: float
    themes: List[str]
    signals: List[str]
    explanation: str
    keyword_matches: Dict[str, int]
    activity_level: str
```

### ProfileAnalyzer

```python
class ProfileAnalyzer:
    def __init__(self, custom_keywords: List[str],
                 language: str, min_activity: int):
        """Initialise l'analyseur"""

    def analyze_profile(self, profile: Profile) -> AnalysisResult:
        """Analyse un profil unique"""

    def analyze_batch(self, profiles: List[Profile]) -> List[AnalysisResult]:
        """Analyse un lot de profils"""

    def _calculate_score(self, ...) -> float:
        """Calcule le score de pertinence (0-100)"""
```

---

## Personnalisation avancée

### 1. Ajouter une nouvelle thématique

Éditez `analyzer.py` :

```python
THEMES = {
    'copywriting': [...],
    'marketing': [...],
    'votre_theme': ['mot1', 'mot2', 'mot3', ...]  # Ajoutez ici
}
```

### 2. Modifier les pondérations

Éditez la méthode `_calculate_score()` dans `analyzer.py` :

```python
def _calculate_score(self, themes, signals, ...):
    score = 0.0

    # Modifier ces valeurs
    theme_score = len(themes) * 8  # Changez 8 par votre valeur
    signal_score = len(signals) * 8  # Changez 8 par votre valeur
    # etc.
```

### 3. Ajuster les seuils d'interprétation

Éditez `_generate_explanation()` dans `analyzer.py` :

```python
if score >= 70:  # Modifier ce seuil
    parts.append("🎯 TRÈS PERTINENT")
elif score >= 50:  # Modifier ce seuil
    parts.append("✅ PERTINENT")
# etc.
```

### 4. Changer l'apparence de l'interface

Éditez les styles CSS dans `templates/index.html` :

```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Modifier les couleurs */
}
```

---

## Tests

### Lancer les tests automatiques

```bash
python test_analyzer.py
```

### Tests manuels via l'interface

1. Charger l'exemple pré-rempli
2. Vérifier que les scores sont cohérents
3. Tester l'export CSV et JSON

### Tests unitaires recommandés

```python
def test_profile_creation():
    profile = Profile("@test", "Bio", ["Tweet"])
    assert profile.username == "@test"

def test_scoring_bounds():
    analyzer = ProfileAnalyzer([], "fr", 1)
    # Le score doit être entre 0 et 100

def test_theme_detection():
    # Vérifier que les thématiques sont correctement détectées
```

---

## Performance

### Capacité recommandée
- **Optimal :** 10-20 profils par analyse
- **Maximum testé :** 100 profils
- **Temps moyen :** ~0.1 seconde par profil

### Optimisations possibles

1. **Cache des résultats**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def analyze_profile(self, profile: Profile):
    ...
```

2. **Traitement parallèle**
```python
from concurrent.futures import ThreadPoolExecutor

def analyze_batch(self, profiles):
    with ThreadPoolExecutor() as executor:
        return list(executor.map(self.analyze_profile, profiles))
```

3. **Utiliser NLTK pour analyse NLP avancée**
```python
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
```

---

## Sécurité

### Considérations

✅ **Pas de stockage persistant** : Données en mémoire uniquement
✅ **Pas d'exécution de code** : Pas d'eval() ou exec()
✅ **Pas de SQL** : Pas de base de données
✅ **Input validation** : Vérification des données entrantes

### Recommandations pour production

⚠️ **Ne PAS utiliser en production sans :**
- Rate limiting sur l'API
- Authentification/autorisation
- HTTPS/SSL
- Logging approprié
- Gestion d'erreurs robuste

---

## Roadmap / Améliorations futures

### Version 1.1
- [ ] Support multilingue (anglais, espagnol)
- [ ] Analyse de sentiment
- [ ] Détection de mots-clés avec synonymes

### Version 1.2
- [ ] Machine Learning pour scoring intelligent
- [ ] Historique des analyses
- [ ] Comparaison de profils

### Version 2.0
- [ ] API REST complète
- [ ] Dashboard analytics
- [ ] Export PDF

---

## Dépendances

### Production
```
Flask==3.0.0
Werkzeug==3.0.1
```

### Développement (optionnel)
```
pytest==7.4.0           # Tests
black==23.0.0           # Formatage
pylint==2.17.0          # Linting
```

---

## Troubleshooting

### "Port 5000 already in use"

**Solution 1 :** Changer le port
```python
# Dans app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Solution 2 :** Tuer le processus
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### "Template not found"

Vérifier la structure :
```
x-profile-analyzer/
├── app.py
└── templates/
    └── index.html
```

### "Module not found"

```bash
pip install -r requirements.txt --upgrade
```

---

## License

Usage personnel uniquement. Non destiné à un usage commercial.

---

## Contributions

Le code est ouvert aux améliorations !

**Comment contribuer :**
1. Fork le projet
2. Créez une branche pour votre feature
3. Committez vos changements
4. Testez avec `test_analyzer.py`
5. Soumettez une pull request

---

**Version :** 1.0.0
**Dernière mise à jour :** Janvier 2026
