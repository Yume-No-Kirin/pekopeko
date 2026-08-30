# Backlog complet Pekopeko (vue indépendante)

Cette liste a été construite en lisant l'intégralité de `specs/` (product, domain, architecture, decisions, modules, ux-design), `docs/ROADMAP.md`, `AGENTS.md` et les trois tickets existants (`TASK-001`, `TASK-002` complétés, `TASK-003` en backlog), **sans consulter** `specs/tasks/BACKLOG.md`. Elle vise à couvrir tout ce que le corpus de specs décrit comme nécessaire — pas seulement un scope V1 minimal — pour servir de point de comparaison. Chaque entrée reste volontairement résumée (objectif + traçabilité) : ce n'est pas un ticket rédigé, juste de quoi savoir ce qu'il faudrait écrire et pourquoi.

Constat de départ : les tickets existants ferment le flux `SOURCE → EXTRACTION → PROPOSAL → REVIEW → CANONICAL` pour les **Assertions** uniquement (TASK-001/002), et s'arrêtent à l'extraction (pas encore la revue) pour **Entity/Event/Relationship** (TASK-003). Tout le reste des 18 cas d'usage (`specs/product/use-cases.md`), des 16 capacités CAP-CORE (`specs/architecture/capabilities.md`), du choix frontend ADI-009 (React tranché, aucun scope V1 ni ticket écrit) et des modules de domaine (`specs/modules/`) n'a encore aucun ticket.

---

## 1. Knowledge Core — déjà ticketé

### TASK-001 — Module d'ingestion de données (Assertions)
**Statut : completed.** Pipeline `SOURCE → EXTRACTION → PROPOSAL` pour les Assertions à partir de sources `.md`, provider LLM pluggable (ADI-008), détection de doublon exact par hash, état de tâche minimal. Implémente UC-001/UC-007/UC-016 pour ce seul type de connaissance.

