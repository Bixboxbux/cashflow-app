"""
Website Audit Tool - Backend API
Analyse SEO, conversion et performance d'un site web
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse, urljoin
import validators

app = Flask(__name__)
CORS(app)

# Configuration
REQUEST_TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def fetch_page(url):
    """Récupère le contenu d'une page web"""
    headers = {'User-Agent': USER_AGENT}
    start_time = time.time()

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        load_time = time.time() - start_time
        return {
            'success': True,
            'html': response.text,
            'status_code': response.status_code,
            'load_time': round(load_time, 2),
            'final_url': response.url,
            'headers': dict(response.headers)
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout - Le site met trop de temps à répondre'}
    except requests.exceptions.SSLError:
        return {'success': False, 'error': 'Erreur SSL - Problème de certificat'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Impossible de se connecter au site'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def analyze_seo(soup, url):
    """Analyse SEO de base"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'successes': [],
        'details': {}
    }

    # Title
    title = soup.find('title')
    title_text = title.get_text().strip() if title else ''
    results['details']['title'] = title_text

    if not title_text:
        results['issues'].append({
            'type': 'critical',
            'message': 'Balise <title> manquante',
            'recommendation': 'Ajoutez un titre unique de 50-60 caractères décrivant votre page'
        })
    elif len(title_text) < 30:
        results['issues'].append({
            'type': 'warning',
            'message': f'Titre trop court ({len(title_text)} caractères)',
            'recommendation': 'Optimisez votre titre entre 50-60 caractères pour un meilleur SEO'
        })
        results['score'] += 5
    elif len(title_text) > 70:
        results['issues'].append({
            'type': 'warning',
            'message': f'Titre trop long ({len(title_text)} caractères)',
            'recommendation': 'Réduisez votre titre à 60 caractères max pour éviter la troncature sur Google'
        })
        results['score'] += 5
    else:
        results['successes'].append('Titre optimisé ✓')
        results['score'] += 15

    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    desc_text = meta_desc.get('content', '').strip() if meta_desc else ''
    results['details']['meta_description'] = desc_text

    if not desc_text:
        results['issues'].append({
            'type': 'critical',
            'message': 'Meta description manquante',
            'recommendation': 'Ajoutez une meta description de 150-160 caractères avec vos mots-clés principaux'
        })
    elif len(desc_text) < 120:
        results['issues'].append({
            'type': 'warning',
            'message': f'Meta description trop courte ({len(desc_text)} caractères)',
            'recommendation': 'Développez votre description à 150-160 caractères'
        })
        results['score'] += 5
    elif len(desc_text) > 170:
        results['issues'].append({
            'type': 'warning',
            'message': f'Meta description trop longue ({len(desc_text)} caractères)',
            'recommendation': 'Réduisez à 160 caractères pour éviter la troncature'
        })
        results['score'] += 5
    else:
        results['successes'].append('Meta description optimisée ✓')
        results['score'] += 15

    # H1
    h1_tags = soup.find_all('h1')
    results['details']['h1_count'] = len(h1_tags)
    results['details']['h1_texts'] = [h1.get_text().strip()[:100] for h1 in h1_tags]

    if len(h1_tags) == 0:
        results['issues'].append({
            'type': 'critical',
            'message': 'Aucune balise H1 trouvée',
            'recommendation': 'Ajoutez un H1 unique décrivant le contenu principal de la page'
        })
    elif len(h1_tags) > 1:
        results['issues'].append({
            'type': 'warning',
            'message': f'{len(h1_tags)} balises H1 trouvées',
            'recommendation': 'Gardez un seul H1 par page pour une structure SEO optimale'
        })
        results['score'] += 5
    else:
        results['successes'].append('Structure H1 correcte ✓')
        results['score'] += 15

    # Structure des headings
    h2_tags = soup.find_all('h2')
    h3_tags = soup.find_all('h3')
    results['details']['h2_count'] = len(h2_tags)
    results['details']['h3_count'] = len(h3_tags)

    if len(h2_tags) == 0:
        results['issues'].append({
            'type': 'warning',
            'message': 'Aucune balise H2 trouvée',
            'recommendation': 'Structurez votre contenu avec des H2 pour améliorer la lisibilité'
        })
    else:
        results['successes'].append(f'{len(h2_tags)} balises H2 ✓')
        results['score'] += 10

    # Images alt
    images = soup.find_all('img')
    images_without_alt = [img for img in images if not img.get('alt')]
    results['details']['total_images'] = len(images)
    results['details']['images_without_alt'] = len(images_without_alt)

    if len(images) > 0:
        if len(images_without_alt) > 0:
            results['issues'].append({
                'type': 'warning',
                'message': f'{len(images_without_alt)}/{len(images)} images sans attribut alt',
                'recommendation': 'Ajoutez des descriptions alt à toutes vos images pour le SEO et l\'accessibilité'
            })
            results['score'] += 5
        else:
            results['successes'].append('Toutes les images ont un alt ✓')
            results['score'] += 10

    # Meta robots
    robots = soup.find('meta', attrs={'name': 'robots'})
    if robots:
        content = robots.get('content', '').lower()
        if 'noindex' in content:
            results['issues'].append({
                'type': 'critical',
                'message': 'Page marquée noindex',
                'recommendation': 'Cette page ne sera pas indexée par Google. Retirez noindex si nécessaire.'
            })
        else:
            results['score'] += 5

    # Canonical
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if canonical:
        results['successes'].append('Balise canonical présente ✓')
        results['details']['canonical'] = canonical.get('href', '')
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Pas de balise canonical',
            'recommendation': 'Ajoutez une balise canonical pour éviter le contenu dupliqué'
        })

    # Open Graph
    og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
    if len(og_tags) >= 3:
        results['successes'].append('Open Graph configuré ✓')
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Open Graph incomplet ou manquant',
            'recommendation': 'Ajoutez og:title, og:description, og:image pour un meilleur partage social'
        })

    # Schema.org
    schema = soup.find_all('script', attrs={'type': 'application/ld+json'})
    if schema:
        results['successes'].append('Données structurées Schema.org présentes ✓')
        results['score'] += 5
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Pas de données structurées Schema.org',
            'recommendation': 'Ajoutez du JSON-LD pour enrichir vos résultats Google'
        })

    return results


def analyze_performance(load_time, html, headers):
    """Analyse de performance basique"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'successes': [],
        'details': {}
    }

    # Temps de chargement
    results['details']['load_time'] = load_time

    if load_time < 1:
        results['successes'].append(f'Excellent temps de réponse ({load_time}s) ✓')
        results['score'] += 30
    elif load_time < 2:
        results['successes'].append(f'Bon temps de réponse ({load_time}s) ✓')
        results['score'] += 20
    elif load_time < 4:
        results['issues'].append({
            'type': 'warning',
            'message': f'Temps de réponse moyen ({load_time}s)',
            'recommendation': 'Optimisez votre serveur et activez la mise en cache'
        })
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'critical',
            'message': f'Temps de réponse lent ({load_time}s)',
            'recommendation': 'Votre site est trop lent. Vérifiez votre hébergement et optimisez.'
        })

    # Taille de la page
    page_size = len(html) / 1024  # KB
    results['details']['page_size_kb'] = round(page_size, 2)

    if page_size < 100:
        results['successes'].append(f'Page légère ({round(page_size)}KB) ✓')
        results['score'] += 20
    elif page_size < 500:
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'warning',
            'message': f'Page volumineuse ({round(page_size)}KB)',
            'recommendation': 'Réduisez la taille de votre HTML en optimisant le code'
        })

    # Compression
    if 'gzip' in headers.get('Content-Encoding', '').lower():
        results['successes'].append('Compression GZIP activée ✓')
        results['score'] += 20
    else:
        results['issues'].append({
            'type': 'warning',
            'message': 'Compression GZIP non détectée',
            'recommendation': 'Activez GZIP sur votre serveur pour réduire le temps de chargement'
        })

    # Cache headers
    cache_control = headers.get('Cache-Control', '')
    if cache_control and 'max-age' in cache_control.lower():
        results['successes'].append('Cache HTTP configuré ✓')
        results['score'] += 15
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Headers de cache non optimisés',
            'recommendation': 'Configurez Cache-Control pour améliorer les performances'
        })

    # HTTPS
    # Check in the calling function based on URL

    return results


