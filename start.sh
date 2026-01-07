#!/bin/bash

# SiteAuditPro - Script de démarrage

echo "🚀 Démarrage de SiteAuditPro..."
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Créer venv si n'existe pas
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer venv
source venv/bin/activate

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r backend/requirements.txt -q

# Démarrer le backend en arrière-plan
echo "🔧 Démarrage du backend sur http://localhost:5000..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Attendre que le backend démarre
sleep 2

# Démarrer le frontend
echo "🌐 Démarrage du frontend sur http://localhost:8080..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ SiteAuditPro est lancé!"
echo ""
echo "   Frontend: http://localhost:8080"
echo "   Backend:  http://localhost:5000"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter..."

# Gérer l'arrêt propre
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Attendre
wait
