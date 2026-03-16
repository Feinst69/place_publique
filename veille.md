# Place Publique

# Choix des modèles et performances

# Quels sont aujourd’hui les principaux modèles de détection d’objets utilisés en vidéosurveillance ? (YOLOv8/YOLO11, Faster R-CNN, DETR, etc.)

En vidéosurveillance (caméras urbaines, parkings, ports, gares, stations de ski…), on utilise majoritairement des modèles de **détection “généralistes”**, adaptés ensuite par fine‑tuning au contexte local.

On peut les classer en **3 grandes familles**.

---

## **1️ - Famille YOLO (You Only Look Once) — le standard industriel**

| **Modèle** | **Pourquoi il est très utilisé** |
| --- | --- |
| YOLOv5 | Très stable, léger, facile à déployer |
| YOLOv8 | Très bonne précision + rapide |
| YOLO11 (2025) | Encore plus précis et plus léger |
| YOLO‑NAS | Optimisé pour edge (Jetson, caméras intelligentes) |

### **Avantages**

- **Temps réel** (20–100 FPS selon matériel)
- Très bon rapport **précision / vitesse**
- Simple à fine‑tuner
- Large écosystème (tracking, export ONNX, TensorRT, etc.)

### **Inconvénients**

- Moins précis sur petits objets très denses (foules serrées)
- Performances sensibles à la qualité caméra

**C’est aujourd’hui le choix n°1 en vidéosurveillance et smart city.**

---

## **2️ - Famille Two‑Stage (Faster R‑CNN, Mask R‑CNN)**

| **Modèle** | **Spécificité** |
| --- | --- |
| Faster R‑CNN | Très précis mais lent |
| Mask R‑CNN | Ajoute la segmentation |

### **Avantages**

- Très grande précision
- Bon pour analyses fines, forensics, annotation offline

### **Inconvénients**

- **Trop lents pour du temps réel**
- Coûteux en calcul
- Peu utilisés en production live

**Utilisés surtout en recherche ou analyse a posteriori.**

---

## **3️ - Famille Transformers (DETR, Deformable DETR, RT‑DETR)**

| **Modèle** | **Spécificité** |
| --- | --- |
| DETR | Transformer pur, simple à entraîner |
| Deformable DETR | Corrige la lenteur de DETR |
| RT‑DETR | Version temps réel (2024–2025) |

### **Avantages**

- Très bonne précision
- Meilleure stabilité dans les foules

### **Inconvénients**

- Plus lourds à déployer
- Écosystème plus jeune
- Besoin GPU plus costaud

**Montent fortement en 2025 dans les villes “smart city”.**

---

## **4️⃣ Comparatif rapide**

| **Critère** | **YOLOv8/11** | **Faster R‑CNN** | **RT‑DETR** |
| --- | --- | --- | --- |
| Temps réel | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| Précision | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Facilité déploiement | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Usage vidéosurveillance | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

# Quels compromis font-ils entre vitesse d’inférence, précision (mAP) et consommation de ressources pour un déploiement temps réel sur du matériel limité ?

## **Définition de la mAP**

**mAP (mean Average Precision)** est la métrique standard pour évaluer un modèle de détection d’objets.

Elle mesure **à quel point un modèle détecte correctement les objets ET place correctement leurs boîtes**.

Concrètement, la mAP combine :

- **Précision** : proportion de détections correctes
- **Rappel** : capacité à ne pas rater d’objets
- **Qualité du positionnement** des boîtes (IoU)

Une mAP de **0,45** signifie que le modèle est correct en moyenne dans **45 % des cas selon le critère officiel**.

Une mAP de **0,60+** est considérée comme très bonne en vidéosurveillance.

---

## **🔺 Le triangle vitesse – mAP – ressources**

On ne peut jamais maximiser les trois :

| **Si on optimise…** | **On sacrifie…** |
| --- | --- |
| la vitesse | la mAP |
| la mAP | la vitesse |
| la légèreté | la stabilité |

---

## **Compromis réels sur matériel limité (Jetson / mini‑PC)**

| **Modèle** | **FPS** | **mAP** | **RAM/VRAM** | **Usage** |
| --- | --- | --- | --- | --- |
| YOLO11n / v8n | ⭐⭐⭐⭐⭐ 30–60 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Edge ultra léger |
| YOLO11s / v8s | ⭐⭐⭐⭐ 20–40 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Sweet spot |
| YOLO11m | ⭐⭐⭐ 10–20 | ⭐⭐⭐⭐½ | ⭐⭐⭐ | Haute qualité |
| RT‑DETR‑R18 | ⭐⭐⭐ 10–25 | ⭐⭐⭐⭐½ | ⭐⭐⭐ | Foule dense |
| Faster R‑CNN | ⭐ 2–5 | ⭐⭐⭐⭐⭐ | ⭐ | Trop lourd |

---

## **Choix industriels**

Les villes et opérateurs préfèrent :

> 40 FPS avec 95 % de détection plutôt que 3 FPS avec 99 %
> 

Car un comptage lent fausse les statistiques.

---

## ** Optimisations edge**

| **Technique** | **Gain** |
| --- | --- |
| Quantization INT8 | ×2 vitesse, –1–2 % mAP |
| TensorRT / ONNX | +40–100 % FPS |
| Résolution 640 → 480 | ×2 FPS, –3–5 % mAP |

# Quelles bonnes pratiques permettent d’évaluer rigoureusement un modèle de détection d’objets sur des scènes de caméras fixes (métriques mAP, précision/rappel par classe, IoU, analyse d’erreurs) afin de garantir la fiabilité des statistiques de comptage dans des conditions réelles (jour/nuit, pluie, foule dense) ?

## **1️ -  Définitions indispensables**

### **🔹 IoU — *Intersection over Union***

L’IoU mesure la qualité du placement d’une boîte détectée par rapport à la vérité terrain.

IoU=Surface d’intersectionSurface d’union

*IoU*=Surface d’unionSurface d’intersection

- IoU = 1 → boîte parfaite
- IoU ≥ 0,5 → détection considérée comme correcte
- Plus l’IoU est élevé, plus la localisation est précise.

---

### **Précision / Rappel**

| **Mesure** | **Signification** |
| --- | --- |
| **Précision** | Parmi les objets détectés, combien sont corrects |
| **Rappel** | Parmi les objets présents, combien sont détectés |

En comptage :

- Faible rappel → on **sous‑compte**
- Faible précision → on **sur‑compte**

---

### ** mAP (mean Average Precision)**

La mAP est la moyenne de la précision du modèle sur toutes les classes et tous les seuils IoU.

Elle mesure :

- la qualité de détection
- la qualité de localisation
- la stabilité du modèle

> En vidéosurveillance, une mAP ≥ 0,50 est exploitable,≥ 0,60 est très bonne.
> 

---

## **2 -  Bonnes pratiques d’évaluation sur caméras fixes**

### ** 1. Tester par conditions réelles**

Ne jamais tester uniquement “au soleil”.

Le jeu de test doit contenir :

| **Condition** | **Pourquoi** |
| --- | --- |
| Jour / Nuit | Variation d’éclairage |
| Pluie / neige / brouillard | Reflets, silhouettes floues |
| Foule dense | Occlusions |
| Angles fixes | Ombres, perspective |
| Heures creuses / pleines | Taille d’objets variable |

On calcule **une mAP par scénario**, pas seulement une mAP globale.

---

### ** 2. Analyse par classe**

Exemple :

| **Classe** | **Précision** | **Rappel** | **Impact** |
| --- | --- | --- | --- |
| Personne | 0.94 | 0.88 | OK |
| Vélo | 0.81 | 0.52 | Sous‑comptage important |
| Bus | 0.97 | 0.96 | Excellent |

Permet d’identifier les biais du modèle.

---

### ** 3. Analyse d’erreurs visuelles**

Toujours analyser manuellement :

| **Erreur** | **Cause typique** |
| --- | --- |
| Personnes non détectées | Occlusion, nuit |
| Doubles détections | Ombres |
| Faux positifs | Poteaux, reflets |
| Mauvais classement | Scooter ↔ vélo |

 Ces erreurs impactent directement le **comptage**.

---

### ** 4. Indicateurs dédiés au comptage**

En plus de la mAP, on mesure :

| **Indicateur** | **Formule** |
| --- | --- |
| MAE (Mean Absolute Error) | |compte réel – compte prédit| |
| MAPE (%) | % d’erreur de comptage |
| Error Bias | Sur‑ ou sous‑comptage systématique |

