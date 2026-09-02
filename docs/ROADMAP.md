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

- **Décisions** : ADI-001 à ADI-010 toutes `Accepted` (voir ci-dessous). Aucune décision d'architecture en attente.
- **Code** : `src/app/ingestion/` (TASK-001, ingestion `.md` → Assertions ; étendu par TASK-001a, provenance d'extraction enrichie, par TASK-001b, journal d'événements de tâche, et par TASK-007, paramètre `task_id`/`list_task_states`), `src/app/review/` (TASK-002, revue des propositions ; étendu par TASK-006, statut EDITED + historisation des Proposals), `src/app/extraction/` (TASK-003, extraction Entity/Event/Relationship ; étendu par TASK-001b et par TASK-007, paramètre `task_id`/`list_task_states`), `src/app/config/` (TASK-004, config locale — provider LLM actif, emplacement de l'index de retrieval, emplacement de l'état de tâche), `src/app/api/` (TASK-007, couche API HTTP REST — Flask, ADI-010), tests sous `src/tests/`. Ces huit tickets sont dans `specs/tasks/completed/`.
- **Cahier de tests** (2026-09-02) : `specs/tests/test-plan.md`, tracé aux 18 UC de `specs/product/use-cases.md` et aux 8 tickets `completed`. Deux couches sous `src/tests/` : `acceptance/` (déterministe, appels directs aux pipelines, provider factice fixe — exécutée par défaut) et `e2e/` (serveur Flask réel + vrai Ollama local, marker `pytest -m e2e`, exclue par défaut via `pytest.ini`). **Deux écarts réels découverts et vérifiés contre un serveur réel** (documentés dans le cahier, section « Findings ») : (1) les propositions entity/event/relationship de `extraction/` (contrat `item_type`, pas de champ `id`) sont invisibles pour tout `review/` — `list_proposals` les omet silencieusement et `get_proposal`/`accept` renvoient `400 ValidationError` — pas seulement bloquées côté métier ; (2) l'AC10 de TASK-007 (« accept sur entity/event/relationship → 422 ») ne se déclenche jamais avec une vraie proposition d'extraction (elle renvoie `400` avant d'atteindre ce chemin) — le test existant qui la vérifie construit sa proposition avec le contrat d'`ingestion`/`review`, pas celui réel d'`extraction`. **TASK-005 devra réconcilier les deux contrats de champs, pas seulement ajouter la logique métier d'acceptation.** Problème préexistant signalé au passage (non corrigé, hors périmètre) : `pytest src/tests/` en un seul run échoue à la collecte sur plusieurs `_helpers.py` de même nom sans `__init__.py` — voir la section dédiée du cahier.
- **Suite** : sept tickets `backlog` restent maintenant (neuf moins TASK-006 et TASK-007,
  complétés respectivement le 2026-09-01 et le 2026-09-01). Cœur GUI : TASK-005 (revue
  Entity/Event/Relationship) ne dépend que du contrat de fichiers TASK-001/003 ;
  TASK-008/009/010/011 (scaffold + Dashboard/Settings,
  Ingestion Logs, Validation, Détail de proposition) forment une chaîne de dépendance
  (008→009→010→011, chacun réutilisant les composants/wrappers API du précédent).
  **Trois tickets backend satellites** (2026-08-31, voir leurs sections ci-dessous) ont été
  ajoutés en écrivant TASK-009/010/011, suite à la décision de Cleo que les maquettes
  `specs/ux-design/` sont la cible : là où le backend manquait une donnée qu'une maquette
  montre, un ticket satellite additif comble le trou plutôt que de couper la fonctionnalité
  GUI — TASK-001a (provenance d'extraction enrichie, étend TASK-001, **`completed`** le
  2026-08-31), TASK-001b (journal d'événements de tâche, étend TASK-001+TASK-003,
  **`completed`** le 2026-08-31), TASK-007a (pagination sur les endpoints de liste, étend TASK-007, encore
  `backlog`). Suffixe lettré délibéré pour ne renuméroter ni les tickets déjà écrits ni
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

## Décisions d'architecture (ADI-001 à ADI-010, toutes `Accepted`)

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

### TASK-007a — Pagination sur les endpoints de liste — `backlog`

`specs/tasks/backlog/TASK-007a-list-endpoint-pagination.md`. Ticket satellite
(2026-08-31) étendant TASK-007 : `?limit=`/`?offset=` sur les 3 endpoints de liste
(ingestions/extractions/proposals), enveloppe de réponse `{items, total, limit, offset}`.
Écrit comme ticket séparé plutôt qu'édition en place de TASK-007, pour ne pas invalider la
numérotation de ses critères d'acceptation déjà cités ailleurs (TASK-008 cite l'AC12 de
TASK-007). TASK-009/TASK-010 en dépendent pour une vraie pagination serveur. Jamais
implémenté.

### TASK-008 — Scaffold React + écrans Dashboard et Settings — `backlog`

`specs/tasks/backlog/TASK-008-react-scaffold-dashboard-settings.md`. Premier code frontend
du dépôt : projet React (Vite, JS, React Router — décisions tranchées par ce ticket,
ADI-009 les avait explicitement laissées ouvertes), nouveau répertoire `frontend/`
(sibling de `src/`). Livre `pekopeko-dashboard.html` (stats agrégées sur les 5 domaines
côté client, cartes de modules) et un écran Settings lecture seule (nouveau, absent des
maquettes). Rédigé le 2026-08-31, jamais implémenté.

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

