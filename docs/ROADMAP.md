# Pekopeko — Roadmap de reprise

## Comment utiliser ce fichier

- Ce fichier est le point d'entrée unique pour reprendre le travail sur Pekopeko — que ce soit toi, une nouvelle conversation avec Claude, ou qwen3-coder:30b en local.
- Avant de faire quoi que ce soit sur ce projet, lire ce fichier en entier. Il est volontairement court.
- Après chaque session qui change quelque chose (spec, décision, code), mettre à jour les sections « État actuel » et « Prochaine action » avant de terminer. Ne jamais les laisser désynchronisées de la réalité du dépôt.
- `docs/PROJECT_HANDOFF.md` est un dump ponctuel de contexte généré une seule fois — ce n'est pas un fichier vivant, il n'est pas mis à jour, ne t'y fie pas pour l'état courant. `ROADMAP.md` est le seul document de continuité à tenir à jour.

## État actuel (résumé)

Phase : Foundation / Discovery → Product Definition (en cours). Aucune ligne de code écrite. Les specs produit/architecture/domaine/modules sont rédigées et globalement cohérentes dans leur intention, mais contiennent des incohérences d'identifiants qui doivent être corrigées avant de servir de base à du code (voir « Problèmes connus »).

Dernière revue complète : 2026-08-16, lecture intégrale de `specs/**`, `README.md` et `docs/PROJECT_HANDOFF.md`.

## Problèmes connus à corriger (non corrigés à ce jour)

1. **Collision INV-001..009** — `specs/architecture/principles.md` et `specs/domain/knowledge-invariants.md` définissent chacun un INV-001 à INV-009 avec des significations différentes (le second va jusqu'à INV-021). À fusionner ou renuméroter l'un des deux jeux.
2. **Renvois CAP-CORE-XXX cassés** dans `specs/architecture/technical-requirements.md` — TR-004, TR-005, TR-006, TR-007, TR-008 citent des CAP-CORE-XXX qui ne correspondent pas à la numérotation canonique de `specs/architecture/capabilities.md` (confirmée par `docs/PROJECT_HANDOFF.md` section 14). TR-008 cite même CAP-CORE-017, qui n'existe pas (la liste s'arrête à 016).
3. **RQR-001/002/003 dupliqués** dans `technical-requirements.md` — définis une première fois section 5 (relations), réutilisés section 7 (recherche/retrieval) pour un sujet différent.
4. **Numérotation de section dupliquée** — deux sections « ## 23. » dans `technical-requirements.md` (Architectural Decision Inputs, puis Final Validation).
5. **Dérive mineure** — liste des domaines incohérente entre documents (PERSONAL/FICTION/LEARNING/RESEARCH vs + PUBLISHING selon les fichiers).

## Plan en phases

### Phase 0 — Nettoyage des identifiants (bloquant)
5 sous-tâches. A-D faites directement par Claude (édition scriptée + vérification par grep, sans passer par qwen — plus rapide et déterministe pour du renommage mécanique). E réservée à qwen (voir `qwen-phase0-prompts.md`) car c'est un vrai travail de jugement sur ~279 items, pas du mécanique — déléguer évite de cramer le budget de raisonnement de la session Claude sur une tâche volumineuse que qwen peut faire en local gratuitement, quitte à ce que Claude vérifie/échantillonne après coup.

- **A. Collision INV-001..009** — FAIT (2026-08-16). `specs/domain/knowledge-invariants.md` garde le namespace `INV-` (001 à 021). Les 9 items de `specs/architecture/principles.md` renommés `AP-001..009` partout où ils étaient cités (`principles.md`, `capabilities.md`, `technical-requirements.md`). Vérifié par grep : plus aucune occurrence de INV-001..009 hors `knowledge-invariants.md`.
- **B. Duplication RQR-001/002/003** — FAIT (2026-08-16). Section Relationship Requirements (section 5) garde `RQR-001..006`. Section Retrieval Requirements (section 7) et le renvoi correspondant dans `capabilities.md` renommés `RTR-001..003`. Vérifié par grep.
- **C. Double section "## 23."** — FAIT (2026-08-16). Renumérotation en cascade : 23 (Architectural Decision Inputs, inchangé) → 24 (Final Validation) → 25 (Summary) → 26 (Contradictions or Gaps Discovered). Séquence 1-26 vérifiée sans trou ni doublon.
- **D. Dérive domaines** — FAIT (2026-08-16). `knowledge-invariants.md` INV-008 (domain isolation) mis à jour pour inclure PUBLISHING. Vérifié : plus aucune occurrence "PERSONAL, FICTION, LEARNING, RESEARCH)" à 4 domaines dans `specs/`.
- **E. Audit exhaustif des renvois CAP-CORE-XXX** dans `technical-requirements.md` (et `capabilities.md` si besoin) — À FAIRE, via qwen (prompt dans `qwen-phase0-prompts.md`). Les ~279 exigences sont vérifiées une par une contre la liste canonique des 16 capacités. Tâche la plus lourde et la plus sujette au jugement (beaucoup de "Source:" sont du texte copié-collé peu discriminant) — qwen doit laisser en l'état et signaler les cas ambigus plutôt que deviner.

**Vérification (Claude)** : pour E, Claude re-stage les fichiers modifiés depuis le poste de Cleo et fait un grep ciblé + échantillonnage (valeurs hors plage 001-016, cohérence d'un sous-ensemble des réaffectations contre la table canonique) — pas de relecture intégrale. Le log compact produit par qwen sert de première passe, le grep/échantillon de Claude sert de contre-vérification indépendante.

**Statut : A/B/C/D faits et vérifiés, E à lancer.**

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

Lancer le prompt qwen "Task E — CAP-CORE audit" (`qwen-phase0-prompts.md`). Une fois fait, dire à Claude que c'est terminé pour vérification (spot-check ciblé, pas de relecture intégrale), puis Cleo relit le `git diff` et commit tout Phase 0 (A-E) en une fois. Ensuite : Phase 1 (les 6 ADR).

---

Note honnête sur la mémoire : ce fichier n'est fiable que si on le tient vraiment à jour. Aucun modèle — Claude y compris — ne « se souvient » de ce projet d'une conversation à l'autre. La mémoire, c'est ce fichier et le dépôt git, pas une session de chat.
