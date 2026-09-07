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

## 2026-09-07 — [incohérence] Sources distantes : le média/HTML brut n'est jamais conservé, contre UC-007 et CAP-002

**Constat.** TASK-016 (décision V1 n°4) : « The downloaded media file is **never persisted** — only
the transcript text becomes the Source file's canonical content », au motif que le média est
« trivially re-fetchable from the URL ». TASK-017 fait de même pour le HTML d'une page web. Trois
frictions, non signalées par les tickets (qui signalent en revanche honnêtement la question des CGU
des plateformes) :

- **UC-007** — Postconditions : « Original content files **preserved and accessible** » ; Human
  Review Points : « Source **preservation** verification ». Scénarios d'échec « Corrupted Source »
  et « Source Deletion » : le système est censé préserver la source brute.
- **CAP-002** — Constraints : « Source materials must be **preserved independently** » ; Acceptance
  Criteria : « preserved **separately from extracted knowledge** ».
- **INV-016 / INV-002** — la sortie Whisper (comme le texte extrait d'un HTML) est une
  *interprétation machine*. La stocker comme « contenu du fichier Source » efface exactement la
  distinction contenu-source / interprétation que ces deux invariants imposent de maintenir.

Le « trivially re-fetchable » est par ailleurs faux dès qu'une vidéo est supprimée, passée en privé,
ou qu'une page change — cas normal à l'échelle de plusieurs années.

**À trancher.** (a) Conserver le média/HTML brut (coûteux en disque, conforme au corpus) ;
(b) amender explicitement UC-007/CAP-002 pour poser que, pour une source distante, la « source
préservée » est le transcript + l'URL + le hash, en assumant la perte ; (c) voie médiane — conserver
le HTML brut (léger) mais pas la vidéo (lourde). Ne pas laisser une décision V1 de ticket trancher
un invariant en silence.

**Fichiers.** `specs/tasks/backlog/TASK-016-audio-video-ingestion-transcription.md` (V1 scope
decision 4), `specs/tasks/backlog/TASK-017-additional-source-readers.md` (Scope §5),
`specs/product/use-cases.md` (UC-007, §Failure Scenarios), `specs/product/capabilities.md` (CAP-002),
`specs/domain/knowledge-invariants.md` (INV-002, INV-016).

---

## 2026-09-07 — [bug potentiel] La règle de stabilité d'ADI-013 suppose que mtime = date d'écriture locale

**Constat.** ADI-013 débounce la détection d'un nouveau fichier par « mtime plus vieux qu'un
`poll_interval_seconds` », présentée comme une protection sans dépendance contre un fichier en cours
d'écriture/copie. Or `_inbox/` vit **à l'intérieur du vault**, lui-même synchronisé en continu sur
plusieurs appareils (ADI-001/ADI-004). La plupart des outils de synchro **préservent le mtime
d'origine** du fichier : un fichier déposé sur un autre appareil peut apparaître ici avec un mtime
déjà vieux de plusieurs heures et être jugé « stable » alors que son transfert n'est pas terminé →
ingestion d'un fichier tronqué (INV-019, INV-020).

**À trancher.** Suffisant en pratique (si Cleo dépose surtout ses fichiers localement) → le noter
dans ADI-013 comme limite connue, à la manière d'ADI-014/015. Sinon : critère de stabilité fondé sur
« taille identique sur deux ticks consécutifs » plutôt que sur mtime seul — quelques lignes de plus
dans `scan_once`, toujours sans dépendance.

**Fichiers.** `specs/decisions/ADI-013-automatic-folder-ingestion.md` (§"Settle rule"),
`specs/tasks/backlog/TASK-001f-automatic-folder-ingestion.md` (Scope §3, AC5/AC6).

---

## 2026-09-07 — [incohérence] La file de revue « à l'échelle » (UC-011 / CAP-CORE-013) n'est portée par aucun ticket

**Constat.** `Validation.jsx` récupère chaque domaine avec `limit=500` en dur (TASK-010, choix
confirmé avec Cleo à l'époque) puis groupe/pagine/filtre/trie entièrement en mémoire. TASK-015,
désigné par `BACKLOG-CLAUDE.md` comme l'implémentation de CAP-CORE-015 (UXR-001) et des étapes
d'UC-011 laissées de côté, ajoute bulk/filtres/tri **tous client-side par-dessus ce plafond**. Donc
au-delà de 500 propositions par domaine : file tronquée en silence, « Tout accepter » sur un
sous-ensemble, tri qui n'atteint jamais la note réellement la plus ancienne.

En face, UC-011 pose comme Expected Result « Large-scale proposal handling capability / human
validation remains practical at scale », les Architectural Pressure Points citent « hundreds of
thousands of proposals », et ADI-002 justifie explicitement l'index précoce par *ce* besoin
(« required infrastructure for the **review queue** and search from early in V1 ») — or TASK-018
n'indexe que les items canoniques, `proposals/` explicitement exclu. Personne ne porte ce besoin.

**À trancher.** À l'échelle personnelle réelle de Cleo, 500 par domaine est peut-être simplement
suffisant — auquel cas il faut l'écrire une fois (dans TASK-010 ou ADI-002) et clore le sujet.
Sinon : ticket dédié pour du filtrage/tri/comptage **côté serveur** sur `list_proposals`,
distinctement plus gros que TASK-015 et à ne pas y glisser.

**Fichiers.** `specs/tasks/completed/TASK-010-validation-screen.md` (§"Pagination design"),
`specs/tasks/backlog/TASK-015-review-queue-bulk-operations.md` (dernière V1 scope decision, ajoutée
le 2026-09-07), `specs/decisions/ADI-002-retrieval-system.md`, `specs/product/use-cases.md` (UC-011,
§Architectural Pressure Points §7).

---

## 2026-09-07 — [incohérence] `sources/` et `_inbox/` étendent le layout d'ADI-004 sans l'amender

**Constat.** ADI-004 énumère 5 sous-dossiers par domaine : `entities`, `assertions`, `events`,
`relationships`, `proposals`. Trois autres existent ou vont exister :

- `sources/` (TASK-001) — écart **déjà signalé** comme non résolu dans `docs/ROADMAP.md` (section
  TASK-001, « Écart architectural non résolu »), ouvert depuis le 2026-08-30.
- `_inbox/` et `_inbox/processed/` (ADI-013 / TASK-001f) — **non signalés**. ADI-013 justifie
  l'emplacement au regard d'AP-005 mais ne se déclare jamais amendement d'ADI-004, alors qu'ADI-012
  l'a fait explicitement pour un changement de même nature (ajout d'un niveau de chemin).

Deux de ces trois dossiers contiennent des données **non canoniques** (source brute, fichiers en
attente d'ingestion) à la racine du stockage canonique — ce qui touche aussi la frontière
canonique/dérivé d'ADI-006.

**À trancher.** Un court amendement d'ADI-004 énumérant les 8 dossiers et disant lesquels sont
canoniques, plutôt que de laisser coexister un écart signalé et un écart silencieux. Traiter les
trois d'un coup, une fois.

**Fichiers.** `specs/decisions/ADI-004-obsidian-role.md` (§"Internal organization"),
`specs/decisions/ADI-013-automatic-folder-ingestion.md` (Decision §2), `docs/ROADMAP.md`
(section TASK-001).