### TASK-002 — Workflow de revue des propositions (Assertions)
**Statut : completed.** Ferme `PROPOSAL → HUMAN REVIEW → CANONICAL` (UC-011, CAP-CORE-002) pour les propositions de type `assertion` : listing, détail, accept/reject uniquement (pas d'édition, pas de bulk).

### TASK-003 — Extraction Entity/Event/Relationship
**Statut : backlog (rédigé, prochain à implémenter).** Même pipeline que TASK-001 mais pour Entity/Event/Relationship ; s'arrête à PROPOSED, ne résout pas encore les endpoints de relation vers des IDs canoniques.

---

## 2. Knowledge Core — cycle de vie proposition/canonique (manquant)

### TASK-004 — Mécanisme de configuration locale
Un système de config unique (fichier ou variables d'environnement, local, par appareil, jamais dans le vault) pour choisir le provider LLM actif, l'emplacement de l'index de retrieval et celui de l'état de tâche. Requis implicitement par ADI-002, ADI-005 et ADI-008, mais aucun ticket ne le formalise encore — TASK-001/003 supposent juste qu'il existe.

### TASK-005 — Revue des propositions Entity/Event/Relationship
Miroir de TASK-002 pour la sortie de TASK-003 : listing/détail/accept/reject pour `proposed_item_type` entity/event/relationship, plus la résolution des `endpoints` d'une relation acceptée vers des IDs canoniques stables (ADI-003), une fois ses propres endpoints eux-mêmes acceptés.

### TASK-006 — Statut EDITED et historisation des Proposals
Introduit `PROPOSED → EDITED` (édition du contenu d'une proposition avant décision) et, comme TASK-002 l'exige explicitement, le mécanisme `history/` pour les Proposals à ce moment-là (ADI-001, INV-004) — jusqu'ici différé car aucune proposition n'avait encore son contenu modifié.

### TASK-007 — Index de retrieval local
Implémente ADI-002 : recherche full-text dérivée et reconstructible sur les fichiers canoniques, jamais dans le vault. V1 en mémoire au démarrage, puis SQLite/FTS5 local si le scan devient coûteux. Sert de fondation à CAP-CORE-010 (RTR-001..003) et au futur TASK-035.

### TASK-008 — Structure d'adjacence pour la traversée de relations
Implémente ADI-003 : structure de graphe dérivée des enregistrements de relations canoniques, jamais persistée dans le vault, reconstruite par appareil. Sert CAP-CORE-009 (RQR-001..006) et est un pré-requis pour TASK-010 et TASK-032.

### TASK-009 — Correction et supersession de connaissance canonique
Implémente UC-010 (Correction Propagation) : accepter une correction sur un item déjà canonique marque l'original `SUPERSEDED` (jamais réécrit silencieusement), écrit la nouvelle version, et déclenche une tâche asynchrone d'analyse d'impact sur les dépendants (ADI-005 règle 3).

### TASK-010 — Suivi des dépendances et staleness du savoir dérivé
Implémente AP-007/CAP-CORE-006 (KSR-011/012, DTR-001) : graphe de dépendances entre savoir dérivé et ses sources, marquage `STALE` quand une source change. Dépend de TASK-008 pour la traversée et alimente TASK-009.

### TASK-011 — Détection de contradictions
Implémente INV-006 : détecter des assertions/relations potentiellement contradictoires dans le canonique et les présenter en revue humaine plutôt que de les résoudre silencieusement (RNR-001, UC-009 en partie).

### TASK-012 — Détection de modification de source et quasi-doublons
Étend TASK-001/003 au-delà du hash exact : détecter qu'une source déjà ingérée a été *modifiée* (pas juste identique) et signaler les items dérivés potentiellement affectés (UC-003, parties riches d'UC-016).

### TASK-013 — Couche d'orchestration de tâches asynchrones
TASK-001/003 ne définissent qu'un enregistrement d'état par tentative, pas un vrai ordonnanceur. Ce ticket implémente une exécution/reprise réelle de tâches concurrentes (TKR-001/002) pour que plusieurs ingestions/extractions/analyses puissent tourner et être suivies en parallèle.

### TASK-014 — Couche d'autorisation domaine et cross-domaine
Implémente explicitement AP-005/AP-006, INV-008/INV-009, CAP-CORE-005/014 : un mécanisme d'autorisation pour les opérations cross-domaine (UC-009, UC-018), au-delà du simple paramètre `domain` passé explicitement dans TASK-001/002/003.

### TASK-015 — Monitoring de santé de la connaissance
Implémente UC-012 (Knowledge Health) et la capacité "à définir" citée par ce cas d'usage : détection de propositions orphelines, endpoints de relation cassés, provenance manquante, savoir dérivé périmé (s'appuie sur TASK-010).

### TASK-016 — Raisonnement temporel et conflits d'agenda
Implémente TMR-001..005 : détection de conflit de planning (UC-004) et gestion des besoins récurrents avec calcul de prochaine occurrence/retard (UC-013).

### TASK-017 — Workflow d'incertitude et statut contesté
Étend UQR-001/002 (UC-017) au-delà de l'enum `direct/inferred/uncertain/contested` déjà écrite par TASK-001/003 : scores de confiance, suivi et résolution d'un statut contesté dans le temps.

### TASK-034 — Opérations de masse, filtrage et priorisation de la file de revue
Implémente CAP-CORE-015 (UXR-001) et les étapes d'UC-011 explicitement laissées de côté par TASK-002 : catégorisation, actions groupées, tri/filtre au-delà d'un simple filtre de statut, priorisation.

### TASK-035 — Moteur de raisonnement et d'explication
Implémente RNR-001/002 pour deux cas d'usage concrets : répondre à une question sur une source précise en distinguant contenu source et interprétation (UC-014), et expliquer le raisonnement derrière une décision passée à partir de sa provenance (UC-005).

---

## 3. Ingestion & Extraction — extensibilité (manquant)

### TASK-018 — Lecteurs de sources additionnels
Ajoute des `SourceReader` pour PDF, texte brut et page web dans le registre déjà établi par TASK-001/003 — aucune modification du pipeline requise par construction (UC-007).

### TASK-019 — Ingestion audio/vidéo avec transcription
Ajoute un chemin d'ingestion pour YouTube/TikTok/Instagram avec transcription (Whisper ou équivalent), tel que montré dans les métadonnées spécifiques par type de source des maquettes UX (`pekopeko-proposal-detail.html`) et UC-007.

### TASK-020 — Second provider LLM concret
Implémente un second provider (par ex. Anthropic ou OpenAI) derrière l'interface `extract()` d'ADI-008, pour prouver en conditions réelles que changer de provider est un changement de config et non de code.

---

## 4. Interface (ADI-009 tranche React, aucun ticket n'existe encore)

### TASK-021 — Cadrage V1 de l'interface
ADI-009 tranche uniquement le framework (React) et dit explicitement que "le scope V1 de l'interface et son découpage en tickets restent à faire". Ce ticket définit les écrans du V1, le contrat avec le backend, le routing et l'outillage de build, avant toute implémentation.

### TASK-022 — Couche API backend pour le Knowledge Core
Aujourd'hui, TASK-001/002/003 n'exposent que des fonctions Python (contrainte explicite : "no GUI or CLI required"). Ce ticket expose ingestion/revue/extraction/retrieval via une API (REST ou équivalent) que le frontend React peut consommer.

### TASK-023 — Écran Dashboard React
Implémente `pekopeko-dashboard.html` en React (ADI-009) : statistiques (ingestions actives, propositions en attente, taux d'acceptation), cartes de modules, navigation.

### TASK-024 — Écran Validation/Revue React
Implémente `pekopeko-workflow.html` : vue unifiée des propositions groupées par source, badge de statut épistémique, folder-path builder interactif, actions individuelles et groupées par source.

### TASK-025 — Écran Logs d'ingestion React
Implémente `pekopeko-ingestion.html` : liste des tâches d'ingestion/extraction avec filtres (statut, domaine, date), détail des erreurs et rejets — s'appuie sur TASK-013 pour avoir un état de tâche réel à afficher.

### TASK-026 — Écran Détail de proposition React
Implémente `pekopeko-proposal-detail.html` : sélecteur de proposition, contenu éditable, rendu spécifique par type de source (Markdown/YouTube/Instagram/TikTok), provenance (provider/modèle/température), actions accepter/rejeter.

### TASK-027 — Support backend pour l'organisation en dossiers
Les maquettes UX montrent un "folder-path builder" permettant de ranger une note acceptée dans une arborescence choisie par l'utilisatrice, au-delà du chemin fixe `<domain>/<type>/<id>/` écrit par TASK-001/002/003. Ce ticket ajoute l'API listant/créant ces dossiers d'organisation.

---

## 5. Modules de domaine (aucun n'existe, seul le Knowledge Core est ticketé)

### TASK-028 — Module Personal Planning V1
Premier module de domaine concret construit sur le Knowledge Core : événements personnels, détection de conflit d'agenda (UC-004), besoins récurrents (UC-013) — consomme TASK-016.

### TASK-029 — Module Fiction V1
Isolation d'univers fictionnels (UC-018, MOD-002), génération de profil de personnage consolidant connaissance directe/inférée/incertaine (UC-002).

### TASK-030 — Module Research V1
Suivi d'une question de recherche, collecte de sources, synthèse et détection d'incertitude entre sources (UC-008).

### TASK-031 — Module apprentissage de langue V1
Suivi de vocabulaire, niveau de maîtrise, planification de révision (UC-006) — un seul module pour japonais/anglais au V1, la vision (`specs/product/vision.md`) les cite comme deux capacités futures distinctes mais aucun cas d'usage ne les différencie techniquement.

### TASK-032 — Opération d'analyse cross-domaine
Implémente UC-009 (ex. compatibilité entre charge de publication et objectifs d'apprentissage japonais) comme opération explicite et autorisée (CAP-CORE-014), traçable à ses domaines source — s'appuie sur TASK-014 et TASK-008.

---

## 6. Dette technique assumée

### TASK-033 — Consolidation du stockage/frontmatter dupliqué
TASK-001 et TASK-003 dupliquent délibérément leur logique d'écriture atomique et de validation de frontmatter plutôt que de dépendre d'un module commun (décision produit explicite). Une fois les patterns stabilisés sur plusieurs tickets, ce ticket factorise cette logique dans un module partagé, sans casser l'indépendance déjà en place entre `ingestion/`, `review/` et `extraction/`.
