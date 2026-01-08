"""
Script de test pour vérifier que l'analyseur fonctionne correctement
"""

from analyzer import ProfileAnalyzer, Profile


def test_basic_analysis():
    """Test basique de l'analyseur"""

    print("=" * 60)
    print("TEST DE L'ANALYSEUR X PROFILE ANALYZER")
    print("=" * 60)
    print()

    # Création de profils de test
    profiles = [
        Profile(
            username="@marie_copywriter",
            bio="Copywriter freelance 🇫🇷 | J'aide les entrepreneurs à créer du contenu qui convertit | Accroches & storytelling",
            tweets=[
                "Comment écrire une accroche qui capte l'attention en moins de 3 secondes ?",
                "Je cherche des exemples d'accroches percutantes pour mes clients e-commerce",
                "La règle d'or du copywriting : toujours partir du problème de votre client",
                "En train de bosser sur une landing page. Le copy fait toute la différence 🔥",
                "Astuce : gardez un swipe file de toutes les pubs qui vous font cliquer"
            ]
        ),
        Profile(
            username="@thomas_dev",
            bio="Développeur Full Stack | React & Node.js | Open source contributor | Tech enthusiast 💻",
            tweets=[
                "Nouveau projet en TypeScript avec Next.js 14",
                "Debug session du dimanche... La joie des memory leaks 😅",
                "Code review time ! J'adore voir du code bien écrit",
                "PSA : Always use TypeScript, your future self will thank you"
            ]
        ),
        Profile(
            username="@julien_growth",
            bio="Growth Marketer | Expert acquisition & conversion | Je booste les ventes des e-commerces 📈",
            tweets=[
                "Mon funnel ne convertit pas assez... Besoin d'optimiser mes emails",
                "Lancement de ma nouvelle formation sur l'acquisition client la semaine prochaine",
                "3 techniques pour doubler votre taux de conversion",
                "La clé d'un bon marketing ? Des accroches qui arrêtent le scroll"
            ]
        )
    ]

    # Configuration de l'analyseur
    custom_keywords = ["copywriting", "accroche", "conversion", "marketing", "vente"]
    analyzer = ProfileAnalyzer(custom_keywords=custom_keywords, language="fr", min_activity=1)

    print("🔍 Analyse en cours...")
    print()

    # Analyse des profils
    results = analyzer.analyze_batch(profiles)

    # Affichage des résultats
    print("📊 RÉSULTATS DE L'ANALYSE")
    print("=" * 60)
    print()

    for i, result in enumerate(results, 1):
        print(f"{i}. {result.username}")
        print(f"   Score: {result.score}/100")
        print(f"   {result.explanation}")
        print()

        if result.themes:
            print(f"   Thématiques: {', '.join(result.themes)}")

        if result.signals:
            print(f"   Signaux: {', '.join(result.signals)}")

        if result.keyword_matches:
            print(f"   Mots-clés trouvés: {', '.join([f'{k} (x{v})' for k, v in result.keyword_matches.items()])}")

        print(f"   Activité: {result.activity_level}")
        print("-" * 60)
        print()

    # Vérifications
    print("✅ VÉRIFICATIONS")
    print("=" * 60)

    # Les deux premiers profils devraient avoir des scores élevés (>= 70)
    assert results[0].score >= 70, f"Le premier profil devrait avoir un score >= 70 (actuel: {results[0].score})"
    assert results[1].score >= 70, f"Le deuxième profil devrait avoir un score >= 70 (actuel: {results[1].score})"
    print(f"✅ Top 2 profils avec scores élevés : {results[0].username} ({results[0].score}) et {results[1].username} ({results[1].score})")

    # Le développeur devrait avoir le score le plus faible
    assert results[-1].username == "@thomas_dev", "Le développeur devrait être classé dernier"
    assert results[-1].score < 30, f"Le développeur devrait avoir un score < 30 (actuel: {results[-1].score})"
    print(f"✅ Profil hors cible correctement identifié : {results[-1].username} ({results[-1].score})")

    # Vérifier que les thématiques sont détectées pour les profils pertinents
    top_profiles = [r for r in results if r.score >= 70]
    assert all(len(r.themes) > 0 for r in top_profiles), "Les profils pertinents devraient avoir des thématiques"
    print("✅ Détection des thématiques fonctionnelle")

    # Vérifier que des signaux sont détectés
    assert any(len(r.signals) > 0 for r in results), "Des signaux devraient être détectés"
    print("✅ Détection des signaux fonctionnelle")

    print("✅ Scoring cohérent et discrimination efficace")
    print()

    print("=" * 60)
    print("🎉 TOUS LES TESTS SONT PASSÉS !")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_basic_analysis()
    except AssertionError as e:
        print(f"❌ ERREUR DE TEST : {e}")
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