👉 Ce sont **les métriques clés pour votre projet**.

---

### ** 5. Stabilité temporelle**

On vérifie que les statistiques ne “tremblent” pas :

- variance du comptage à l’heure creuse
- cohérence heure → heure
- pas de pics aberrants

---

## **3️ - Critères de validation “acceptables” (réalistes)**

| **Critère** | **Seuil recommandé** |
| --- | --- |
| mAP globale | ≥ 0,55 |
| MAE de comptage | ≤ 10 % |
| Biais systématique | ≈ 0 |
| Faux positifs nocturnes | très faibles |
| Stabilité horaire | élevée |

# Données, annotation et robustesse

# Comment sélectionner, combiner et annoter des datasets (Roboflow Universe, datasets de trafic, webcams publiques) pour couvrir la
variété des contextes clients (places, ports, stations de ski) tout en contrôlant la taille du dataset pour un entraînement faisable sur
laptop/Colab ?

## **1️ - Sélection des datasets**

### **Sources pertinentes**

| **Source** | **Utilité** |
| --- | --- |
| **Roboflow Universe** | Datasets prêts à l’emploi (people, traffic, boats, bikes…) |
| UA‑DETRAC | Trafic routier |
| VisDrone | Piétons + vues en hauteur |
| MARVEL / Seaships | Bateaux & ports |
| Webcams publiques | Réalisme (angles fixes, météo réelle) |

👉 On choisit **2–3 domaines clients max** pour rester maîtrisable.

---

## **2️ - Principe clé : Dataset “équilibré mais compact”**

### **Taille cible recommandée (MVP)**

| **Classe** | **Nb images** |
| --- | --- |
| Personnes | 1 000 – 1 500 |
| Véhicules | 800 – 1 200 |
| Bateaux / skieurs | 500 – 800 |
| **Total** | **3 000 – 4 000 images max** |

Suffisant pour un fine‑tuning efficace

Compatible Colab / laptop GPU

---

## **3️⃣ Combinaison des sources**

On construit un **dataset multi‑domaines** :

| **Domaine** | **%** |
| --- | --- |
| Urbain (places, rues) | ~50 % |
| Portuaire | ~25 % |
| Station de ski | ~25 % |

Empêche le modèle d’être biaisé “ville uniquement”.

---

## **4️ - Annotation & harmonisation**

### **Problème**

Chaque dataset a :

- ses propres noms de classes,
- ses propres règles d’annotation.

### **Solution**

Créer un **schéma commun minimal** :

| **Classe finale** | **Exemples fusionnés** |
| --- | --- |
| person | pedestrian, people |
| car | car, van |
| bus | bus |
| bike | bike, scooter |
| boat | boat, ship |
| skier | skier, snowboarder |

 Harmonisation via Roboflow / scripts Python.

---

## **5️ - Réduction intelligente de la taille**

Pour éviter un dataset trop lourd :

| **Technique** | **Effet** |
| --- | --- |
| Limiter images similaires | évite sur‑apprentissage |
| Downsampling 1280→640 | ×4 vitesse d’entraînement |
| Data augmentation | augmente diversité sans ajouter d’images |
| Balance par classe | évite biais (pas 90 % “personnes”) |

---

## **6️ - Validation du dataset**

On crée **3 jeux séparés** :

| **Set** | **Rôle** |
| --- | --- |
| Train | Apprentissage |
| Validation | Choix des hyperparamètres |
| Test multi‑conditions | Jour / nuit / pluie / foule |

# Quelles stratégies d’augmentation de données et d’adaptation de domaine (changement de météo, saison, angle de caméra, résolution)
sont pertinentes pour améliorer la robustesse d’un modèle de détection appliqué à des flux webcams hétérogènes et évolutifs ?

## **Définitions rapides**

- **Augmentation de données** : transformations appliquées aux images d’entraînement pour simuler des variations (lumière, flou, pluie…), sans changer le label.
- **Adaptation de domaine** : techniques pour transférer un modèle d’un domaine source (dataset A) vers un domaine cible (webcams réelles) **quand la distribution d’images diffère**.

---

## **1) Augmentations pertinentes pour webcams**

### **A) Variations photométriques (les + importantes)**

Objectif : jour/nuit, contre-jour, ombres, capteurs cheap.

- **Brightness/Contrast/Gamma**
- **Color jitter** (teinte/saturation)
- **White balance / température de couleur**
- **Ombres synthétiques** (shadow augmentation)
- **Vignetting** léger (caméras bas de gamme)

Impact direct : évite la chute de rappel la nuit / par ciel couvert.

### **B) Météo & atmosphère (robustesse terrain)**

- **Pluie / neige / brouillard** (effets de voile + streaks)
- **Haze/fog** (baisse de contraste)
- **Gouttes sur lentille** (rare mais très réel sur webcams)

⚠️ À faire “modéré” : trop fort = apprentissage sur images irréalistes.

### **C) Qualité vidéo & compression (très réaliste pour webcams)**

- **Downscale / Upscale** (résolution variable)
- **Blur** (motion blur + defocus)
- **JPEG compression artifacts**
- **Noise** (ISO élevé la nuit)

Souvent plus utile que des augmentations “stylées”.

### **D) Géométrie (attention en caméras fixes)**

- **Petites rotations** (±2–5°), **petits shifts/crops**, **perspective légère**
- Éviter gros flips/rotations si la scène a une orientation sémantique (route, port).

### **E) Occlusions & densité (foule)**

- **Cutout / Random erasing**
- **Copy-paste** (coller des objets découpés) pour simuler densité
- **Mosaic/MixUp** (YOLO le fait souvent) utile mais à doser en “caméra fixe”

---

## **2) Stratégies d’adaptation de domaine (quand les webcams changent vraiment)**

### **A) Fine-tuning ciblé “client-like”**

- Prendre un modèle pré-entraîné + **ré-entraîner sur un petit set d’images webcam réelles** (même 200–500 images bien choisies).
- C’est **le meilleur ROI** pour un projet type Place Publique.

### **B) “Hard test set” + rééquilibrage**

Construire un **jeu de test par conditions** : nuit/pluie/foule/résolution basse.

Puis ajuster le dataset (ajouter des exemples là où ça échoue).

### **C) Pseudo-labeling / self-training (si peu d’annotations)**

- Lancer le modèle sur beaucoup d’images webcam non annotées
- Garder les détections **à haute confiance** comme labels approximatifs
- Ré-entraîner → ça “colle” au domaine cible sans tout annoter

### **D) Domain randomization (robustesse générale)**

Augmentations larges (lumière, bruit, compression, météo) pour que le modèle apprenne des invariants.

Très adapté si tu as **peu de clients** mais beaucoup de variabilité.

### **E) Test-Time Adaptation (option avancée)**

Ajuster légèrement certains paramètres (ex. normalisation) **au moment du déploiement** sur un nouveau flux. À garder simple dans un MVP.

---

## **3) Recette “simple et efficace” pour votre projet (MVP)**

1. **Base dataset** multi-domaines (ville/port/ski) mais compact.
2. Augmentations **fortes sur photométrie + compression + blur**, modérées sur géométrie.
3. **Échantillon réel webcam** (50–200 images) pour valider + corriger.
4. Si temps : **pseudo-labeling** sur 1–2 webcams publiques.

# Architecture logicielle, DataOps et MLOps

# Quelles architectures applicatives sont les plus adaptées pour relier flux vidéo, service d’inférence, base de données temporelle et frontend (Flask) : traitement batch périodique vs quasi temps réel, microservices, file de messages, et quels impacts sur la scalabilité et la tolérance aux pannes ?

## **1) Traitement batch périodique (le plus simple, très adapté webcams)**

**Principe :** toutes les *X minutes*, on capture une image (ou un court extrait), on infère, on stocke les compteurs + (option) une image annotée.

**Architecture type**

- **Scheduler** (cron / APScheduler) → déclenche
- **Worker d’inférence** (process séparé) → modèle YOLO/DETR
- **DB time-series** (TimescaleDB/PostgreSQL ou InfluxDB) → **`counts(timestamp, cam_id, class, count)`**
- **Flask** → dashboards + API de lecture

**+ Scalabilité**

- Ajout facile de caméras tant que le worker suit.
- Scaling “vertical” (GPU plus costaud) ou “horizontal” (plusieurs workers).

