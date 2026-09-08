# Backlog complet Pekopeko — v2, priorité GUI (vue indépendante)

Ce document ne remplace ni `specs/tasks/BACKLOG-CLAUDE.md`, ni les tickets déjà rédigés dans
`specs/tasks/backlog/`/`specs/tasks/completed/` — il les reprend et les **réordonne** autour
d'une seule contrainte demandée par Cleo le 2026-08-31 : rendre le système visualisable/testable
via une interface le plus tôt possible, plutôt que de continuer à empiler des capacités Knowledge
Core invisibles avant d'atteindre l'interface. `BACKLOG-CLAUDE.md` reste la référence pour le
contenu détaillé de chaque capacité ; ce fichier reprend les mêmes ~33 entrées (TASK-005..035
dans son ancienne numérotation) mais change leur ordre, leur regroupement backend/frontend, et
renumérote tout ce qui n'est pas déjà écrit à partir de `TASK-007`.

Comme `BACKLOG-CLAUDE.md`, chaque entrée reste un résumé (objectif + traçabilité), pas un ticket
rédigé au format `specs/tasks/README.md` — à détailler en ticket complet au moment de la
prioriser réellement.

---

## 0. Déjà écrit ou complété — inchangé

Ces six entrées existent déjà comme fichiers dans `specs/tasks/` et ne sont pas retouchées ici.
Voir `docs/ROADMAP.md` (« Tickets et implémentation ») pour leur état à jour.

- **TASK-001** — Module d'ingestion de données (Assertions). `completed`.
- **TASK-002** — Workflow de revue des propositions (Assertions). `completed`.
- **TASK-003** — Extraction Entity/Event/Relationship. `completed`.
- **TASK-004** — Mécanisme de configuration locale. `completed`.
- **TASK-005** — Revue des propositions Entity/Event/Relationship. `completed` (2026-09-05,
  `specs/tasks/completed/TASK-005-entity-event-relationship-review.md`).
- **TASK-006** — Statut EDITED et historisation des Proposals. `completed` (2026-09-01,
  `specs/tasks/completed/TASK-006-proposal-edit-and-history.md`).

Trois tickets satellites supplémentaires ont été rédigés le 2026-08-31, après ce document,
pendant l'écriture de TASK-009/010/011 — ils n'étaient pas prévus dans la renumérotation
initiale ci-dessous mais sont des dépendances réelles du socle GUI (section 1) :

- **TASK-001a** — Métadonnées de provenance d'extraction enrichies. `completed` (2026-08-31).
  Étend TASK-001, requis pour la section Provenance de TASK-011
  (`specs/tasks/completed/TASK-001a-extraction-provenance-metadata.md`).
- **TASK-001b** — Journal d'événements de tâche (ingestion/extraction). `completed` (2026-08-31).
  Étend TASK-001 et TASK-003, requis pour les sections logs de TASK-009 et TASK-011
  (`specs/tasks/completed/TASK-001b-task-event-log.md`).
- **TASK-007a** — Pagination des endpoints de listing. `completed` (2026-09-02). Étend TASK-007,
  requis par TASK-009 et TASK-010 pour une pagination serveur réelle
  (`specs/tasks/completed/TASK-007a-list-endpoint-pagination.md`).

Statuts de cette section 0 remis à jour le 2026-09-07 (revue de cohérence) : les six entrées
ci-dessus étaient toutes encore marquées `backlog` alors qu'elles sont `completed` depuis les
2026-08-31 → 2026-09-05. `docs/ROADMAP.md` reste la source d'état faisant foi.

---

## 1. Socle GUI (TASK-007 → TASK-012)

Objectif de ce socle : brancher une interface sur ce qui existe déjà (TASK-001..004) et sur ce
qui est déjà spécifié (TASK-005), avant de continuer à construire des capacités Knowledge Core
supplémentaires. Chaque écran cité correspond à une maquette de `specs/ux-design/` (ADI-009,
React). Les écrans de ce socle restent volontairement en MVP : chemin canonique fixe
`<domain>/<type>/<id>/` (pas de folder-path builder) et actions individuelles uniquement (pas de
bulk actions) — ces deux éléments visibles dans les maquettes deviennent des tâches dédiées juste
après le socle (section 2) pour ne pas retarder le premier rendu visuel.

