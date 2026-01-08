"""
X Profile Analyzer - Application Web SÉCURISÉE
Interface simple pour analyser des profils X/Twitter avec authentification
"""

from flask import Flask, render_template, request, jsonify, send_file
from analyzer import ProfileAnalyzer, Profile, AnalysisResult
import csv
import io
import json
import os
from datetime import datetime
from typing import List
from functools import wraps

app = Flask(__name__)

# Clé API pour sécuriser l'accès (à définir dans les variables d'environnement Render)
API_KEY = os.environ.get('API_KEY', 'change_moi_en_production_xyz789')

# Stockage en mémoire des résultats d'analyse
analysis_history: List[AnalysisResult] = []


def require_api_key(f):
    """Décorateur pour vérifier la clé API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Récupérer la clé depuis le header ou le body JSON
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key and request.is_json:
            provided_key = request.get_json().get('api_key')
        
        if not provided_key or provided_key != API_KEY:
            return jsonify({
                'error': 'Clé API manquante ou invalide',
                'message': 'Fournissez votre clé API dans le header X-API-Key ou dans le body JSON'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
@require_api_key
def analyze():
    """Endpoint pour analyser des profils - PROTÉGÉ"""
    try:
        data = request.get_json()

        # Récupération des paramètres
        profiles_data = data.get('profiles', [])
        custom_keywords = data.get('keywords', [])
        language = data.get('language', 'fr')
        min_activity = data.get('min_activity', 1)

        # Validation
        if not profiles_data:
            return jsonify({'error': 'Aucun profil fourni'}), 400

        # Création des objets Profile
        profiles = []
        for p in profiles_data:
            username = p.get('username', '').strip()
            bio = p.get('bio', '').strip()
            tweets_text = p.get('tweets', '').strip()

            # Parsing des tweets (un par ligne)
            tweets = [t.strip() for t in tweets_text.split('\n') if t.strip()]

            if not username:
                continue

            profiles.append(Profile(
                username=username,
                bio=bio,
                tweets=tweets
            ))

        if not profiles:
            return jsonify({'error': 'Aucun profil valide'}), 400

        # Analyse
        analyzer = ProfileAnalyzer(
            custom_keywords=custom_keywords,
            language=language,
            min_activity=min_activity
        )

        results = analyzer.analyze_batch(profiles)

        # Sauvegarde dans l'historique
        global analysis_history
        analysis_history = results

        # Export en format JSON
        results_json = analyzer.export_to_dict(results)

        return jsonify({
            'success': True,
            'results': results_json,
            'total_analyzed': len(results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/csv')
@require_api_key
def export_csv():
    """Exporte les résultats en CSV - PROTÉGÉ"""
    try:
        if not analysis_history:
            return "Aucune analyse disponible", 404

        # Création du CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow([
            'Username',
            'Score',
            'Niveau',
            'Thématiques',
            'Signaux',
            'Mots-clés trouvés',
            'Activité',
            'Explication'
        ])

        # Données
        for result in analysis_history:
            # Niveau de pertinence
            if result.score >= 70:
                level = "TRÈS PERTINENT"
            elif result.score >= 50:
                level = "PERTINENT"
            elif result.score >= 30:
                level = "MOYEN"
            else:
                level = "PEU PERTINENT"

            writer.writerow([
                result.username,
                result.score,
                level,
                '; '.join(result.themes),
                '; '.join(result.signals),
                '; '.join([f"{k} (x{v})" for k, v in result.keyword_matches.items()]),
                result.activity_level,
                result.explanation
            ])

        # Préparation du téléchargement
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'x_profile_analysis_{timestamp}.csv'

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM pour Excel
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return f"Erreur lors de l'export: {str(e)}", 500


@app.route('/export/json')
@require_api_key
def export_json():
    """Exporte les résultats en JSON - PROTÉGÉ"""
    try:
        if not analysis_history:
            return jsonify({'error': 'Aucune analyse disponible'}), 404

        results_dict = [
            {
                'username': r.username,
                'score': r.score,
                'themes': r.themes,
                'signals': r.signals,
                'keyword_matches': r.keyword_matches,
                'activity_level': r.activity_level,
                'explanation': r.explanation
            }
            for r in analysis_history
        ]

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        response = jsonify({
            'export_date': timestamp,
            'total_profiles': len(results_dict),
            'profiles': results_dict
        })

        response.headers['Content-Disposition'] = f'attachment; filename=x_profile_analysis_{timestamp}.json'

        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Endpoint de santé - PUBLIC (pour monitoring Render)"""
    return jsonify({'status': 'ok', 'version': '1.0.0-secured'})


if __name__ == '__main__':
    print("=" * 60)
    print("X PROFILE ANALYZER - Démarrage (VERSION SÉCURISÉE)")
    print("=" * 60)
    print("Interface web disponible sur : http://localhost:5000")
    print(f"Clé API active : {API_KEY[:10]}...")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
                