def analyze_conversion(soup):
    """Analyse orientée conversion"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'successes': [],
        'details': {}
    }

    # CTAs (Call to Action)
    cta_patterns = [
        r'acheter|buy|commander|order',
        r'essayer|try|demo|test',
        r'inscription|sign.?up|register|créer.?compte',
        r'contact|nous.?contacter',
        r'télécharger|download',
        r'devis|quote',
        r'réserver|book',
        r'commencer|start|get.?started',
        r'en.?savoir.?plus|learn.?more'
    ]

    buttons = soup.find_all(['button', 'a'])
    cta_buttons = []

    for btn in buttons:
        text = btn.get_text().strip().lower()
        classes = ' '.join(btn.get('class', [])).lower()

        for pattern in cta_patterns:
            if re.search(pattern, text, re.I) or re.search(pattern, classes, re.I):
                cta_buttons.append(text[:50])
                break

    results['details']['cta_found'] = list(set(cta_buttons))[:5]

    if len(cta_buttons) == 0:
        results['issues'].append({
            'type': 'critical',
            'message': 'Aucun CTA clair détecté',
            'recommendation': 'Ajoutez des boutons d\'action clairs: "Essai gratuit", "Demander un devis", "Acheter"'
        })
    elif len(cta_buttons) < 3:
        results['issues'].append({
            'type': 'warning',
            'message': 'Peu de CTAs détectés',
            'recommendation': 'Multipliez les points de conversion stratégiques sur votre page'
        })
        results['score'] += 10
    else:
        results['successes'].append(f'{len(set(cta_buttons))} CTAs détectés ✓')
        results['score'] += 25

    # Formulaires
    forms = soup.find_all('form')
    results['details']['forms_count'] = len(forms)

    if len(forms) > 0:
        results['successes'].append(f'{len(forms)} formulaire(s) de conversion ✓')
        results['score'] += 15
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Aucun formulaire détecté',
            'recommendation': 'Ajoutez un formulaire de contact ou de capture d\'email'
        })

    # Signaux de confiance
    trust_patterns = [
        r'avis|review|témoignage|testimonial',
        r'client|customer',
        r'partenaire|partner',
        r'certif|garantie|warranty',
        r'sécuris|secure|ssl',
        r'\d+\s*(ans|years|clients|utilisateurs|users)'
    ]

    page_text = soup.get_text().lower()
    trust_signals = 0

    for pattern in trust_patterns:
        if re.search(pattern, page_text, re.I):
            trust_signals += 1

    results['details']['trust_signals'] = trust_signals

    if trust_signals >= 3:
        results['successes'].append('Signaux de confiance présents ✓')
        results['score'] += 20
    elif trust_signals >= 1:
        results['score'] += 10
        results['issues'].append({
            'type': 'warning',
            'message': 'Peu de signaux de confiance',
            'recommendation': 'Ajoutez des témoignages clients, logos partenaires, certifications'
        })
    else:
        results['issues'].append({
            'type': 'warning',
            'message': 'Aucun signal de confiance détecté',
            'recommendation': 'La preuve sociale est cruciale: ajoutez avis, témoignages, chiffres clés'
        })

    # Numéro de téléphone
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    if re.search(phone_pattern, page_text):
        results['successes'].append('Numéro de téléphone visible ✓')
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'info',
            'message': 'Pas de numéro de téléphone visible',
            'recommendation': 'Un numéro visible renforce la confiance et facilite le contact'
        })

    # Email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, soup.get_text()):
        results['successes'].append('Email de contact visible ✓')
        results['score'] += 10

    # Prix / Offre claire
    price_patterns = [r'€|\$|£|prix|price|tarif|€|gratuit|free|essai']
    for pattern in price_patterns:
        if re.search(pattern, page_text, re.I):
            results['successes'].append('Information tarifaire présente ✓')
            results['score'] += 10
            break

    return results


def analyze_mobile(soup, html):
    """Analyse mobile-friendliness"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'successes': [],
        'details': {}
    }

    # Viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport:
        content = viewport.get('content', '')
        if 'width=device-width' in content:
            results['successes'].append('Viewport responsive configuré ✓')
            results['score'] += 30
        else:
            results['issues'].append({
                'type': 'warning',
                'message': 'Viewport mal configuré',
                'recommendation': 'Utilisez: <meta name="viewport" content="width=device-width, initial-scale=1">'
            })
            results['score'] += 10
    else:
        results['issues'].append({
            'type': 'critical',
            'message': 'Balise viewport manquante',
            'recommendation': 'Ajoutez la balise viewport pour un affichage mobile correct'
        })

    # Media queries dans le HTML inline
    if '@media' in html or 'responsive' in html.lower():
        results['successes'].append('CSS responsive détecté ✓')
        results['score'] += 20

    # Taille des polices
    small_font_pattern = r'font-size:\s*[0-9]px|font-size:\s*1[01]px'
    if re.search(small_font_pattern, html, re.I):
        results['issues'].append({
            'type': 'warning',
            'message': 'Polices potentiellement trop petites pour mobile',
            'recommendation': 'Utilisez des tailles de police d\'au moins 16px pour le texte principal'
        })
    else:
        results['score'] += 15

    # Touch targets
    results['score'] += 15  # Difficile à vérifier sans rendu

    # Pas de Flash
    if 'flash' not in html.lower() and 'swf' not in html.lower():
        results['successes'].append('Pas de contenu Flash ✓')
        results['score'] += 10
    else:
        results['issues'].append({
            'type': 'critical',
            'message': 'Contenu Flash détecté',
            'recommendation': 'Remplacez Flash par du HTML5 - non supporté sur mobile'
        })

    # Horizontal scroll potential
    if 'overflow-x' in html.lower() or 'width: 100%' in html.lower():
        results['score'] += 10

    return results


