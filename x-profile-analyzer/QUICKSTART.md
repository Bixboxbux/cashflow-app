# 🚀 Guide de démarrage rapide

## En 3 étapes simples

### 1️⃣ Installation (2 minutes)

```bash
cd x-profile-analyzer
pip install -r requirements.txt
```

### 2️⃣ Lancement (10 secondes)

```bash
python app.py
```

Ouvrez votre navigateur : **http://localhost:5000**

### 3️⃣ Utilisation (30 secondes)

1. Cliquez sur **"📝 Charger exemple"**
2. Cliquez sur **"🚀 ANALYSER LES PROFILS"**
3. Admirez les résultats ! 🎉

---

## Workflow recommandé

### Sur X/Twitter :

1. Trouvez un profil intéressant
2. Copiez sa bio
3. Copiez 5-10 tweets récents

### Dans l'outil :

4. Collez les données dans un profil
5. Ajoutez vos mots-clés personnalisés
6. Lancez l'analyse
7. Consultez le score et les explications
8. Exportez en CSV si besoin

---

## Commandes utiles

**Lancer l'application :**
```bash
python app.py
```

**Arrêter l'application :**
Appuyez sur `Ctrl+C` dans le terminal

**Réinstaller les dépendances :**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## Personnalisation rapide

### Modifier les mots-clés par défaut

Éditez `analyzer.py` ligne 25-50 pour ajouter vos propres thématiques.

### Ajuster le scoring

Éditez `analyzer.py` ligne 150-180 pour modifier les pondérations.

---

## Troubleshooting

**Erreur "Port 5000 déjà utilisé" :**
```bash
# Changez le port dans app.py (dernière ligne)
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Erreur "Module Flask not found" :**
```bash
pip install Flask
```

**Page blanche dans le navigateur :**
- Vérifiez que le serveur est bien lancé
- Essayez http://127.0.0.1:5000

---

## 🎯 Cas d'usage

### 1. Identifier des prospects pour votre swipe file d'accroches

**Mots-clés recommandés :**
```
copywriting, accroche, headline, hook, conversion, vente
```

**Profils à chercher :**
- Copywriters freelance
- Growth marketers
- Entrepreneurs e-commerce
- Créateurs de contenu

### 2. Trouver des partenaires pour affiliation

**Mots-clés recommandés :**
```
affiliation, marketing, audience, monétisation, revenus
```

### 3. Repérer des clients potentiels pour coaching

**Mots-clés recommandés :**
```
besoin, cherche, aide, conseil, formation, apprendre
```

---

**Prêt à commencer ? Lancez `python app.py` ! 🚀**
