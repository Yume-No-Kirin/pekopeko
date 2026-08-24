# Pekopeko — Questions ouvertes, points à définir, incohérences

Compilation de tout ce qui reste non tranché ou non aligné dans `specs/`, réunie en un seul endroit. **Ceci est un instantané de compilation** (2026-08-24), pas un document vivant tenu à jour automatiquement — comme `docs/PROJECT_HANDOFF.md`, il peut devenir obsolète si `specs/` évolue sans que ce fichier soit relu et régénéré. `docs/ROADMAP.md` reste le seul document de continuité fiable.

Statuts :
- `[ouvert]` — question jamais tranchée nulle part dans le corpus.
- `[à trancher]` — sous-question explicitement différée à l'intérieur d'une ADR par ailleurs `Accepted` (conditionnelle : « à revoir si le besoin devient réel »), pas bloquante aujourd'hui.
- `[incohérence]` — désaccord factuel entre documents (ID/nom qui diverge, document non mis à jour après une décision, terme manquant) — une correction documentaire à faire, pas une décision à prendre.
- `[fermé]` — point de vérification qui aurait pu sembler ouvert ; confirmé résolu pendant cette compilation.

## 1. Vision & portée produit

- [ouvert] Détails d'implémentation concrets de l'architecture modulaire — `specs/product/vision.md`, « Things That Still Need to be Defined »
- [ouvert] Choix technologiques finaux (bases de données, vector stores) — `specs/product/vision.md` (langage backend déjà tranché, ADI-007 ; providers LLM = architecture pluggable tranchée, choix concret encore ouvert, voir section 11)
- [ouvert] Design UI/UX complet et patterns d'interaction — `specs/product/vision.md`, `specs/product/scope.md` (hors scope Foundation) ; recoupe ADI-007 (frontend différé) et section 7 Q4 ci-dessous
- [ouvert] Spécifications détaillées des modules d'apprentissage (learning modules) — `specs/product/vision.md`, `specs/product/scope.md` (hors scope Foundation)
- [ouvert] Approches d'intégration entre modules/capacités — `specs/product/vision.md` ; recoupe section 7 Q7 et section 5 Gap 1 ci-dessous
- [ouvert] Quels besoins utilisateurs doivent piloter la priorisation des futures fonctionnalités — `specs/product/scope.md`, Open Product Questions #1
- [ouvert] Comment structurer la connaissance personnelle pour supporter à la fois rappel et raisonnement — `specs/product/scope.md`, Open Product Questions #2
- [ouvert] Niveau de persistance/continuité requis pour l'expérience utilisateur — `specs/product/scope.md`, Open Product Questions #3
- [ouvert] Comment intégrer différentes modalités d'apprentissage — `specs/product/scope.md`, Open Product Questions #4
- [ouvert] Implications de vie privée et de propriété des données selon les approches — `specs/product/scope.md`, Open Product Questions #5
- [ouvert] Équilibre optimal entre modularité et infrastructure partagée — `specs/product/scope.md`, Open Architectural Questions #1
- [ouvert] Comment les modules doivent communiquer en gardant un couplage faible — `specs/product/scope.md`, Open Architectural Questions #2 ; recoupe section 7 Q7, section 5 Gap 1, section 6 §26.1
- [ouvert] Patterns de gestion de données persistantes à travers les modules — `specs/product/scope.md`, Open Architectural Questions #3
- [ouvert] Comment garantir une observabilité cohérente sur tous les composants — `specs/product/scope.md`, Open Architectural Questions #4
- [ouvert] Stratégies de test appropriées pour des systèmes intégrant de l'IA — `specs/product/scope.md`, Open Architectural Questions #5
- [ouvert] Comment gérer l'évolution des interfaces à mesure que les modules se développent — `specs/product/scope.md`, Open Architectural Questions #6
- [ouvert] Bonnes pratiques de gestion des dépendances entre modules — `specs/product/scope.md`, Open Architectural Questions #7

## 2. Besoins utilisateurs

