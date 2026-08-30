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

- **Décisions** : ADI-001 à ADI-009 toutes `Accepted` (voir ci-dessous). Aucune décision d'architecture en attente.
- **Code** : `src/app/ingestion/` (TASK-001, ingestion `.md` → Assertions), `src/app/review/` (TASK-002, revue des propositions), `src/app/extraction/` (TASK-003, extraction Entity/Event/Relationship), `src/app/config/` (TASK-004, config locale — provider LLM actif, emplacement de l'index de retrieval, emplacement de l'état de tâche), tests sous `src/tests/`. Les quatre tickets sont dans `specs/tasks/completed/`.
- **Suite** : le reste du travail du Knowledge Core (revue des propositions Entity/Event/Relationship, statut EDITED, retrieval, etc.) n'est pas encore ticketé — voir `specs/tasks/BACKLOG-CLAUDE.md` pour l'inventaire complet (rédigé indépendamment, sans consulter un éventuel `BACKLOG.md`) avant d'écrire le prochain ticket.
- **Reste à ticketer** : l'interface (framework tranché par ADI-009, mais ni scope V1 ni ticket écrits).

## Décisions d'architecture (ADI-001 à ADI-009, toutes `Accepted`)

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

`specs/tasks/completed/TASK-004-local-configuration.md`. Formalise ce qu'ADI-008 (et implicitement ADI-002/ADI-005) supposait déjà : un fichier YAML local (`~/.pekopeko/config.yaml`, jamais dans le vault) plus une liste bornée d'overrides par variable d'env, pour le provider LLM actif, l'emplacement de l'index de retrieval (réservé pour la future TASK-007, non consommé ici) et celui de l'état de tâche. Code : `src/app/config/` (`schema.py`, `loader.py`, `errors.py`), plus `providers/factory.py` neuf dans `src/app/ingestion/` et `src/app/extraction/`, 19 tests dans `src/tests/config/` (100 % de couverture de lignes), quelques tests additionnels dans `src/tests/ingestion/` et `src/tests/extraction/`.

Branchement minimal : `ingestion/pipeline.py` et `extraction/pipeline.py` tirent désormais leur défaut de `state_dir` de la config (`<task_state.dir>/ingestion` et `<task_state.dir>/extraction`), et chacun reçoit une factory optionnelle (`providers/factory.py`) pour construire son `OllamaProvider` depuis la config — sans changer la signature publique de `ingest_source`/`extract_source` ni le fait que `provider` reste un paramètre obligatoire fourni par l'appelant.

- **Amendement (2026-08-30)** : Cleo a ajouté après coup un fichier `.env` compagnon pour les secrets et un champ `default.domain` réservé. Après clarification (3 questions posées et tranchées, voir le ticket) : `.env` (via `python-dotenv`, nouvelle dépendance pinnée) ne fait que charger les mêmes 7 clés bornées `PEKOPEKO_*` déjà existantes — pas un second espace de clés — et une vraie variable d'env réelle garde toujours la priorité sur `.env`. `default.domain` est réservé (comme `retrieval.index_dir` pour TASK-007) : présent dans le schéma, jamais lu par `ingest_source`/`extract_source`, aucun changement de signature. `vault_root` n'a toujours aucune surface de config. 24/24 tests `config` (100 % couverture), vérification en environnement isolé rejouée indépendamment — détail complet dans la section « Amendment verification » du ticket.

- Vérifié par Claude selon la discipline du projet (environnement isolé, 19/19 tests `config` rejoués + couverture 100 % reconfirmée, 44/44 `extraction` et 29/31 `ingestion` (2 échecs préexistants et non liés à ce ticket) rejoués, 11 critères un par un, plus un script de reproduction manuelle bout-en-bout par l'œil). Rapport dans la section « Verification record » du ticket. Même limite que TASK-002/TASK-003 : vérification faite par la même session Claude que l'implémentation, pas par un second réviseur indépendant.

### Interface — pas encore ticketée

Framework tranché (ReactJS, ADI-009) et écrans définis par les maquettes de `specs/ux-design/`, mais le scope V1 et le découpage en tickets restent à faire.

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

**TASK-001, TASK-002, TASK-003 et TASK-004 sont tous `completed`** (2026-08-30). Prochaine action : revoir `specs/tasks/BACKLOG-CLAUDE.md` (inventaire complet du travail restant) et demander à Cleo lequel prioriser ensuite — candidat évident : TASK-005 (revue des propositions Entity/Event/Relationship, miroir de TASK-002 pour la sortie de TASK-003).

---

Note honnête sur la mémoire : ce fichier n'est fiable que si on le tient vraiment à jour. Aucun modèle — Claude y compris — ne « se souvient » de ce projet d'une conversation à l'autre. La mémoire, c'est ce fichier, les ADR dans `specs/decisions/`, les tickets dans `specs/tasks/`, et le dépôt git — pas une session de chat.
