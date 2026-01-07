"""
WebAudit Pro - Website Audit Tool for Conversion & SEO
A micro-SaaS MVP for automated website analysis
"""

from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
import json
import random
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
FREE_TIER_LIMIT = 3  # Analyses gratuites par session
TIMEOUT_CONNECT = 5   # Timeout de connexion (secondes)
TIMEOUT_READ = 15     # Timeout de lecture (secondes)
MAX_RETRIES = 2       # Nombre de tentatives en cas d'échec

# Stripe Configuration (à remplacer par vos vraies clés)
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_XXXXXX')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_XXXXXX')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_XXXXXX')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID', 'price_XXXXXX')  # ID du prix Pro à 29€/mois

# Base URL pour les redirections Stripe
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'webaudit.db')


# ========================================
# Database Setup
# ========================================

def init_db():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table des leads (emails collectés via exit-intent)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'exit_intent',
            audit_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table des abonnés Pro (après paiement Stripe)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            plan TEXT DEFAULT 'pro',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table des demandes de contact Agence
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            agency TEXT,
            clients TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Initialiser la DB au démarrage
init_db()


def get_db():
    """Retourne une connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_pro_user(email):
    """Vérifie si un utilisateur est abonné Pro"""
    if not email:
        return False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM subscribers WHERE email = ? AND status = ?',
        (email.lower(), 'active')
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Pool de User-Agents réalistes (navigateurs modernes)
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Linux
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Langues acceptées pour les headers
ACCEPT_LANGUAGES = [
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr,en-US;q=0.9,en;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
]


def get_random_headers():
    """Génère des headers HTTP réalistes avec rotation de User-Agent"""
    user_agent = random.choice(USER_AGENTS)
    accept_language = random.choice(ACCEPT_LANGUAGES)

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    # Ajouter des headers spécifiques à Chrome si c'est un UA Chrome
    if "Chrome" in user_agent and "Edg" not in user_agent:
        headers["Sec-Ch-Ua"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        headers["Sec-Ch-Ua-Mobile"] = "?0"
        headers["Sec-Ch-Ua-Platform"] = '"Windows"' if "Windows" in user_agent else '"macOS"'

    return headers

class WebsiteAnalyzer:
    """Analyse complète d'un site web pour SEO et conversion"""

    def __init__(self, url):
        self.url = self._normalize_url(url)
        self.soup = None
        self.response = None
        self.load_time = 0
        self.results = {
            'url': self.url,
            'scores': {},
            'details': {},
            'recommendations': [],
            'global_score': 0
        }

    def _normalize_url(self, url):
        """Normalise l'URL avec https si nécessaire"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')

    def fetch_page(self):
        """Récupère la page avec mesure du temps de chargement, retry et rotation de User-Agent"""
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                # Obtenir des headers aléatoires à chaque tentative
                headers = get_random_headers()

                # Créer une session pour gérer les cookies
                session = requests.Session()

                start_time = time.time()

                # Timeout séparé pour connexion et lecture
                self.response = session.get(
                    self.url,
                    headers=headers,
                    timeout=(TIMEOUT_CONNECT, TIMEOUT_READ),
                    allow_redirects=True,
                    verify=True  # Vérification SSL
                )

                self.load_time = time.time() - start_time

                # Vérifier le code de statut HTTP
                if self.response.status_code >= 400:
                    if self.response.status_code == 403:
                        # Accès refusé - essayer avec un autre User-Agent
                        if attempt < MAX_RETRIES:
                            time.sleep(0.5 * (attempt + 1))  # Backoff progressif
                            continue
                        self.results['error'] = "Accès refusé par le site (403)"
                        return False
                    elif self.response.status_code == 404:
                        self.results['error'] = "Page non trouvée (404)"
                        return False
                    elif self.response.status_code >= 500:
                        if attempt < MAX_RETRIES:
                            time.sleep(1 * (attempt + 1))
                            continue
                        self.results['error'] = f"Erreur serveur ({self.response.status_code})"
                        return False

                # Parser le HTML
                self.soup = BeautifulSoup(self.response.text, 'html.parser')

                # Stocker les infos de la requête pour debug
                self.results['request_info'] = {
                    'status_code': self.response.status_code,
                    'final_url': self.response.url,
                    'attempts': attempt + 1
                }

                return True

            except requests.exceptions.ConnectTimeout:
                last_error = "Timeout de connexion - le serveur ne répond pas"
                if attempt < MAX_RETRIES:
                    time.sleep(1 * (attempt + 1))
                    continue

            except requests.exceptions.ReadTimeout:
                last_error = "Timeout de lecture - la page met trop de temps à charger"
                if attempt < MAX_RETRIES:
                    time.sleep(1 * (attempt + 1))
                    continue

            except requests.exceptions.SSLError:
                last_error = "Erreur SSL - certificat invalide ou expiré"
                # Pas de retry pour les erreurs SSL
                break

            except requests.exceptions.TooManyRedirects:
                last_error = "Trop de redirections - possible boucle de redirection"
                break

            except requests.exceptions.ConnectionError:
                last_error = "Erreur de connexion - vérifiez l'URL"
                if attempt < MAX_RETRIES:
                    time.sleep(1 * (attempt + 1))
                    continue

            except requests.exceptions.RequestException as e:
                last_error = f"Erreur réseau: {str(e)}"
                if attempt < MAX_RETRIES:
                    time.sleep(0.5 * (attempt + 1))
                    continue

        # Toutes les tentatives ont échoué
        self.results['error'] = f"Impossible d'accéder au site: {last_error}"
        return False

    def analyze_speed(self):
        """Analyse la vitesse perçue"""
        score = 100
        details = {
            'load_time': round(self.load_time, 2),
            'page_size': len(self.response.content) / 1024,  # KB
            'issues': []
        }

        # Pénalités basées sur le temps de chargement
        if self.load_time > 1:
            score -= 10
        if self.load_time > 2:
            score -= 20
        if self.load_time > 3:
            score -= 20
            details['issues'].append("Temps de chargement élevé (>3s)")

        # Pénalités basées sur la taille
        page_size_kb = details['page_size']
        if page_size_kb > 500:
            score -= 10
            details['issues'].append("Page trop lourde (>500KB)")
        if page_size_kb > 1000:
            score -= 15
            details['issues'].append("Page très lourde (>1MB)")

        # Analyse des images sans lazy loading
        images = self.soup.find_all('img')
        images_without_lazy = [img for img in images if not img.get('loading') == 'lazy']
        if len(images_without_lazy) > 5:
            score -= 10
            details['issues'].append(f"{len(images_without_lazy)} images sans lazy loading")

        details['image_count'] = len(images)
        self.results['scores']['speed'] = max(0, score)
        self.results['details']['speed'] = details

        if score < 70:
            self.results['recommendations'].append({
                'category': 'Vitesse',
                'priority': 'haute',
                'issue': 'Performance de chargement insuffisante',
                'action': 'Optimisez les images, activez le lazy loading, et réduisez le poids de la page.',
                'premium': False
            })

    def analyze_seo(self):
        """Analyse SEO de base"""
        score = 100
        details = {
            'title': None,
            'meta_description': None,
            'h1_count': 0,
            'h2_count': 0,
            'canonical': None,
            'issues': []
        }

        # Title
        title_tag = self.soup.find('title')
        if title_tag:
            details['title'] = title_tag.text.strip()
            title_len = len(details['title'])
            if title_len < 30:
                score -= 10
                details['issues'].append("Titre trop court (<30 caractères)")
            elif title_len > 60:
                score -= 5
                details['issues'].append("Titre trop long (>60 caractères)")
        else:
            score -= 25
            details['issues'].append("Pas de balise title")

        # Meta description
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            details['meta_description'] = meta_desc['content']
            desc_len = len(details['meta_description'])
            if desc_len < 120:
                score -= 10
                details['issues'].append("Meta description trop courte")
            elif desc_len > 160:
                score -= 5
                details['issues'].append("Meta description trop longue")
        else:
            score -= 20
            details['issues'].append("Pas de meta description")

        # H1
        h1_tags = self.soup.find_all('h1')
        details['h1_count'] = len(h1_tags)
        if len(h1_tags) == 0:
            score -= 15
            details['issues'].append("Pas de balise H1")
        elif len(h1_tags) > 1:
            score -= 10
            details['issues'].append(f"Plusieurs balises H1 ({len(h1_tags)})")

        # H2
        h2_tags = self.soup.find_all('h2')
        details['h2_count'] = len(h2_tags)
        if len(h2_tags) == 0:
            score -= 5
            details['issues'].append("Pas de balises H2")

        # Canonical
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            details['canonical'] = canonical.get('href')
        else:
            score -= 5
            details['issues'].append("Pas de balise canonical")

        # Open Graph
        og_title = self.soup.find('meta', property='og:title')
        og_desc = self.soup.find('meta', property='og:description')
        og_image = self.soup.find('meta', property='og:image')

        details['open_graph'] = {
            'title': bool(og_title),
            'description': bool(og_desc),
            'image': bool(og_image)
        }

        if not all([og_title, og_desc, og_image]):
            score -= 5
            details['issues'].append("Open Graph incomplet")

        # Alt text on images
        images = self.soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        if images_without_alt:
            score -= min(10, len(images_without_alt) * 2)
            details['issues'].append(f"{len(images_without_alt)} images sans attribut alt")

        self.results['scores']['seo'] = max(0, score)
        self.results['details']['seo'] = details

        if score < 70:
            self.results['recommendations'].append({
                'category': 'SEO',
                'priority': 'haute',
                'issue': 'Optimisation SEO insuffisante',
                'action': 'Ajoutez un titre optimisé, une meta description attractive et structurez vos titres H1/H2.',
                'premium': False
            })

    def analyze_conversion(self):
        """Analyse des éléments de conversion (CTA, formulaires)"""
        score = 100
        details = {
            'cta_buttons': [],
            'forms': 0,
            'social_proof': False,
            'contact_info': False,
            'issues': []
        }

        # Recherche des CTA
        cta_keywords = ['acheter', 'commander', 'inscription', 'essayer', 'démarrer',
                       'obtenir', 'télécharger', 'contact', 'devis', 'buy', 'order',
                       'sign up', 'try', 'start', 'get', 'download', 'free', 'gratuit']

        buttons = self.soup.find_all(['button', 'a'])
        cta_found = []
        for btn in buttons:
            btn_text = btn.get_text().lower().strip()
            btn_class = ' '.join(btn.get('class', []))
            if any(kw in btn_text for kw in cta_keywords) or 'cta' in btn_class.lower() or 'btn' in btn_class.lower():
                if btn_text and len(btn_text) < 50:
                    cta_found.append(btn_text[:30])

        details['cta_buttons'] = list(set(cta_found))[:5]

        if len(cta_found) == 0:
            score -= 30
            details['issues'].append("Aucun CTA visible détecté")
        elif len(cta_found) < 2:
            score -= 10
            details['issues'].append("Peu de CTA sur la page")

        # Formulaires
        forms = self.soup.find_all('form')
        details['forms'] = len(forms)
        if len(forms) == 0:
            score -= 10
            details['issues'].append("Aucun formulaire de capture")

        # Social proof (témoignages, avis)
        social_keywords = ['témoignage', 'avis', 'client', 'review', 'testimonial', 'rating', 'étoile', 'star']
        page_text = self.soup.get_text().lower()
        if any(kw in page_text for kw in social_keywords):
            details['social_proof'] = True
        else:
            score -= 10
            details['issues'].append("Pas de preuve sociale visible")

        # Contact info
        contact_patterns = [
            r'\b[\w.-]+@[\w.-]+\.\w+\b',  # Email
            r'\b\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b',  # Phone FR
            r'\b\+\d{1,3}[\s.-]?\d+\b'  # International phone
        ]
        for pattern in contact_patterns:
            if re.search(pattern, page_text):
                details['contact_info'] = True
                break

        if not details['contact_info']:
            score -= 5
            details['issues'].append("Pas d'informations de contact visibles")

        self.results['scores']['conversion'] = max(0, score)
        self.results['details']['conversion'] = details

        if score < 70:
            self.results['recommendations'].append({
                'category': 'Conversion',
                'priority': 'haute',
                'issue': 'Potentiel de conversion faible',
                'action': 'Ajoutez des CTA clairs, un formulaire de capture et des témoignages clients.',
                'premium': False
            })

    def analyze_mobile(self):
        """Analyse de la compatibilité mobile"""
        score = 100
        details = {
            'viewport': False,
            'responsive_meta': False,
            'touch_friendly': True,
            'issues': []
        }

        # Viewport meta tag
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            details['viewport'] = True
            content = viewport.get('content', '')
            if 'width=device-width' in content:
                details['responsive_meta'] = True
            else:
                score -= 15
                details['issues'].append("Viewport mal configuré")
        else:
            score -= 30
            details['issues'].append("Pas de balise viewport")

        # Check for fixed widths (simple heuristic)
        styles = self.soup.find_all('style')
        inline_styles = str(self.soup)
        fixed_width_pattern = r'width:\s*\d{4,}px'
        if re.search(fixed_width_pattern, inline_styles):
            score -= 15
            details['issues'].append("Largeurs fixes détectées (problème responsive)")

        # Check for small touch targets (buttons, links)
        small_font_pattern = r'font-size:\s*(\d+)px'
        matches = re.findall(small_font_pattern, inline_styles)
        small_fonts = [int(m) for m in matches if int(m) < 14]
        if len(small_fonts) > 3:
            score -= 10
            details['issues'].append("Textes trop petits pour mobile")

        self.results['scores']['mobile'] = max(0, score)
        self.results['details']['mobile'] = details

        if score < 70:
            self.results['recommendations'].append({
                'category': 'Mobile',
                'priority': 'moyenne',
                'issue': 'Compatibilité mobile à améliorer',
                'action': 'Ajoutez une balise viewport et utilisez des tailles relatives (%, rem).',
                'premium': False
            })

    def analyze_security(self):
        """Analyse de sécurité basique"""
        score = 100
        details = {
            'https': False,
            'issues': []
        }

        # HTTPS
        if self.url.startswith('https://'):
            details['https'] = True
        else:
            score -= 40
            details['issues'].append("Site non sécurisé (HTTP)")

        # Check for mixed content hints
        if details['https']:
            http_resources = self.soup.find_all(src=re.compile(r'^http://'))
            http_resources += self.soup.find_all(href=re.compile(r'^http://'))
            if http_resources:
                score -= 20
                details['issues'].append("Contenu mixte détecté (HTTP dans HTTPS)")

        self.results['scores']['security'] = max(0, score)
        self.results['details']['security'] = details

        if score < 70:
            self.results['recommendations'].append({
                'category': 'Sécurité',
                'priority': 'haute',
                'issue': 'Problèmes de sécurité détectés',
                'action': 'Passez votre site en HTTPS et éliminez le contenu mixte.',
                'premium': False
            })

    def add_premium_recommendations(self):
        """Ajoute des recommandations premium (teaser)"""
        premium_recs = [
            {
                'category': 'SEO Avancé',
                'priority': 'moyenne',
                'issue': 'Analyse des backlinks et autorité de domaine',
                'action': 'Débloquez l\'analyse complète des backlinks et du profil de liens.',
                'premium': True
            },
            {
                'category': 'Conversion Avancée',
                'priority': 'moyenne',
                'issue': 'Heatmap et analyse comportementale',
                'action': 'Obtenez une analyse du parcours utilisateur et des points de friction.',
                'premium': True
            },
            {
                'category': 'Concurrence',
                'priority': 'moyenne',
                'issue': 'Benchmark concurrentiel',
                'action': 'Comparez vos performances à celles de vos concurrents directs.',
                'premium': True
            },
            {
                'category': 'Contenu',
                'priority': 'basse',
                'issue': 'Analyse sémantique et mots-clés',
                'action': 'Identifiez les opportunités de mots-clés et optimisez votre contenu.',
                'premium': True
            }
        ]
        self.results['recommendations'].extend(premium_recs)

    def calculate_global_score(self):
        """Calcule le score global pondéré"""
        weights = {
            'seo': 0.30,
            'conversion': 0.25,
            'speed': 0.20,
            'mobile': 0.15,
            'security': 0.10
        }

        total = 0
        for key, weight in weights.items():
            if key in self.results['scores']:
                total += self.results['scores'][key] * weight

        self.results['global_score'] = round(total)

        # Grade
        if total >= 90:
            self.results['grade'] = 'A'
        elif total >= 80:
            self.results['grade'] = 'B'
        elif total >= 70:
            self.results['grade'] = 'C'
        elif total >= 60:
            self.results['grade'] = 'D'
        else:
            self.results['grade'] = 'F'

    def run_full_analysis(self):
        """Exécute l'analyse complète"""
        if not self.fetch_page():
            return self.results

        self.analyze_speed()
        self.analyze_seo()
        self.analyze_conversion()
        self.analyze_mobile()
        self.analyze_security()
        self.calculate_global_score()
        self.add_premium_recommendations()

        return self.results


