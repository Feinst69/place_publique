const socket = io();

// Éléments DOM
const liveImage      = document.getElementById('liveImage');
const placeholder    = document.getElementById('placeholder');
const statusBar      = document.getElementById('status-bar');
const totalImages    = document.getElementById('total-images');
const totalObjects   = document.getElementById('total-objects');
const lastCount      = document.getElementById('last-count');
const lastTime       = document.getElementById('last-time');
const detectionBadges = document.getElementById('detection-badges');
const historyList    = document.getElementById('history-list');
const historyPlaceholder = document.getElementById('history-placeholder');

// --- Chart.js ---
const ctx = document.getElementById('classChart').getContext('2d');
const classChart = new Chart(ctx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'Total détections', data: [],
        backgroundColor: '#e94560', borderRadius: 6 }] },
    options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: '#aaa' }, grid: { color: '#0f3460' } },
            y: { ticks: { color: '#aaa' }, grid: { color: '#0f3460' }, beginAtZero: true }
        }
    }
});

function updateChart(classStats) {
    const ALLOWED = ['person', 'car'];
    const labels = Object.keys(classStats).filter(k => ALLOWED.includes(k));
    const values = labels.map(k => classStats[k].total_detections);
    classChart.data.labels = labels;
    classChart.data.datasets[0].data = values;
    classChart.update();
}

// --- Stats globales (person + car uniquement) ---
const ALLOWED = ['person', 'car'];

// --- Rotation des cameras ---
const camSlots = document.querySelectorAll('.cam-slot');
const currentCameraEl = document.getElementById('current-camera');

function updateCameraIndicator(source) {
    camSlots.forEach(slot => {
        const isActive = slot.dataset.source === source;
        slot.classList.toggle('active', isActive);
    });
    if (currentCameraEl && source) {
        const slot = document.querySelector(`.cam-slot[data-source="${source}"]`);
        currentCameraEl.textContent = slot ? '— ' + slot.querySelector('span').textContent : '';
    }
}

function updateGlobalStats(stats) {
    totalImages.textContent = stats.total_images;
    if (stats.class_stats) {
        const filteredTotal = Object.entries(stats.class_stats)
            .filter(([k]) => ALLOWED.includes(k))
            .reduce((sum, [, v]) => sum + v.total_detections, 0);
        totalObjects.textContent = filteredTotal;
        updateChart(stats.class_stats);
    } else {
        totalObjects.textContent = stats.total_objects;
    }
}

// --- Historique ---
function addHistoryRow(det) {
    if (historyPlaceholder) historyPlaceholder.style.display = 'none';
    const row = document.createElement('div');
    row.className = 'history-row';
    const thumb = document.createElement('img');
    thumb.src = det.image_url;
    thumb.onerror = () => { thumb.style.display = 'none'; };
    const info = document.createElement('div');
    info.className = 'info';
    const counts = det.detection_count || det.class_counts || {};
    const parts = [];
    if (counts.car)    parts.push(`<span style="color:#e94560;font-weight:bold;">${counts.car} car</span>`);
    if (counts.person) parts.push(`<span style="color:#6c63ff;font-weight:bold;">${counts.person} person</span>`);
    const countStr = parts.length ? parts.join(' &nbsp;·&nbsp; ') : `${det.num_detections} objet(s)`;
    info.innerHTML = `
        <div class="time">${det.datetime || (det.date + ' ' + det.time)}</div>
        <div class="count">${countStr}</div>
    `;
    row.appendChild(thumb);
    row.appendChild(info);
    historyList.insertBefore(row, historyList.firstChild);
    while (historyList.children.length > 11) historyList.removeChild(historyList.lastChild);
}

function loadHistory() {
    fetch('/api/detections?limit=10')
        .then(r => r.json())
        .then(data => {
            if (!data || data.length === 0) {
                if (historyPlaceholder) historyPlaceholder.textContent = 'Aucune détection en base de données.';
                return;
            }
            historyList.innerHTML = '';
            data.forEach(det => addHistoryRow(det));
        })
        .catch(() => {
            if (historyPlaceholder) historyPlaceholder.textContent = 'Impossible de charger l historique.';
        });
}

function loadStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(stats => updateGlobalStats(stats))
        .catch(() => {});
}

// --- WebSocket ---
socket.on('connect', () => {
    statusBar.textContent = 'Connecté au serveur de surveillance';
    statusBar.className = 'active';
    loadHistory();
    loadStats();
});

socket.on('disconnect', () => {
    statusBar.textContent = 'Déconnecté — tentative de reconnexion...';
    statusBar.className = '';
});

// Nouvelle image détectée
socket.on('new_detection', (data) => {
    // Image live
    liveImage.src = data.image_url + '?t=' + Date.now();
    liveImage.style.display = 'block';
    placeholder.style.display = 'none';

    // Compteurs de la dernière image (person + car uniquement)
    lastTime.textContent = data.time || data.datetime;
    detectionBadges.innerHTML = '';
    let filteredCount = 0;
    if (data.detection_count) {
        for (const [cls, cnt] of Object.entries(data.detection_count)) {
            if (!ALLOWED.includes(cls)) continue;
            filteredCount += cnt;
            const b = document.createElement('span');
            b.className = 'detection-badge';
            b.innerHTML = cls + '<span>' + cnt + '</span>';
            detectionBadges.appendChild(b);
        }
    }
    lastCount.textContent = filteredCount;

    statusBar.textContent = 'Dernière détection : ' + data.datetime;
    statusBar.className = 'active';

    if (data.source) updateCameraIndicator(data.source);

    addHistoryRow(data);
});

// Stats DB mises à jour après chaque image
socket.on('stats_update', (stats) => {
    updateGlobalStats(stats);
});