**+ Tolérance aux pannes**

- Si une inférence rate : tu perds juste un point de mesure, pas tout le système.
- Reprise simple (relancer au tick suivant).

**👉 Recommandation MVP :** batch périodique + workers (Celery/RQ) = meilleur ratio simplicité/robustesse.

---

## **2) Quasi temps réel (streaming léger, “near real-time”)**

**Principe :** on traite plus souvent (ex. 1–5 FPS) ou des mini-bursts, pour alertes rapides (affluence).

**Architecture type**

- Capture continue (RTSP/HTTP) → “frame grabber”
- **Queue** (Redis/RabbitMQ/Kafka) → envoie des “jobs frames”
- **Workers GPU** → inférence + tracking éventuel
- DB time-series + cache (Redis) pour les “dernières valeurs”
- Flask lit DB + cache pour afficher “live”

**+ Scalabilité**

- Très bonne si queue + workers.
- Permet de lisser la charge (backpressure : la queue absorbe les pics).

**– Tolérance aux pannes**

- Si la queue grossit : **latence augmente** (tu n’es plus “temps réel”).
- Il faut des limites (drop frames, priorités, sampling adaptatif).

---

## **3) Monolithe Flask “tout-en-un” (à éviter au-delà du mini proto)**

**Principe :** Flask capture, infère, écrit en DB, sert le front.

**+ Simple** à coder.

**– Scalabilité faible**

- Une requête web lente peut bloquer l’inférence.
- Difficulté à exploiter GPU proprement.
    
    **– Tolérance aux pannes faible**
    
- Si Flask tombe, tout tombe (UI + inférence).

👉 OK pour démo ultra courte, mais pas pour un système “place publique” crédible.

---

## **4) Microservices (prod / multi-clients)**

**Principe :** services séparés, chacun déployable indépendamment.

**Exemple**

1. **Service Ingestion** (capture frames)
2. **Service Inference** (GPU)
3. **Service Storage** (écritures DB + rétention)
4. **Service API/Frontend** (Flask)
- **Message broker** (Kafka/RabbitMQ) entre ingestion et inference

**+ Scalabilité**

- Excellente : tu scales uniquement le goulot (souvent inference GPU).
- Multi-sites / multi-contrats plus propre.

**+ Tolérance aux pannes**

- Un service peut tomber sans tout casser (si la queue et la DB tiennent).
- Rejouabilité (reprocess) possible.

**– Coût complexité**

- Observabilité, versioning d’API, déploiement plus lourd (Docker/K8s).

👉 Souvent “trop” pour un projet, mais tu peux le décrire en **architecture.md** comme cible.

---

## **5) Quel rôle pour la “base temporelle” et le stockage images ?**

- **DB time-series** : métriques de comptage (rapide pour agrégations par heure/jour).
- **Stockage images annotées** : optionnel (debug/qualité). En prod, souvent **rétention courte** + accès restreint.

---

## **Reco concrète “projet Place Publique”**

**Meilleur compromis :** *Batch périodique + file de jobs + workers*

- Flask = UI + API
- **Celery (RabbitMQ/Redis)** ou **RQ (Redis)** = exécution asynchrone
- 1+ workers GPU = inférence
- PostgreSQL/TimescaleDB = séries temporelles

**Pourquoi :**

- Simple, robuste, scalable par ajout de workers
- Tolérant aux pannes (jobs réessayables, pas de blocage UI)
- Suffisant pour des stats d’affluence

Si tu veux, je te rédige aussi un mini schéma (ASCII) + une “phrase de conclusion” prête à coller dans la veille.

# Quels outils et patterns MLOps (MLflow, CI/CD, versioning de modèles, tests automatisés) sont recommandés pour assurer un cycle de vie maîtrisé des modèles de détection d’objets, depuis l’expérimentation jusqu’au déploiement reproductible en production (Docker, cloud/on premise) ?

## ** Objectif MLOps**

Assurer :

- traçabilité des expériences,
- reproductibilité des modèles,
- déploiement maîtrisé (cloud / on‑premise),
- capacité de mise à jour sans casser la production.

---

## **1️ - Suivi d’expérimentation & traçabilité — MLflow**

| **Fonction** | **Utilité** |
| --- | --- |
| Tracking des runs | hyperparamètres, métriques (mAP, MAE…), modèles |
| Artifacts | stockage des poids, config, plots |
| Model Registry | versionnement des modèles validés |
| Comparaison | choisir le meilleur modèle |

👉 Permet de répondre à : *« quel modèle tourne en prod, entraîné avec quelles données ? »*

---

## **2️ - Versioning des données & modèles**

| **Outil** | **Rôle** |
| --- | --- |
| **DVC** | versionner datasets & poids |
| Git | code + pipelines |
| MLflow Registry | versions prod / staging |

👉 Indispensable pour rollback et audit.

---

## **3️ - Tests automatisés (qualité & dérive)**

| **Test** | **Exemple** |
| --- | --- |
| Unit tests | chargement modèle, pipeline |
| Data tests | schéma des labels |
| Perf tests | mAP ≥ seuil |
| Drift tests | baisse de confiance, MAE |

Outils : **`pytest`**, **`great_expectations`**, **`evidently`**

---

## **4️ - CI/CD IA (GitHub Actions / GitLab CI)**

Pipeline type :

1. Push Git
2. Tests → OK
3. Entraînement sur données versionnées
4. Évaluation automatique
5. Enregistrement MLflow
6. Build Docker
7. Déploiement (staging → prod)

---

## **5️ - Déploiement reproductible — Docker**

Chaque modèle = image Docker contenant :

- le modèle MLflow
- le code d’inférence
- les versions exactes des libs

👉 Résultat : même comportement **local / cloud / edge**.

---

## **6️ - Cloud / On‑prem / Edge**

| **Contexte** | **Déploiement** |
| --- | --- |
| Laptop / MVP | Docker + Flask |
| Serveur | Docker Compose |
| Multi‑sites | Kubernetes |
| Edge | Docker + TensorRT |

---

## **7️ - Monitoring en production**

| **Élément** | **Outils** |
| --- | --- |
| Logs | ELK / Grafana |
| Latence | Prometheus |
| Dérive | Evidently |
| Erreurs | Sentry |

# Monitoring, dérive et réentraînement

# Quelles métriques et quels signaux statistiques de distribution, taux de détection, feedback utilisateur, anomalies sur les séries temporelles de comptage) permettent de détecter efficacement la dérive de données ou de concepts dans un système de vidéosurveillance algorithmique, et comment déclencher un processus de réentraînement pertinent ?

## **Définitions rapides**

- **Dérive de données (data drift)** : la distribution des images change (météo, saison, nouvelle caméra, résolution, éclairage).
- **Dérive de concept (concept drift)** : la relation *image → comptage* change (nouveaux usages, foule plus dense, nouveaux types d’objets, travaux…).

---

## **1️ - Signaux statistiques sur les distributions d’images**

| **Signal** | **Ce qu’il mesure** | **Alerte typique** |
| --- | --- | --- |
| Moyenne luminosité | Nuit/jour/saison | Chute ou hausse brutale |
| Histogramme couleurs | Capteur/météo | Divergence > seuil |
| Variance / bruit | Qualité caméra | Hausse brutale |
| Score de similarité (PSI, KL) | Drift global | PSI > 0.2 |

Permet de détecter **avant même que la mAP ne chute**.

---

## **2️ - Signaux côté modèle (qualité des détections)**

| **Signal** | **Drift détecté** |
| --- | --- |
| Confiance moyenne ↓ | modèle “moins sûr” |
| Nb détections / frame ↓ | sous‑détection |
| Faux positifs nocturnes ↑ | bruit lumineux |
| Distribution des classes change | nouveaux usages |

---

## **3️ - Séries temporelles de comptage (le plus parlant)**

| **Indicateur** | **Alerte** |
| --- | --- |
| Pics anormaux | bug / faux positifs |
| Tendance décroissante lente | sous‑détection progressive |
| Variance excessive | instabilité |
| Changement de saison | concept drift |

Outils : détection d’anomalies (Z‑score, EWMA, Prophet, STL).

---

## **4️ - Feedback terrain / utilisateurs**

| **Feedback** | **Signification** |
| --- | --- |
| “On voit plus de monde que vos stats” | sous‑comptage |
| “Pics la nuit” | faux positifs |
| “Depuis la nouvelle caméra ça bug” | drift matériel |