def analyze_security(url, headers):
    """Analyse de sécurité basique"""
    results = {
        'score': 0,
        'max_score': 100,
        'issues': [],
        'successes': [],
        'details': {}
    }

    parsed = urlparse(url)

    # HTTPS
    if parsed.scheme == 'https':
        results['successes'].append('HTTPS activé ✓')
        results['score'] += 40
    else:
        results['issues'].append({
            'type': 'critical',
            'message': 'Site non sécurisé (HTTP)',
            'recommendation': 'Passez à HTTPS immédiatement - crucial pour le SEO et la confiance'
        })

    # Security headers
    security_headers = {
        'X-Content-Type-Options': 'Protège contre les attaques MIME',
        'X-Frame-Options': 'Protège contre le clickjacking',
        'X-XSS-Protection': 'Protection XSS du navigateur',
        'Strict-Transport-Security': 'Force HTTPS'
    }

    found_headers = 0
    for header, desc in security_headers.items():
        if header.lower() in [h.lower() for h in headers.keys()]:
            found_headers += 1

    results['details']['security_headers_found'] = found_headers

    if found_headers >= 3:
        results['successes'].append('Headers de sécurité configurés ✓')
        results['score'] += 30
    elif found_headers >= 1:
        results['score'] += 15
        results['issues'].append({
            'type': 'warning',
            'message': 'Headers de sécurité partiels',
            'recommendation': 'Ajoutez X-Content-Type-Options, X-Frame-Options, HSTS'
        })
    else:
        results['issues'].append({
            'type': 'warning',
            'message': 'Aucun header de sécurité détecté',
            'recommendation': 'Configurez les headers de sécurité HTTP'
        })

    # Content Security Policy
    if 'content-security-policy' in [h.lower() for h in headers.keys()]:
        results['successes'].append('Content Security Policy active ✓')
        results['score'] += 15

    return results


