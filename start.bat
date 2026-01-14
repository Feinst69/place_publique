@echo off
REM Script de démarrage pour le système de webcams et détection YOLO

REM Vérifier que l'environnement virtuel existe
if not exist "venv_yolo\Scripts\activate.bat" (
    echo Erreur: L'environnement virtuel n'existe pas
    echo Créez-le d'abord avec: python -m venv venv_yolo
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call venv_yolo\Scripts\activate.bat

REM Vérifier les dépendances
echo Vérification des dépendances...
python -c "import requests" 2>nul
if errorlevel 1 (
    echo Installation de requests...
    pip install requests
)

REM Créer les répertoires nécessaires
echo Création des répertoires...
if not exist "data\raw\webcam_cardiff_snapshots" mkdir data\raw\webcam_cardiff_snapshots
if not exist "data\raw\webcam_trevi_snapshots" mkdir data\raw\webcam_trevi_snapshots
if not exist "data\processed\web_cam_cardiff_metadata" mkdir data\processed\web_cam_cardiff_metadata
if not exist "data\processed\web_cam_trevi_metadata" mkdir data\processed\web_cam_trevi_metadata
if not exist "data\final\image_annoted" mkdir data\final\image_annoted
if not exist "data\final\yolo_json" mkdir data\final\yolo_json

echo.
echo ========================================
echo Système de Webcams et Détection YOLO
echo ========================================
echo.
echo Options:
echo 1 - Démarrer Flask uniquement
echo 2 - Démarrer le scraping uniquement
echo 3 - Démarrer les deux (dans deux terminals)
echo.

set /p choice="Choisissez une option (1-3): "

if "%choice%"=="1" (
    echo Démarrage du serveur Flask...
    cd src\backend\api_flask
    python app.py
) else if "%choice%"=="2" (
    echo Démarrage du scraping webcams...
    cd src\backend\scrapping
    python scrapping_skylinewebcams.py
) else if "%choice%"=="3" (
    echo Démarrage des deux services...
    echo.
    echo IMPORTANT: Ce script va ouvrir deux nouveaux terminals
    echo Vous pouvez les fermer individuellement pour arrêter un service
    echo.
    
    REM Démarrer Flask dans un nouveau terminal
    start "Flask API Server" cmd /k "cd /d %cd% && call venv_yolo\Scripts\activate.bat && cd src\backend\api_flask && python app.py"
    
    REM Attendre un peu que Flask démarre
    timeout /t 2 /nobreak
    
    REM Démarrer le scraping dans un nouveau terminal
    start "Webcam Scraping" cmd /k "cd /d %cd% && call venv_yolo\Scripts\activate.bat && cd src\backend\scrapping && python scrapping_skylinewebcams.py"
    
    echo.
    echo Services démarrés!
    echo Accédez à http://localhost:5000 dans votre navigateur
    echo.
    pause
) else (
    echo Option invalide
    pause
    exit /b 1
)
