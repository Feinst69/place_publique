# Rapport de conformité réglementaire  
## Projet **Place Publique** – Analyse automatisée de flux urbains par vision par ordinateur

## 1. Introduction
Le projet **Place Publique** vise à analyser automatiquement des images issues de webcams publiques afin de mesurer la fréquentation d’un espace urbain. Le système utilise un modèle de détection d’objets basé sur **YOLOv8** pour identifier et compter deux classes d’objets : **personnes** et **voitures**. Les images analysées sont mises à jour périodiquement et les résultats sont stockés dans un fichier **CSV** contenant les statistiques de comptage associées aux images traitées.
L’objectif principal est de produire des **indicateurs statistiques de fréquentation et de circulation** dans une rue urbaine, permettant aux collectivités ou aux acteurs économiques de mieux comprendre l’utilisation de l’espace public et d’optimiser la gestion des infrastructures. :contentReference[oaicite:0]{index=0}  
Cependant, l’utilisation de technologies de vision par ordinateur dans l’espace public soulève des enjeux **juridiques, éthiques et réglementaires**, notamment au regard du **Règlement Général sur la Protection des Données (RGPD)** et du **Règlement européen sur l’intelligence artificielle (AI Act)**.
Ce document analyse les implications réglementaires du système et propose des mesures permettant d’assurer une conception conforme au cadre juridique européen.

---

# 2. Analyse des risques liés à la vidéosurveillance algorithmique

## 2.1 Risques pour la vie privée
Les systèmes de vision par ordinateur appliqués à des images captées dans l’espace public peuvent traiter des **données personnelles**, notamment lorsque des personnes apparaissent dans les images. Selon le RGPD, toute information permettant d’identifier directement ou indirectement une personne physique constitue une donnée personnelle (Article 4 du RGPD).
Même si le système ne réalise **aucune reconnaissance faciale**, les images peuvent contenir :
- des visages identifiables
- des comportements individuels
- des informations contextuelles permettant l’identification indirecte d’une personne.

Ces éléments impliquent que le traitement peut relever du cadre juridique de la protection des données.

**Référence :**  
- Règlement Général sur la Protection des Données (RGPD) – Article 4  
https://eur-lex.europa.eu/eli/reg/2016/679/oj

## 2.2 Risque de surveillance de masse
Les technologies de vidéosurveillance algorithmique peuvent contribuer à une **augmentation des capacités de surveillance de l’espace public**, notamment lorsqu’elles sont combinées avec des outils d’analyse automatisée.

Même si le système étudié se limite à un comptage statistique, plusieurs dérives sont théoriquement possibles :
- extension du système vers l’identification biométrique
- utilisation des images à des fins de surveillance comportementale
- croisement avec d’autres bases de données.

Ces risques ont été soulignés par plusieurs institutions européennes qui recommandent l’intégration de principes de **privacy by design** et de **limitation des finalités** dans les systèmes d’intelligence artificielle.

**Références :**
European Data Protection Board – Guidelines on video surveillance  
https://edpb.europa.eu

CNIL – Vidéosurveillance et protection des données  
https://www.cnil.fr/fr/la-videosurveillance-videoprotection-au-travail

## 2.3 Biais algorithmiques et fiabilité des modèles
Les modèles de détection d’objets peuvent présenter des biais liés :
- aux conditions d’éclairage
- aux variations météorologiques
- à la densité de la foule
- à la diversité des scènes urbaines.

Ces biais peuvent conduire à des erreurs de comptage et à une mauvaise estimation des flux de fréquentation.
Pour garantir la fiabilité des statistiques produites, il est nécessaire de mettre en place :
- une **évaluation rigoureuse des performances** du modèle
- un **monitoring continu des résultats**
- des procédures de **réentraînement en cas de dérive du modèle**.

---

# 3. Conformité au RGPD
## 3.1 Qualification juridique du traitement
Le RGPD s’applique lorsque des données personnelles sont collectées ou traitées. Dans ce projet, les images analysées peuvent contenir des personnes et doivent donc être considérées comme **susceptibles de contenir des données personnelles**.
Le traitement correspond à :
**Analyse automatisée d’images issues d’un dispositif de captation dans l’espace public.**
Par conséquent, plusieurs principes fondamentaux du RGPD doivent être respectés.

## 3.2 Base légale du traitement
Conformément à l’article 6 du RGPD, un traitement de données personnelles doit reposer sur une base légale.
Dans le cadre d’un système de comptage de fréquentation dans l’espace public, deux bases juridiques sont généralement envisagées :

### Mission d’intérêt public
Applicable si le système est utilisé par une collectivité territoriale pour :
- analyser la circulation
- améliorer l’aménagement urbain
- optimiser les services publics.

### Intérêt légitime
Applicable dans le cas d’acteurs privés souhaitant analyser la fréquentation d’une zone commerciale.

