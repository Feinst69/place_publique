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
echo Verification des dependances...
python -c "import requests" 2>nul
if errorlevel 1 (
    echo Installation de requests...
    pip install requests
)

REM Créer les répertoires nécessaires
echo Creation des repertoires...
if not exist "data\raw\webcam_cardiff_snapshots" mkdir data\raw\webcam_cardiff_snapshots
if not exist "data\raw\webcam_madrid_snapshots" mkdir data\raw\webcam_madrid_snapshots
if not exist "data\raw\webcam_trevi_snapshots" mkdir data\raw\webcam_trevi_snapshots
if not exist "data\raw\webcam_murcia_snapshots" mkdir data\raw\webcam_murcia_snapshots
if not exist "data\raw\webcam_lapalma_snapshots" mkdir data\raw\webcam_lapalma_snapshots
if not exist "data\processed\web_cam_cardiff_metadata" mkdir data\processed\web_cam_cardiff_metadata
if not exist "data\processed\web_cam_madrid_metadata" mkdir data\processed\web_cam_madrid_metadata
if not exist "data\processed\web_cam_trevi_metadata" mkdir data\processed\web_cam_trevi_metadata
if not exist "data\processed\web_cam_murcia_metadata" mkdir data\processed\web_cam_murcia_metadata
if not exist "data\processed\web_cam_lapalma_metadata" mkdir data\processed\web_cam_lapalma_metadata
if not exist "data\final\image_annoted" mkdir data\final\image_annoted
if not exist "data\final\yolo_json" mkdir data\final\yolo_json

echo.
echo ========================================
echo Systeme de Webcams et Detection YOLO
echo ========================================
echo.
echo Options:
echo 1 - Demarrer Flask uniquement
echo 2 - Demarrer le scraping uniquement (Cardiff)
echo 3 - Demarrer les deux (Flask + Cardiff + Madrid + Trevi + Murcia + La Palma)
echo.

set /p choice="Choisissez une option (1-3): "

if "%choice%"=="1" (
    echo Demarrage du serveur Flask...
    cd src\backend\api_flask
    python app.py
) else if "%choice%"=="2" (
    echo Demarrage du scraping Cardiff...
    cd src\backend\scrapping
    python scrapping_skylinewebcams.py
) else if "%choice%"=="3" (
    echo Demarrage de tous les services...
    echo.
    echo Flask + 5 webcams (Cardiff, Madrid, Trevi, Murcia, La Palma)
    echo.

    REM Démarrer Flask dans un nouveau terminal
    start "Flask API Server" cmd /k "cd /d %cd% && call venv_yolo\Scripts\activate.bat && cd src\backend\api_flask && python app.py"

    REM Attendre que Flask démarre
    timeout /t 3 /nobreak

    REM Démarrer les scrappings dans des terminaux séparés
    start "Scraping Rotation" cmd /k "cd /d %cd% && call venv_yolo\Scripts\activate.bat && cd src\backend\scrapping && python scrapping_rotation.py"

    echo.
    echo Services demarres!
    echo Accedez a http://localhost:5000 dans votre navigateur
    echo.
    pause
) else (
    echo Option invalide
    pause
    exit /b 1
)
