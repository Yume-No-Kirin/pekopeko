# Pekopeko — Roadmap de reprise

## Comment utiliser ce fichier

- Ce fichier est le point d'entrée unique pour reprendre le travail sur Pekopeko — que ce soit toi, une nouvelle conversation avec Claude, ou qwen3-coder:30b en local.
- Avant de faire quoi que ce soit sur ce projet, lire ce fichier en entier. Il est volontairement court.
- Après chaque session qui change quelque chose (spec, décision, code), mettre à jour les sections « État actuel » et « Prochaine action exacte » avant de terminer. Ne jamais les laisser désynchronisées de la réalité du dépôt.
- Ce fichier pointe vers les ADR de `specs/decisions/` et les tickets de `specs/tasks/`, il ne les remplace pas. Une décision d'architecture significative vit dans une ADR, pas dans un paragraphe d'ici.

## Démarrage de session (dans cet ordre, à chaque nouvelle conversation)

1. Lire ce fichier en entier.
2. Repérer l'étape en cours dans « Prochaine action exacte » (fin de fichier).
3. Lire la **« Lecture requise »** correspondante (section « Tickets et implémentation » ci-dessous) — les fichiers eux-mêmes, pas un résumé de conversation précédente. Ne rien proposer avant d'avoir fait cette lecture.
4. Lire les ADR de `specs/decisions/` que le ticket cite explicitement — elles contiennent la décision ET sa justification, pas seulement le résultat.
5. Ne poser une question de cadrage à Cleo que si cette lecture ne suffit pas à y répondre. Le corpus existe précisément pour éviter d'avoir à reposer ces questions.

## État actuel

Phase : implémentation des tickets `TASK-XXX` (en cours).

- **Décisions** : ADI-001 à ADI-011 toutes `Accepted` (voir ci-dessous). ADI-011 (contrat
  zero-output des providers) confirmée par Cleo le 2026-09-03. Aucune décision
  d'architecture en attente.
- **Code** : `src/app/ingestion/` (TASK-001, ingestion `.md` → Assertions ; étendu par TASK-001a, provenance d'extraction enrichie, par TASK-001b, journal d'événements de tâche, par TASK-001c, échec explicite sur extraction à zéro résultat (ADI-011), par TASK-001d, détection de doublon basée sur le succès d'une tâche antérieure plutôt que sur la seule existence du fichier source, et par TASK-007, paramètre `task_id`/`list_task_states`), `src/app/review/` (TASK-002, revue des propositions ; étendu par TASK-006, statut EDITED + historisation des Proposals), `src/app/extraction/` (TASK-003, extraction Entity/Event/Relationship ; étendu par TASK-001b, TASK-001c, TASK-001d et par TASK-007, paramètre `task_id`/`list_task_states`), `src/app/config/` (TASK-004, config locale — provider LLM actif, emplacement de l'index de retrieval, emplacement de l'état de tâche), `src/app/api/` (TASK-007, couche API HTTP REST — Flask, ADI-010 ; étendu par TASK-007a, pagination `?limit=`/`?offset=` sur les 3 endpoints de liste), tests sous `src/tests/`. `frontend/` (TASK-008, scaffold React + Dashboard/Settings — premier code frontend du dépôt ; étendu par TASK-009, écran Logs d'ingestion, par TASK-010, écran Validation, dont le bug de statut de groupe par `source_id` est corrigé par TASK-001d, et par TASK-011, écran Détail de proposition — contenu/métadonnées/source/provenance/logs pour une seule proposition, navigation Précédent/Suivant, accepter/rejeter). Ces quinze tickets sont dans `specs/tasks/completed/`.
- **Cahier de tests** (2026-09-02) : `specs/tests/test-plan.md`, tracé aux 18 UC de `specs/product/use-cases.md` et aux 8 tickets `completed`. Deux couches sous `src/tests/` : `acceptance/` (déterministe, appels directs aux pipelines, provider factice fixe — exécutée par défaut) et `e2e/` (serveur Flask réel + vrai Ollama local, marker `pytest -m e2e`, exclue par défaut via `pytest.ini`). **Deux écarts réels découverts et vérifiés contre un serveur réel** (documentés dans le cahier, section « Findings ») : (1) les propositions entity/event/relationship de `extraction/` (contrat `item_type`, pas de champ `id`) sont invisibles pour tout `review/` — `list_proposals` les omet silencieusement et `get_proposal`/`accept` renvoient `400 ValidationError` — pas seulement bloquées côté métier ; (2) l'AC10 de TASK-007 (« accept sur entity/event/relationship → 422 ») ne se déclenche jamais avec une vraie proposition d'extraction (elle renvoie `400` avant d'atteindre ce chemin) — le test existant qui la vérifie construit sa proposition avec le contrat d'`ingestion`/`review`, pas celui réel d'`extraction`. **TASK-005 devra réconcilier les deux contrats de champs, pas seulement ajouter la logique métier d'acceptation.** Problème préexistant signalé au passage (non corrigé, hors périmètre) : `pytest src/tests/` en un seul run échoue à la collecte sur plusieurs `_helpers.py` de même nom sans `__init__.py` — voir la section dédiée du cahier.
- **Suite** : deux tickets `backlog` restent maintenant (TASK-005, TASK-012 —
  TASK-001c, satellite additif à TASK-001+TASK-003 implémentant ADI-011, a été rédigé
  **et** implémenté le 2026-09-03 dans la même session, voir sa propre section ci-dessous,
  désormais `completed` ; TASK-001d, satellite additif à TASK-001+TASK-003 corrigeant
  aussi `Validation.jsx` de TASK-010, rédigé le 2026-09-03 par un autre agent suite à un
  bug réel trouvé en usage par Cleo, a été implémenté et vérifié le 2026-09-03 dans cette
  même session, voir sa propre section ci-dessous, désormais `completed` ; TASK-011,
  écran Détail de proposition, implémenté et vérifié le 2026-09-03 dans cette même
  session, voir sa propre section ci-dessous, désormais `completed`).
  Cœur GUI : TASK-005 (revue
  Entity/Event/Relationship) ne dépend que du contrat de fichiers TASK-001/003 ;
  TASK-008/009/010/011 (scaffold + Dashboard/Settings,
  Ingestion Logs, Validation, Détail de proposition) forment une chaîne de dépendance
  (008→009→010→011, chacun réutilisant les composants/wrappers API du précédent).
  Les quatre maillons de cette chaîne sont désormais tous `completed` — il ne reste que
  TASK-012, qui referme le socle GUI en s'appuyant sur TASK-010/TASK-011 côté frontend et
  sur TASK-005 (toujours `backlog`) côté backend.
  **Trois tickets backend satellites** (2026-08-31, voir leurs sections ci-dessous) ont été
  ajoutés en écrivant TASK-009/010/011, suite à la décision de Cleo que les maquettes
  `specs/ux-design/` sont la cible : là où le backend manquait une donnée qu'une maquette
  montre, un ticket satellite additif comble le trou plutôt que de couper la fonctionnalité
  GUI — TASK-001a (provenance d'extraction enrichie, étend TASK-001, **`completed`** le
  2026-08-31), TASK-001b (journal d'événements de tâche, étend TASK-001+TASK-003,
  **`completed`** le 2026-08-31), TASK-007a (pagination sur les endpoints de liste, étend
  TASK-007, **`completed`** le 2026-09-02 — les trois satellites sont maintenant tous
  `completed`). Suffixe lettré délibéré pour ne renuméroter ni les tickets déjà écrits ni
  leurs citations croisées. Le reste du travail du Knowledge Core (retrieval, etc.) n'est
  pas encore ticketé — voir `specs/tasks/BACKLOG-CLAUDE.md` pour l'inventaire complet avant
  d'écrire le prochain ticket.
- **TASK-012** (revue Entity/Event/Relationship — intégration API + GUI) est maintenant
  rédigé (2026-08-31, `backlog`) : ferme le socle GUI en branchant TASK-005 (backend,
  déjà écrit, repris par référence sans modification) sur les écrans Validation
  (TASK-010) et Détail (TASK-011), jusqu'ici volontairement limités au type `assertion`.
  Ajoute deux points d'intégration que TASK-005 laissait ouverts (il précède la couche
  API) : nommer son erreur typée `UnresolvedRelationshipEndpointError` et l'ajouter à la
  table de mapping d'erreurs de TASK-007 (`src/app/api/app.py`, → `409`) — ce qui
  supersède l'AC10 de TASK-007 (422 pour accept sur entity/event/relationship). Le socle
  GUI (TASK-007 → TASK-012) est donc désormais **entièrement rédigé**.
  `specs/tasks/BACKLOG-CLAUDE-V2.md` (proposition de re-priorisation GUI-first de Cleo,
  2026-08-31) reprend les mêmes ~33 entrées de `BACKLOG-CLAUDE.md` mais réordonnées pour
  amener le GUI avant de continuer le Knowledge Core — TASK-007 à TASK-012 (plus les 3
  satellites) en ont été extraits et rédigés (ce fichier) ; le reste de cette
  re-priorisation (section 2, TASK-013 à TASK-037) demeure une proposition, pas une
  décision actée par Cleo.

## Décisions d'architecture (ADI-001 à ADI-011, toutes `Accepted`)