- [ouvert] Quelles capacités V1 prioriser — `specs/product/user-needs.md` §7 ; reposée à l'identique dans `specs/product/product-model.md` §9 et `specs/product/capabilities.md` (produit) → 3 formulations non reliées entre elles
- [ouvert] Comment concevoir l'UX de la file de revue (review queue) pour l'efficacité — `specs/product/user-needs.md` §7 ; reposée à l'identique dans `product-model.md` §9 et CAP-002 de `capabilities.md` → 3 formulations non reliées
- [ouvert] Niveau d'automatisation approprié selon le type de validation de connaissance — `specs/product/user-needs.md` §7 ; reposée à l'identique dans `product-model.md` §9 et CAP-002 de `capabilities.md` → 3 formulations non reliées
- [ouvert] Comment implémenter conceptuellement la séparation par domaine (sans détails techniques) — `specs/product/user-needs.md` §7 ; reposée dans `product-model.md` §9 → 2 formulations non reliées
- [ouvert] Quels sont les workflows utilisateurs les plus critiques à supporter dans la version initiale — `specs/product/user-needs.md` §7

## 3. Modèle produit

- [ouvert] Limites et interfaces précises des modules initiaux — `specs/product/product-model.md` §9
- [ouvert] Quels types d'information dérivée par IA nécessitent une revue humaine obligatoire — `specs/product/product-model.md` §9
- [ouvert] Quelles actions futures pourraient un jour devenir autonomes (sans revue humaine) — `specs/product/product-model.md` §9
- (les 3 autres questions de cette section sont des doublons déjà listés en section 2 : portée V1, UX file de revue, séparation par domaine)

## 4. Capacités produit (CAP-001/002/003)