@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Endpoint d'analyse"""
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL requise'}), 400

    # Validation basique de l'URL
    try:
        parsed = urlparse(url if url.startswith('http') else 'https://' + url)
        if not parsed.netloc:
            return jsonify({'error': 'URL invalide'}), 400
    except Exception:
        return jsonify({'error': 'URL invalide'}), 400

    analyzer = WebsiteAnalyzer(url)
    results = analyzer.run_full_analysis()

    return jsonify(results)


@app.route('/api/export', methods=['POST'])
def export_report():
    """Génère un rapport texte structuré"""
    data = request.get_json()
    results = data.get('results', {})

    if not results:
        return jsonify({'error': 'Pas de résultats à exporter'}), 400

    report = generate_text_report(results)
    return jsonify({'report': report})


def generate_text_report(results):
    """Génère un rapport texte structuré"""
    report = []
    report.append("=" * 60)
    report.append("RAPPORT D'AUDIT WEBAUDIT PRO")
    report.append("=" * 60)
    report.append("")
    report.append(f"URL analysée: {results.get('url', 'N/A')}")
    report.append(f"Score global: {results.get('global_score', 0)}/100 (Grade: {results.get('grade', 'N/A')})")
    report.append("")
    report.append("-" * 60)
    report.append("SCORES PAR CATÉGORIE")
    report.append("-" * 60)

    scores = results.get('scores', {})
    categories = {
        'seo': 'SEO',
        'conversion': 'Conversion',
        'speed': 'Vitesse',
        'mobile': 'Mobile',
        'security': 'Sécurité'
    }

    for key, label in categories.items():
        score = scores.get(key, 0)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        report.append(f"{label:15} [{bar}] {score}/100")

    report.append("")
    report.append("-" * 60)
    report.append("PROBLÈMES DÉTECTÉS")
    report.append("-" * 60)

    details = results.get('details', {})
    for category, data in details.items():
        issues = data.get('issues', [])
        if issues:
            report.append(f"\n{categories.get(category, category).upper()}:")
            for issue in issues:
                report.append(f"  • {issue}")

    report.append("")
    report.append("-" * 60)
    report.append("RECOMMANDATIONS")
    report.append("-" * 60)

    recommendations = results.get('recommendations', [])
    free_recs = [r for r in recommendations if not r.get('premium')]
    premium_recs = [r for r in recommendations if r.get('premium')]

    if free_recs:
        report.append("\nACTIONS PRIORITAIRES:")
        for i, rec in enumerate(free_recs, 1):
            report.append(f"\n{i}. [{rec['priority'].upper()}] {rec['category']}")
            report.append(f"   Problème: {rec['issue']}")
            report.append(f"   Action: {rec['action']}")

    if premium_recs:
        report.append("\n" + "-" * 60)
        report.append("ANALYSES PREMIUM (débloquer avec l'offre Pro)")
        report.append("-" * 60)
        for rec in premium_recs:
            report.append(f"  🔒 {rec['category']}: {rec['issue']}")

    report.append("")
    report.append("=" * 60)
    report.append("Rapport généré par WebAudit Pro")
    report.append("Passez à la version Pro pour un audit complet!")
    report.append("=" * 60)

    return "\n".join(report)


