@echo off
REM Script de lancement pour X Profile Analyzer (Windows)
REM Double-cliquez sur ce fichier pour lancer l'application

echo ==========================================
echo   X PROFILE ANALYZER - Lancement
echo ==========================================
echo.

REM Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python n'est pas installe
    echo Installez Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

echo [OK] Python trouve
echo.

REM Vérification des dépendances
echo Verification des dependances...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances...
    python -m pip install -r requirements.txt
    echo.
)

echo [OK] Dependances installees
echo.

REM Lancement de l'application
echo Lancement de l'application...
echo.
echo Interface disponible sur : http://localhost:5000
echo Appuyez sur Ctrl+C pour arreter
echo.
echo ==========================================
echo.

python app.py

pause
