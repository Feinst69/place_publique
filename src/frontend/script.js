const socket = io();

// Elements YOLO
const liveImage = document.getElementById('liveImage');
const placeholder = document.getElementById('placeholder');
const countVal = document.getElementById('count-val');
const timeVal = document.getElementById('time-val');
const statsLive = document.getElementById('stats-live');
const statusBar = document.getElementById('status-bar');
const detectionsDetails = document.getElementById('detections-details');
const detectionList = document.getElementById('detection-list');

// Elements Webcams
const webcamsContainer = document.getElementById('webcams-container');
const cameraElements = {}; // Stockage dynamique des éléments caméra

// Variables pour l'actualisation automatique
let autoRefreshInterval = null;
let currentActiveTab = 'global';
let currentWebcamFilter = 'all';
let currentSelectedClass = '';

// Gestion des onglets de statistiques
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        currentActiveTab = tabName;
        
        // Retirer la classe active de tous les boutons et contenus
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Ajouter la classe active au bouton cliqué
        btn.classList.add('active');
        
        // Afficher le contenu correspondant
        if (tabName === 'global') {
            document.getElementById('global-stats').classList.add('active');
            loadGlobalStats();
        } else if (tabName === 'webcams') {
            document.getElementById('webcams-stats').classList.add('active');
            loadWebcamStats();
        }
    });
});

// Charger les statistiques globales
function loadGlobalStats() {
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('global-stats-content');
            
            if (Object.keys(data).length === 0) {
                container.innerHTML = '<div class="no-data">Aucune donnée disponible</div>';
                return;
            }
            
            let html = '';
            for (const [className, stats] of Object.entries(data)) {
                html += `
                    <div class="stat-card">
                        <div class="stat-card-title">${className}</div>
                        <div class="stat-card-value">${stats.total_detections}</div>
                        <div class="stat-card-info">
                            Dans ${stats.count} images<br>
                            Confiance: ${(stats.avg_confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Erreur chargement stats globales:', error);
            document.getElementById('global-stats-content').innerHTML = 
                '<div class="no-data">Erreur lors du chargement des statistiques</div>';
        });
}

// Charger les statistiques par webcam
function loadWebcamStats() {
    fetch('/api/statistics/webcam')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('webcams-stats-content');
            
            if (data.length === 0) {
                container.innerHTML = '<div class="no-data">Aucune donnée disponible par webcam</div>';
                return;
            }
            
            let html = '';
            data.forEach(webcam => {
                // Charger les détails de cette webcam
                fetch(`/api/statistics/webcam/${webcam.webcam_name}`)
                    .then(response => response.json())
                    .then(details => {
                        const webcamData = details[webcam.webcam_name];
                        if (!webcamData) return;
                        
                        // Compter les objets par classe pour cette webcam
                        const classCounts = {};
                        Object.values(webcamData).forEach(imageData => {
                            Object.entries(imageData.detections).forEach(([className, data]) => {
                                classCounts[className] = (classCounts[className] || 0) + data.count;
                            });
                        });
                        
                        let detailsHtml = '';
                        for (const [className, count] of Object.entries(classCounts)) {
                            detailsHtml += `
                                <div class="detection-badge">
                                    <span class="detection-badge-name">${className}</span>
                                    <span class="detection-badge-count">${count}</span>
                                </div>
                            `;
                        }
                        
                        const webcamHtml = `
                            <div class="webcam-stat-card">
                                <div class="webcam-stat-header">
                                    <div class="webcam-stat-name"> ${webcam.webcam_name}</div>
                                    <div class="webcam-stat-count">${webcam.total_images} images</div>
                                </div>
                                <div class="webcam-detections">
                                    ${detailsHtml}
                                </div>
                            </div>
                        `;
                        
                        container.innerHTML += webcamHtml;
                    });
            });
            
            container.innerHTML = '<div class="loading-stats">Chargement des détails...</div>';
        })
        .catch(error => {
            console.error('Erreur chargement stats webcams:', error);
            document.getElementById('webcams-stats-content').innerHTML = 
                '<div class="no-data">Erreur lors du chargement des statistiques</div>';
        });
}

// Charger les statistiques globales au démarrage
setTimeout(() => loadGlobalStats(), 1000);

// Variables pour le graphique
let detectionChart = null;
let currentTimelineData = null;

// Initialiser le graphique
function initChart() {
    const ctx = document.getElementById('detectionChart').getContext('2d');
    
    detectionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution du nombre de détections par image',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Numéro d\'image'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Nombre d\'occurrences'
                    },
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Charger les données temporelles
function loadTimelineData(webcamFilter = 'all') {
    const url = webcamFilter === 'all' 
        ? '/api/statistics/timeline'
        : `/api/statistics/timeline?webcam=${webcamFilter}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            currentTimelineData = data;
            
            // Remplir le sélecteur de classes
            const classSelect = document.getElementById('class-select');
            const previousValue = classSelect.value || currentSelectedClass;
            classSelect.innerHTML = '<option value="">-- Sélectionnez une classe --</option>';
            
            Object.keys(data).sort().forEach(className => {
                const option = document.createElement('option');
                option.value = className;
                option.textContent = className;
                classSelect.appendChild(option);
            });
            
            // Restaurer la sélection précédente si elle existe toujours
            if (previousValue && data[previousValue]) {
                classSelect.value = previousValue;
                currentSelectedClass = previousValue;
                updateChart(previousValue);
            } else if (Object.keys(data).length > 0 && currentSelectedClass && data[currentSelectedClass]) {
                // Sinon utiliser la dernière classe sélectionnée si elle existe
                classSelect.value = currentSelectedClass;
                updateChart(currentSelectedClass);
            }
        })
        .catch(error => console.error('Erreur chargement timeline:', error));
}