def calculate_global_score(analyses):
    """Calcule le score global pondéré"""
    weights = {
        'seo': 0.30,
        'performance': 0.20,
        'conversion': 0.25,
        'mobile': 0.15,
        'security': 0.10
    }

    total_score = 0
    for key, weight in weights.items():
        if key in analyses:
            normalized = (analyses[key]['score'] / analyses[key]['max_score']) * 100
            total_score += normalized * weight

    return round(total_score)


def get_priority_recommendations(analyses):
    """Génère les recommandations prioritaires"""
    all_issues = []

    priority_order = {'critical': 0, 'warning': 1, 'info': 2}

    for category, data in analyses.items():
        for issue in data.get('issues', []):
            all_issues.append({
                'category': category,
                'priority': priority_order.get(issue['type'], 3),
                **issue
            })

    # Trier par priorité
    all_issues.sort(key=lambda x: x['priority'])

    return all_issues[:10]  # Top 10


def get_grade(score):
    """Convertit le score en note lettre"""
    if score >= 90:
        return 'A+'
    elif score >= 80:
        return 'A'
    elif score >= 70:
        return 'B'
    elif score >= 60:
        return 'C'
    elif score >= 50:
        return 'D'
    else:
        return 'F'


@app.route('/api/audit', methods=['POST'])
def audit():
    """Endpoint principal d'audit"""
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'URL requise'}), 400

    url = data['url'].strip()

    # Ajouter https si pas de protocole
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Valider l'URL
    if not validators.url(url):
        return jsonify({'error': 'URL invalide'}), 400

    # Récupérer la page
    fetch_result = fetch_page(url)

    if not fetch_result['success']:
        return jsonify({'error': fetch_result['error']}), 400

    # Parser le HTML
    soup = BeautifulSoup(fetch_result['html'], 'lxml')

    # Effectuer les analyses
    analyses = {
        'seo': analyze_seo(soup, url),
        'performance': analyze_performance(
            fetch_result['load_time'],
            fetch_result['html'],
            fetch_result['headers']
        ),
        'conversion': analyze_conversion(soup),
        'mobile': analyze_mobile(soup, fetch_result['html']),
        'security': analyze_security(fetch_result['final_url'], fetch_result['headers'])
    }

    # Score global
    global_score = calculate_global_score(analyses)
    grade = get_grade(global_score)

    # Recommandations prioritaires
    priority_recommendations = get_priority_recommendations(analyses)

    # Construire la réponse
    response = {
        'success': True,
        'url': url,
        'final_url': fetch_result['final_url'],
        'analyzed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'global_score': global_score,
        'grade': grade,
        'analyses': analyses,
        'priority_recommendations': priority_recommendations,
        'load_time': fetch_result['load_time']
    }

    return jsonify(response)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'Website Audit API'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