### TASK-007 — Couche API backend pour le Knowledge Core
Expose `ingestion`, `extraction`, `review` (accept/reject) et `config` (lecture) via une API HTTP
(REST ou équivalent), au-dessus des fonctions Python pures existantes (contrainte explicite de
TASK-001/002/003 : "no GUI or CLI required" — cette contrainte tombe ici). Pré-requis obligatoire
avant tout écran : aucune des tâches suivantes de ce socle ne peut être construite sans ce
connecteur. Correspond à l'ancien `TASK-022` de `BACKLOG-CLAUDE.md`. Étendu par le satellite
**TASK-007a** (pagination serveur des endpoints de listing), requis avant TASK-008.

### TASK-008 — Scaffold React + écrans Dashboard et Settings
Met en place le projet React (ADI-009) : routing, outillage de build, structure de composants.
Implémente `pekopeko-dashboard.html` (statistiques : ingestions actives, propositions en attente,
taux d'acceptation ; cartes de modules ; navigation) via l'API de TASK-007 (dont TASK-007a pour
les compteurs, cf. dépendance ajoutée dans le ticket lui-même). Ajoute un écran Settings basique
(nouveau, absent des maquettes UX, demandé explicitement par Cleo) qui affiche en lecture seule
la configuration locale de TASK-004 (provider LLM actif, domaine par défaut, emplacements — dans
les limites de ce que TASK-004 expose déjà ; décision explicite de Cleo du 2026-08-31 : pas
d'édition en V1, superséde la formulation "visualise/édite" initiale de cette entrée). Correspond
aux anciens `TASK-021` (cadrage V1) + `TASK-023` (Dashboard) de `BACKLOG-CLAUDE.md`, plus l'écran
Settings qui n'existait dans aucune des deux versions du backlog.

### TASK-009 — Écran Logs d'ingestion
Implémente `pekopeko-ingestion.html` : liste des tâches d'ingestion/extraction avec filtres
(statut, domaine, date), détail des erreurs et rejets — lit l'état de tâche minimal déjà produit
par TASK-001/003 (pas encore le vrai ordonnateur de TASK-013/ancien TASK-013, qui viendra
enrichir cet écran plus tard sans le remplacer). Rend visible pour la première fois le travail
déjà `completed` de TASK-001/TASK-003. Dépend des satellites **TASK-007a** (pagination) et
**TASK-001b** (journal d'événements, détail par tâche). Correspond à l'ancien `TASK-025`.

### TASK-010 — Écran Validation (Assertions)
Implémente `pekopeko-workflow.html`, scope Assertions uniquement (miroir du scope de TASK-002) :
vue des propositions groupées par source, badge de statut épistémique, actions individuelles
accepter/rejeter via l'API de TASK-007. Dépend du satellite **TASK-007a** (pagination). Sans
folder-path builder ni bulk actions (voir note d'introduction de la section). Rend visible pour
la première fois le workflow déjà `completed` de TASK-002. Correspond à l'ancien `TASK-024`,
réduit au scope assertion-only pour matcher ce qui existe réellement à ce stade.

### TASK-011 — Écran Détail de proposition (Assertions)
Implémente `pekopeko-proposal-detail.html`, scope Assertions uniquement : contenu, métadonnées,
provenance (provider/modèle/température), actions accepter/rejeter (avec motif de rejet).
Rendu spécifique par type de source limité à Markdown à ce stade (seul type que TASK-001 lit).
Sections Provenance et Logs dépendent des satellites **TASK-001a** et **TASK-001b**
respectivement, mais dégradent proprement si ceux-ci ne sont pas encore implémentés (non
bloquants). Correspond à l'ancien `TASK-026`, réduit au même scope que TASK-010.

### TASK-012 — Revue Entity/Event/Relationship (backend + frontend)
Backend : implémente TASK-005 tel qu'il est déjà rédigé (listing/détail/accept/reject pour
`proposed_item_type` entity/event/relationship, résolution des `endpoints` vers des IDs
canoniques). Frontend : étend les écrans Validation (TASK-010) et Détail (TASK-011) pour couvrir
les 3 types restants (rendu des `endpoints`, du `entity_type`, des bornes temporelles
`starts_at`/`ends_at`). Ferme la visualisation de TASK-003. Regroupe TASK-005 (déjà écrit,
inchangé) et la tranche frontend des anciens `TASK-024`/`TASK-026` qui en dépendait.

---

## 2. Suite re-priorisée (TASK-013 → TASK-037)

Après le socle, chaque entrée associe une capacité Knowledge Core à sa contrepartie GUI quand une
maquette ou un écran déjà construit est concerné — en une tâche unique ou en deux (backend puis
frontend) selon que la partie frontend est petite (intégrée à la tâche) ou substantielle (tâche
séparée). L'ordre continue de privilégier ce qui rend quelque chose de nouveau visible/testable
sur ce qui reste purement backend.

### TASK-013 — Édition de proposition (EDITED + historique)
Backend : implémente TASK-006 tel qu'il est déjà rédigé (`edit_proposal`, statut `EDITED`, mécanisme `history/`). Frontend : ajoute un mode édition dans l'écran Détail (TASK-011/012) —
champs éditables selon l'allow-list de TASK-006, bouton de sauvegarde appelant `edit_proposal`.
Regroupe TASK-006 (déjà écrit, inchangé) et la tranche frontend correspondante de l'ancien
`TASK-026`.

### TASK-014 — Organisation en dossiers (folder-path builder)
Backend : API listant/créant les dossiers d'organisation au-delà du chemin fixe
`<domain>/<type>/<id>/` utilisé jusqu'ici. Frontend : intègre le "folder path builder" interactif
des maquettes (`[segment ▼] / [segment ▼] [+ Ajouter]`) dans les écrans Validation (TASK-010) et
Détail (TASK-011/012). Rapproche ces deux écrans de la fidélité complète aux maquettes UX.
Avec gestion de l'historique du chemin original proposé (`edit_proposal`, statut `EDITED`, mécanisme `history/`).
Correspond à l'ancien `TASK-027`.

### TASK-015 — Opérations de masse et priorisation de la file de revue
Backend + frontend : catégorisation, actions groupées, tri/filtre au-delà du simple filtre de
statut. Ajoute les "bulk actions (accept/reject all)" par source déjà visibles dans la maquette
`pekopeko-workflow.html` mais volontairement absentes du MVP de TASK-010. Correspond à l'ancien
`TASK-034`.

### TASK-016 — Ingestion audio/vidéo avec transcription
Backend : ajoute un chemin d'ingestion pour YouTube/TikTok/Instagram avec transcription (Whisper
ou équivalent). Frontend : étend l'écran Détail pour le rendu spécifique par type de source déjà
prévu par la maquette (`pekopeko-proposal-detail.html` : titre/créateur/durée/URL, transcription
horodatée pour YouTube, légende + transcription audio pour Instagram Reels, hashtags pour
TikTok). Correspond à l'ancien `TASK-019`. À scinder en deux tickets (backend puis frontend) si
la richesse du rendu par plateforme s'avère volumineuse.

### TASK-017 — Lecteurs de sources additionnels
Backend : ajoute des `SourceReader` pour PDF, texte brut et page web au registre déjà établi par
TASK-001/003 — aucune modification du pipeline requise par construction. Frontend : ajustements
mineurs du rendu Détail pour ces nouveaux types de source. Correspond à l'ancien `TASK-018`.

### TASK-018 — Index de retrieval local (backend)
Implémente ADI-002 : recherche full-text dérivée et reconstructible sur les fichiers canoniques,
jamais dans le vault. V1 en mémoire au démarrage, puis SQLite/FTS5 local si le scan devient
coûteux. Pas de frontend dans cette tâche — voir TASK-019. Correspond à l'ancien `TASK-007`.

### TASK-019 — Écran de recherche (frontend)
Consomme TASK-018 via l'API de TASK-007. Le Dashboard des maquettes (TASK-008) référence déjà un
module "Search" à venir dans sa liste de modules à venir — cette tâche le construit. N'existait
sous aucun ID dans `BACKLOG-CLAUDE.md` (le retrieval y était backend-only) : nouvelle entrée créée
par cette re-priorisation GUI-first.

### TASK-020 — Structure d'adjacence pour la traversée de relations (backend)
Implémente ADI-003 : structure de graphe dérivée des enregistrements de relations canoniques,
jamais persistée dans le vault, reconstruite par appareil. Pas de frontend dédié à ce stade (sert
de fondation à TASK-023 et TASK-031). Correspond à l'ancien `TASK-008`.

### TASK-021 — Second provider LLM concret (backend)
Implémente un second provider (par ex. Anthropic ou OpenAI) derrière l'interface `extract()`
d'ADI-008, pour prouver en conditions réelles que changer de provider est un changement de config
et non de code. Le choix du provider actif reste visible/éditable via l'écran Settings de
TASK-008, sans travail frontend supplémentaire. Correspond à l'ancien `TASK-020`.

### TASK-022 — Correction et supersession de connaissance canonique
Backend : implémente UC-010 — accepter une correction sur un item déjà canonique marque
l'original `SUPERSEDED`, écrit la nouvelle version, déclenche une analyse d'impact asynchrone sur
les dépendants. Frontend : indicateur "superseded" dans les écrans concernés (Validation, Détail,
recherche de TASK-019). Correspond à l'ancien `TASK-009`.

### TASK-023 — Suivi des dépendances et staleness du savoir dérivé (backend)
Dépend de TASK-020 pour la traversée. Marque `STALE` le savoir dérivé quand une source change ;
alimente TASK-022 et le futur monitoring de santé (TASK-024). Pas de frontend dédié à ce stade.
Correspond à l'ancien `TASK-010`.

### TASK-024 — Monitoring de santé de la connaissance
Backend : détection de propositions orphelines, endpoints de relation cassés, provenance
manquante, savoir dérivé périmé (s'appuie sur TASK-023). Frontend : panneau de santé sur le
Dashboard (TASK-008), qui liste déjà "Analytics" parmi ses modules à venir. Correspond à l'ancien
`TASK-015`.

### TASK-025 — Détection de contradictions
Backend : détecte des assertions/relations potentiellement contradictoires dans le canonique.
Frontend : surface ces contradictions dans la file de revue (Validation, TASK-010/015) plutôt que
de les résoudre silencieusement. Correspond à l'ancien `TASK-011`.

### TASK-026 — Détection de modification de source et quasi-doublons
Backend : étend TASK-001/003 au-delà du hash exact pour détecter qu'une source déjà ingérée a été
*modifiée*, et signaler les items dérivés potentiellement affectés. Frontend : signalement dans
l'écran Logs d'ingestion (TASK-009). Correspond à l'ancien `TASK-012`.

### TASK-027 — Couche d'orchestration de tâches asynchrones (backend)
TASK-001/003 ne définissent qu'un enregistrement d'état par tentative, pas un vrai ordonnanceur.
Implémente une exécution/reprise réelle de tâches concurrentes. Enrichit l'écran Logs
d'ingestion existant (TASK-009) en données plus riches, sans changement d'écran nécessaire.
Correspond à l'ancien `TASK-013`.

### TASK-028 — Couche d'autorisation domaine et cross-domaine (backend)
Implémente explicitement AP-005/AP-006, INV-008/INV-009, CAP-CORE-005/014 : mécanisme
d'autorisation pour les opérations cross-domaine, au-delà du simple paramètre `domain` explicite
déjà en place. Pré-requis pour TASK-031. Pas de frontend dédié. Correspond à l'ancien `TASK-014`.

### TASK-029 — Raisonnement temporel et conflits d'agenda
Backend : détection de conflit de planning, gestion des besoins récurrents avec calcul de
prochaine occurrence/retard. Frontend : associé selon la granularité nécessaire une fois le
Module Personal Planning (TASK-033) cadré. Correspond à l'ancien `TASK-016`.

### TASK-030 — Workflow d'incertitude et statut contesté
Backend : scores de confiance, suivi et résolution d'un statut contesté dans le temps, au-delà de
l'enum `direct/inferred/uncertain/contested` déjà écrite. Frontend : raffinement des badges de
statut épistémique déjà présents dans Validation/Détail. Correspond à l'ancien `TASK-017`.

### TASK-031 — Opération d'analyse cross-domaine
Dépend de TASK-028 (autorisation) et TASK-020 (traversée). Backend + frontend associé une fois le
cas d'usage concret (ex. compatibilité charge de publication / objectifs d'apprentissage) cadré.
Correspond à l'ancien `TASK-032`.

### TASK-032 — Moteur de raisonnement et d'explication
Backend + frontend associé : répondre à une question sur une source précise en distinguant
contenu source et interprétation, expliquer le raisonnement derrière une décision passée à partir
de sa provenance. Correspond à l'ancien `TASK-035`.

### TASK-033 — Module Personal Planning V1
Backend + frontend associé : premier module de domaine concret construit sur le Knowledge Core —
événements personnels, détection de conflit d'agenda, besoins récurrents. Consomme TASK-029.
Correspond à l'ancien `TASK-028`.

### TASK-034 — Module Fiction V1
Backend + frontend associé : isolation d'univers fictionnels, génération de profil de personnage
consolidant connaissance directe/inférée/incertaine. Correspond à l'ancien `TASK-029`.

### TASK-035 — Module Research V1
Backend + frontend associé : suivi d'une question de recherche, collecte de sources, synthèse et
détection d'incertitude entre sources. Correspond à l'ancien `TASK-030`.

### TASK-036 — Module apprentissage de langue V1
Backend + frontend associé : suivi de vocabulaire, niveau de maîtrise, planification de révision —
un seul module pour japonais/anglais au V1. Correspond à l'ancien `TASK-031`.

### TASK-037 — Consolidation du stockage/frontmatter dupliqué (dette technique)
Backend uniquement, pas de frontend : factorise la logique d'écriture atomique et de validation
de frontmatter dupliquée délibérément entre `ingestion/`, `review/` et `extraction/`, une fois les
patterns stabilisés sur plusieurs tickets. Correspond à l'ancien `TASK-033`.


## 3. Entrées ajoutées par la revue de cohérence du 2026-09-07

Trois entrées issues de la revue de cohérence du 2026-09-07 : deux trous de couverture confirmés en
confrontant les 29 tickets (21 `completed`, 8 `backlog`) et les deux backlogs aux 18 cas d'usage,
plus une exigence d'ADR restée sans porteur (TASK-005a, depuis rédigée en ticket complet). Ils n'existaient sous **aucun ID** dans `BACKLOG-CLAUDE.md` ni
dans les sections 0-2 ci-dessus — ce ne sont donc pas des reclassements, ce sont des manques. Leur
place dans l'ordre de priorité reste à décider par Cleo ; ils sont listés ici, pas insérés d'autorité
dans la section 2.

### TASK-009a — Déclenchement d'une ingestion depuis le GUI

**Rédigé en ticket complet le 2026-09-07** :
`specs/tasks/backlog/TASK-009a-gui-ingestion-trigger.md`, désormais `backlog` (pas encore
implémenté — dépend de TASK-014a). Le sketch ci-dessous est conservé pour son historique/rationale,
mais Cleo a précisé deux points le jour de la rédaction qui en font dévier le ticket réel : (1) un
**vrai upload de fichier** (multipart, écrit dans `_inbox/<domain>/`) plutôt qu'un champ « chemin
local » — la route `chemin local` existante ne convient pas pour un vrai bouton d'upload depuis un
navigateur, qui ne peut pas lire un chemin absolu local ; (2) un **champ `context` optionnel avec
autocomplétion** (ADI-016), absent de ce sketch, ajouté au ticket réel avec TASK-014a comme
dépendance bloquante. L'entrée URL ci-dessous (gated sur TASK-016) est explicitement **hors
périmètre** du ticket réel — à traiter en satellite séparé si besoin une fois TASK-016 fait.

Satellite lettré de TASK-009 (même convention que TASK-001a-f / TASK-007a : ne renuméroter ni les
tickets écrits ni leurs citations croisées). Ajoute à l'écran Logs d'ingestion le bouton
« + Nouvelle ingestion » de la maquette `pekopeko-ingestion.html`, avec un formulaire à deux
entrées : chemin de fichier local (route `POST /domains/<domain>/ingestions`, existante depuis
TASK-007) et URL (route `POST /domains/<domain>/ingestions/url`, apportée par TASK-016) — cette
seconde entrée conditionnée à TASK-016, la première livrable seule.

**Pourquoi.** TASK-009 a délibérément laissé ce bouton non porté, en écrivant « no endpoint exists
to start an ingestion from an arbitrary user-supplied path… **no satellite proposed for it** —
flagging it here rather than silently building a non-functional button ». Le satellite n'a jamais
été écrit, et l'endpoint qui manquait existe depuis TASK-007. Conséquence mesurée le 2026-09-07 :
les six écrans construits **plus les huit tickets `backlog` restants** ne permettent toujours pas
d'alimenter le système autrement qu'en `curl` ou en éditant `config.yaml` à la main — TASK-001f
(surveillance de dossier) est `enabled: false` par défaut et sans UI par son propre « Out of scope ».
TASK-016 aggrave discrètement le trou : il ajoute un wrapper frontend `startUrlIngestion(domain,
url)` qu'aucun composant de son scope n'appelle, donc du code mort à la livraison.

C'est aussi en tension directe avec la posture actée du projet — les maquettes sont la cible, et un
trou GUI donne un ticket satellite additif plutôt qu'une coupe silencieuse (précédent
TASK-001a/001b/007a, décision de Cleo du 2026-08-31).

**Traçabilité.** UC-001, UC-007 (déclenchement d'ingestion), `specs/ux-design/pekopeko-ingestion.html`
(bouton d'en-tête), `specs/tasks/completed/TASK-009-ingestion-logs-screen.md` (V1 scope decisions et
Out of scope), `specs/tasks/backlog/TASK-016-audio-video-ingestion-transcription.md` (Requirements —
le wrapper sans appelant).

### TASK-005a — Organisation en dossiers pour entity/event/relationship (adoption d'ADI-012)

**Rédigé en ticket complet le 2026-09-07, implémenté et vérifié le même jour dans la même
session** : `specs/tasks/completed/TASK-005a-entity-event-relationship-folder-path.md`, désormais
`completed`. Étend le layout d'ADI-012 (aujourd'hui assertion-only) aux trois autres types canoniques, dans ses
deux moitiés : la structure (`entity_path`/`event_path`/`relationship_path` et leurs writers
acceptent des segments, `accept_proposal` les lit, le `FolderPathBuilder` s'affiche pour les
4 types) et la valeur (le provider Ollama d'`extraction/` propose ces segments, une fois par note
et par type). Satellite lettré de TASK-005, dont il amende les writers canoniques.

**Pourquoi c'est une entrée de cette section 3 et pas une entrée de backlog ordinaire.** Ce n'est
pas du travail nouveau : ADI-012 le prescrit déjà (« their canonical writers, once implemented,
**must adopt this same layout** »). Le « future ticket » désigné était TASK-005 lui-même, qui a
choisi le chemin plat une fois implémenté — laissant l'exigence d'une ADR `Accepted` sans porteur.
Trouvé par la revue de cohérence du 2026-09-07, tranché par Cleo le même jour en faveur de
l'adoption complète. TASK-005a acquitte cette exigence ; aucune ADR n'est amendée, ADI-012 est
appliquée.

### TASK-038 — Historisation et consultation de l'état passé d'un item canonique (UC-015)

Backend + frontend associé. Écrit le `history/` d'un item **canonique** (versions complètes,
`lifecycle_status: SUPERSEDED`, jamais de diff — ADI-001) à chaque modification, et expose la lecture
de cet historique : liste des versions d'un item, contenu d'une version donnée, et « quel était
l'état de cet item à telle date ».