👉 Signal humain = **très fort déclencheur**.

---

## **5️ - Déclenchement du réentraînement (processus pro)**

### **Conditions automatiques (exemples)**

| **Condition** | **Action** |
| --- | --- |
| PSI > 0.25 | marquer drift |
| Confiance moyenne ↓ 15% | flag |
| MAE comptage > 12% | flag |
| 2 flags consécutifs | réentraînement |

---

## **6️ - Pipeline de réentraînement**

1. Collecte images récentes (webcams)
2. Échantillonnage “hard cases”
3. Annotation ciblée (200–500 images)
4. Fine‑tuning
5. Évaluation multi‑scénarios
6. Si amélioration → **MLflow Registry → Prod**

# Quelles approches existent pour intégrer le monitoring de modèles (MLflow, dashboards, alertes) dans une application de vision par
ordinateur en production, afin de suivre à la fois la qualité des prédictions et la santé opérationnelle du pipeline de traitement vidéo ?

## ** Objectif du monitoring**

Suivre **deux dimensions en parallèle** :

| **Axe** | **Ce qu’on surveille** |
| --- | --- |
| **Qualité IA** | dérive, précision, cohérence des comptages |
| **Santé système** | latence, erreurs, files d’attente, disponibilité |

---

## **1️ - Monitoring de la qualité des prédictions (IA)**

### **A) MLflow — traçabilité des modèles**

MLflow permet de :

- suivre les métriques d’évaluation (mAP, MAE, rappel, biais),
- comparer les modèles,
- savoir **exactement quel modèle tourne en production**.

Utilisation :

- chaque nouveau modèle = enregistré dans le *Model Registry*,
- seuils d’acceptation (ex : mAP ≥ 0,55, MAE ≤ 10 %).

---

### **B) Surveillance de la dérive (Evidently / dashboards)**

On suit en production :

| **Indicateur** | **Alerte** |
| --- | --- |
| Confiance moyenne ↓ | modèle instable |
| Distribution des classes change | nouveaux usages |
| PSI / KL divergence | dérive image |
| MAE comptage ↑ | perte de fiabilité |

Outils : **Evidently**, Grafana, Prometheus.

---

## **2️ - Monitoring opérationnel (pipeline vidéo)**

### **A) Indicateurs système**

| **Signal** | **But** |
| --- | --- |
| Latence inférence | fluidité |
| FPS / job/min | débit |
| Queue size | saturation |
| Erreurs worker | pannes |
| GPU / RAM | surcharge |

Outils : Prometheus + Grafana, Sentry (erreurs), Redis Insights.

---

### **B) Alertes automatisées**

| **Condition** | **Action** |
| --- | --- |
| Latence > seuil | alerte |
| Queue > seuil | scale workers |
| Drift détecté | flag réentraînement |
| Erreur répétée | rollback modèle |

---

## **3️ - Dashboards décisionnels (frontend)**

Flask peut afficher :

- courbes de comptage horaire / journalier,
- indicateurs qualité IA (confiance, drift),
- état du pipeline (OK / dégradé / HS).

---

## **4️ - Cycle pro “monitoring → action”**

1. Collecte métriques (Prometheus + Evidently)
2. Visualisation (Grafana / Flask)
3. Alerte automatique
4. Déclenchement CI/CD
5. Réentraînement ou rollback
6. Nouveau modèle validé via MLflow

# RGPD, AI Act et éthique

# Comment les cadres réglementaires RGPD et AI Act classifient-ils les systèmes de vidéosurveillance algorithmique, quelles obligations en découlent (base légale, DPIA, registres, transparence) et quelles pratiques techniques (anonymisation, absence de stockage vidéo, agrégation) sont recommandées pour rester conforme ?

## **1️ - Comment ces systèmes sont classifiés ?**

### **🔹 RGPD (Règlement Général sur la Protection des Données)**

Un système de vidéosurveillance algorithmique est **un traitement de données personnelles** dès lors que :

- il capte des images de personnes **identifiables ou identifiables indirectement**,
- même si l’objectif est seulement statistique (comptage).

Il est donc **pleinement soumis au RGPD**.

---

### **🔹 AI Act (Règlement européen sur l’IA)**

Les systèmes d’analyse vidéo automatisée sont classés selon leur **usage** :

| **Usage** | **Classement** |
| --- | --- |
| Comptage statistique sans identification | **Risque limité** |
| Reconnaissance faciale, suivi biométrique, police | **Haut risque / interdit** |
| Maintien de l’ordre, surveillance ciblée | **Très haut risque** |

Un outil comme Place Publique doit être **explicitement positionné comme “statistique non biométrique”** pour rester en zone “risque limité”.

---

## **2️ - Obligations RGPD principales**

| **Obligation** | **Contenu** |
| --- | --- |
| **Base légale** | Intérêt public / mission d’intérêt public / intérêt légitime |
| **Registre des traitements** | Description du traitement |
| **DPIA (AIPD)** | Analyse d’impact souvent obligatoire en espace public |
| **Information du public** | Panneaux, mentions légales |
| **Sécurité** | Contrôle accès, chiffrement |
| **Minimisation** | Pas plus de données que nécessaire |
| **Durée de conservation** | La plus courte possible |

---

## **3️ - Obligations AI Act (systèmes à risque limité)**

| **Obligation** | **Exigence** |
| --- | --- |
| Transparence | Mention qu’un système automatisé est utilisé |
| Documentation technique | Description du modèle |
| Traçabilité | Versioning des modèles |
| Gouvernance des données | Qualité & biais |
| Supervision humaine | Possibilité d’intervention |

---

## **4️ - Bonnes pratiques techniques recommandées**

| **Pratique** | **Pourquoi** |
| --- | --- |
| **Pas de stockage vidéo** | Réduction maximale du risque RGPD |
| **Agrégation immédiate** | On stocke seulement des compteurs |
| **Floutage automatique** | Si image temporaire conservée |
| **Pas de biométrie** | Interdit / haut risque |
| **Rétention courte (heures/jours)** | Limiter exposition |
| **Logs & audit** | Traçabilité |
| **DPIA documentée** | Conformité démontrable |

# Quels sont les principaux enjeux éthiques liés au comptage automatisé de personnes et de véhicules dans l’espace public (risque
de surveillance de masse, biais sur certaines populations, réutilisation des données) et quelles mesures de conception (privacy by design, limitation des finalités, gouvernance des modèles) peuvent en limiter les risques ?

## **1️ - Enjeux éthiques majeurs**

### ** 1. Risque de surveillance de masse**

Même un système conçu pour du **comptage statistique** peut contribuer à :

- une **normalisation de la surveillance permanente**,
- une perte de confiance des citoyens,
- une extension progressive vers des usages plus intrusifs.

👉 Risque : banalisation d’un contrôle généralisé de l’espace public.

---

### ** 2. Biais et discriminations algorithmiques**

Les modèles peuvent :

- moins bien détecter certaines populations (enfants, personnes âgées, personnes en fauteuil, cyclistes, piétons la nuit),
- sous‑représenter certains usages (mobilités douces),
- produire des statistiques biaisées.

👉 Risque : **décisions publiques inadaptées** (mauvais aménagements, services mal dimensionnés).

---

### **3. Réutilisation ou détournement des données**

Un système de comptage peut être :

- réutilisé pour de l’identification,
- connecté à d’autres bases (profilage),
- étendu vers des finalités non prévues.

👉 Risque : **glissement fonctionnel (function creep)**.

---

## **2️ - Mesures de conception pour limiter les risques (Ethics & Privacy by Design)**

### ** Privacy by Design**

| **Mesure** | **Effet** |
| --- | --- |
| **Pas de reconnaissance faciale** | Empêche toute identification |
| **Agrégation immédiate** | Aucune trajectoire individuelle |
| **Pas de stockage vidéo** | Réduction maximale du risque |
| **Floutage automatique** | Si images temporaires nécessaires |
| **Rétention très courte** | Limite exposition juridique |

---

### ** Limitation stricte des finalités**

- Finalité unique : **statistiques d’affluence**
- Verrouillage des classes détectables
- Interdiction technique des modules biométriques

---

### ** Gouvernance des modèles**

| **Pratique** | **But** |
| --- | --- |
| Documentation des modèles | Transparence |
| Jeux de tests multi‑populations | Réduction des biais |
| Supervision humaine | Contrôle |
| Comité d’usage | Validation des évolutions |
| Journalisation & audits | Traçabilité |