### TASK-009 — Écran Logs d'ingestion — `backlog`

`specs/tasks/backlog/TASK-009-ingestion-logs-screen.md`. Implémente
`pekopeko-ingestion.html` : table filtrable/paginée des tâches d'ingestion **et**
extraction, détail des erreurs/doublons/événements par tâche (via TASK-001b), pagination
serveur réelle (via TASK-007a). Fait passer la carte de module « Logs d'ingestion » du
Dashboard à `available`. Rédigé le 2026-08-31 en appliquant le principe « les maquettes
sont la cible » (voir note en tête de section « Suite » ci-dessus) : aucun élément de la
maquette n'a été silencieusement supprimé — pagination et journal d'événements comblés par
TASK-007a/TASK-001b plutôt que retirés. Dépend de TASK-007/TASK-007a/TASK-001b/TASK-008.
Jamais implémenté.

### TASK-010 — Écran Validation (Assertions) — `backlog`

`specs/tasks/backlog/TASK-010-validation-screen.md`. Implémente `pekopeko-workflow.html`,
scope assertion-only (miroir de TASK-002) : propositions groupées par source (jointure
client sur `provenance.source_id`, y compris un N+1 assumé sur `GET /proposals/<id>` faute
de `body`/`source_id` sur `ProposalSummary` — décision explicite de Cleo plutôt qu'étendre
TASK-007), badge de statut épistémique (4 valeurs réelles), accepter/rejeter individuels.
Sans folder-path builder ni bulk actions — déféré **pré-existant** (TASK-013/TASK-015,
acté avant cette session dans `BACKLOG-CLAUDE-V2.md`/TASK-007), pas une coupe de ce
ticket. `reviewer_id` fourni par une variable d'env au build (`VITE_REVIEWER_ID`, même
pattern que `VITE_API_KEY`). Dépend de TASK-007/TASK-007a/TASK-008/TASK-009 (réutilise
`api/tasks.js`). Jamais implémenté.

### TASK-011 — Écran Détail de proposition (Assertions) — `backlog`

`specs/tasks/backlog/TASK-011-proposal-detail-screen.md`. Implémente
`pekopeko-proposal-detail.html`, scope assertion-only : contenu/métadonnées/source
(Markdown uniquement) en pleine fidélité ; section Provenance complète et section « Logs
d'ingestion complets » qui dépendent de TASK-001a/TASK-001b respectivement — dégradation
gracieuse (champ par champ / note "aucun journal disponible") si ces satellites ne sont
pas encore implémentés, jamais un crash. Navigation Précédent/Suivant réelle sur la file du
domaine courant (remplace le sélecteur de note simulé de la maquette). Sans édition en
place (TASK-006/TASK-014, déféré pré-existant) ni folder-path builder (TASK-013, déféré
pré-existant). Dépend de TASK-007/TASK-008/TASK-009/TASK-010 ; TASK-001a/TASK-001b pour
la pleine fidélité (non bloquants). Jamais implémenté.

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
  TASK-008 → TASK-009 → TASK-010 → TASK-011 (tous `backlog`) côté frontend. Indépendant
  de TASK-006/TASK-013/TASK-015.
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

**TASK-001, TASK-002, TASK-003, TASK-004, TASK-001a, TASK-001b, TASK-006 et TASK-007
sont tous `completed`** (TASK-007 le 2026-09-01, TASK-006 le 2026-09-01, TASK-001a et
TASK-001b le 2026-08-31, les quatre autres le 2026-08-30). **Sept tickets restent
rédigés (`backlog`), aucun implémenté** — voir leurs sections ci-dessus (TASK-005, 007a,
008, 009, 010, 011, 012 — compte vérifié contre `specs/tasks/backlog/`, cohérent avec
« État actuel » ci-dessus).

- Indépendant de tout le reste : TASK-005 (désormais aussi le scope backend de TASK-012,
  voir ci-dessous — toujours implémentable seul, mais plus totalement indépendant du reste
  du socle GUI).
- Chaîne GUI, à implémenter dans cet ordre relatif : TASK-008 → TASK-009 →
  TASK-010 → TASK-011 → TASK-012 (chacun dépend du/des précédent(s) pour son
  shell/composants/wrappers API ; TASK-012 dépend en plus de TASK-005 côté backend — voir
  sa propre section ci-dessus). TASK-008 peut démarrer dès maintenant : son unique
  prérequis backend, TASK-007, est `completed`.
- Satellite backend restant : TASK-007a dépend de TASK-007 (`completed`) — peut être fait
  dès maintenant. TASK-009 tire pleinement parti de TASK-007a s'il est fait en premier ;
  TASK-011 tire déjà pleinement parti de TASK-001a et TASK-001b (tous deux `completed`)
  pour ses sections Provenance et Logs respectivement.

Prochaine action : demander à Cleo l'ordre d'implémentation. Suggestion si aucune
préférence : TASK-007a → TASK-008 → TASK-009 → TASK-010 →
TASK-011 → TASK-005 → TASK-012 dans l'ordre (TASK-005 doit précéder TASK-012, qui reprend
son backend par référence).

---

Note honnête sur la mémoire : ce fichier n'est fiable que si on le tient vraiment à jour. Aucun modèle — Claude y compris — ne « se souvient » de ce projet d'une conversation à l'autre. La mémoire, c'est ce fichier, les ADR dans `specs/decisions/`, les tickets dans `specs/tasks/`, et le dépôt git — pas une session de chat.