**Pourquoi.** UC-015 (« Knowledge Change History ») est le **seul des 18 cas d'usage sans aucune
entrée** nulle part sous `specs/tasks/` — vérifié par recherche exhaustive le 2026-09-07 : ni ticket,
ni entrée dans `BACKLOG-CLAUDE.md`, ni dans les sections 0-2 de ce fichier. Ce n'est pas un oubli
sans conséquence : ADI-001 **impose** un sous-dossier `history/` par item avec les versions complètes
précédentes, et ce mécanisme n'existe aujourd'hui que pour les **Proposals** (TASK-006), donc
uniquement *avant* acceptation. Le cahier de tests le dit sans détour : « Canonical (accepted) items
have no history/versioning mechanism at all ». Un invariant structurant d'ADI-001 n'est donc appliqué
à aucun item canonique, et rien au backlog ne le corrige.

**Relation à TASK-022** (correction et supersession). TASK-022 produirait cet historique comme
*effet de bord* d'une correction. Ce ticket-ci en est distinct sur deux points : il couvre toute
mutation d'un item canonique (pas seulement une correction explicite), et surtout il couvre la
**consultation**, qui est l'objectif propre d'UC-015 et que TASK-022 ne mentionne pas. À implémenter
après ou avec TASK-022, jamais à la place.