---

### ** Transparence & responsabilité**

- Information claire du public
- Publication des politiques d’usage des données
- Mécanismes de recours

# Pour aller plus loin : Robustesse, dérive et classes inconnues

# Comment passer d’un détecteur « fermé » classique (qui choisit toujours une classe connue) à une approche d’open‑set object
detection capable de signaler des objets inconnus ou « autre » dans une scène réelle de vidéosurveillance ?

## **1️ - Problème du monde réel**

Un détecteur standard (YOLO, Faster‑RCNN, DETR) est **fermé** :

> Tout ce qu’il voit est forcé dans une classe connue,même si l’objet n’existe pas dans le dataset.
> 

Exemples réels :

- un scooter électrique → classé “vélo”
- une trottinette → “personne”
- un chantier → “camion”

👉 Cela **pollue totalement les statistiques**.

---

## **2️ - Principe de l’Open‑Set Detection**

Un modèle open‑set doit pouvoir dire :

> “Je vois bien un objet, mais je ne sais pas ce que c’est.”
> 

Il doit produire 3 sorties possibles :

- classe connue
- classe connue avec doute
- **UNKNOWN / OTHER**

---

## **3️ - Briques techniques pour l’open‑set**

## **A. Détection d’inconnus par confiance adaptative**

### **Idée simple & efficace (recommandée MVP)**

Au lieu d’un seuil fixe (ex: 0.25), on apprend des **seuils par classe** :

si p(classe)<μc−kσc⇒UNKNOWN

- μ, σ = moyenne et variance des confiances par classe
- k ≈ 2–3

Méthode robuste, très utilisée en smart‑city.

---

## **B. OpenMax (extension Softmax)**

Remplace Softmax par **OpenMax** :

- modélise la distribution des “scores corrects”
- calcule la probabilité qu’un objet soit hors‑distribution

 Très bonne détection d’objets jamais vus.

---

## **C. Reconstruction autoencoder (fort mais plus lourd)**

- Un autoencoder est entraîné sur objets normaux
- Si erreur de reconstruction élevée → objet inconnu

---

## **D. Clustering des embeddings (pratique)**

- On extrait le vecteur interne du détecteur (backbone)
- Si trop loin de tout cluster connu → UNKNOWN

Très bon pour découvrir de **nouvelles classes clients**.

---

## **4️ - Architecture Open‑Set recommandée (Place Publique)**

```
YOLO11s
   ↓
Backbone embeddings
   ↓
Classifieur
   ↓
Open‑set filter (OpenMax + seuils adaptatifs)
   ↓
{car, person, bike, ... , UNKNOWN}

```

---

## **5️ - Utilité métier directe**

| **Avant** | **Après** |
| --- | --- |
| Scooter compté comme vélo | Scooter → UNKNOWN |
| Stat faussée | Stat fiable |
| Pas d’alerte | Alerte “nouvel objet” |

# Quelles stratégies (seuils de confiance, incertitude, bruit de fond, pseudo‑labels, zones d’attention) permettent de distinguer un vrai «
objet inconnu » d’un simple faux positif ou d’un bruit de fond dans un modèle de détection ?

## **1️ - Seuils de confiance adaptatifs par classe**

Au lieu d’un seuil global (ex: 0.25), on apprend **la distribution réelle des scores** pour chaque classe :

UNKNOWN si p<μc−kσc

| **Avantage** | **Effet** |
| --- | --- |
| Classe‑aware | évite de rejeter trop de vraies voitures |
| Dynamique | suit la dérive |

👉 Les faux positifs ont une **confiance très basse et instable** → filtrés.

---

## **2️ - Mesure d’incertitude (entropie, margin)**

Un vrai objet inconnu :

- a **une forte incertitude inter‑classes**
- mais une **structure spatiale cohérente**

H(p)=−∑pilog⁡pi

| **Cas** | **Entropie** | **Interprétation** |
| --- | --- | --- |
| Faux bruit | haute | rejet |
| Objet inconnu | haute mais stable | UNKNOWN |
| Objet connu | basse | accepté |

---

## **3️ - Filtrage du bruit de fond (background modeling)**

On apprend un **modèle du fond de la scène** (zones immobiles, textures fixes).

- Si la “détection” ressemble au fond → rejet
- Sinon → candidat UNKNOWN

👉 Évite que les ombres, arbres, reflets deviennent UNKNOWN.

---

## **4️ - Stabilité temporelle (le secret industriel)**

| **Objet** | **Frames consécutives** |
| --- | --- |
| Faux positif | apparaît 1 frame |
| Objet réel | persiste ≥ 3–5 frames |
| Objet inconnu | persiste + déplacement |

👉 On n’accepte UNKNOWN **que s’il persiste**.

---

## **5️ - Pseudo‑labels & clustering**

On regroupe les embeddings :

| **Groupe** | **Décision** |
| --- | --- |
| Cluster cohérent récurrent | nouvelle classe potentielle |
| Points isolés | bruit |

👉 Seuls les clusters persistants deviennent UNKNOWN.

---

## **6️ - Zones d’attention & cohérence spatiale**

On valide qu’un UNKNOWN :

- est dans une zone logique (sol, route, quai),
- a une taille réaliste,
- respecte la perspective.

👉 Un reflet au ciel est éliminé.

---

## **7️ - Recette Place Publique (simple & efficace)**

1. YOLO11s
2. Seuils adaptatifs par classe
3. Entropie + persistance temporelle
4. Clustering embeddings
    
    → UNKNOWN fiable
    

# Comment exploiter les objets détectés comme « inconnus/autre » pour déclencher un processus de ré‑annotation / ré‑entraînement, et transformer progressivement ces inconnus en nouvelles classes utiles pour le client (nouveaux types de véhicules, engins de chantier, équipements saisonniers, etc.)?

## **1️ - Collecte intelligente des UNKNOWN**

Tous les objets détectés comme **UNKNOWN** ne sont **pas** intéressants.

On conserve uniquement ceux qui sont :

| **Critère** | **Pourquoi** |
| --- | --- |
| Persistants ≥ 3 frames | vrais objets |
| Taille & zone cohérentes | pas du bruit |
| Confiance stable | structure réelle |
| Fréquence suffisante | usage réel |

👉 Ce filtre réduit 95 % du bruit.

---

## **2️ - Regroupement automatique (clustering)**

On extrait leurs **embeddings profonds** (vecteurs du backbone) et on les regroupe :

- DBSCAN / HDBSCAN
- k‑means adaptatif

| **Cluster** | **Interprétation** |
| --- | --- |
| Gros cluster stable | **nouvel usage réel** |
| Micro‑cluster | bruit |
| Outliers | ignorés |

---

## **3️ - Boucle de ré‑annotation humaine ultra‑efficace**

On montre à l’annotateur :

> « Voilà 100 images représentatives d’un cluster inconnu »
> 

→ En 10 minutes :

- il nomme la classe (ex : *trottinette*, *dameuse*, *grue*),
- corrige 100 labels,
- et crée une **nouvelle classe métier**.

---

## **4️ - Ré‑entraînement incrémental**

Pipeline :

1. Ajout de la nouvelle classe au schéma
2. Fine‑tuning du modèle existant
3. Tests multi‑conditions
4. Validation MLflow
5. Déploiement continu

⏱️ Cycle complet ≈ 30–60 min sur Colab.

---

## **5️ - Bénéfice client immédiat**

| **Avant** | **Après** |
| --- | --- |
| Trottinettes = vélos | Trottinettes = classe dédiée |
| Dameuse = camion | Dameuse = *engin de piste* |
| Chantier ignoré | Nouvelle classe *grue* |

→ **Statistiques deviennent exploitables métier**.

# Quelles métriques ou protocoles d’évaluation spécifiques à l’open‑set
(taux de détection d’inconnus, calibration de la confiance, analyse des
erreurs sur les classes « autre ») peut‑on utiliser pour juger la robustesse
réelle du système dans un environnement ouvert ?

## **1️ - Taux de détection des inconnus**

### ** UDR — *Unknown Detection Rate***

> Proportion d’objets réellement inconnus correctement classés UNKNOWN.
> 

$$
UDR=UNKOWN_{correct}/UNKOWN_{total}
$$

- Mesure la capacité du système à **repérer de nouveaux usages**.
- En smart‑city, un bon système vise **UDR ≥ 70–85 %**.

---

