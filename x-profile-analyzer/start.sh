#!/bin/bash

# Script de lancement pour X Profile Analyzer
# Usage: ./start.sh

echo "=========================================="
echo "  X PROFILE ANALYZER - Lancement"
echo "=========================================="
echo ""

# Vérification de Python
if ! command -v python3 &> /dev/null
then
    if ! command -v python &> /dev/null
    then
        echo "❌ Python n'est pas installé"
        echo "Installez Python 3.8+ depuis https://python.org"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "✅ Python trouvé : $($PYTHON_CMD --version)"
echo ""

# Vérification des dépendances
echo "🔍 Vérification des dépendances..."
if ! $PYTHON_CMD -c "import flask" &> /dev/null
then
    echo "📦 Installation des dépendances..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo ""
fi

echo "✅ Dépendances installées"
echo ""

# Lancement de l'application
echo "🚀 Lancement de l'application..."
echo ""
echo "Interface disponible sur : http://localhost:5000"
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""
echo "=========================================="
echo ""

$PYTHON_CMD app.py
