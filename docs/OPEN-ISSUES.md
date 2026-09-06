# Pekopeko — Incohérences, bugs, améliorations à débattre

Registre vivant (contrairement à `docs/QUESTIONS.md`, qui est un instantané figé du 2026-08-24) des
points repérés au fil du développement — dans le code, dans les specs, ou dans l'écart entre les
deux — qui méritent une discussion avec Cleo avant de devenir une ADR, une task ou un amendement de
spec. Tant qu'une entrée est ici, elle n'est **pas** tranchée : ne pas l'implémenter, ne pas la
citer comme décision.

Une entrée qui se tranche migre vers sa vraie destination (ADR dans `specs/decisions/`, ticket dans
`specs/tasks/`, correction directe dans `specs/`) et est retirée d'ici plutôt que marquée `[fermé]`
— ce fichier ne garde pas d'historique de ce qui a été résolu, `git log` s'en charge.

Chaque entrée : date de découverte, type, constat, pointeurs vers les fichiers concernés.

---

## 2026-09-06 — Pas d'isolation "Context/Universe" à l'intérieur du domaine FICTION

**Type**: gap spec ↔ implémentation, à débattre avant de devenir une task.

**Constat**: Les specs anticipent explicitement le besoin de séparer plusieurs univers fictionnels
distincts *à l'intérieur* du même domaine `FICTION` (deux romans avec un personnage homonyme, par
exemple) :
- `specs/domain/knowledge-model.md:45-46` définit un concept "Context / Universe" séparé de
  `Domain`, avec l'exemple explicite « in the FICTION domain, different novels or shared fictional
  universes would be contexts ».
- `specs/product/use-cases.md` UC-018 (« Fictional Universe Isolation ») décrit précisément ce
  scénario (deux romans, personnages "Alex" homonymes, isolement attendu).
- `specs/architecture/technical-requirements.md:272` (KSR-005 « Domain Contexts ») exige des
  « Context identifiers within domains » comme besoin de stockage.

Rien de tout cela n'est implémenté : aucun champ `context`/`universe`/`project` dans
`ExtractedAssertion` (`src/app/ingestion/providers/base.py`) ni ailleurs dans le code. Le seul
mécanisme d'organisation existant à l'intérieur d'un domaine est le folder-path builder
(`specs/decisions/ADI-012`, `ADI-014`, `ADI-015`) — un chemin de dossier libre, choisi par
l'utilisatrice ou proposé par le LLM, mais qui n'est qu'un rangement visuel, pas une isolation
garantie : le scan qui alimente les suggestions de chemin (`scan_existing_assertion_folders`,
`scan_proposed_path_segments`, ADI-015) est scopé par domaine entier, pas par projet — les dossiers
d'un roman A influencent donc les suggestions faites pour un roman B. Sans champ univers, rien
n'empêche non plus deux personnages homonymes de deux projets différents d'être fusionnés en une
seule entité canonique lors de la dédup/résolution d'entités.

Le module qui est censé implémenter UC-018 (**TASK-029 — Module Fiction V1**,
`specs/tasks/BACKLOG-CLAUDE.md` §5) est encore en backlog, jamais démarré — cohérent avec le fait
que rien n'existe encore côté code, mais confirme que ce n'est pas un oubli isolé : toute la
section "Modules de domaine" est non commencée.

**À débattre**: faut-il un champ `context`/`universe` de première classe sur les items canoniques
(entity/assertion/event/relationship), séparé du folder-path libre et réellement appliqué comme
frontière (au même titre que `domain` aujourd'hui via AP-005) ? Ou le folder-path suffit-il comme
convention si on le rend plus strict (ex. scope le scan de dossiers existants par sous-arbre
choisi plutôt que par domaine entier) ? Impacte directement le scope de TASK-029 quand il sera
priorisé.

**Contournement actuel**: utiliser un segment de dossier dédié par projet dès l'ingestion (ex.
`FICTION/assertions/roman-a/...`) et rester vigilante sur les homonymes entre projets pendant la
revue — la dédup ne raisonne pas encore par univers.