### ** U-FPR — *False Positive Rate on Unknown***

> Taux d’objets connus classés à tort comme UNKNOWN.
> 

Objectif : **le plus bas possible** (< 10 %).

---

## **2️ - Capacité à rejeter le bruit (fond / faux positifs)**

### **🔹 OSCR — *Open Set Classification Rate***

Courbe qui montre le compromis :

- accepter correctement les classes connues
- rejeter correctement les inconnus

→ équivalent open‑set de la ROC.

---

## **3️ - Calibration de la confiance**

### **🔹 ECE — *Expected Calibration Error***

Mesure si une confiance de 80 % signifie vraiment “80 % de chance d’avoir raison”.

Un mauvais calibrage = **faux UNKNOWN ou faux KNOWN**.

---

## **4️ - Erreurs spécifiques à « autre »**

| **Erreur** | **Signification** |
| --- | --- |
| Known → Unknown | rejet excessif |
| Unknown → Known | pollution des stats |
| Unknown ↔ Unknown | instabilité |

On analyse ces erreurs **par scénario** (nuit, pluie, foule).

---

## **5️ - Métriques métier orientées comptage**

| **Indicateur** | **Pourquoi** |
| --- | --- |
| MAE avec/ sans UNKNOWN | gain réel |
| % d’objets basculés en UNKNOWN | bruit |
| Découverte de nouvelles classes | valeur métier |

---

## **6️ - Protocole d’évaluation recommandé (simple & pro)**

1. Jeu **Known** (classes vues)
2. Jeu **Unknown** (classes jamais vues)
3. Jeu **Background** (bruit)
4. Matrice 3×3 (Known / Unknown / Background)
5. Calcul : mAP + UDR + OSCR + ECE + MAE comptage

# Pour aller plus loin : Backend production : de Flask à gUnicorn

# Pourquoi le serveur intégré de Flask n’est‑il pas une solution adaptée à la production (concurrence limitée, pas de gestion robuste des workers, absence de fonctionnalités avancées de log et de monitoring) et en quoi un serveur WSGI comme gUnicorn répond‑il à ces limites?

Quand tu fais :

```bash
flask run
```

tu lances le **serveur de développement intégré** de Flask (Werkzeug).

Il est conçu **uniquement pour le debug**, pas pour un service réel.

## **Limites majeures**

| **Problème** | **Impact concret** |
| --- | --- |
| **Mono‑processus / mono‑thread** | Une requête lente bloque toutes les autres |
| **Pas de vraie gestion des workers** | Impossible d’exploiter plusieurs cœurs CPU |
| **Crash = service mort** | Pas de redémarrage automatique |
| **Logs très basiques** | Difficile à auditer / monitorer |
| **Pas de timeouts / quotas** | Facilement saturable |
| **Aucune isolation** | Un bug fait tomber toute l’app |

Résultat : **instable, lent, dangereux en prod**.

---

# **Ce que fait un serveur WSGI comme Gunicorn**

Gunicorn est un **serveur d’application WSGI industriel** conçu pour exécuter Flask en production.

Il agit comme une **couche robuste entre Internet et ton app Flask**.

---

## **Ce qu’apporte Gunicorn**

| **Fonction** | **Bénéfice** |
| --- | --- |
| **Multi‑workers** | Exploite tous les cœurs CPU |
| **Isolation des workers** | Un crash n’arrête pas le service |
| **Timeouts / redémarrage auto** | Service toujours disponible |
| **Gestion de la concurrence** | Des dizaines de requêtes en parallèle |
| **Logs structurés** | Monitoring + audit |
| **Intégration Nginx** | Sécurité, SSL, compression |

Exemple :

```bash
gunicorn app:app --workers 4 --timeout 30
```

→ 4 processus Flask indépendants

→ si un worker plante, Gunicorn le relance

→ le service reste UP.

---

# **Différence réelle en prod**

| **Flask dev** | **Gunicorn** |
| --- | --- |
| 1 requête à la fois | 50+ en parallèle |
| Crash = tout tombe | Crash isolé |
| Pas de monitoring | Logs + métriques |
| Non scalable | Scalabilité horizontale |

# Comment architecturer un déploiement typique Flask + gUnicorn (+ éventuellement Nginx) : rôle de chaque composant, gestion des workers, équilibrage de charge, gestion des timeouts pour les requêtes d’inférence lourdes (vision par ordinateur)?

```
Utilisateurs
     ↓
   NGINX
     ↓
 Gunicorn (WSGI)
     ↓
   Flask API
     ↓
 Workers GPU / CPU
```

---

## **1️ - Rôle de chaque composant**

| **Composant** | **Rôle** |
| --- | --- |
| **Nginx** | Reverse proxy, SSL, sécurité, load balancing |
| **Gunicorn** | Serveur WSGI, gestion des workers Flask |
| **Flask** | API + dashboards |
| **Workers d’inférence** | Exécution YOLO / DETR |

---

## **2️ - Pourquoi Nginx devant Gunicorn ?**

| **Fonction** | **Pourquoi** |
| --- | --- |
| Terminaison SSL | HTTPS |
| Limites requêtes | Anti‑DoS |
| Cache statique | Dashboards rapides |
| Load‑balancing | Multi‑serveurs |
| Proxy buffering | Absorbe latence GPU |

---

## **3️ - Gunicorn : gestion des workers**

Règle standard :

```
workers =2 × CPU +1
```

Mais pour de l’IA lourde :

| **Worker type** | **Quand l’utiliser** |
| --- | --- |
| sync | API légère |
| gthread | I/O |
| **uvicorn workers** | API async |
| **workers dédiés GPU** | inference |

Commande recommandée :

```bash
gunicorn app:app \
  --workers 4 \
  --worker-class gthread \
  --threads 2 \
  --timeout 120 \
  --max-requests 500
```

- **`timeout 120`** → inference lourde autorisée
- **`max-requests`** → empêche fuites mémoire

---

## **4️ - Gestion des requêtes lourdes (vision)**

Ne jamais faire l’inférence directement dans Flask.

### **Pattern pro :**

```
Flask API  →  Redis Queue  →  WorkerGPU(Celery/RQ)
```

Avantages :

- pas de timeout HTTP
- isolation GPU
- retry automatique
- scaling horizontal

---

## **5️ - Load balancing**

Nginx peut répartir :

```
upstream inference_backend {
    least_conn;
server10.0.0.1:8000;
server10.0.0.2:8000;
}
→ ajoute/supprime des serveurs GPU sans downtime.
```

---

## **6️ - Tolérance aux pannes**

| **Problème** | **Résolution** |
| --- | --- |
| Worker crash | Gunicorn relance |
| GPU HS | Nginx redirige |
| Surcharge | Queue absorbe |

---

## **7️ - Architecture recommandée Place Publique**

```
Nginx
   ↓
Flask (Gunicorn)
   ↓
Redis Queue
   ↓
WorkersGPU(Docker)
   ↓
PostgreSQL / TimescaleDB
```

# Quelles options de configuration gUnicorn (nombre de workers, worker class sync / gevent, limites de temps, logs) sont particulièrement critiques pour une API de détection d’objets qui doit traiter simultanément plusieurs flux webcams?

## **1️ - Nombre de workers (le plus important)**

Gunicorn = **multiprocess**.

Chaque worker = une instance Flask indépendante.

### **Règle standard :**

```
workers =2 × CPU +1
```

Mais pour une API IA lourde :

| **Cas** | **Recommandation** |
| --- | --- |
| 1 GPU | 1–2 workers max |
| 2 GPUs | 2–4 workers |
| CPU only | 2×CPU +1 |

⚠️ Trop de workers GPU = **crash VRAM**.

---

## **2️ - Worker class (impact direct sur la stabilité)**

| **Worker class** | **Quand** |
| --- | --- |
| **`sync`** | ❌ Mauvais pour IA |
| **`gthread`** | OK si I/O (API légère) |
| **`gevent`** | OK pour streaming |
| **sync + queue workers** | ✅ Recommandé |
| **uvicorn workers (async)** | très bon pour pipelines modernes |

👉 **Jamais d’inférence lourde dans Flask** → utiliser queue GPU.

---

## **3️ - Timeouts (sinon ton API meurt)**

| **Paramètre** | **Reco** |
| --- | --- |
| **`timeout`** | 90–180 s |
| **`graceful-timeout`** | 30 s |
| **`keepalive`** | 5–10 s |