// Mettre à jour le graphique avec une classe spécifique
function updateChart(className) {
    if (!currentTimelineData || !currentTimelineData[className]) return;
    
    const classData = currentTimelineData[className];
    
    detectionChart.data.labels = classData.labels;
    detectionChart.data.datasets = [{
        label: className,
        data: classData.data,
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4,
        fill: true
    }];
    
    detectionChart.update();
}

// Charger les webcams pour le filtre
function loadWebcamFilter() {
    fetch('/api/statistics/webcam')
        .then(response => response.json())
        .then(data => {
            const webcamFilter = document.getElementById('webcam-filter');
            webcamFilter.innerHTML = '<option value="all">Toutes les webcams</option>';
            
            data.forEach(webcam => {
                const option = document.createElement('option');
                option.value = webcam.webcam_name;
                option.textContent = webcam.webcam_name;
                webcamFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Erreur chargement webcams:', error));
}

// Event listeners pour les contrôles du graphique
document.getElementById('class-select').addEventListener('change', (e) => {
    const className = e.target.value;
    currentSelectedClass = className;
    e.target.dataset.lastSelected = className;
    if (className) {
        updateChart(className);
    }
});

document.getElementById('webcam-filter').addEventListener('change', (e) => {
    const webcamName = e.target.value;
    currentWebcamFilter = webcamName;
    loadTimelineData(webcamName);
});

// Fonction pour rafraîchir toutes les données
function refreshAllData() {
    console.log('🔄 Actualisation automatique des données...');
    
    // Rafraîchir les statistiques selon l'onglet actif
    if (currentActiveTab === 'global') {
        loadGlobalStats();
    } else if (currentActiveTab === 'webcams') {
        loadWebcamStats();
    }
    
    // Rafraîchir le graphique
    loadTimelineData(currentWebcamFilter);
    
    // Rafraîchir le filtre webcam
    loadWebcamFilter();
}

// Démarrer l'actualisation automatique toutes les 10 secondes
function startAutoRefresh() {
    // Nettoyer l'intervalle existant si présent
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Créer un nouvel intervalle
    autoRefreshInterval = setInterval(refreshAllData, 60000); // 10 secondes
    console.log('✅ Actualisation automatique activée (toutes les 10 secondes)');
}

// Écouter les événements WebSocket pour mise à jour immédiate
socket.on('new_webcam', (data) => {
    console.log(' Nouvelle image détectée, actualisation des stats...');
    // Actualiser immédiatement les statistiques
    setTimeout(() => {
        refreshAllData();
    }, 1000); // Petit délai pour laisser la DB se mettre à jour
});

// Initialiser le graphique au chargement
setTimeout(() => {
    initChart();
    loadTimelineData();
    loadWebcamFilter();
    startAutoRefresh(); // Démarrer l'actualisation automatique
}, 1500);

socket.on('connect', () => {
    statusBar.innerText = "Statut : Connecte au serveur de surveillance";
    console.log("Connecté au serveur");
    loadCamerasConfig();
});

// Charger la configuration des caméras
function loadCamerasConfig() {
    fetch('/api/cameras/config')
        .then(response => response.json())
        .then(camerasConfig => {
            console.log("Configuration des caméras chargée:", camerasConfig);
            
            // Vider le conteneur
            webcamsContainer.innerHTML = '';
            
            // Créer les éléments pour chaque caméra
            for (const [cameraName, cameraData] of Object.entries(camerasConfig)) {
                createCameraElement(cameraName, cameraData);
            }
            
            // Charger les images initiales
            loadInitialWebcams();
        })
        .catch(error => console.error('Erreur chargement config caméras:', error));
}

// Créer les éléments HTML pour une caméra
function createCameraElement(cameraName, cameraData) {
    const displayName = cameraData.display_name || cameraName;
    
    const cameraBox = document.createElement('div');
    cameraBox.className = 'webcam-box';
    cameraBox.innerHTML = `
        <div class="webcam-header">
            <span class="webcam-status"></span>${displayName}
        </div>
        <div class="webcam-image" id="${cameraName}-container">
            <div class="loading">En attente de connexion...</div>
        </div>
        <div class="webcam-info">
            <p class="webcam-timestamp" id="${cameraName}-time">Aucune image</p>
        </div>
    `;
    
    webcamsContainer.appendChild(cameraBox);
    
    // Stocker les références aux éléments
    cameraElements[cameraName] = {
        box: cameraBox,
        container: document.getElementById(`${cameraName}-container`),
        timeElement: document.getElementById(`${cameraName}-time`),
        statusElement: cameraBox.querySelector('.webcam-status')
    };
}

// Charger les webcams au démarrage
function loadInitialWebcams() {
    fetch('/api/webcams')
        .then(response => response.json())
        .then(data => {
            console.log("Webcams initiales chargées:", data);
            for (const [cameraName, cameraData] of Object.entries(data)) {
                updateWebcam(cameraName, cameraData);
            }
        })
        .catch(error => console.error('Erreur chargement webcams:', error));
}

// Mettre à jour une webcam
function updateWebcam(cameraName, data) {
    if (!cameraElements[cameraName]) {
        console.warn(`Caméra ${cameraName} non trouvée dans les éléments`);
        return;
    }
    
    const elements = cameraElements[cameraName];
    const container = elements.container;
    const timeElement = elements.timeElement;
    const statusElement = elements.statusElement;
    
    // Créer ou mettre à jour l'image
    let img = container.querySelector('img');
    if (!img) {
        img = document.createElement('img');
        container.innerHTML = '';
        container.appendChild(img);
    }
    
    img.src = data.image;
    
    // Mettre à jour l'horodatage
    const now = new Date();
    timeElement.innerText = `Mise à jour: ${now.toLocaleTimeString('fr-FR')}`;
    
    // Mettre à jour le statut (online)
    statusElement.classList.remove('offline');
    
    // Afficher les statistiques si disponibles
    if (data.stats && Object.keys(data.stats).length > 0) {
        let statsDiv = elements.box.querySelector('.webcam-stats');
        if (!statsDiv) {
            statsDiv = document.createElement('div');
            statsDiv.className = 'webcam-stats';
            elements.box.appendChild(statsDiv);
        }
        
        let statsHTML = '<h4>Détections:</h4><ul>';
        
        // Icônes personnalisées par classe
        const classIcons = {
            'person': '',
            'car': '',
            'truck': '',
            'bus': '',
            'bicycle': '',
            'motorcycle': '',
            'dog': '',
            'cat': ''
        };
        
        for (const [className, count] of Object.entries(data.stats)) {
            const icon = classIcons[className] || '';
            statsHTML += `<li>${icon} <strong>${className}</strong>: ${count}</li>`;
        }
        
        statsHTML += `</ul><p class="total-detections">Total: ${data.num_detections || 0} objets détectés</p>`;
        statsDiv.innerHTML = statsHTML;
    }
}

// Écouter les nouvelles images webcam en temps réel
socket.on('new_webcam', (data) => {
    console.log(`Nouvelle webcam reçue: ${data.webcam_name}`, data);
    updateWebcam(data.webcam_name, {
        image: `data:image/png;base64,${data.image}`,
        timestamp: data.timestamp,
        stats: data.stats,
        num_detections: data.num_detections
    });
});

// Cette fonction se declenche toute seule quand le backend trouve une image YOLO
socket.on('new_detection', (data) => {
    console.log("Nouvelle detection recue", data);
    
    // Mise a jour de l'image
    liveImage.src = data.image_url;
    liveImage.style.display = "block";
    placeholder.style.display = "none";
    
    // Mise a jour des stats
    statsLive.style.display = "grid";
    countVal.innerText = data.num_detections;
    timeVal.innerText = data.datetime;
    
    // Affichage des détections par classe
    if (data.detection_count && Object.keys(data.detection_count).length > 0) {
        detectionsDetails.style.display = "block";
        detectionList.innerHTML = "";
        
        for (const [className, count] of Object.entries(data.detection_count)) {
            const item = document.createElement('div');
            item.style.padding = "8px 0";
            item.style.borderBottom = "1px solid #ddd";
            item.innerHTML = `<strong>${className}</strong>: ${count}`;
            detectionList.appendChild(item);
        }
    } else {
        detectionsDetails.style.display = "none";
    }
    
    statusBar.style.background = "#fff3e0";
    statusBar.innerText = "Derniere detection recue a " + data.datetime;
});