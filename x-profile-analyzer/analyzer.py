"""
X Profile Analyzer - Moteur d'analyse sémantique
Analyse des profils X/Twitter pour détecter la pertinence marketing/copywriting
"""

import re
from typing import Dict, List, Tuple
from collections import Counter
from dataclasses import dataclass, asdict
import json


@dataclass
class Profile:
    """Représente un profil X avec ses données"""
    username: str
    bio: str
    tweets: List[str]

    def get_all_text(self) -> str:
        """Retourne tout le texte du profil concaténé"""
        return f"{self.bio} {' '.join(self.tweets)}"


@dataclass
class AnalysisResult:
    """Résultat d'analyse d'un profil"""
    username: str
    score: float
    themes: List[str]
    signals: List[str]
    explanation: str
    keyword_matches: Dict[str, int]
    activity_level: str


class ProfileAnalyzer:
    """Analyseur de profils X avec scoring sémantique"""

    # Thématiques principales
    THEMES = {
        'copywriting': [
            'copy', 'copywriting', 'rédaction', 'écriture', 'contenu',
            'accroches', 'headlines', 'storytelling', 'persuasion'
        ],
        'marketing': [
            'marketing', 'digital marketing', 'growth', 'acquisition',
            'conversion', 'funnel', 'leads', 'prospect', 'client'
        ],
        'business': [
            'business', 'entrepreneur', 'startup', 'entreprise',
            'vente', 'sales', 'chiffre d\'affaires', 'revenus'
        ],
        'content_creation': [
            'créateur', 'contenu', 'audience', 'communauté',
            'newsletter', 'blog', 'vidéo', 'podcast'
        ],
        'ecommerce': [
            'ecommerce', 'e-commerce', 'boutique', 'shopify',
            'produit', 'vente en ligne', 'dropshipping'
        ]
    }

    # Signaux d'intention/besoin
    INTENT_SIGNALS = {
        'needs_help': [
            'besoin', 'cherche', 'recherche', 'galère', 'difficulté',
            'problème', 'comment', 'aide', 'conseil'
        ],
        'selling': [
            'vendre', 'vente', 'offre', 'promo', 'lancement',
            'nouveau produit', 'disponible', 'acheter'
        ],
        'improving': [
            'améliorer', 'optimiser', 'booster', 'augmenter',
            'doubler', 'tripler', 'croissance', 'performance'
        ],
        'creating': [
            'créer', 'lancer', 'démarrer', 'nouveau', 'projet',
            'construire', 'développer', 'préparer'
        ]
    }

    # Mots-clés liés aux accroches/copywriting
    HOOK_KEYWORDS = [
        'accroche', 'hook', 'titre', 'headline', 'premier paragraphe',
        'intro', 'ouverture', 'captiver', 'attirer l\'attention',
        'clic', 'engagement', 'scroll', 'retenir'
    ]

    def __init__(self, custom_keywords: List[str] = None, language: str = 'fr',
                 min_activity: int = 1):
        """
        Initialise l'analyseur

        Args:
            custom_keywords: Mots-clés personnalisés à rechercher
            language: Langue cible (actuellement seul 'fr' est supporté)
            min_activity: Nombre minimum de tweets pour considérer un profil actif
        """
        self.custom_keywords = [kw.lower() for kw in (custom_keywords or [])]
        self.language = language
        self.min_activity = min_activity

    def analyze_profile(self, profile: Profile) -> AnalysisResult:
        """Analyse un profil et retourne le scoring complet"""

        text = profile.get_all_text().lower()

        # Détection des thématiques
        themes = self._detect_themes(text)

        # Détection des signaux d'intention
        signals = self._detect_signals(text)

        # Correspondance avec mots-clés personnalisés
        keyword_matches = self._match_custom_keywords(text)

        # Détection de mots-clés liés aux accroches
        hook_keywords_found = self._match_hook_keywords(text)

        # Niveau d'activité
        activity_level = self._assess_activity(profile)

        # Calcul du score
        score = self._calculate_score(
            themes, signals, keyword_matches,
            hook_keywords_found, activity_level
        )

        # Génération de l'explication
        explanation = self._generate_explanation(
            score, themes, signals, keyword_matches,
            hook_keywords_found, activity_level
        )

        return AnalysisResult(
            username=profile.username,
            score=round(score, 2),
            themes=themes,
            signals=signals,
            explanation=explanation,
            keyword_matches=keyword_matches,
            activity_level=activity_level
        )

    def _detect_themes(self, text: str) -> List[str]:
        """Détecte les thématiques principales dans le texte"""
        detected = []

        for theme, keywords in self.THEMES.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                detected.append(f"{theme} ({matches} mentions)")

        return detected

    def _detect_signals(self, text: str) -> List[str]:
        """Détecte les signaux d'intention dans le texte"""
        detected = []

        for signal_type, keywords in self.INTENT_SIGNALS.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                signal_name = {
                    'needs_help': 'Recherche d\'aide',
                    'selling': 'Vend actuellement',
                    'improving': 'Cherche à optimiser',
                    'creating': 'Lance un projet'
                }.get(signal_type, signal_type)
                detected.append(f"{signal_name} ({matches} mentions)")

        return detected

    def _match_custom_keywords(self, text: str) -> Dict[str, int]:
        """Compte les occurrences des mots-clés personnalisés"""
        matches = {}
        for keyword in self.custom_keywords:
            count = text.count(keyword)
            if count > 0:
                matches[keyword] = count
        return matches

    def _match_hook_keywords(self, text: str) -> int:
        """Compte les mots-clés liés aux accroches"""
        return sum(1 for kw in self.HOOK_KEYWORDS if kw in text)

    def _assess_activity(self, profile: Profile) -> str:
        """Évalue le niveau d'activité du profil"""
        tweet_count = len(profile.tweets)

        if tweet_count == 0:
            return "Inactif (0 tweet)"
        elif tweet_count < 3:
            return f"Peu actif ({tweet_count} tweets)"
        elif tweet_count < 10:
            return f"Actif ({tweet_count} tweets)"
        else:
            return f"Très actif ({tweet_count} tweets)"

    def _calculate_score(self, themes: List[str], signals: List[str],
                         keyword_matches: Dict[str, int], hook_keywords: int,
                         activity_level: str) -> float:
        """Calcule le score de pertinence (0-100)"""

        score = 0.0

        # Thématiques (max 40 points)
        theme_score = len(themes) * 8
        score += min(theme_score, 40)

        # Signaux d'intention (max 25 points)
        signal_score = len(signals) * 8
        score += min(signal_score, 25)

        # Mots-clés personnalisés (max 20 points)
        custom_score = sum(min(count * 3, 10) for count in keyword_matches.values())
        score += min(custom_score, 20)

        # Mots-clés d'accroches (max 10 points)
        hook_score = min(hook_keywords * 3, 10)
        score += hook_score

        # Niveau d'activité (max 5 points)
        if "Très actif" in activity_level:
            score += 5
        elif "Actif" in activity_level:
            score += 3
        elif "Peu actif" in activity_level:
            score += 1

        return min(score, 100)

    def _generate_explanation(self, score: float, themes: List[str],
                             signals: List[str], keyword_matches: Dict[str, int],
                             hook_keywords: int, activity_level: str) -> str:
        """Génère une explication claire du score"""

        parts = []

        # Qualification générale
        if score >= 70:
            parts.append("🎯 TRÈS PERTINENT")
        elif score >= 50:
            parts.append("✅ PERTINENT")
        elif score >= 30:
            parts.append("⚠️ MOYENNEMENT PERTINENT")
        else:
            parts.append("❌ PEU PERTINENT")

        # Thématiques
        if themes:
            parts.append(f"Thématiques : {', '.join(themes)}")

        # Signaux
        if signals:
            parts.append(f"Signaux : {', '.join(signals)}")

        # Mots-clés personnalisés
        if keyword_matches:
            kw_text = ', '.join([f"{kw} (x{count})" for kw, count in keyword_matches.items()])
            parts.append(f"Mots-clés : {kw_text}")

        # Accroches
        if hook_keywords > 0:
            parts.append(f"Intérêt pour les accroches : {hook_keywords} mentions")

        # Activité
        parts.append(f"Activité : {activity_level}")

        return " | ".join(parts)

    def analyze_batch(self, profiles: List[Profile]) -> List[AnalysisResult]:
        """Analyse un lot de profils et retourne les résultats triés par score"""
        results = [self.analyze_profile(p) for p in profiles]
        return sorted(results, key=lambda r: r.score, reverse=True)

    def export_to_dict(self, results: List[AnalysisResult]) -> List[Dict]:
        """Exporte les résultats en format dictionnaire"""
        return [asdict(result) for result in results]