Ex :

```bash
--timeout 150 --graceful-timeout 30 --keep-alive 5
```

---

## **4️ - Protection mémoire (très important pour PyTorch)**

| **Paramètre** | **Pourquoi** |
| --- | --- |
| **`max-requests 500`** | évite fuites mémoire |
| **`max-requests-jitter 50`** | redémarrage étalé |

---

## **5️ - Logs & monitoring**

| **Paramètre** | **Reco** |
| --- | --- |
| **`--access-logfile -`** | stdout |
| **`--error-logfile -`** | stderr |
| **`--log-level info`** | prod |
| **`--capture-output`** | erreurs Python |

---

## **6️ - Configuration type (Place Publique)**

```bash
gunicorn app:app \
  --workers 2 \
  --worker-class gthread \
  --threads 2 \
  --timeout 150 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --max-requests 500 \
  --max-requests-jitter 50 \
  --log-level info \
  --access-logfile - \
  --error-logfile -

```

---

## **7️ - Résultat métier**

| **Mauvais réglage** | **Bon réglage** |
| --- | --- |
| Timeouts | Inference stable |
| Crash VRAM | GPU maîtrisé |
| Saturation | Files absorbent |

# Comment intégrer gUnicorn dans la chaîne CI/CD existante du projet (Dockerfile, commande d’entrée, health checks) afin de passer facilement d’un serveur de dev Flask à un service de prod reproductible?

## **1️ - Dockerfile “prod ready”**

```docker
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Variables Gunicorn
ENV WORKERS=2
ENV TIMEOUT=150

EXPOSE 8000

CMD ["sh", "-c", "gunicorn app:app \
  --bind 0.0.0.0:8000 \
  --workers $WORKERS \
  --timeout $TIMEOUT \
  --max-requests 500 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile -"]
```

➡️ L’image Docker **contient directement Gunicorn**, plus jamais **`flask run`**.

---

## **2️ - Séparation dev / prod**

| **Environnement** | **Lancement** |
| --- | --- |
| Dev | **`flask run`** |
| CI / Prod | **`docker run …`** (Gunicorn inside) |

→ même code, mais **serveur différent**.

---

## **3️ - Health‑check applicatif**

Dans Flask :

```python
@app.route("/health")
defhealth():
return {"status":"ok"}
```

Dans Docker :

```docker
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1
```

➡️ Le pipeline CI/CD sait si le conteneur est **vraiment opérationnel**.

---

## **4️ - Pipeline CI/CD (GitHub Actions exemple)**

```yaml
name:Build&Deploy

on: [push]

jobs:
build:
runs-on:ubuntu-latest
steps:
-uses:actions/checkout@v3
-run:dockerbuild-tplacepublique:latest.
-run:dockerrun-d-p8000:8000placepublique
-run:curl--failhttp://localhost:8000/health
```

➡️ Si le health‑check échoue → **déploiement bloqué**.

---

## **5️ - Scaling & upgrades**

En prod (Docker Compose / Kubernetes) :

```yaml
services:
api:
image:placepublique
deploy:
replicas:3
```

→ Nginx load‑balance automatiquement.

# Pour aller plus loin : Déploiement cloud et scalabilité

# Quelles sont les principales options de déploiement d’un service de vision par ordinateur dans le cloud (VM classique, conteneur Docker sur Kubernetes, serverless type Lambda/Cloud Functions, endpoints
managés type Vertex AI / SageMaker) et quels sont leurs avantages / limites pour un traitement de flux vidéos périodiques ou temps quasi réel ?

## **1) VM classique (Compute Engine / EC2 / Azure VM)**

**Principe :** une ou plusieurs VMs (CPU ou GPU) où tu déploies ton stack (Docker, Gunicorn, workers d’inférence, DB/queue).

**Avantages**

- Très bon contrôle (drivers GPU, versions CUDA, perf stable)
- Simple à mettre en place (MVP → prod)
- Excellent pour **flux continus** ou **quasi temps réel**
- Coût prévisible si charge stable (instances réservées)

**Limites**

- Scalabilité plus manuelle (auto-scaling possible mais à configurer)
- Maintenance (patch OS, monitoring, logs)

**Idéal pour**

- **Traitement périodique** (1 image / X minutes) : ✅ très adapté
- **Quasi temps réel** (1–10 FPS, alertes) : ✅ si VM GPU dimensionnée

---

## **2) Conteneurs + Kubernetes (GKE / EKS / AKS)**

**Principe :** microservices conteneurisés + orchestrateur (auto-scaling, rolling updates), avec nœuds GPU si besoin.

**Avantages**

- Scalabilité horizontale très forte (ajouter des workers GPU/CPU)
- Tolérance aux pannes (pods remplacés automatiquement)
- Déploiements propres (rolling update, blue/green)
- Très bon quand tu as **beaucoup de caméras / clients**

**Limites**

- Complexité (observabilité, réseau, storage, GPU scheduling)
- Surcoût d’exploitation (même si “managé”, ça reste lourd)
- Overkill pour un petit projet si vous êtes 2–3 et 2 webcams

**Idéal pour**

- **Périodique** : si grand volume de caméras
- **Quasi temps réel** : (avec queue + workers GPU), très scalable

---

## **3) Serverless (AWS Lambda / Cloud Functions)**

**Principe :** fonctions déclenchées à la demande (HTTP, événement, cron), sans gérer de serveurs.

**Avantages**

- Très simple côté infra
- Auto-scaling instantané
- Très économique pour **petites charges ponctuelles**

**Limites critiques pour la vision**

- Temps d’exécution limité + “cold start”
- GPU rarement dispo / contraintes fortes
- Pas adapté au streaming continu
- Le packaging ML (PyTorch/YOLO) peut être lourd

**Idéal pour**

- **Périodique léger** (ex: une image ponctuelle, modèle compact) : parfois OK
- **Quasi temps réel / multi-webcams** :  généralement non

---

## **4) Endpoints managés ML (Vertex AI / SageMaker / Azure ML Endpoints)**

**Principe :** tu déploies un modèle sur un endpoint géré (autoscale, monitoring, versions).

**Avantages**

- Déploiement “entreprise” (versions, scaling, IAM)
- Monitoring et MLOps mieux intégrés
- Bon pour “appel API d’inférence” standardisé

**Limites**

- Coût souvent élevé si appel fréquent (webcams → beaucoup de requêtes)
- Moins naturel pour du **streaming** (on fait plutôt “frames → API”)
- Gestion GPU/latence dépend du service + de la config

**Idéal pour**

- **Inférence à la demande** (upload d’images, pics de trafic) : ✅
- **Webcams quasi temps réel** : possible mais souvent cher / moins optimal qu’une VM GPU ou K8s

---

## **Reco simple pour “flux webcams” (Place Publique)**

- **MVP / quelques webcams (2–20)** : **VM GPU + Docker + Gunicorn + queue (Redis/Celery) + DB time-series**
- **Beaucoup de webcams / multi-clients** : **Kubernetes + workers GPU + message queue**
- **Serverless** : seulement si vous faites **du périodique très léger** et un modèle ultra-compact (et encore)
- **Vertex/SageMaker** : utile si vous voulez surtout un **endpoint standard** et une gouvernance ML “pro”, mais attention au coût à haute fréquence

Si tu me dis “périodique (toutes les 5 min) ou quasi temps réel (toutes les 1–2 sec) + nombre de webcams”, je te donne le **choix optimal** + une **architecture cible** en 6 lignes.

# Comment concevoir une architecture scalable où le service d’inférence est conteneurisé (Docker) et déployé sur un orchestrateur
(Kubernetes, ECS, AKS, GKE) afin d’ajuster automatiquement le nombre de workers de détection en fonction du nombre de webcams et du volume de requêtes ?

## **1) Principe clé**

Tu veux **découpler** :

- **Ingestion** (récupération images/frames depuis webcams)
- **Inférence** (GPU/CPU, coûteux)
- **Stockage + Frontend** (Flask)

Et surtout : **mettre une file de messages** entre ingestion et inférence, sinon tu autoscalerais sur de la latence HTTP (fragile).

## **2) Architecture cible (scalable + tolérante aux pannes)**

**Flux**

1. **`ingestor`** (pods) lit chaque webcam (1 image/5 min, ou 1 FPS, etc.)
2. pousse des jobs dans une **queue** (Kafka / RabbitMQ / SQS / Redis Streams)
3. **`detector-worker`** (pods GPU) consomme la queue, fait l’inférence, écrit résultats
4. **`api`** (Flask + Gunicorn) sert dashboards + API (lit la DB, pas la queue)

