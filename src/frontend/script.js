const socket = io();

const liveImage = document.getElementById('liveImage');
const placeholder = document.getElementById('placeholder');
const countVal = document.getElementById('count-val');
const timeVal = document.getElementById('time-val');
const statsLive = document.getElementById('stats-live');
const statusBar = document.getElementById('status-bar');
const detectionsDetails = document.getElementById('detections-details');
const detectionList = document.getElementById('detection-list');

socket.on('connect', () => {
    statusBar.innerText = "Statut : Connecte au serveur de surveillance";
});

// Cette fonction se declenche toute seule quand le backend trouve une image
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