# ========================================
# Stripe Checkout Endpoints
# ========================================

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Crée une session Stripe Checkout pour le plan Pro"""
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        data = request.get_json() or {}
        email = data.get('email', '')

        # Créer la session Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=BASE_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=BASE_URL + '/#pricing',
            customer_email=email if email else None,
            metadata={
                'plan': 'pro'
            }
        )

        return jsonify({'url': checkout_session.url})

    except ImportError:
        # Stripe non installé - mode simulation
        return jsonify({
            'url': BASE_URL + '/success?session_id=simulated_session',
            'simulated': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/success')
def checkout_success():
    """Page de succès après paiement Stripe"""
    session_id = request.args.get('session_id')

    # En production, vérifier la session avec Stripe
    # et activer l'abonnement dans la base de données

    return render_template('success.html', session_id=session_id)


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour gérer les événements de paiement"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        # Gérer les différents types d'événements
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_completed(session)

        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_cancelled(subscription)

        return jsonify({'status': 'success'})

    except ImportError:
        return jsonify({'status': 'stripe not installed'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def handle_checkout_completed(session):
    """Traite un paiement réussi"""
    email = session.get('customer_email') or session.get('customer_details', {}).get('email')
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')

    if email:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO subscribers (email, stripe_customer_id, stripe_subscription_id, plan, status)
                VALUES (?, ?, ?, 'pro', 'active')
                ON CONFLICT(email) DO UPDATE SET
                    stripe_customer_id = ?,
                    stripe_subscription_id = ?,
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
            ''', (email.lower(), customer_id, subscription_id, customer_id, subscription_id))
            conn.commit()
        finally:
            conn.close()


def handle_subscription_cancelled(subscription):
    """Traite une annulation d'abonnement"""
    subscription_id = subscription.get('id')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE subscribers SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = ?
        ''', (subscription_id,))
        conn.commit()
    finally:
        conn.close()


# ========================================
# Email Collection Endpoints
# ========================================

@app.route('/api/subscribe-email', methods=['POST'])
def subscribe_email():
    """Enregistre un email (exit-intent popup)"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    source = data.get('source', 'exit_intent')
    audit_url = data.get('audit_url', '')

    if not email or '@' not in email:
        return jsonify({'error': 'Email invalide'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO leads (email, source, audit_url)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                audit_url = COALESCE(?, audit_url),
                created_at = created_at
        ''', (email, source, audit_url, audit_url))
        conn.commit()
        return jsonify({'success': True, 'message': 'Email enregistré'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/contact-agency', methods=['POST'])
def contact_agency():
    """Enregistre une demande de contact Agence"""
    data = request.get_json()

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    agency = data.get('agency', '').strip()
    clients = data.get('clients', '')
    message = data.get('message', '')

    if not name or not email:
        return jsonify({'error': 'Nom et email requis'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO agency_contacts (name, email, agency, clients, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, agency, clients, message))
        conn.commit()
        return jsonify({'success': True, 'message': 'Demande enregistrée'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/check-pro', methods=['POST'])
def check_pro_status():
    """Vérifie si un utilisateur est abonné Pro"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'is_pro': False})

    return jsonify({'is_pro': is_pro_user(email)})


@app.route('/api/config')
def get_config():
    """Retourne la configuration publique (clé Stripe publishable)"""
    return jsonify({
        'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY,
        'ga_measurement_id': 'G-XXXXXX'  # À remplacer par votre ID GA4
    })


# ========================================
# Email Collection with JSON Storage
# ========================================

EMAILS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'emails.json')


def load_emails():
    """Charge les emails depuis le fichier JSON"""
    if os.path.exists(EMAILS_FILE):
        try:
            with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_emails(emails):
    """Sauvegarde les emails dans le fichier JSON"""
    # Créer le dossier data si nécessaire
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Enregistre un email avec le plan choisi dans data/emails.json"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    plan = data.get('plan', 'pro')
    name = data.get('name', '')
    agency = data.get('agency', '')
    clients = data.get('clients', '')
    message = data.get('message', '')

    # Validation de l'email
    if not email or '@' not in email or '.' not in email:
        return jsonify({'error': 'Email invalide'}), 400

    # Charger les emails existants
    emails = load_emails()

    # Vérifier si l'email existe déjà
    existing = next((e for e in emails if e.get('email') == email), None)

    if existing:
        # Mettre à jour les informations
        existing['plan'] = plan
        existing['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if name:
            existing['name'] = name
        if agency:
            existing['agency'] = agency
        if clients:
            existing['clients'] = clients
        if message:
            existing['message'] = message
    else:
        # Ajouter un nouvel email
        new_entry = {
            'email': email,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'plan': plan
        }
        if name:
            new_entry['name'] = name
        if agency:
            new_entry['agency'] = agency
        if clients:
            new_entry['clients'] = clients
        if message:
            new_entry['message'] = message
        emails.append(new_entry)

    # Sauvegarder
    save_emails(emails)

    return jsonify({
        'success': True,
        'message': 'Email enregistré avec succès'
    })


@app.route('/api/admin/emails', methods=['GET'])
def get_all_emails():
    """Retourne la liste de tous les emails collectés"""
    emails = load_emails()
    return jsonify({
        'count': len(emails),
        'emails': emails
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