**Composants**

- Queue : **absorbe les pics** et permet le “backpressure” (si surcharge, on accumule au lieu de tomber)
- DB time-series : TimescaleDB/Postgres ou InfluxDB pour les compteurs
- Object storage (optionnel) : S3/GCS/Azure Blob pour images annotées (rétention courte)

## **3) Autoscaling “pro” des workers**

### **Sur Kubernetes (AKS/GKE/EKS)**

Tu as 2 niveaux d’autoscaling :

**A) HPA (Horizontal Pod Autoscaler)**

- Scale les **`detector-worker`** selon :
    - CPU/GPU utilization (GPU via métriques NVIDIA + Prometheus)
    - ou requêtes/sec si tu fais de l’inférence en HTTP (moins recommandé que queue)

**B) KEDA (recommandé si queue)**

- Scale **sur la longueur de file** / le lag Kafka / SQS depth / RabbitMQ queue length
- Exemple de logique :
    - si **`queue_length`** monte → augmente le nombre de workers
    - si **`queue_length`** retombe → réduit automatiquement

Pour du multi-webcams, **KEDA + queue** est souvent le meilleur déclencheur : c’est directement “la demande réelle”.

### **Sur ECS (AWS)**

- Même logique :
    - SQS depth / Kafka lag / CloudWatch metrics
    - ECS Service Auto Scaling ajuste le nombre de tasks **`detector-worker`**

## **4) Dimensionnement et règles simples**

- **Batch périodique (1 image / X minutes)** :
    
    Le volume dépend surtout de **`nb_webcams / X`**. Tu scales sur le débit de jobs.
    
- **Quasi temps réel** :
    
    Tu dois aussi limiter le débit (sample, drop frames) sinon tu “poursuis” une queue infinie.
    

Règles pratiques :

- 1 GPU = **1 à quelques workers** selon le modèle et la VRAM (sinon OOM)
- Prévoir une stratégie de **priorité** (certaines webcams plus importantes)
- Mettre un **deadline / TTL** : si un job est trop vieux, on le jette (sinon tu traites en retard)

## **5) Fiabilité et tolérance aux pannes**

Indispensables :

- **ack/retry** dans la queue (si un worker crash, le job revient)
- **idempotence** côté stockage (job_id unique) pour éviter double écriture
- **circuit breaker** sur une webcam qui time-out (ne pas bloquer tout l’ingestor)
- **liveness/readiness probes** + autoscaling safe

## **6) Ce que ça donne “Place Publique” (simple et scalable)**

- **`flask-api`** (Gunicorn) : stable, peu de charge
- **`ingestor`** : 1 pod peut gérer N webcams (selon latence réseau)
- **`queue`** : Redis/RabbitMQ/Kafka (selon ambition)
- **`detector-worker`** : autoscalé via KEDA/HPA (GPU)
- **`timeseries-db`** : compteurs + agrégations

Si tu veux, je peux te donner une **version “MVP Kubernetes”** (manifests YAML : Deployment + Service + HPA/KEDA + probes) en restant générique (sans dépendre d’un cloud particulier).

# Dans quels cas un déploiement « edge » (Docker sur une machine sur site, cluster on‑premise) est‑il préférable au full cloud pour ce type d’application (latence, confidentialité, coûts de bande passante) et comment intégrer cette contrainte dans l’architecture proposée pour ce projet?

## **1️ - Cas où le edge est objectivement meilleur**

| **Problème** | **Full cloud** | **Edge** |
| --- | --- | --- |
| **Latence** | 50–300 ms réseau | **<10 ms** |
| **Bande passante** | Vidéo coûte cher | **Images traitées localement** |
| **Confidentialité RGPD** | Données sortent du site | **Données restent sur site** |
| **Réseau instable** | Service dégradé | **Fonctionne offline** |
| **Coûts à long terme** | Très cher à l’échelle | **Coût fixe faible** |

👉 Donc **edge préférable** si :

- **5 webcams sur un site**
- zones sensibles (mairie, port, gare, hôpital)
- besoin d’alertes rapides
- RGPD strict / refus d’envoyer de la vidéo au cloud
- connectivité faible

---

## **2️ - Architecture edge recommandée**

```
Webcams locales
      ↓
Mini‑serveurEdge(Docker)
  - Ingestor
  - Redis Queue
  - WorkersGPU(YOLO)
  - DBlocale(TimescaleDB)
      ↓
Envoi vers Cloud :
  - Comptages agrégés (JSON)
  - Alertes

```

**Jamais de vidéo brute envoyée au cloud**

Seulement des statistiques.

---

## **3️ - Cloud devient “centre de contrôle”**

Le cloud sert uniquement à :

- dashboards globaux
- comparaison multi‑sites
- sauvegardes
- monitoring / MLOps

```
Sites Edge  →  Cloud central  →  Dashboards
```

---

## **4️ - Coût réel (exemple)**

| **Solution** | **Coût 3 ans** |
| --- | --- |
| 10 webcams full cloud | ~8 000 – 12 000 € |
| 1 mini‑serveur edge GPU | **~1 500 – 2 000 €** |

---

## **5️ - Intégration dans votre projet Place Publique**

Votre projet peut être **hybride** :

- **Edge = inference & stockage**
- **Cloud = supervision & MLOps**

Exactement le modèle utilisé par :

- villes intelligentes
- ports
- stations de ski
- parkings

# Quelles bonnes pratiques de monitoring et d’observabilité cloud (logs centralisés, métriques, traces, dashboards) doit‑on ajouter à MLflow pour suivre à la fois la santé du cluster (CPU/GPU, mémoire) et la qualité des prédictions (drift, erreurs, temps de réponse) à grande échelle ?

## ** Objectif**

Surveiller simultanément :

| **Axe** | **Ce qu’on veut voir** |
| --- | --- |
| **Infra** | CPU, GPU, RAM, VRAM, latence, erreurs |
| **Pipeline** | files d’attente, débit, saturation |
| **Qualité IA** | dérive, biais, faux positifs, stabilité |
| **Métier** | cohérence du comptage |

---

# **1️ - Logs centralisés**

### **Outils**

- ELK Stack (Elasticsearch + Logstash + Kibana)
- ou Grafana Loki
- ou Cloud Logging (GCP / AWS / Azure)

### **Logs essentiels**

| **Log** | **Pourquoi** |
| --- | --- |
| Début/fin inférence | latence |
| Score moyen modèle | dérive |
| Nb objets/frame | anomalies |
| Exceptions GPU | pannes |
| UNKNOWN rate | open‑set drift |

---

# **2️ - Métriques infra (Prometheus)**

À exporter :

| **Métrique** | **Alerte** |
| --- | --- |
| GPU VRAM > 90 % | risque crash |
| Queue length ↑ | saturation |
| Inference latency ↑ | surcharge |
| Erreurs / min | panne |
| FPS ↓ | perte temps réel |

→ Visualisation : **Grafana**

---

# **3️ - Qualité des prédictions (Evidently + MLflow)**

| **Signal** | **Utilité** |
| --- | --- |
| PSI / KL divergence | drift image |
| MAE comptage | fiabilité |
| Confiance moyenne | instabilité |
| Distribution classes | nouveaux usages |
| UNKNOWN rate | open‑set drift |
- MLflow = versions & historique
- Evidently = dérive en production
- Grafana = dashboards temps réel

---

# **4️ - Traces & latence**

- OpenTelemetry
- Jaeger / Tempo

→ permet de voir :

- temps réseau
- temps queue
- temps GPU

---

# **5️ - Dashboards types**

| **Dashboard** | **Contenu** |
| --- | --- |
| **Infra GPU** | VRAM, charge, crash |
| **Pipeline** | backlog, débit |
| **IA Quality** | drift, MAE |
| **Métier** | comptage par heure |
| **Alertes** | SLA / erreurs |

---

# **6️ - Alertes automatiques**

| **Condition** | **Action** |
| --- | --- |
| Queue > seuil | autoscale |
| Drift détecté | flag ré‑entraînement |
| GPU > 95 % | alerte |
| MAE > 12 % | rollback |

---

# **7️ - Architecture cible**

```
Workers GPU → Prometheus → Grafana
          → Loki/ELK
          → Evidently
          → MLflow

```