**Traçabilité.** UC-015 (intégral), CAP-CORE-004 (Knowledge History), INV-004 (« History Is Never
Silently Destroyed »), INV-018 (« Important Mutations Are Auditable »), ADI-001 (§historisation par
dossier `history/`), `specs/tests/test-plan.md` (§UC-015, « ⛔ Not testable »).

---

## Table de correspondance (ancien ID `BACKLOG-CLAUDE.md` → nouvel ID)

| Ancien | Nouveau | Ancien | Nouveau | Ancien | Nouveau |
|---|---|---|---|---|---|
| TASK-005 | TASK-005 (inchangé ; tranche GUI = TASK-012) | TASK-018 | TASK-017 | TASK-029 | TASK-034 |
| TASK-006 | TASK-006 (inchangé ; tranche GUI = TASK-013) | TASK-019 | TASK-016 | TASK-030 | TASK-035 |
| TASK-007 | TASK-018 | TASK-020 | TASK-021 | TASK-031 | TASK-036 |
| TASK-008 | TASK-020 | TASK-021 | TASK-008 (partiel) | TASK-032 | TASK-031 |
| TASK-009 | TASK-022 | TASK-022 | TASK-007 | TASK-033 | TASK-037 |
| TASK-010 | TASK-023 | TASK-023 | TASK-008 (partiel) | TASK-034 | TASK-015 |
| TASK-011 | TASK-025 | TASK-024 | TASK-010 (+ TASK-012) | TASK-035 | TASK-032 |
| TASK-012 | TASK-026 | TASK-025 | TASK-009 | | |
| TASK-013 | TASK-027 | TASK-026 | TASK-011 (+ 012, 013) | | |
| TASK-014 | TASK-028 | TASK-027 | TASK-014 | | |
| TASK-015 | TASK-024 | TASK-028 | TASK-033 | | |
| TASK-016 | TASK-029 | | | | |
| TASK-017 | TASK-030 | | | | |