- [ouvert] CAP-001 — Quelle granularité de versioning maintenir — `specs/product/capabilities.md`
- [ouvert] CAP-001 — Comment gérer les différents types de relations de connaissance — `specs/product/capabilities.md`
- [ouvert] CAP-001 — Ce qui constitue une connaissance « importante » nécessitant un traitement spécial — `specs/product/capabilities.md`
- [ouvert] CAP-002 — Quels formats d'entrée supporter en version initiale — `specs/product/capabilities.md`
- [ouvert] CAP-003 — Quels types de relations supporter initialement — `specs/product/capabilities.md`
- [ouvert] CAP-003 — Comment prioriser les différents types de raisonnement — `specs/product/capabilities.md`
- [ouvert] CAP-003 — Ce qui constitue une « contradiction potentielle » nécessitant l'attention de l'utilisateur — `specs/product/capabilities.md`
- [incohérence] `CAP-001/002/003` (`specs/product/capabilities.md`) ne sont référencés par ID nulle part ailleurs dans le corpus — catalogue de capacités produit totalement déconnecté des 16 `CAP-CORE-XXX` (architecture) et des 18 `UC-XXX` (cas d'usage). Déjà consigné dans `docs/ROADMAP.md` (Phase 0 tâche F, et gap #3 de la correction de traçabilité du 2026-08-23), toujours non résolu.

## 5. Cas d'usage

- [ouvert] Gap 1 — Coordination entre modules non définie au-delà des capacités partagées — `specs/product/use-cases.md`, « Potential Gaps »
- [ouvert] Gap 2 — Exigences de performance/scaling pour bases de connaissance volumineuses ou ingestion à haut volume non définies — `specs/product/use-cases.md`
- [ouvert] Gap 3 — Cohérence UX à travers les différents modules non adressée — `specs/product/use-cases.md`
- [incohérence] Libellé « A définir — Source and Ingestion Management » cité dans 6 cas d'usage (UC-001, UC-003, UC-006, UC-007, UC-008, UC-016) sans ID `CAP-CORE` assigné et sans capacité correspondante dans `specs/architecture/capabilities.md` — capacité manquante au catalogue, ou couverture incomplète
- [incohérence] Libellé « A définir — Knowledge Health / Integrity Monitoring » cité dans UC-012, même gap
- [incohérence] Ces deux libellés « A définir » sont en français, alors que `specs/` est censé être rédigé en anglais — rupture de convention linguistique
- [incohérence] Noms de capacités divergents entre `use-cases.md` et `specs/architecture/capabilities.md` sous le même ID `CAP-CORE` (IDs cohérents, libellés non synchronisés) : `CAP-CORE-001` « Knowledge Management » vs « Knowledge Representation Capability » ; `CAP-CORE-002` « Human Review » vs « Human Validation Capability » ; `CAP-CORE-009` « Relationship Management » vs « Relationship Traversal Capability » ; `CAP-CORE-011` nommé différemment même entre UC-002 et UC-003/UC-008 au sein de `use-cases.md` lui-même ; `CAP-CORE-014` « Explicit Cross-Domain Operations » vs « Cross-Domain Authorization Capability »
- [ouvert] `CAP-CORE-012` (Asynchronous Task Management) et `CAP-CORE-016` (Module Integration) définis dans `specs/architecture/capabilities.md` mais jamais cités par aucun cas d'usage — capacités purement d'infrastructure, ou couverture incomplète de `use-cases.md` à vérifier

## 6. Exigences techniques

- [incohérence] `specs/architecture/technical-requirements.md` §23 « Architectural Decision Inputs » (ADI-001 à ADI-006) toujours rédigée comme questions non tranchées (« must determine... ») alors que les 6 ADR correspondantes sont `Accepted` depuis le 2026-08-16 — document source jamais mis à jour après la décision
- [incohérence] §25 « Summary » → la liste des « unresolved architectural questions » reprend les mêmes points déjà tranchés par ADI-001..006 — même désynchronisation
- [ouvert] Point #10 de cette même liste : « Quelle est la plus petite architecture qui satisfait les invariants ? » — jamais répondu explicitement par aucune ADR
- [ouvert] §26 « Contradictions or Gaps Discovered » — les 4 points (communication inter-modules, scaling perf, cohérence UX, specs d'intégration modules↔capacités) recoupent quasi mot pour mot les « Potential Gaps » de `use-cases.md` (section 5 ci-dessus), jamais adressés par une ADR

## 7. Architecture des modules

Les 7 « Open Questions » de `specs/modules/module-architecture.md`, explicitement qualifiées dans le document source de « genuinely unresolved conceptual decisions » :

- [ouvert] Q1 — Quelles capacités appartiennent directement au Knowledge Core plutôt qu'à une couche plateforme partagée
- [ouvert] Q2 — Si de futurs modules devraient être des plugins activables/désactivables
- [ouvert] Q3 — Comment fonctionnent les permissions spécifiques à un module selon le rôle ou niveau d'accès de l'utilisateur
- [ouvert] Q4 — Comment synchroniser les représentations spécifiques à un module avec la GUI unifiée — recoupe ADI-007 (frontend différé, section 11)
- [ouvert] Q5 — Si certains calculs dérivés doivent être mis en cache ou régénérés selon les changements de la connaissance source
- [ouvert] Q6 — Quel mécanisme gouverne la mise à jour de la logique spécifique à un domaine dans un module
- [ouvert] Q7 — Comment le système gère les scénarios où plusieurs modules doivent coordonner une opération cross-domain unique — recoupe section 5 Gap 1

## 8. Modèle de connaissance

- [ouvert] Faut-il des distinctions sémantiques supplémentaires entre types d'entités ou de relations — `specs/domain/knowledge-model.md`, Open Questions
- [ouvert] Comment traiter une connaissance qui s'étend sur plusieurs domaines mais reste contextuellement unifiée — `specs/domain/knowledge-model.md` ; tension non croisée avec INV-008/INV-009 (isolation de domaine déjà imposée par ailleurs, cf. `specs/domain/knowledge-invariants.md`)
- [ouvert] Quels niveaux de granularité temporelle sont appropriés pour le suivi de validité — `specs/domain/knowledge-model.md`
- [ouvert] Faut-il distinguer « vérité source » et « interprétation système » en plus des concepts existants — `specs/domain/knowledge-model.md`

## 9. Invariants de connaissance

- [ouvert] Faut-il des invariants supplémentaires pour la connaissance partiellement acceptée ou conditionnellement valide — `specs/domain/knowledge-invariants.md`, Open Questions
- [ouvert] Comment traiter les frontières de domaine ambiguës ou qui se chevauchent — `specs/domain/knowledge-invariants.md`
- [ouvert] Quels mécanismes garantissent le maintien des invariants pendant l'évolution du système — `specs/domain/knowledge-invariants.md`
- [ouvert] Faut-il davantage de nuance entre « rejeté » et « inconnu » — `specs/domain/knowledge-invariants.md`

## 10. Glossaire

- [incohérence] Termes définis formellement dans `specs/domain/knowledge-model.md` mais absents de `specs/product/glossary.md` malgré un usage intensif dans tout le corpus : Assertion, Entity, Event, Relationship, Proposal, Canonical Knowledge, Derived Knowledge, Provenance, Representation, Context/Universe, Validation, Epistemic Status, Lifecycle Status, Temporal Validity, Cross-Domain Task/Operation
- [incohérence] Définition de « Knowledge » légèrement divergente entre `glossary.md` et `knowledge-model.md` (formulations différentes, non contradictoires mais non identiques)

## 11. ADR — sous-questions différées

Ces ADR sont `Accepted` — la décision elle-même n'est pas à rouvrir — mais chacune contient un point explicitement différé :

- [à trancher] ADI-001 — Discipline d'écriture concurrente (single-writer ou verrouillage de fichier) pas encore conçue ; à faire avant la Phase 3 — `specs/decisions/ADI-001-canonical-persistence-model.md`, Consequences
- [à trancher] ADI-002 — Serveur d'index partagé multi-appareils explicitement laissé ouvert pour une future ADR si le besoin devient réel — `specs/decisions/ADI-002-retrieval-system.md`, Alternatives considered
- [à trancher] ADI-003 — Bascule vers une base graphe si le traversal devient un goulot d'étranglement, nécessiterait une nouvelle ADR — `specs/decisions/ADI-003-relationship-model.md`, Consequences
- [à trancher] ADI-005 — Visibilité cross-device des tâches asynchrones en cours, volontairement simplifiée en V1 ; nécessiterait une nouvelle ADR si le besoin réel apparaît — `specs/decisions/ADI-005-sync-vs-async.md`, Consequences
- [à trancher] ADI-006 — La discipline d'identifiants stables (précondition de la montée en charge sans redesign) n'est pas encore vérifiée en pratique — à surveiller en Phase 3 — `specs/decisions/ADI-006-persistence-vs-recomputation.md`, « Why this scales »
- [ouvert] ADI-007 — Choix du framework frontend/GUI explicitement différé à une future ADR, une fois le travail GUI cadré — `specs/decisions/ADI-007-implementation-language.md` ; recoupe section 7 Q4
- [ouvert] ADI-008 — Choix des 1-2 providers LLM concrets par défaut et du mécanisme de config, pas encore cadré (l'architecture pluggable elle-même est tranchée) — `specs/decisions/ADI-008-llm-provider-architecture.md`, Consequences

## 12. Format des ADR

- [incohérence] `specs/decisions/README.md` documente l'enum de statut en minuscules (« proposed, accepted, superseded, rejected ») alors que les 8 ADR réelles utilisent `Accepted` capitalisé, et aucune n'utilise superseded/rejected/proposed — dérive terminologique mineure entre la spec de format et la pratique
- [incohérence] La note finale de `specs/decisions/README.md` (« Actual ADRs will be created as decisions are made during development ») est obsolète — 8 ADR existent déjà dans le dossier

## 13. Points de vérification (pour mémoire — pas des questions ouvertes)

- [fermé] Aucune des 8 ADR (ADI-001 à ADI-008) n'est au statut `Proposed` — toutes `Accepted` ; la règle CLAUDE.md (« Proposed n'est pas une décision ») n'est donc violée nulle part actuellement
- [fermé] Working tree vérifié le 2026-08-24 : `docs/ROADMAP.md`, `specs/architecture/capabilities.md`, `specs/architecture/technical-requirements.md`, `specs/product/glossary.md`, `specs/product/use-cases.md` produisent un diff vide malgré leur statut « modifié » dans `git status` — tout est déjà commité. `specs/tasks/backlog/KC-001-canonical-item-storage.md` apparaît « Deleted » seulement parce qu'il a été déplacé (et commité) vers `specs/tasks/completed/KC-001-canonical-item-storage.md`, où il est bien présent avec le statut `completed`.
