@echo off
setlocal enabledelayedexpansion

REM Se placer a la racine du projet (dossier du .bat)
cd /d "%~dp0"

REM -----------------------------------------------------------------
REM Resolution de Python: priorite a pyenv 'place', sinon python du PATH
REM -----------------------------------------------------------------
set "PYTHON_EXE="

REM 1) Emplacements pyenv-win frequents
if exist "%USERPROFILE%\.pyenv\pyenv-win\versions\place\python.exe" set "PYTHON_EXE=%USERPROFILE%\.pyenv\pyenv-win\versions\place\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\.pyenv\versions\place\python.exe" set "PYTHON_EXE=%USERPROFILE%\.pyenv\versions\place\python.exe"

REM 2) via commande pyenv (si dispo)
if not defined PYTHON_EXE (
    where pyenv >nul 2>nul
    if %errorlevel%==0 (
        for /f "delims=" %%i in ('pyenv which python 2^>nul') do (
            if exist "%%i" (
                set "PYTHON_EXE=%%i"
                goto :python_found
            )
        )
    )
)

REM 3) fallback: python dans le PATH
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set "PYTHON_EXE=%%i"
        goto :python_found
    )
)

:python_found
if not defined PYTHON_EXE (
    echo Erreur: Aucun interpreteur Python detecte.
    echo Installez Python ou configurez pyenv version place.
    pause
    exit /b 1
)

"%PYTHON_EXE%" --version >nul 2>nul
if errorlevel 1 (
    echo Erreur: Python detecte mais non executable: %PYTHON_EXE%
    pause
    exit /b 1
)

echo Python detecte: %PYTHON_EXE%

REM -----------------------------------------------------------------
REM Installation dependances (environnement 'place' si detecte)
REM -----------------------------------------------------------------
echo Verification des dependances...
if exist "requirements.txt" (
    "%PYTHON_EXE%" -m pip install --upgrade pip
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Erreur pendant l'installation des dependances.
        pause
        exit /b 1
    )
) else (
    echo Attention: requirements.txt introuvable, installation ignoree.
)

REM -----------------------------------------------------------------
REM Creation des repertoires necessaires
REM -----------------------------------------------------------------
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

if not exist "data\final\weights_model\yolo11n.pt" (
    echo Attention: modele manquant data\final\weights_model\yolo11n.pt
)
if not exist "data\final\weights_model\best_car.pt" (
    echo Attention: modele manquant data\final\weights_model\best_car.pt
)

echo.
echo ========================================
echo Systeme de Webcams et Detection YOLO
echo ========================================
echo.
echo Options:
echo 1 - Demarrer Flask uniquement
echo 2 - Demarrer le scraping uniquement (Cardiff)
echo 3 - Demarrer les deux (Flask + Cardiff + Murcia + La Palma)
echo.

set /p choice="Choisissez une option (1-3): "
set "choice=%choice: =%"

if "%choice%"=="1" goto :opt1
if "%choice%"=="2" goto :opt2
if "%choice%"=="3" goto :opt3

echo Option invalide
pause
exit /b 1

:opt1
echo Demarrage du serveur Flask...
cd src\backend\api_flask
"%PYTHON_EXE%" app.py
exit /b %errorlevel%

:opt2
echo Demarrage du scraping Cardiff...
cd src\backend\scrapping
"%PYTHON_EXE%" scrapping_skylinewebcams.py
exit /b %errorlevel%

:opt3
echo Demarrage de tous les services...
echo.
echo Flask + webcams (Cardiff, Murcia, La Palma)
echo.

REM Demarrer Flask dans un nouveau terminal
start "Flask API Server" cmd /k "cd /d %cd% && \"%PYTHON_EXE%\" src\backend\api_flask\app.py"

REM Attendre que Flask demarre
timeout /t 3 /nobreak

REM Demarrer le scraping rotation dans un terminal separe
start "Scraping Rotation" cmd /k "cd /d %cd% && \"%PYTHON_EXE%\" src\backend\scrapping\scrapping_rotation.py"

echo.
echo Services demarres
echo Accedez a http://localhost:5000 dans votre navigateur
echo.
pause
exit /b 0
