# Pekopeko — Roadmap de reprise

## Comment utiliser ce fichier

- Ce fichier est le point d'entrée unique pour reprendre le travail sur Pekopeko — que ce soit toi, une nouvelle conversation avec Claude, ou qwen3-coder:30b en local.
- Avant de faire quoi que ce soit sur ce projet, lire ce fichier en entier. Il est volontairement court.
- Après chaque session qui change quelque chose (spec, décision, code), mettre à jour les sections « État actuel » et « Prochaine action » avant de terminer. Ne jamais les laisser désynchronisées de la réalité du dépôt.
- `docs/PROJECT_HANDOFF.md` est un dump ponctuel de contexte généré une seule fois — ce n'est pas un fichier vivant, il n'est pas mis à jour, ne t'y fie pas pour l'état courant. `ROADMAP.md` est le seul document de continuité à tenir à jour.

## État actuel (résumé)

Phase : Foundation / Discovery → Product Definition (en cours). Aucune ligne de code écrite — tout le travail à ce jour porte sur les documents de spec eux-mêmes, pas sur le système. Phase 0 (nettoyage de cohérence des identifiants) est terminée et vérifiée. Prochaine étape : Phase 1, les 6 décisions d'architecture (ADI-001 à 006) — ce sont de vrais choix produit/architecture, pas du travail mécanique délégable ; ils demandent l'arbitrage de Cleo, Claude aide à peser les options.

Dernière revue complète : 2026-08-16, lecture intégrale de `specs/**`, `README.md` et `docs/PROJECT_HANDOFF.md`. Détail des corrections : voir Phase 0 ci-dessous.

## Plan en phases

### Phase 0 — Nettoyage des identifiants (bloquant)
5 sous-tâches, toutes faites directement par Claude (édition scriptée + vérification par grep). La tentative initiale de déléguer E à qwen a été abandonnée : qwen n'a produit qu'un plan (aucun fichier édité), et ce plan contenait au moins une affirmation fausse (il indiquait que KSR-004 citait CAP-CORE-017, ce qui était inexact) — vérification faite avant de faire confiance au rapport. Leçon retenue : ce type de tâche (audit sémantique précis, cross-référencement entre documents) n'est pas un bon candidat de délégation à un modèle local de 30B ; les tâches de code volumineuses et bien bornées de la Phase 3 sont un test plus représentatif.

- **A. Collision INV-001..009** — FAIT (2026-08-16). `specs/domain/knowledge-invariants.md` garde le namespace `INV-` (001 à 021). Les 9 items de `specs/architecture/principles.md` renommés `AP-001..009` partout où ils étaient cités (`principles.md`, `capabilities.md`, `technical-requirements.md`). Vérifié par grep.
- **B. Duplication RQR-001/002/003** — FAIT (2026-08-16). Section Relationship Requirements (section 5) garde `RQR-001..006`. Section Retrieval Requirements (section 7) et le renvoi correspondant dans `capabilities.md` renommés `RTR-001..003`. Vérifié par grep.
- **C. Double section "## 23."** — FAIT (2026-08-16). Renumérotation en cascade : 23 (Architectural Decision Inputs, inchangé) → 24 (Final Validation) → 25 (Summary) → 26 (Contradictions or Gaps Discovered). Séquence 1-26 vérifiée sans trou ni doublon.
- **D. Dérive domaines** — FAIT (2026-08-16). `knowledge-invariants.md` INV-008 (domain isolation) mis à jour pour inclure PUBLISHING. Vérifié par grep.
- **E. Audit exhaustif des renvois CAP-CORE-XXX** — FAIT (2026-08-16), par Claude directement (relecture complète de `technical-requirements.md` croisée avec les listes "Technical Requirements" officielles de `capabilities.md`, utilisées comme source de vérité plutôt que de deviner par mot-clé). 45 réattributions + 1 valeur invalide supprimée (CAP-CORE-017 dans MQR-001, redondante avec CAP-CORE-016 déjà présent dans la même liste). Vérifié : plus aucune valeur hors 001-016 dans le fichier.
  - Restent volontairement non tranchés (ambigus, pas de mapping autoritaire dans `capabilities.md`, valeur actuelle laissée telle quelle) : TCR-001, TCR-002, SQR-001, FHR-001, FHR-002, CPR-001, ADI-001, ADI-004, ADI-006 ; et deux items où `capabilities.md` liste la même exigence sous deux capacités différentes (KSR-009 sous capacités 1 et 7 → tranché en faveur de 007 ; TR-005/DMR-002 sous capacités 5 et 14 → tranché en faveur de 014, correspondance de titre).
  - Repérés comme incomplets plutôt que faux (aucune citation CAP-CORE du tout, non ajoutée car hors périmètre de cette tâche) : PRQ-001, IQR-001, SSR-001, IPR-001.

