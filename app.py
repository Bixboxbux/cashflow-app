"""
WebAudit Pro - Website Audit Tool for Conversion & SEO
A micro-SaaS MVP for automated website analysis
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
import json

app = Flask(__name__)
CORS(app)

# Configuration
FREE_TIER_LIMIT = 3  # Analyses gratuites par session
TIMEOUT = 10

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
        """Récupère la page avec mesure du temps de chargement"""
        try:
            start_time = time.time()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            self.response = requests.get(self.url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            self.load_time = time.time() - start_time
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
            return True
        except requests.exceptions.RequestException as e:
            self.results['error'] = f"Impossible d'accéder au site: {str(e)}"
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