**Lecture requise avant de rédiger une nouvelle ADR :** `specs/product/vision.md`, `user-needs.md`, `scope.md`, `non-goals.md`, `product-model.md`, `use-cases.md` (cité comme justification derrière presque chaque exigence, et seul document porteur des signaux de volume), `specs/domain/knowledge-model.md`, `specs/domain/knowledge-invariants.md`, `specs/architecture/principles.md`, `specs/architecture/capabilities.md`, la section 23 (« Architectural Decision Inputs ») de `specs/architecture/technical-requirements.md`, et les ADR déjà écrites. Le format attendu est défini dans `specs/decisions/README.md`.

Les 6 premières répondent aux questions ouvertes de la section 23 ; ADI-007/008/009 ont été tranchées ensuite, en butant sur des gaps bloquants pour écrire un ticket implémentable.

- **ADI-001 — Modèle de persistance canonique.** Fichiers structurés (un par item), pas de base de données. **Pas d'historisation via git** : Cleo utilise un vault Obsidian synchronisé en continu sur plusieurs appareils, et faire tourner git en parallèle d'un outil de synchro tiers actif est un vrai risque de conflit. L'historisation se fait au niveau des fichiers : sous-dossier `history/` par item, contenant les **versions complètes** précédentes (`lifecycle_status: SUPERSEDED`), jamais des diffs. Sauvegarde/redondance = la synchro Obsidian de Cleo, hors scope de Pekopeko.
- **ADI-002 — Retrieval.** Index dérivé et reconstructible, jamais canonique, **jamais stocké dans le vault Obsidian** (même logique anti-conflit qu'ADI-001). Montée en charge : V1 en mémoire au démarrage → SQLite/FTS5 local hors vault, incrémental → index vectoriel local si la recherche sémantique devient nécessaire. Un serveur de recherche partagé multi-appareils est explicitement hors scope.
- **ADI-003 — Modèle de relations.** Enregistrements structurés dans les fichiers (références par ID stable, jamais de contenu dupliqué), traversal via une structure d'adjacence dérivée. Même règle de placement qu'ADI-002 : jamais dans le vault, reconstruite par appareil.
- **ADI-004 — Rôle d'Obsidian.** Le vault de Cleo **est** la racine du stockage canonique (pas un miroir). Organisation par domaine puis par type d'item, choisie pour des raisons techniques (isolation de domaine, localité de l'historique) et non pour le confort de consultation. Pekopeko n'utilise jamais les fonctionnalités natives d'Obsidian (graphe, backlinks, recherche) comme mécanisme de fonctionnement, et ne duplique pas les relations en wikilinks. **Écritures canoniques atomiques** (fichier temporaire + renommage) : le vault est surveillé simultanément par Obsidian, l'outil de synchro et Pekopeko.
- **ADI-005 — Synchrone vs asynchrone.** (1) Tout traitement AI/LLM ou calcul non trivial sur le graphe est asynchrone et produit une Proposal dans la file de revue, sans jamais bloquer l'utilisatrice ; (2) toute lecture locale contre des fichiers canoniques ou index déjà persistés est synchrone ; (3) accepter/rejeter une proposition est synchrone pour l'écriture, mais toute analyse d'impact en aval repart en tâche asynchrone. L'état des tâches asynchrones est persisté localement, hors vault et par appareil — non canonique, donc une perte d'état signifie resoumettre la tâche, jamais une corruption du canonique.
- **ADI-006 — Persister vs recalculer.** Seuls les fichiers canoniques (et leurs sous-dossiers d'historique) sont persistés ; tout le reste est dérivé et reconstructible. L'ADR contient une section « Why this scales » expliquant à quelles conditions (discipline d'identifiants stables) l'architecture reste évolutive vers DB/graphe/vectoriel sans redesign.
- **ADI-007 — Langage d'implémentation.** Python pour le Knowledge Core / backend. Ne présume rien du frontend (tranché séparément par ADI-009).
- **ADI-008 — Architecture des providers LLM.** Cleo veut pouvoir changer de LLM d'extraction librement, jamais verrouillée sur un provider. Le pipeline passe toujours par une interface d'abstraction (`extract(text, context) -> ExtractionResult`), jamais un appel direct ; le provider actif est choisi par **config locale** (hors vault, par appareil, comme ADI-002/005). Changer de provider = changer la config, pas le code. L'ADR tranche l'architecture (pluggable), pas quel provider est le défaut.
- **ADI-009 — Framework frontend.** **ReactJS**, choisi pour familiarité (pas d'évaluation exhaustive des alternatives — même logique pragmatique qu'ADI-007). Déclenchée par `specs/ux-design/` (4 maquettes HTML/CSS/JS statiques et framework-agnostiques : Dashboard, Validation, Ingestion Logs, Proposal Detail — voir le README du dossier). L'ADR ne tranche que le framework : ni le scope V1 de l'interface ni son découpage en tickets.
- **ADI-010 — Couche API backend et contrat d'intégration frontend.** Tranche ce qu'ADI-009 avait explicitement laissé ouvert ("comment l'interface parle au backend"). REST/HTTP via **Flask** (synchrone, pas de nouveau paradigme async — rien dans le backend n'est `asyncio`-natif). Ingestion/extraction restent asynchrones (ADI-005 règle 1) via un job HTTP `202` + `task_id` miné et persisté de façon synchrone avant la réponse, puis polling `GET .../<task_id>` (pas de push/websocket) ; review/config restent synchrones (ADI-005 règle 3), appel direct. `vault_root` (qui n'a aujourd'hui aucune surface de config, cf. amendement TASK-004 ci-dessous) est lu par le process API via une variable d'environnement dédiée `PEKOPEKO_VAULT_ROOT`, jamais par requête, et sans étendre le schéma partagé de `config/`. Sécurité : bind `127.0.0.1` uniquement + jeton partagé (`X-API-Key` contre `PEKOPEKO_API_KEY`) — pas d'authentification multi-utilisateur, `reviewer_id`/`domain` restent "trusted as given" comme dans tous les tickets précédents.
- **ADI-011 — Contrat zero-output des providers.** Confirmée par Cleo le 2026-09-03. Déclenchée par un incident réel : gpt-oss:20b a épuisé sa fenêtre de contexte (`done_reason: "length"`, réponse vide) et `OllamaProvider.extract()` (ingestion et extraction) a silencieusement renvoyé une liste vide, faisant passer la tâche en `completed` avec 0 propositions — indiscernable d'une source n'ayant vraiment rien à extraire. Décide que le contrat `Provider.extract()` doit lever une exception dès que 0 élément est extrait pour un contenu source non vide (jamais un `ExtractionResult` vide "réussi"), qu'une source réellement vide/blanche est un cas distinct intercepté par le pipeline **avant** l'appel au provider, et que le provider doit si possible remonter la raison machine-lisible d'une génération tronquée (ex. `done_reason` d'Ollama) dans le message d'erreur. Implémentée par TASK-001c (`completed`, 2026-09-03).

## Conventions d'identifiants (issues du nettoyage de cohérence, terminé)

Un nettoyage complet des identifiants du corpus a été fait en amont des ADR (collisions de namespaces, sections dupliquées, citations `CAP-CORE-XXX` erronées). Ce qui en reste comme règle :

- `INV-001..021` = invariants de domaine (`specs/domain/knowledge-invariants.md`) ; `AP-001..009` = principes d'architecture (`specs/architecture/principles.md`). Les deux namespaces sont distincts — ne pas appeler les `AP-` des « invariants ».
- `RQR-001..006` = Relationship Requirements ; `RTR-001..003` = Retrieval Requirements (`specs/architecture/technical-requirements.md`).
- `CAP-CORE-001..016` : **l'ordre du fichier `specs/architecture/capabilities.md` fait foi**, chaque section y porte son ID explicite. Toute citation ailleurs dans le corpus doit s'y conformer.
- Leçon de délégation : l'audit sémantique / cross-référencement entre documents n'est pas un bon candidat pour un modèle local 30B — la tentative a produit un plan sans édition, contenant au moins une affirmation fausse. Les tâches de code volumineuses et bien bornées restent, elles, de bons candidats.

**Points ouverts (non bloquants, à trancher si l'un devient gênant) :**

1. 14 citations `CAP-CORE-XXX` de `technical-requirements.md` n'ont aucun mapping autoritaire dans `capabilities.md`, donc non confirmables : TCR-001..004, SQR-001, FHR-001/002, CPR-001, ADI-001/002/003/004/005/006. À revoir si `capabilities.md` est un jour complété.
2. 3 capacités définies dans `capabilities.md` ne sont référencées par aucun cas d'usage : CAP-CORE-012 (Asynchronous Task Management), CAP-CORE-013 (Large-Scale Knowledge Handling), CAP-CORE-016 (Module Integration). Soit aucun UC ne les mobilise encore, soit `use-cases.md` a une couverture incomplète.
3. 2 concepts cités dans `use-cases.md` sans capacité formelle correspondante : « Source and Ingestion Management » et « Knowledge Health / Integrity Monitoring ». Il manque potentiellement 2 capacités à `capabilities.md` — décision de contenu, pas de traçabilité.
4. `specs/product/capabilities.md` (CAP-001..003, capacités **produit**) reste totalement déconnecté par ID des 16 `CAP-CORE-XXX` et des 18 `UC-XXX` — les trois catalogues du corpus ne sont que partiellement réconciliés.

## Tickets et implémentation (en cours)

**Lecture requise pour rédiger un ticket :** les ADR `Accepted` concernées, `specs/modules/module-architecture.md`, `specs/tasks/README.md` (format et cycle de vie `backlog/` → `active/` → `completed/`).
**Lecture requise pour implémenter un ticket :** uniquement le ticket lui-même et les invariants qu'il cite explicitement — pas l'ensemble de `specs/`. Si un ticket ne peut pas être traité sans relire tout le corpus, il est mal découpé.

Un ticket doit être assez petit et autonome pour être traité par qwen3-coder:30b sans relire le corpus : fichiers concernés, schéma/interface attendu, critères d'acceptation testables, et les 2-3 invariants pertinents cités explicitement (pas par renvoi global). Toujours préférer un scope V1 minimal plutôt que d'adresser les 18 cas d'usage d'un coup.

**Historique de numérotation :** une première série `KC-XXX` a existé (KC-001, primitive de stockage du Knowledge Core, implémentée puis supprimée avec son code). Le 2026-08-24, à la demande de Cleo, la numérotation et la logique de dépendance repartent de zéro en série `TASK-XXX`, indépendante. Le premier ticket de la nouvelle série est l'ingestion et non le workflow de proposition : c'est la partie à plus haute incertitude technique (extraction LLM), donc celle qu'il vaut mieux de-risquer en premier.

### TASK-001 — Module d'ingestion de données (V1) — `completed`

`specs/tasks/completed/TASK-001-data-ingestion.md`. Code : `src/app/ingestion/` (`pipeline.py`, `storage.py`, `task_state.py`, `readers/markdown_reader.py`, `providers/ollama_provider.py`), tests sous `src/tests/ingestion/`.

Scope V1 : sources `.md` uniquement (derrière une interface extensible pour ajouter d'autres formats sans redesign), extraction d'**Assertions uniquement** (pas encore Entity/Event/Relationship), un seul provider LLM concret derrière l'interface d'ADI-008, détection de doublons par hash de contenu, état de tâche asynchrone minimal (ADI-005).

- **Écart architectural non résolu :** ADI-004 ne prévoit que 5 sous-dossiers par domaine (`entities/`, `assertions/`, `events/`, `relationships/`, `proposals/`). TASK-001 en ajoute un 6ᵉ, `sources/`, pour la préservation de la source brute — exigée par CAP-002/UC-001 mais absente d'ADI-004 telle qu'écrite. Signalé dans le ticket plutôt que tranché en silence.
- **Écart de vérification assumé :** Cleo a confirmé le 2026-08-29 que TASK-001 est vérifiée, mais sans le rapport indépendant que demande la discipline ci-dessous (code copié en environnement isolé, tests rejoués, 9 critères d'acceptation vérifiés un par un). Les seuls documents présents (`FINAL_IMPLEMENTATION_SUMMARY.md`, `src/src/FINAL_COMPLIANCE_REPORT.md`) sont des auto-rapports commités avec l'implémentation elle-même. À combler si l'écart devient gênant.

### TASK-001a — Provenance d'extraction enrichie — `completed`

`specs/tasks/completed/TASK-001a-extraction-provenance-metadata.md`. Ticket satellite
(rédigé 2026-08-31, implémenté 2026-08-31) étendant TASK-001 de façon additive : ajoute
`provider_model`, `provider_temperature`, `extraction_id`, `extraction_duration_seconds` au
dict `provenance` de chaque Proposal — champs que la maquette
`pekopeko-proposal-detail.html` montre mais que le contrat frontmatter de TASK-001 ne
capturait pas. Écrit en préparant TASK-011 (écran Détail de proposition), qui en dépend
pour sa section Provenance complète. Aucun changement de signature publique de
`ingest_source` ; champs `null` si le `Provider` ne les fournit pas.

- **Écart signalé et tranché avec Cleo avant l'implémentation** : le ticket supposait à
  tort que `OllamaProvider` avait déjà une `temperature` configurée "juste pas encore
  surfacée" — faux, `temperature` n'existait nulle part dans le code avant cette
  implémentation. Résolu en ajoutant un vrai champ `temperature: float = 0.7` à
  `OllamaProviderConfig` (pas à `config/schema.py` partagé — aucune nouvelle surface de
  config utilisateur) et en le câblant réellement dans l'appel à l'API Ollama
  (`options.temperature`), pour que la valeur reportée influence réellement la génération.
  Détail complet dans la section « Deviation » du ticket.
- Vérifié par Claude selon la discipline du projet (environnement isolé, copie hors dépôt
  dans `scratchpad/task001a_verify/`, 34/36 `tests/ingestion` rejoués — mêmes 2 échecs
  préexistants et non liés que TASK-004, confirmés par `git stash`/`git stash pop` avant/
  après ce ticket —, couverture des fichiers touchés 83-100 % reconfirmée à l'identique
  entre dépôt et copie isolée, 6 critères d'acceptation un par un, plus un script de
  reproduction manuelle bout-en-bout inspectant le fichier Proposal écrit et le payload
  JSON réellement envoyé à Ollama). Rapport dans la section « Verification record » du
  ticket. Même limite que TASK-002/003/004 : vérification faite par la même session Claude
  que l'implémentation, pas par un second réviseur indépendant.

### TASK-001b — Journal d'événements de tâche, ingestion + extraction — `completed`

`specs/tasks/completed/TASK-001b-task-event-log.md`. Ticket satellite (rédigé 2026-08-31,
implémenté 2026-08-31) étendant TASK-001 **et** TASK-003 de façon additive et symétrique
(deux édits séparés, sans import croisé, même discipline que TASK-004/TASK-007) : ajoute
`events: list[TaskEvent]` (timestamp/niveau/message/détails) à `TaskState`, peuplé à chaque
étape du pipeline. Comble l'absence de donnée derrière la section « Logs d'ingestion
complets » de la maquette Détail et les actions « Voir logs »/« Voir erreur » de la
maquette Ingestion Logs. `events` vide par défaut, rétrocompatible avec les `TaskState`
déjà sur disque. Écrit en préparant TASK-009/TASK-011, qui en dépendent.

- Vérifié par Claude selon la discipline du projet (environnement isolé, copie hors dépôt
  dans `scratchpad/task001b_verify/`, 43/45 `tests/ingestion` et 51/51 `tests/extraction`
  rejoués — mêmes 2 échecs préexistants et non liés qu'aux tickets précédents —, couverture
  des fichiers touchés 97-100 % reconfirmée à l'identique entre dépôt et copie isolée, 8
  critères d'acceptation un par un, plus un script de reproduction manuelle bout-en-bout
  inspectant le fichier `TaskState` JSON réellement écrit. Rapport dans la section
  « Verification record » du ticket. Même limite que TASK-001a/002/003/004 : vérification
  faite par la même session Claude que l'implémentation, pas par un second réviseur
  indépendant.

### TASK-001c — Échec explicite sur extraction à zéro résultat — `completed`

`specs/tasks/completed/TASK-001c-zero-output-extraction-failure.md`. Ticket satellite
(rédigé et implémenté le 2026-09-03) étendant TASK-001 **et** TASK-003 de façon additive et
symétrique (même posture que TASK-001b) : implémente ADI-011 (`Accepted`) —
`OllamaProvider.extract()` (ingestion et extraction) lève désormais une exception si 0
élément est extrait pour un contenu source non vide, message incluant `done_reason=...`
quand Ollama l'expose, plutôt que de renvoyer un `ExtractionResult` vide traité comme un
succès ; un fichier source réellement vide est intercepté séparément par le pipeline
(`if not content.strip()`) avant l'appel au provider, erreur distincte `"Source file is
empty"`. Déclenché par un incident réel avec gpt-oss:20b (contexte épuisé,
`done_reason: "length"`, réponse vide, tâche enregistrée `completed` avec 0 propositions).

- **Écart trouvé et corrigé pendant l'implémentation, via reproduction manuelle** : la
  première version du correctif côté `extraction/` ne vérifiait la sortie vide qu'*après*
  `_parse_extraction_result()`, mais cette fonction lève elle-même `"did not contain a JSON
  object"` dès que `extracted_text` est une chaîne vide — exactement la forme de l'incident
  gpt-oss:20b réel — court-circuitant le nouveau contrôle avant qu'il n'ajoute
  `done_reason` au message. Un script de reproduction manuelle bout-en-bout (appelant les
  vrais `OllamaProvider.extract()` via `ingest_source()`/`extract_source()`, `requests.post`
  simulé) l'a révélé alors que les tests unitaires seuls ne l'avaient pas détecté. Corrigé
  en ajoutant un contrôle *avant* l'appel à `_parse_extraction_result()` : si
  `extracted_text.strip()` est vide, lever immédiatement avec le diagnostic `done_reason`.
- Code : `ingestion/providers/ollama_provider.py`, `extraction/providers/ollama_provider.py`,
  `ingestion/pipeline.py`, `extraction/pipeline.py`. Nouveau fichier
  `src/tests/ingestion/test_ollama_provider.py` (n'existait pas avant ce ticket). Un test
  extraction pré-existant (`test_extract_handles_missing_lists`) renommé et son assertion
  inversée en place, changement de comportement volontaire (ADI-011), pas une régression.
  Aucun changement de signature publique, aucun nouveau statut `TaskState`, aucun champ
  structuré ajouté (`done_reason` reste uniquement dans le texte du message d'erreur).
- Vérifié par Claude selon la discipline du projet (copie isolée hors dépôt dans
  `scratchpad/task001c_verify/`, `tests/extraction` 61/61 rejoués (100 % couverture, +5
  tests nets vs 56/56 avant ce ticket), `tests/ingestion` 56/58 rejoués (98 % couverture,
  +8 tests nets vs 48/50 avant ce ticket, mêmes 2 échecs préexistants et non liés que
  TASK-001a/001b/003/004 reconfirmés par `git stash`/`git stash pop` ciblé sur les seuls
  fichiers de ce ticket), 7 critères d'acceptation un par un, plus un script de
  reproduction manuelle bout-en-bout à 5 scénarios (incident réel ingestion+extraction,
  garde-fou source vide ingestion+extraction, non-régression du chemin nominal) — c'est ce
  script qui a révélé l'écart ci-dessus. Rapport dans la section « Verification record » du
  ticket. Même limite que les tickets précédents : vérification faite par la même session
  Claude que l'implémentation, pas par un second réviseur indépendant.

### TASK-001d — Détection de doublon ignore les retries après échec partiel — `completed`

`specs/tasks/completed/TASK-001d-duplicate-detection-partial-failure.md`. Ticket satellite
(rédigé 2026-09-03, implémenté 2026-09-03) étendant TASK-001 **et** TASK-003 de façon
additive et symétrique (même posture que TASK-001b/TASK-001c), et corrigeant en plus un
bug dans le code déjà `completed` de TASK-010. Bug réel trouvé en usage par Cleo
(2026-09-03) : `ingest_source`/`extract_source` écrivent le fichier source **avant**
d'appeler le provider ; si le provider échoue ensuite, la tâche passe `failed` mais le
fichier source reste sur disque, et toute tentative suivante ne vérifiait que
`Path.exists()` → retombait en `skipped_duplicate` pour toujours, sans jamais rappeler le
provider. Distinct de TASK-001c/ADI-011 (provider qui renvoie silencieusement zéro
résultat) — ici le provider lève une exception après écriture du source ; les deux bugs
sont indépendants, ce ticket n'était pas bloqué par ADI-011 et ne le remplace pas. Corrige
aussi `Validation.jsx` (TASK-010) : le statut de groupe par `source_id` était calculé en
écrasant sans condition à chaque tâche itérée, ce qui — la liste étant déjà triée
`started_at` décroissant côté API — faisait gagner la tâche la plus **ancienne** au lieu de
la plus récente.

- Fix retenu pour la détection de doublon : skip seulement si `list_task_states` trouve une
  tâche antérieure `completed` pour ce `source_id` (cohérent avec ADI-005 — perte d'état de
  tâche = resoumettre, jamais corrompre le canonique), sinon réutiliser le fichier source
  déjà écrit (sans le réécrire) et relancer l'extraction comme une tentative normale.
  Nouveau message d'événement distinct (`"Existing source reused, retrying
  ingestion/extraction"`) pour ce troisième chemin, désormais visible séparément du skip
  de vrai doublon et de l'écriture initiale dans `TaskState.events` (TASK-001b).
- Code : `src/app/ingestion/pipeline.py` et `src/app/extraction/pipeline.py`
  (restructuration à trois branches du bloc de détection de doublon, deux éditions
  séparées et symétriques sans import croisé, même discipline que TASK-001b/TASK-001c) ;
  `frontend/src/pages/Validation.jsx` (`fetchGroups()` — garde `!taskStatusBySourceId.has()`
  avant le `.set()`, plus un commentaire signalant la dépendance à l'ordre de tri de
  l'API). 8 nouveaux tests Python (4 `src/tests/ingestion/test_pipeline.py`, 4
  `src/tests/extraction/test_pipeline.py`, un par critère d'acceptation backend/pipeline)
  et 1 nouveau test Vitest (`Validation.test.jsx`, critère AC6 frontend). Limitation
  assumée et documentée dans le ticket (non traitée) : un échec ayant déjà écrit certaines
  Proposals avant de planter en cours de boucle peut produire des Proposals dupliquées au
  retry — déduplication idempotente hors scope.
- Vérifié par Claude selon la discipline du projet : `pytest src/tests/ingestion/` 60/62
  (les 2 échecs sont préexistants et non liés, confirmés par `git stash`/`git stash pop` —
  mêmes échecs sur le code d'avant ce ticket), `pytest src/tests/extraction/` 65/65 (aucun
  échec préexistant dans cette suite), couverture 99 %/100 % sur les deux `pipeline.py`
  touchés ; `npx vitest run --coverage` 45/45 (couverture globale 97,77 %, `Validation.jsx`
  96,5 %) ; script de reproduction manuelle bout-en-bout en environnement isolé
  (`scratchpad/task001d_manual_repro.py`, non commité) rejouant le scénario réel de Cleo
  pour les deux pipelines indépendamment (échec après écriture du source → retry réussi
  sans réécriture du fichier, contenu/mtime identiques → doublon réel toujours skippé),
  plus inspection par l'œil des trois séquences d'événements distinctes. 8 critères
  d'acceptation vérifiés un par un. Rapport dans la section « Verification record » du
  ticket. Même limite que tous les tickets précédents : vérification faite par la même
  session Claude que l'implémentation, pas par un second réviseur indépendant.

### TASK-002 — Workflow de revue des propositions (V1) — `completed`

`specs/tasks/completed/TASK-002-proposal-review-workflow.md`. Code : `src/app/review/` (`errors.py`, `frontmatter.py`, `storage.py`, `pipeline.py`), 56 tests dans `src/tests/review/`, 100 % de couverture de lignes. Ferme le flux `PROPOSAL → HUMAN REVIEW → CANONICAL KNOWLEDGE` (UC-011, CAP-CORE-002).

Scope V1 : revue individuelle uniquement (pas d'opérations en masse, filtrage, tri ni analytics), propositions de type `assertion` uniquement, transitions `PROPOSED → ACCEPTED` et `PROPOSED → REJECTED` seulement.

- **Indépendance entre modules :** `review/` n'importe jamais `app.ingestion` — le parsing du frontmatter y est réimplémenté. La dépendance à TASK-001 passe uniquement par le contrat de fichiers/frontmatter (ADI-001/ADI-004), jamais par le code. Discipline à conserver pour les tickets suivants.
- **Engagement à ne pas perdre :** contrairement à la règle générale d'ADI-001, TASK-002 ne crée **pas** de sous-dossier `history/` pour une simple transition de statut d'une Proposal — mise à jour en place (atomique) avec `reviewed_by`/`reviewed_at`/`resulting_item_id`. Justification : l'historisation complète n'a de sens que quand le *contenu* d'une Proposal change, ce qui n'arrive qu'avec le statut `EDITED`, hors scope ici. **Le futur ticket qui introduira `EDITED` devra impérativement ajouter le mécanisme `history/` pour les Proposals à ce moment-là.**
- Vérifié par Claude selon la discipline du projet (environnement isolé, 56/56 rejoués, 9 critères un par un, reproduction manuelle bout-en-bout) — un bug réel trouvé et corrigé à cette occasion (`_write_atomic_file` laissait un `.tmp` orphelin si `os.replace()` échouait). Rapport dans la section « Verification record » du ticket. Puis revérifié par un second réviseur (codex / qwen3-coder:30b) : conforme.

### TASK-003 — Extraction Entity/Event/Relationship — `completed`

`specs/tasks/completed/TASK-003-entity-event-relationship-extraction.md`. Code : `src/app/extraction/` (`errors.py`, `frontmatter.py`, `storage.py`, `task_state.py`, `readers/`, `providers/`, `pipeline.py`), 41 tests dans `src/tests/extraction/`, 100 % de couverture de lignes. Étend `SOURCE → EXTRACTION → PROPOSAL` (TASK-001 pour les Assertions) aux Entities/Events/Relationships ; s'arrête à `proposal_status: PROPOSED`.

Scope V1 : indépendant de `app.ingestion` et `app.review` (aucun import ; seul le contrat de fichiers/frontmatter ADI-001/ADI-004 est partagé), suit le pattern plus abouti de `review/` (exceptions typées, atomic-write avec nettoyage sur échec de `os.replace()`, helpers de chemin) plutôt que celui de `ingestion/`. Les noms de champs frontmatter suivent la propre section « File layout (exact contract) » du ticket, littéralement — différents de ceux de TASK-001 (`item_type` vs `type`, `source_id` vs `id`, etc.), les deux tickets ayant chacun leur propre contrat sans dépendre du code de l'autre. Résolution des `endpoints` d'une relation : la spec ne code pas ce mécanisme — implémenté via un `local_id` transitoire assigné par le provider à chaque entity/event, résolu vers le vrai `proposal_id` par le pipeline au moment de l'écriture (documenté dans « Implementation notes » du ticket).

- Vérifié par Claude selon la discipline du projet (environnement isolé — copie hors dépôt, 41/41 rejoués, 100 % couverture reconfirmée, 9 critères un par un, plus une reproduction manuelle bout-en-bout avec inspection par l'œil des fichiers Source/Proposal produits). Rapport dans la section « Verification record » du ticket. Même limite que TASK-002 : vérification faite par la même session Claude que l'implémentation, pas par un second réviseur indépendant.
- **Relecture demandée par Cleo (2026-08-30)** : deux points vérifiés post-implémentation. (1) `VALID_EPISTEMIC_STATUSES` était défini deux fois (`storage.py` en `set`, `ollama_provider.py` en `list`) — mêmes valeurs, pas de bug fonctionnel, mais risque de dérive silencieuse ; consolidé en une seule définition dans `providers/base.py`, importée par les deux autres fichiers. (2) Hash de détection de doublon (`_generate_source_id`) confirmé calculé sur l'intégralité du contenu (SHA-256 consomme tout l'input ; seul le digest hexadécimal résultant est tronqué à 16 caractères pour raccourcir l'id) — pas de bug, un test explicite ajouté pour le démontrer. Voir « Post-verification cleanup » dans le ticket.

### TASK-004 — Mécanisme de configuration locale — `completed`

`specs/tasks/completed/TASK-004-local-configuration.md`. Formalise ce qu'ADI-008 (et implicitement ADI-002/ADI-005) supposait déjà : un fichier YAML local (`~/.pekopeko/config.yaml`, jamais dans le vault) plus une liste bornée d'overrides par variable d'env, pour le provider LLM actif, l'emplacement de l'index de retrieval (réservé pour le futur ticket de retrieval, `TASK-018` dans la numérotation de `BACKLOG-CLAUDE-V2.md`, non consommé ici) et celui de l'état de tâche. Code : `src/app/config/` (`schema.py`, `loader.py`, `errors.py`), plus `providers/factory.py` neuf dans `src/app/ingestion/` et `src/app/extraction/`, 19 tests dans `src/tests/config/` (100 % de couverture de lignes), quelques tests additionnels dans `src/tests/ingestion/` et `src/tests/extraction/`.

Branchement minimal : `ingestion/pipeline.py` et `extraction/pipeline.py` tirent désormais leur défaut de `state_dir` de la config (`<task_state.dir>/ingestion` et `<task_state.dir>/extraction`), et chacun reçoit une factory optionnelle (`providers/factory.py`) pour construire son `OllamaProvider` depuis la config — sans changer la signature publique de `ingest_source`/`extract_source` ni le fait que `provider` reste un paramètre obligatoire fourni par l'appelant.

- **Amendement (2026-08-30)** : Cleo a ajouté après coup un fichier `.env` compagnon pour les secrets et un champ `default.domain` réservé. Après clarification (3 questions posées et tranchées, voir le ticket) : `.env` (via `python-dotenv`, nouvelle dépendance pinnée) ne fait que charger les mêmes 7 clés bornées `PEKOPEKO_*` déjà existantes — pas un second espace de clés — et une vraie variable d'env réelle garde toujours la priorité sur `.env`. `default.domain` est réservé (comme `retrieval.index_dir` pour le futur ticket de retrieval, `TASK-018`) : présent dans le schéma, jamais lu par `ingest_source`/`extract_source`, aucun changement de signature. `vault_root` n'a toujours aucune surface de config. 24/24 tests `config` (100 % couverture), vérification en environnement isolé rejouée indépendamment — détail complet dans la section « Amendment verification » du ticket.

- Vérifié par Claude selon la discipline du projet (environnement isolé, 19/19 tests `config` rejoués + couverture 100 % reconfirmée, 44/44 `extraction` et 29/31 `ingestion` (2 échecs préexistants et non liés à ce ticket) rejoués, 11 critères un par un, plus un script de reproduction manuelle bout-en-bout par l'œil). Rapport dans la section « Verification record » du ticket. Même limite que TASK-002/TASK-003 : vérification faite par la même session Claude que l'implémentation, pas par un second réviseur indépendant.

### TASK-005 — Revue des propositions Entity/Event/Relationship — `backlog`

`specs/tasks/backlog/TASK-005-entity-event-relationship-review.md`. Miroir de TASK-002 pour la sortie de TASK-003 : listing/détail/accept/reject pour `proposed_item_type` entity/event/relationship, plus résolution des `endpoints` d'une relation acceptée vers des IDs canoniques stables (ADI-003), une fois ses propres endpoints eux-mêmes acceptés. Ticket entièrement rédigé (objectif, contrat de fichiers, 10 critères d'acceptation) mais jamais implémenté — aucune section « Verification record » ni « Implementation notes ».

### TASK-006 — Statut EDITED et historisation des Proposals — `completed`

`specs/tasks/completed/TASK-006-proposal-edit-and-history.md`. Ajoute `PROPOSED → EDITED` (édition du contenu d'une Proposal avant décision, UC-011 stage 5) et le mécanisme `history/` pour les Proposals qu'ADI-001 exige dès que le contenu change — engagement pris explicitement dans TASK-002 (« Le futur ticket qui introduira EDITED devra impérativement ajouter le mécanisme history/ pour les Proposals »). Rédigé le 2026-08-31, implémenté le 2026-09-01.

- **Décision de scope notable** : `edit_proposal` est générique aux 4 `proposed_item_type` (assertion/entity/event/relationship) — indépendant de TASK-005, car éditer ne touche que le frontmatter/body de la Proposal, jamais un writer canonique type-spécifique. `accept_proposal`/`reject_proposal` restent assertion-only (TASK-002/TASK-005), ce ticket élargit seulement leur statut accepté (`PROPOSED` ou `EDITED`), pas leur type. Conséquence assumée et documentée dans le ticket : une proposition entity/event/relationship éditée par ce ticket ne pourra toujours pas être acceptée avant TASK-005.
- **Historisation sans nouveau champ `version`** : numéro de version dérivé (par parsing du nom de fichier `--v<n>.md`, pas par comptage — robuste à un fichier parasite dans `history/`) plutôt que du nombre de fichiers déjà présents dans `history/` au moment de l'édition ; chaque snapshot archivé reçoit `lifecycle_status: SUPERSEDED` + `superseded_by: v<n+1>`, jamais réécrit après coup (INV-004).
- TASK-005 et TASK-006 sont indépendants entre eux (aucune dépendance de code) — les implémenter dans n'importe quel ordre est possible.
- Code : extension en place de `src/app/review/` (`errors.py` : `UneditableFieldError` ; `storage.py` :
  `EDITABLE_FIELDS_BY_TYPE`, `proposal_history_dir`, `archive_proposal_version`,
  `_validate_editable_fields` ; `pipeline.py` : `edit_proposal`, `_load_and_validate_for_edit`,
  élargissement du check de statut de `_load_and_validate_for_review` à `PROPOSED`/`EDITED`), tests
  sous `src/tests/review/` (94 tests, 100 % de couverture de lignes).
- Vérifié par Claude selon la discipline du projet (environnement isolé hors dépôt, 94/94 tests
  rejoués indépendamment, couverture 100 % reconfirmée à l'identique, 13 critères d'acceptation un
  par un, plus un script de reproduction manuelle bout-en-bout double-édition inspectant par l'œil
  le fichier Proposal live et les deux snapshots `history/` produits). Rapport dans la section
  « Verification record » du ticket. Même limite que TASK-001a/001b/002/003/004 : vérification
  faite par la même session Claude que l'implémentation, pas par un second réviseur indépendant.

### TASK-007 — Couche API backend pour le Knowledge Core — `completed`

`specs/tasks/completed/TASK-007-backend-api-layer.md`. Premier ticket du socle GUI de
`specs/tasks/BACKLOG-CLAUDE-V2.md` (correspond à l'ancien `TASK-022` de
`BACKLOG-CLAUDE.md`) : expose `ingestion`/`extraction`/`review` (accept/reject
uniquement)/`config` (lecture seule) via une API HTTP REST, levant pour la première fois
la contrainte explicite "no GUI or CLI required" de TASK-001/002/003. Pré-requis
obligatoire avant TASK-008 à TASK-012 — aucun écran ne peut être construit sans ce
connecteur. Rédigé le 2026-08-31, implémenté le 2026-09-01.

- Implémente **ADI-010** (rédigée dans la même session que le ticket, en butant sur 4
  gaps bloquants pour l'écrire : aucun framework HTTP existant, forme du contrat de job
  asynchrone jamais tranchée par ADI-005, absence totale de surface de config pour
  `vault_root`, absence de tout mécanisme d'authentification) — voir la section ADI-010
  ci-dessus pour le détail des décisions.
- Code : nouveau paquet `src/app/api/` (10 fichiers : `app.py`, `settings.py`,
  `serialization.py`, `tasks.py`, `domains.py`, `routes_ingestion.py`,
  `routes_extraction.py`, `routes_review.py`, `routes_config.py`, `__init__.py`), plus
  deux changements additifs et rétrocompatibles à du code déjà `completed` :
  `ingest_source`/`extract_source` et leurs `create_task_state` respectifs
  (`src/app/ingestion/` et `src/app/extraction/`) gagnent un paramètre optionnel
  `task_id: Optional[str] = None`, plus une nouvelle fonction `list_task_states` dans
  chacun des deux modules — même catégorie de "branchement minimal" que celui déjà fait
  par TASK-004. Aucun changement à `review/` ni `config/`. `flask>=3.0` ajouté à
  `src/requirements.txt`. Tests : `src/tests/api/` (66 tests, 99 % de couverture de
  lignes), plus tests de régression ajoutés à `src/tests/ingestion/` et
  `src/tests/extraction/` pour `task_id`/`list_task_states`.
- Indépendant de TASK-005/TASK-006 (ne dépendait que de TASK-001/002/003/004, tous
  `completed`) — confirmé implémentable indépendamment d'eux.
- **Bug trouvé et corrigé pendant la vérification** : l'écriture de `TaskState.save()`
  (code TASK-001/003 préexistant, non modifié par ce ticket au-delà des deux
  changements additifs ci-dessus) n'est pas atomique — un `GET` immédiat après le `202`
  peut, rarement, tomber sur une lecture concurrente à la première mise à jour de statut
  du thread d'arrière-plan et voir un fichier tronqué, que `load_task_state` avale en
  `None` comme si la tâche n'existait pas (`404` erroné, violant l'AC1 "an immediate GET
  on that task_id never returns 404"). Corrigé uniquement côté couche API (aucune
  modification de `task_state.py`) via un nouvel helper `load_task_state_resilient`
  (`src/app/api/tasks.py`) qui retente brièvement tant que le fichier existe sur disque
  mais ne s'est pas encore parsé, et renvoie `None` immédiatement si le fichier n'a
  jamais existé. Détail complet et reproduction dans la section « Implementation
  notes » du ticket.

### TASK-007a — Pagination sur les endpoints de liste — `completed`

`specs/tasks/completed/TASK-007a-list-endpoint-pagination.md`. Ticket satellite
(rédigé 2026-08-31, implémenté 2026-09-02) étendant TASK-007 : `?limit=`/`?offset=` sur
les 3 endpoints de liste (ingestions/extractions/proposals), enveloppe de réponse
`{items, total, limit, offset}`. Écrit comme ticket séparé plutôt qu'édition en place de
TASK-007, pour ne pas invalider la numérotation de ses critères d'acceptation déjà cités
ailleurs (TASK-008 cite l'AC12 de TASK-007). TASK-009/TASK-010 en dépendent pour une vraie
pagination serveur.

- Code : `src/app/api/errors.py` (nouveau, `ValidationError` dédiée aux paramètres de
  pagination invalides, enregistrée dans la table d'erreurs de `app.py`), extension de
  `serialization.py` (`parse_pagination_args`, `paginate`, partagés par les 3 routes),
  extension de `routes_ingestion.py`/`routes_extraction.py`/`routes_review.py`. **Écart
  signalé** : le périmètre de fichiers du ticket ne citait pas `app.py`/`errors.py`, mais
  satisfaire l'AC4 littéralement (`error.type == "ValidationError"`) l'exigeait — ajout
  additif seul (nouvelle clé dans `ERROR_STATUS_MAP`), aucun mapping existant modifié.
  Détail dans la section « Deviation » du ticket.
- 31 nouveaux tests dans `src/tests/api/test_pagination.py` (paramétrés sur les 3
  endpoints), plus 3 tests TASK-007 existants mis à jour en place (forme de réponse
  liste bare-list → `{items, ...}`, seul changement aux tests déjà écrits par TASK-007).
  97/97 tests `api/` passent (66 + 31), 98 % de couverture sur `src/app/api/` (100 % sur
  chaque fichier touché par ce ticket).
- Vérifié par Claude selon la discipline du projet (copie isolée hors dépôt
  `/tmp/task007a_verify/`, 97/97 rejoués à l'identique, 8 critères d'acceptation un par un,
  script de reproduction manuelle bout-en-bout par l'œil du JSON réellement renvoyé).
  Rapport dans la section « Verification record » du ticket. Même limite que les tickets
  précédents : vérification faite par la même session Claude que l'implémentation, pas par
  un second réviseur indépendant.

### TASK-008 — Scaffold React + écrans Dashboard et Settings — `completed`

`specs/tasks/completed/TASK-008-react-scaffold-dashboard-settings.md`. Premier code
frontend du dépôt : projet React (Vite, JS, React Router — décisions tranchées par ce
ticket, ADI-009 les avait explicitement laissées ouvertes), nouveau répertoire `frontend/`
(sibling de `src/`). Livre `pekopeko-dashboard.html` (stats agrégées sur les 5 domaines
côté client, cartes de modules) et un écran Settings lecture seule (nouveau, absent des
maquettes). Rédigé le 2026-08-31, implémenté le 2026-09-02.

- Deux clarifications tranchées par Cleo avant rédaction (aucune spec ne les couvrait) :
  la clé `X-API-Key` est injectée au build via une variable d'environnement Vite
  (`VITE_API_KEY`, jamais un flux runtime/localStorage) ; l'écran Settings reste lecture
  seule pour V1 (affiche le chemin du `config.yaml` local avec une note d'édition
  manuelle, pas de nouvel endpoint d'écriture) — le libellé "visualise/édite" de
  `BACKLOG-CLAUDE-V2.md` est superseded par cette décision.
- Dépend de TASK-007 (`completed` — connecteur API obligatoire) et transitivement de
  TASK-004 (`completed`, forme de `GET /config`). Indépendant de TASK-005/TASK-006.
- Prérequis pour TASK-009 à TASK-012 : la structure de routing/composants posée ici est
  ce à quoi ces tickets ajoutent des écrans, sans la refondre.
- **Écart réel trouvé et tranché avec l'utilisatrice avant implémentation** : le ticket
  supposait que `GET /domains/<d>/proposals?status=` renvoie `reviewed_at` par item pour
  le calcul du « Taux d'acceptation » — faux, `ProposalSummary`
  (`src/app/review/pipeline.py`) ne porte pas ce champ, seul le détail par item
  (`GET .../proposals/<id>`, `ProposalDetail.frontmatter`) l'a. Résolu en suivant le
  précédent déjà posé par TASK-010 (N+1 sur l'endpoint de détail) plutôt qu'en écrivant un
  ticket satellite pour étendre `ProposalSummary` — aucun changement backend. Détail
  complet dans la section « Deviation found and resolved during implementation » du
  ticket.
- Code : nouveau répertoire `frontend/` (Vite + React + React Router, JS/JSX, pas de
  TypeScript) — `src/api/client.js` (wrapper fetch unique, `ApiError` typée),
  `src/api/domains.js`, `src/components/` (`Sidebar`, `StatCard`, `ModuleCard`),
  `src/pages/` (`Dashboard`, `Settings`). Vitest + React Testing Library, 13 tests (un par
  groupe de critère d'acceptation), 96 % de couverture sur `src/api/`+`src/pages/`. Aucun
  fichier sous `src/` (Python) modifié.
- Vérifié par Claude selon la discipline du projet (`npm run build` rejoué, 13/13 tests
  rejoués, couverture recalculée, grep confirmant qu'aucun `fetch()` direct n'existe hors
  `api/client.js`, `git status --porcelain -- src/` vide). Rapport dans la section
  « Verification record » du ticket. Limite explicite : pas de second réviseur
  indépendant, et pas de test de fumée contre une vraie instance Flask/vault (aucun vault
  local disponible dans cette session) — recommandé comme vérification manuelle de suivi
  avant usage opérationnel de cet écran.

### TASK-009 — Écran Logs d'ingestion — `completed`

`specs/tasks/completed/TASK-009-ingestion-logs-screen.md`. Implémente
`pekopeko-ingestion.html` : table filtrable/paginée des tâches d'ingestion **et**
extraction, détail des erreurs/doublons/événements par tâche (via TASK-001b), pagination
serveur réelle (via TASK-007a). Fait passer la carte de module « Logs d'ingestion » du
Dashboard à `available`. Rédigé le 2026-08-31 en appliquant le principe « les maquettes
sont la cible » (voir note en tête de section « Suite » ci-dessus) : aucun élément de la
maquette n'a été silencieusement supprimé — pagination et journal d'événements comblés par
TASK-007a/TASK-001b plutôt que retirés. Dépend de TASK-007/TASK-007a/TASK-001b/TASK-008
(tous `completed`). Implémenté le 2026-09-03.

- Code : `frontend/src/api/tasks.js` (`listIngestions`/`listExtractions`, nouveau),
  `frontend/src/components/TaskStatusBadge.jsx`/`TaskEventLog.jsx` (nouveaux, génériques
  ingestion/extraction — `TaskEventLog` réutilisable tel quel par TASK-011),
  `frontend/src/pages/IngestionLogs.jsx` (nouveau — fan-out paginé sur les 5 domaines × 2
  types, fusion/tri client `started_at` desc, filtre Période client-side), extension de
  `App.jsx` (route `/ingestion-logs`), `Dashboard.jsx` (carte `available`), `Sidebar.jsx`
  (déviation signalée : pas listé dans le ticket, mais nécessaire pour ne pas laisser un
  lien mort grisé alors que la page est joignable), `index.css` (classes portées de la
  maquette `pekopeko-ingestion.html` + nouvelles classes pour l'accordéon de détail et le
  badge Type, absentes de toute maquette). Aucun fichier sous `src/` (Python) modifié.
- **Deux déviations signalées avant implémentation, tranchées avec Cleo** (détail dans la
  section « Deviations » du ticket) : (1) `Sidebar.jsx` modifié malgré son absence du
  périmètre déclaré du ticket ; (2) fidélité à la maquette allégée sur la pagination
  (Précédent/Suivant + compteur plutôt que les boutons numérotés 1-5 — le vrai nombre de
  pages n'est pas proprement connaissable à travers le fan-out à 10 sources) et sur l'en-tête
  (bouton « + Nouvelle ingestion » non porté, hors périmètre déjà assumé par le ticket ;
  bouton « ↻ Rafraîchir » porté à la demande explicite de Cleo malgré son absence des
  items de Scope du ticket).
- 25/25 tests Vitest (`tasks.test.js` 3 nouveaux, `IngestionLogs.test.jsx` 8 nouveaux — un
  par critère d'acceptation AC1-7/9 —, `Dashboard.test.jsx` 9 dont 1 mis à jour en place et
  1 nouveau bout-en-bout), couverture 100 % lignes sur `api/tasks.js` et
  `pages/IngestionLogs.jsx` (90,5 % branches), largement au-dessus du seuil 80 % du projet.
  Vérifié par Claude selon la discipline du projet (`npm run build`, `npx vitest run
  --coverage`, `grep` confirmant qu'aucun `fetch()` direct n'existe hors `api/client.js`,
  `git status --porcelain -- src/` vide). Rapport dans la section « Verification record »
  du ticket. Même limite que les tickets précédents : pas de second réviseur indépendant,
  pas de test de fumée contre une vraie instance Flask/vault (aucun vault local disponible
  dans cette session) — recommandé en suivi avant usage opérationnel, en particulier pour la
  stratégie de pagination fusionnée (approximative par construction, à valider manuellement
  contre un domaine/type réel avec plus de 10 tâches).

### TASK-010 — Écran Validation (Assertions) — `completed`

`specs/tasks/completed/TASK-010-validation-screen.md`. Implémente `pekopeko-workflow.html`,
scope assertion-only (miroir de TASK-002) : propositions groupées par source (jointure
client sur `provenance.source_id`, y compris un N+1 assumé sur `GET /proposals/<id>` faute
de `body`/`source_id` sur `ProposalSummary` — décision explicite de Cleo plutôt qu'étendre
TASK-007), badge de statut épistémique (4 valeurs réelles), accepter/rejeter individuels.
Sans folder-path builder ni bulk actions — déféré **pré-existant** (TASK-013/TASK-015,
acté avant cette session dans `BACKLOG-CLAUDE-V2.md`/TASK-007), pas une coupe de ce
ticket. `reviewer_id` fourni par une variable d'env au build (`VITE_REVIEWER_ID`, même
pattern que `VITE_API_KEY`). Dépend de TASK-007/TASK-007a/TASK-008/TASK-009 (réutilise
`api/tasks.js`, tous `completed`). Implémenté le 2026-09-03.

- Code : `frontend/src/api/review.js` (`listProposals`/`getProposal`/`acceptProposal`/
  `rejectProposal`, nouveau), `frontend/src/components/EpistemicStatusBadge.jsx`/
  `SourceGroupHeader.jsx`/`RejectReasonModal.jsx` (nouveaux — `RejectReasonModal` partagé
  avec TASK-011), `frontend/src/pages/Validation.jsx` (nouveau — fetch en 3 étapes :
  liste paginée par domaine → jointure N+1 sur le détail → jointure avec les tâches
  d'ingestion pour le statut de groupe), extension de `App.jsx` (route `/validation`),
  `Dashboard.jsx` (carte `available`), `Sidebar.jsx` (déviation signalée, même raison que
  TASK-009), `.env.example`/`.env.test` (`VITE_REVIEWER_ID`), `index.css` (classes
  portées de `pekopeko-workflow.html` + nouvelles classes pour la modale de rejet, absente
  de toute maquette). Aucun fichier sous `src/` (Python) modifié.
- **Pagination confirmée avec Cleo avant implémentation** (question posée explicitement :
  fetch borné unique façon `Dashboard.jsx` vs. Précédent/Suivant réel façon TASK-009 adapté
  pour ne jamais couper un groupe source entre deux pages — Cleo a choisi la seconde
  option). Détail complet dans la section « Deviations » du ticket : un seul appel borné
  (`limit=500`) par domaine, regroupement complet par `source_id` (impossible à couper
  puisque le regroupement n'a lieu qu'une fois la page domaine entière en main), puis
  pagination d'affichage sur la liste complète de groupes (empaquetage glouton vers une
  cible de ~10 notes/page, sans jamais scinder un groupe) — Précédent/Suivant navigue entre
  ces pages déjà construites, sans round-trip réseau par clic (différent de TASK-009).
- **Autre déviation signalée** : l'étape 2 (jointure détail N+1) utilise
  `Promise.allSettled`, pas `Promise.all` — une proposition malformée (sans
  `provenance.source_id`) fait échouer son seul appel de détail (`400 ValidationError`,
  `review/pipeline.py::get_proposal`) ; l'écran ignore cette seule proposition plutôt que
  de planter entièrement, reprenant le principe déjà documenté de `list_proposals`
  (« a single malformed proposal file must not break the whole review queue »).
- 42/42 tests Vitest (`review.test.js` 5 nouveaux, `Validation.test.jsx` 11 nouveaux — un
  par critère d'acceptation AC1-8/10, plus AC5b et un test bonus sur la pagination —,
  `Dashboard.test.jsx` 10 dont 1 mis à jour en place et 1 nouveau bout-en-bout), couverture
  100 % lignes sur `api/review.js`, 94,17 % lignes sur `pages/Validation.jsx` (87,8 %
  branches), largement au-dessus du seuil 80 % du projet. Vérifié par Claude selon la
  discipline du projet (`npm run build`, `npx vitest run --coverage`, `grep` confirmant
  qu'aucun `fetch()` direct n'existe hors `api/client.js`, `git status --porcelain --
  src/` vide). Rapport dans la section « Verification record » du ticket. Même limite que
  les tickets précédents : pas de second réviseur indépendant, pas de test de fumée
  contre une vraie instance Flask/vault (aucun vault local disponible dans cette
  session) — recommandé en suivi avant usage opérationnel, en particulier pour valider la
  pagination adaptée contre un domaine ayant un groupe source dépassant la cible de ~10
  notes/page.

### TASK-011 — Écran Détail de proposition (Assertions) — `completed`

`specs/tasks/completed/TASK-011-proposal-detail-screen.md`. Implémente
`pekopeko-proposal-detail.html`, scope assertion-only : contenu/métadonnées/source
(Markdown uniquement) en pleine fidélité ; section Provenance complète et section « Logs
d'ingestion complets », toutes deux à pleine fidélité puisque TASK-001a et TASK-001b sont
déjà `completed` (dégradation field-by-field / note "Aucun journal disponible." conservée
si l'un des deux venait à manquer, comme prévu par le ticket). Navigation Précédent/Suivant
réelle sur la file `PROPOSED`/assertion du domaine courant (remplace le sélecteur de note
simulé de la maquette) ; sans édition en place (TASK-006/TASK-014, déféré pré-existant) ni
folder-path builder (TASK-013, déféré pré-existant). Quatrième et dernier maillon de la
chaîne TASK-008→009→010→011 — le socle GUI n'a plus que TASK-012 (backend TASK-005 +
intégration frontend) avant d'être entièrement implémenté. Rédigé le 2026-08-31, implémenté
le 2026-09-03.

- Code : `frontend/src/pages/ProposalDetail.jsx` (nouveau — trois fetches indépendants au
  montage : `getProposal` bloquant pour l'état d'erreur de la page, `listIngestions` et
  `listProposals({status: "PROPOSED"})` dégradant chacun vers une liste vide en cas
  d'échec), `frontend/src/components/ProvenanceSection.jsx` (nouveau — rendu
  conditionnel champ par champ des 4 champs optionnels de TASK-001a), extension de
  `App.jsx` (route `/validation/:domain/:proposalId`), `index.css` (blocs status-bar/
  two-column/section-card/metadata-table/source-preview/logs-section portés de
  `pekopeko-proposal-detail.html`, avec deux classes renommées pour éviter une collision
  avec des classes déjà existantes — `.section-title` du Dashboard → `.card-section-title`,
  `.status-badge` de `TaskStatusBadge` → `.proposal-status-badge`, ce dernier recevant en
  plus une variante de couleur par valeur réelle de `proposal_status`). Réutilise sans
  modification `api/review.js`/`api/tasks.js` (TASK-009/TASK-010),
  `RejectReasonModal.jsx`/`EpistemicStatusBadge.jsx` (TASK-010),
  `TaskEventLog.jsx` (TASK-009). Aucun fichier sous `src/` (Python) modifié.
- **Déviation signalée** : la section Logs distingue le texte de repli propre à cet écran
  ("Aucun journal disponible.", couvrant à la fois "aucune tâche ne correspond" et "tâche
  trouvée mais `events` vide", per l'AC7 du ticket) du texte de repli interne de
  `TaskEventLog` ("Aucun événement enregistré.") — `TaskEventLog` n'est monté que quand une
  tâche est trouvée avec au moins un événement, donc son propre texte de repli n'est en
  pratique jamais atteint depuis cet écran. Détail complet (plus deux autres déviations
  mineures : Métadonnées volontairement plus étroit que la maquette, config de couverture
  `vite.config.js` délibérément non élargie à `src/components/**`) dans la section
  « Deviations from the ticket text » du ticket.
- 56/56 tests Vitest (45 préexistants inchangés + 11 nouveaux :
  `ProvenanceSection.test.jsx` 2 — AC4/AC5 ; `ProposalDetail.test.jsx` 9 — AC1, AC2, AC3,
  AC6, AC7, AC8, AC9, AC9b, AC10), couverture agrégée (`api/**`+`pages/**`, glob existant du
  projet) 97,39 % lignes, `pages/ProposalDetail.jsx` 96,03 % lignes/instructions
  individuellement (branches/fonctions un peu sous 80 % isolément, agrégat au-dessus —
  même limite déjà signalée par le rapport de TASK-010). `ProvenanceSection.jsx` vérifié à
  100 % via un run Vitest ciblé distinct (hors du glob de couverture partagé, voir
  Déviations). Vérifié par Claude selon la discipline du projet (`npx vite build`, `npx
  vitest run --coverage`, `grep` confirmant qu'aucun `fetch()` direct n'existe hors
  `api/client.js`, `git status --porcelain -- src/` vide). Rapport dans la section
  « Verification record » du ticket. Même limite que les tickets précédents : pas de
  second réviseur indépendant, pas de test de fumée contre une vraie instance Flask/vault
  (aucun vault local disponible dans cette session).

### TASK-012 — Revue Entity/Event/Relationship, intégration API + GUI — `backlog`

`specs/tasks/backlog/TASK-012-entity-event-relationship-review-gui.md`. Ferme le socle
GUI : reprend le backend de TASK-005 par référence (aucune modification de son scope ni
de ses 10 AC), ajoute le nom de son erreur typée jusqu'ici innommée
(`UnresolvedRelationshipEndpointError`, `review/errors.py`) et son entrée dans la table
de mapping d'erreurs de TASK-007 (`src/app/api/app.py`, → `409`) — ce qui supersède
l'AC10 de TASK-007 (422 pour `accept` sur entity/event/relationship). Côté frontend,
lève les deux filtres client-side codés en dur sur `assertion` (`Validation.jsx` TASK-010
Scope item 1, `ProposalDetail.jsx` TASK-011 Scope item 8) et ajoute 3 nouveaux composants
de rendu (`EntityTypeBadge`, `EventTemporalRange`, `RelationshipEndpoints`) — aucune
maquette UX n'existe pour ces 3 types (confirmé par grep sur `specs/ux-design/`), donc
pas de portage de maquette, seulement réutilisation des conventions de badge existantes.
Résolution des labels d'`endpoints` de relation sans nouvel endpoint backend : réutilise
les données déjà récupérées par chaque écran (N+1 déjà existant sur Validation, un
nouveau N+1 ciblé par endpoint sur Détail), id non résolu affiché tel quel plutôt que de
bloquer l'écran. Rédigé le 2026-08-31, jamais implémenté.

- Dépend de TASK-005 (`backlog`) et TASK-007 (`completed`) côté backend ; de la chaîne
  TASK-008 → TASK-009 → TASK-010 → TASK-011 (tous `completed`)
  côté frontend. Indépendant de TASK-006/TASK-013/TASK-015.
- Avec ce ticket, **le socle GUI (TASK-007 → TASK-012) est entièrement rédigé** —
  framework tranché (ReactJS, ADI-009), contrat d'intégration backend tranché (Flask,
  ADI-010). Le reste de `specs/tasks/BACKLOG-CLAUDE-V2.md` (section 2, TASK-013 à
  TASK-037) demeure une proposition de re-priorisation, pas une décision actée par Cleo.

## Discipline de continuité (pour humain ou IA, quelle qu'elle soit)

- Toujours lire ce fichier avant de commencer une session, puis suivre « Démarrage de session » ci-dessus.
- Ne jamais assumer qu'une décision `Proposed` a été acceptée sans confirmation explicite de Cleo — même si une ADR existe déjà en brouillon. Une ADR `Proposed` documente une proposition, pas une décision actée.
- Mettre à jour « État actuel » et « Prochaine action exacte » à la fin de chaque session, **et vérifier que les deux restent cohérents entre eux** — pas seulement édités séparément. Une vraie désynchronisation est déjà arrivée : « Prochaine action exacte » pointait encore vers un ticket abandonné par un recalibrage décidé plus haut dans le fichier.
- Préférer des commits git atomiques avec messages clairs plutôt que de compter sur la mémoire de qui que ce soit — `git log` doit rester une source fiable du « pourquoi » d'une décision. (Rien à voir avec ADI-001 : git versionne le *dépôt de code*, jamais le vault canonique.)
- Un ticket de `specs/tasks/` doit être traitable sans relire l'intégralité de `specs/` — s'il ne l'est pas, il est mal découpé.
- Avant de proposer des options d'architecture ou de poser une question de cadrage à Cleo (échelle, déploiement, contraintes...), relire d'abord la « Lecture requise » correspondante en entier — ne pas raisonner depuis des connaissances générales ou une mémoire résumée de conversation. Ces documents existent précisément pour répondre à ce type de question sans avoir à la reposer. Erreur déjà commise sur ADI-001 : ne pas reproduire.
- Une décision d'architecture significative doit exister comme fichier dans `specs/decisions/` (format : `specs/decisions/README.md`), pas seulement comme paragraphe ici ou comme conclusion d'une conversation.
- **Discipline de vérification** (établie sur KC-001, où elle a révélé 2 bugs réels invisibles en se fiant à « les tests passent ») : ne jamais se contenter de relire le rapport de qwen/codex ni de faire confiance à son propre run de tests. Copier le code dans un environnement isolé, rejouer les tests indépendamment, vérifier chaque critère d'acceptation un par un — au besoin en écrivant ses propres scripts de reproduction pour les cas non couverts.
- Tout rapport de vérification/audit demandé à qwen doit être écrit **dans un fichier** (pas seulement dans le chat), format compact ligne par ligne (`[STATUS] check — résultat`), et lister CHAQUE vérification tentée y compris celles qui ont échoué à s'exécuter — jamais résumées ou omises. Raison : lors de l'audit de KC-001, qwen a trouvé un vrai bug et prétendu avoir testé un cas qu'il n'avait jamais exécuté — les deux ont été perdus/déformés dans un résumé chat non structuré.

## Prochaine action exacte

**TASK-001, TASK-002, TASK-003, TASK-004, TASK-001a, TASK-001b, TASK-001c, TASK-001d,
TASK-006, TASK-007, TASK-007a, TASK-008, TASK-009, TASK-010 et TASK-011 sont tous
`completed`** (TASK-011 le 2026-09-03, TASK-001d le 2026-09-03, TASK-001c le 2026-09-03,
TASK-010 le 2026-09-03, TASK-009 le 2026-09-03, TASK-008 le 2026-09-02, TASK-007a le
2026-09-02, TASK-007 le 2026-09-01, TASK-006 le 2026-09-01, TASK-001a et TASK-001b le
2026-08-31, les quatre autres le 2026-08-30). **Deux tickets restent rédigés (`backlog`),
aucun implémenté** — voir leurs sections ci-dessus (TASK-005, TASK-012 — compte vérifié
contre `specs/tasks/backlog/`, cohérent avec « État actuel » ci-dessus).

- Indépendant de tout le reste : TASK-005 (désormais aussi le scope backend de TASK-012,
  voir ci-dessous — toujours implémentable seul, mais plus totalement indépendant du reste
  du socle GUI).
- Chaîne GUI TASK-008 → TASK-009 → TASK-010 → TASK-011 (scaffold, Logs d'ingestion,
  Validation, Détail de proposition) est désormais **entièrement `completed`**. Il ne reste
  que TASK-012, qui dépend en plus de TASK-005 côté backend (voir sa propre section
  ci-dessus) et de cette chaîne frontend au complet côté GUI (satisfait).

Prochaine action : TASK-005 (revue Entity/Event/Relationship) ou TASK-012 (intégration
GUI de TASK-005) — TASK-012 doit suivre TASK-005, qui reprend son backend par référence.
Seul TASK-005 est immédiatement disponible ; TASK-012 le devient une fois TASK-005
`completed`. Avec TASK-011 fini, le socle GUI (TASK-007 → TASK-012) n'a plus que ces deux
tickets avant d'être entièrement implémenté.

---

Note honnête sur la mémoire : ce fichier n'est fiable que si on le tient vraiment à jour. Aucun modèle — Claude y compris — ne « se souvient » de ce projet d'une conversation à l'autre. La mémoire, c'est ce fichier, les ADR dans `specs/decisions/`, les tickets dans `specs/tasks/`, et le dépôt git — pas une session de chat.
