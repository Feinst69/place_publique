# Conformité du projet Place Publique

## 1. Objet du document
Ce document formalise les exigences de conformité applicables au projet **Place Publique** (capture webcam, détection d'objets par IA, stockage des résultats, dashboard et monitoring).

## 2. Portée
Sont couverts:
- la collecte des données (snapshots webcam),
- l'inférence IA (person/car),
- la persistance en base,
- la visualisation et les API,
- l'exploitation en environnement de production.

## 3. Cadre réglementaire et référentiels
### 3.1 Protection des données
- **RGPD / GDPR** (UE 2016/679), si données personnelles potentiellement traitées.
- Principe de minimisation des données.
- Principe de limitation de la conservation.

### 3.2 Sécurité
- Bonnes pratiques OWASP (API/web).
- Gestion des secrets (pas de clé API en dur dans le code).
- Contrôle d'accès et traçabilité.

### 3.3 IA responsable
- Transparence sur le fonctionnement du modèle et ses limites.
- Suivi de performance et dérive.
- Processus de rollback modèle.

## 4. Données traitées
### 4.1 Données d'entrée
- Images de webcams publiques (sources externes).
- Métadonnées capture: date/heure, source caméra.

### 4.2 Données générées
- Images annotées (boîtes de détection).
- Résultats JSON (classe, confiance, compte).
- Enregistrements DB (`detection_main`, `detection_class`).

### 4.3 Données personnelles
- Risque possible de présence de personnes visibles sur image.
- Le projet doit être considéré **potentiellement sensible** et traité avec prudence (durée de conservation, contrôle d'accès, finalité explicite).

## 5. Mesures de conformité implémentées / recommandées
## 5.1 Minimisation
- Ne stocker que les champs strictement nécessaires:
  - timestamp,
  - source,
  - compteurs et classes,
  - image_url.
- Éviter le stockage de données d'identification non nécessaires.

### 5.2 Conservation
- Définir une politique de rétention:
  - images brutes: 5 jours,
  - images annotées: 10 jours,
  - logs techniques: 30 jours,
  - agrégats statistiques: conservation longue possible.
- Prévoir purge automatique planifiée.

### 5.3 Sécurité technique
- Chiffrement en transit (TLS) en production.
- Chiffrement au repos des volumes sensibles.
- Accès restreint aux DB et dashboards.
- Authentification sur endpoints d'administration.
- Rotation des secrets (API keys).

### 5.4 Journalisation & audit
- Journal des actions d'administration.
- Journal des changements modèle (version, date, auteur, métriques).
- Logs d'erreurs et incidents de disponibilité.

### 5.5 Gouvernance IA
- Versionner les modèles (`yolo11l`, `yolo11x`, fine-tuned).
- Suivre la performance (précision, rappel, latence).
- Définir un seuil de qualité minimal avant mise en prod.
- Prévoir rollback automatique en cas de régression.

## 6. Monitoring conformité en production
### 6.1 Indicateurs techniques
- disponibilité API,
- latence p95,
- taux d'erreur,
- backlog ingestion/traitement.

### 6.2 Indicateurs IA
- distribution des classes détectées,
- évolution des scores de confiance,
- dérive de distribution (data drift / prediction drift).

### 6.3 Alertes
- absence de données entrantes pendant N minutes,
- chute brutale des détections,
- hausse anormale faux positifs présumés,
- erreurs répétées scraping/inférence.

## 7. Gestion des risques
- **Risque vie privée**: présence de personnes sur images.
  - Mitigation: rétention courte, accès restreint, anonymisation optionnelle.
- **Risque biais modèle**: performance variable selon contexte/luminosité.
  - Mitigation: datasets diversifiés, ré-entrainement périodique.
- **Risque disponibilité**: dépendance sources webcam externes.
  - Mitigation: retry, circuit breaker, supervision.

## 8. Exigences opérationnelles minimales avant production
1. Authentification et contrôle d'accès activés.
2. TLS actif pour API/dashboard.
3. Politique de rétention documentée et automatisée.
4. Sauvegarde/restauration DB testée.
5. Monitoring + alerting actifs.
6. Processus de gestion de dérive documenté.

## 9. Checklist conformité (prête audit)
- [ ] Finalité du traitement documentée.
- [ ] Inventaire des données stockées validé.
- [ ] Durées de conservation définies.
- [ ] Purge automatique implémentée.
- [ ] Secrets externalisés (pas en dur).
- [ ] Accès API/admin sécurisés.
- [ ] Journal d'audit activé.
- [ ] Versioning modèle et rollback validés.
- [ ] Indicateurs monitoring en place.
- [ ] Procédure incident et support définie.

## 10. Décisions spécifiques au projet (état actuel)
- Le système utilise actuellement SQLite (adapté dev/proto).
- Migration recommandée vers PostgreSQL en production.
- Les modèles YOLO sont configurables via variables d'environnement.
- Les alertes de dépassement de seuil sont visibles dans `/stats`.

## 11. Actions prioritaires recommandées
1. Ajouter authentification (JWT/session) sur les endpoints sensibles.
2. Passer en base PostgreSQL + sauvegardes chiffrées.
3. Mettre en place purge planifiée des images.
4. Ajouter pseudo-anonymisation (floutage) si usage public étendu.
5. Formaliser une procédure DPIA si nécessaire selon contexte d'exploitation.

---

## Résumé
Le projet est techniquement structuré pour évoluer vers la conformité production, mais nécessite le renforcement des volets **sécurité, rétention, gouvernance IA et protection des données** avant un déploiement à large échelle.