Aucune entrée nouvelle sauf TASK-019 (écran de recherche) et l'écran Settings intégré à TASK-008,
tous deux absents de `BACKLOG-CLAUDE.md` parce qu'il n'organisait pas encore le travail autour
d'un GUI précoce. La section 3 ci-dessus (TASK-009a, TASK-038) ajoute deux entrées de plus, le
2026-09-07 — elles ne figurent pas dans cette table : elles n'ont pas d'ancien ID, elles comblent
des trous que ni `BACKLOG-CLAUDE.md` ni ce fichier n'avaient repérés.

**Correction 2026-09-07 (revue de cohérence).** La ligne `TASK-027` de la table ci-dessus
mappait encore l'ancien `TASK-027` (support backend de l'organisation en dossiers) vers
`TASK-013`, alors que le corps de la section 2 le mappe vers `TASK-014` — l'inversion
`TASK-013`/`TASK-014` confirmée par Cleo le 2026-09-04 (voir `docs/ROADMAP.md`, section
TASK-013) avait été répercutée dans les trois tickets concernés et dans ROADMAP, mais pas
dans cette table. Corrigée ici. Les colonnes `TASK-005`/`TASK-006` ont aussi été annotées :
leur numéro est inchangé, mais leur tranche GUI a été extraite en `TASK-012`/`TASK-013`
respectivement — ce que la table seule ne laissait pas voir.