**Référence :**
Article 6 – RGPD  
https://gdpr-info.eu/art-6-gdpr/

## 3.3 Principe de minimisation des données
Le principe de minimisation impose que seules les données nécessaires à la finalité du traitement soient collectées.
Dans le projet Place Publique, plusieurs mesures contribuent à respecter ce principe :
- détection limitée à deux classes d’objets (personnes, voitures)
- absence de reconnaissance faciale
- absence d’identification individuelle.

Les données enregistrées dans le fichier CSV sont limitées à des informations statistiques.

Exemple de structure :
timestamp, webcam_id, person_count, car_count
2024-03-20T12:00:00, webcam_rue_1, 34, 12

## 3.4 Limitation de la finalité
Le RGPD impose que les données soient collectées pour une finalité spécifique, explicite et légitime.
Dans ce projet, la finalité est strictement limitée à :
- l’analyse statistique de la fréquentation
- l’étude des flux de circulation
- la production de tableaux de bord.

Toute utilisation du système pour :
- identifier des individus
- analyser des comportements
- réaliser de la reconnaissance biométrique
serait contraire à cette finalité et nécessiterait une réévaluation du cadre juridique.

## 3.5 Analyse d’impact relative à la protection des données (DPIA)
Selon l’article 35 du RGPD, une **Analyse d’Impact relative à la Protection des Données (AIPD)** peut être requise lorsque le traitement présente un risque élevé pour les droits et libertés des personnes.

Les critères justifiant une DPIA incluent :
- surveillance systématique d’une zone accessible au public
- utilisation de technologies innovantes
- traitement automatisé d’images.

Dans ce contexte, la réalisation d’une DPIA est recommandée afin d’évaluer :
- les risques pour les individus
- la proportionnalité du système
- les mesures de protection mises en place.

---

# 4. Positionnement du système au regard de l’AI Act
Le **Règlement européen sur l’intelligence artificielle (AI Act)** classe les systèmes d’IA selon leur niveau de risque.

Référence :
European Artificial Intelligence Act  
https://artificialintelligenceact.eu/

## 4.1 Classification du système
Le système Place Publique peut être considéré comme un système d’IA de **vision par ordinateur appliqué à l’analyse statistique de flux urbains**.

Dans la mesure où il ne réalise pas :
- d’identification biométrique
- de reconnaissance faciale
- de profilage individuel
il peut être classé comme **IA à risque limité**.

Cependant, l’utilisation d’IA dans des systèmes de surveillance de l’espace public pourrait être requalifiée en **IA à haut risque** si :
- une identification biométrique était ajoutée
- les données étaient utilisées pour surveiller des individus.

## 4.2 Obligations associées
Même pour un système à risque limité, certaines obligations s’appliquent :
- transparence sur l’utilisation de l’IA
- documentation technique du système
- supervision humaine du système.

---

# 5. Mesures techniques de conformité

## 5.1 Privacy by Design
Le principe de **privacy by design** implique l’intégration de mécanismes de protection des données dès la conception du système.

Dans ce projet, plusieurs mesures contribuent à cette approche :
- limitation des classes détectées
- absence de traitement biométrique
- production de données agrégées.

## 5.2 Limitation de la conservation des images
La conservation des images constitue un risque important pour la vie privée.
Afin de limiter ce risque, il est recommandé de :
- supprimer automatiquement les images après analyse
- conserver uniquement les statistiques agrégées.

Cette approche permet de réduire fortement l’exposition aux risques juridiques.

## 5.3 Sécurité des données
Les données doivent être protégées contre les accès non autorisés.
Mesures recommandées :
- chiffrement des communications (HTTPS)
- authentification des utilisateurs
- journalisation des accès au système.

## 5.4 Gouvernance des modèles d’IA
La gestion du cycle de vie du modèle YOLOv8 doit inclure :
- le versioning des modèles
- le suivi des performances
- la détection de dérive des données.

L’intégration d’outils de MLOps tels que **MLflow** permet de tracer les expérimentations et de garantir la reproductibilité des modèles.

Référence :

MLflow Documentation  
https://mlflow.org/docs/latest/index.html

---

# 6. Conclusion
Le projet Place Publique illustre l’utilisation de technologies de vision par ordinateur pour produire des statistiques de fréquentation à partir d’images de webcams publiques.
Bien que ce type de système présente des bénéfices importants pour la gestion des espaces urbains, il doit être conçu dans le respect du cadre réglementaire européen.

La conformité au **RGPD** et au **AI Act** repose notamment sur :
- la limitation de la finalité du traitement
- la minimisation des données collectées
- la transparence vis-à-vis du public
- l’intégration de principes de **privacy by design**.

Dans sa configuration actuelle — détection d’objets limitée, absence de reconnaissance biométrique et production de statistiques agrégées — le système peut être considéré comme compatible avec les exigences réglementaires, sous réserve de la mise en œuvre de mesures organisationnelles et techniques adaptées.