**Statut : Phase 0 terminée (A-E faits et vérifiés).**

### Phase 1 — Décisions d'architecture (ADI-001 à ADI-006)
Les 6 questions ouvertes dans `technical-requirements.md` (section « Architectural Decision Inputs ») doivent être tranchées et écrites comme de vraies ADR dans `specs/decisions/` (le dossier ne contient aujourd'hui qu'un README de format, aucune décision réelle) :
- ADI-001 : modèle de persistance canonique
- ADI-002 : retrieval sémantique intégré ou système dédié
- ADI-003 : le modèle de relations nécessite-t-il une base graphe ou de simples structures graph-like
- ADI-004 : rôle d'Obsidian vis-à-vis de la connaissance canonique
- ADI-005 : quelles opérations synchrones vs asynchrones
- ADI-006 : quoi persister vs recalculer

**Statut : à faire** (dépend de la Phase 0 pour ne pas référencer des ID cassés dans les ADR).

### Phase 2 — Premiers tickets concrets
Découper `specs/tasks/backlog/` en tickets suffisamment petits et autonomes pour être traités par qwen3-coder:30b sans relire tout le corpus : fichiers concernés, schéma/interface attendu, critères d'acceptation testables, et les 2-3 invariants pertinents cités explicitement dans le ticket (pas par renvoi global). Choisir en priorité un scope V1 minimal plutôt que de vouloir adresser les 18 cas d'usage d'un coup.

**Statut : à faire** (dépend de la Phase 1 pour avoir un schéma minimal à partir duquel écrire des tickets concrets).

### Phase 3 — Implémentation
qwen3-coder:30b (ou autre) traite les tickets un par un. Chaque ticket terminé passe de `specs/tasks/backlog/` à `active/` puis `completed/`.

**Statut : pas commencé.**

## Discipline de continuité (pour humain ou IA, quelle qu'elle soit)

- Toujours lire ce fichier avant de commencer une session de travail sur Pekopeko.
- Ne jamais assumer qu'une décision « PROPOSED » a été acceptée sans confirmation explicite dans `specs/decisions/`.
- Mettre à jour « État actuel » et « Prochaine action » à la fin de chaque session.
- Préférer des commits git atomiques avec messages clairs plutôt que de compter sur la mémoire de qui que ce soit — `git log` doit rester une source fiable du « pourquoi » d'une décision.
- Un ticket de `specs/tasks/` doit être traitable sans avoir besoin de relire l'intégralité de `specs/` — s'il ne l'est pas, il est mal découpé.

## Prochaine action exacte

Phase 0 terminée. Cleo relit le `git diff` complet et commit (rien n'a été commité automatiquement). Ensuite : Phase 1 — trancher les 6 questions ADI-001 à 006 avec Claude (discussion des options, pas une délégation ni à qwen ni à Claude seul), puis les écrire comme de vraies ADR dans `specs/decisions/`.

---

Note honnête sur la mémoire : ce fichier n'est fiable que si on le tient vraiment à jour. Aucun modèle — Claude y compris — ne « se souvient » de ce projet d'une conversation à l'autre. La mémoire, c'est ce fichier et le dépôt git, pas une session de chat.
