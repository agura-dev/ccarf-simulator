# CLAUDE.md

Practice simulator for the CCAR-F exam (Claude Certified Architect – Foundations). The full specification and product decisions are in [context/project_overview.md](context/project_overview.md) (local only, not in the repo): read it before changing behavior.

## Structure

- `index.html` — the whole app: HTML + CSS + JS + data in a single file. Opens directly in the browser (`file://`), with no server or build.
- `data/questions_heavy.json` — **source of truth** for scenarios, the bank (211 questions) and sample questions (12). Edited by hand. The bank uses the "heavy" style (more context, plausible distractors, options of similar length): the 151 `Practice Exam` + `Practice Test` questions were rewritten this way, and the 60 `Purcell Practice Set` questions already came in that style. Style rules are in `Preliminaries/heavy_style_guide.md` (local); follow them when adding or editing questions.
- `tools/embed_data.py` — validates `data/questions_heavy.json` and embeds it in `index.html`.
- `README.md` — usage instructions for people who clone the repo, with the question credits.
- `.nojekyll` — empty. The site is published on GitHub Pages from `main` / root (https://agura-dev.github.io/ccarf-simulator/), with no build; this file stops Pages from processing it with Jekyll.

Local only (in `.gitignore`, not in the repo):
- `context/project_overview.md` — specification and decisions (source of truth).
- `data/CCAR_F_exam_guide_official.pdf` — official exam guide (domain weights in section 4, objectives in section 6, scoring in section 10).
- `Preliminaries/` — prompts, drafts and the historical files the bank came from: `questions.json` (archived standard bank: a concise version of the same 211 questions, same IDs and answers; the app no longer uses it), `CCAR-F_Practice_Exam_QuestionsDB.md` (bank as a table), `CCARF_ExamGuide_SampleQuestions_DB.md` (guide samples), `Practice_Test_Questions.md` (origin of the `Practice Test` questions), `mock exam1.pdf` (origin of the `Purcell Practice Set` questions), `Scenarios.md`. The app doesn't use them.
- `create_repo.md` — steps to publish on GitHub.

## Constraints (non-negotiable)

- A single HTML file. No frameworks, no CDN, no external resources, no fetching local files. `<meta charset="utf-8">`.
- Light/dark theme through CSS tokens on `:root` (`data-theme` + `prefers-color-scheme`).
- Accessibility: correct/incorrect marked with ✓/✕ as well as color; everything keyboard-operable; visible focus.
- All app content in English: interface, questions, options and explanations. `CLAUDE.md` and `README.md` are in English; code comments and the local docs (`context/`, `Preliminaries/`) stay in Spanish.

## Embedded data

`data/questions_heavy.json` is embedded, minified, in `<script type="application/json" id="ccarf-data">` inside `index.html` (fetch doesn't work over `file://`). After editing the JSON, run from the project root:

```
python3 tools/embed_data.py
```

The script validates (unique IDs per group, well-formed `d`/`ts`/`sc`/`o`/`a`/`w`, enough questions per domain for the Full exam), escapes `</` as `<\/` and replaces the block. If there are errors it leaves `index.html` untouched. If it finds the old `ccarf-data-heavy` block, it removes it. Never edit the block by hand.

Format:

```
{ scenarios: [{ n, t, b }],            // number, title, description
  bank:      [{ id, d, ts, sc, q, o, a, w, src }],
  samples:   [{ id, d, ts, sc, q, o, a, w }] }
```

`d` domain 1–5 · `ts` task statement · `sc` scenario 1–6 · `q` question · `o` 4 options in original order · `a` index of the correct one (0–3) · `w` single explanation ("Why X": why it's correct and, if the source includes it, why the others aren't) · `src` origin (`Practice Exam` | `Practice Test` | `Purcell Practice Set`; the app doesn't use it yet). `bank` and `samples` IDs are numbered separately and may overlap. Text supports only `` `code` `` (rendered by `fmt()`, which escapes HTML).

### Scenario mapping

In the JSON, `sc` is the official number. The original sources used short names, mapped as follows:

| `sc` | Official scenario | Name in the bank (Practice Exam) | Name in Practice Test |
|---|---|---|---|
| 1 | Customer Support Resolution Agent | Customer Support | Customer Support Agent |
| 2 | Code Generation with Claude Code | Code Generation | Code Generation with Claude Code |
| 3 | Multi-Agent Research System | Multi-Agent Research | Multi-agent Research System |
| 4 | Developer Productivity with Claude | Developer Productivity, CI / Developer Productivity | — |
| 5 | Claude Code for Continuous Integration | CI | Claude Code for Continuous Integration |
| 6 | Structured Data Extraction | Structured Data Extraction | — |

The guide's sample questions and the Purcell Practice Set already use the official names and numbers.

## Key logic (index.html)

- **Domain split** (`TEST_MODES[*].dist`, D1..D5): official weights 27/18/20/20/15 with largest-remainder rounding. Short 4/3/3/3/2 · Medium 8/5/6/6/5 · Full 16/11/12/12/9. Knowledge 15 → 4/3/3/3/2 · 10 → 3/2/2/2/1.
- **Scenarios** (`buildItems`): 4 are picked at random; each domain draws from those 4 first and fills from the others if it runs short. With the current bank, the Full exam always ends up using all 6 scenarios; this is expected.
- **Order**: questions grouped by scenario, random within each group; options shuffled per question (`order[pos] = original index`). Answers are stored as the original index.
- **Explanations cite the original letters (A–D)**: that's why the review and the practice question show options in original order. Don't show explanations next to shuffled options without solving this.
- **Score** (Test mode, `scaledScore`):
  - Pass with ≥ 72% correct (`PASS_PCT`).
  - The scaled score (100–1000) is piecewise linear so that 72% maps exactly to 720: 0% → 100, 72% → 720, 100% → 1000.
    - If accuracy < 72%: `100 + (accuracy / 72) × 620`.
    - If accuracy ≥ 72%: `720 + ((accuracy − 72) / 28) × 280`.
    - Rounded to the nearest integer.
  - The displayed % uses `Math.floor` so a fail never shows "72%".
- **Time**: the clock uses `endAt` (a timestamp), not tick counting. Warnings at 5 min and 1 min; automatic submission at 0. The practice question doesn't use exam time.
- **Question bank**: a single bank (`DATA.bank`, the heavy one), the only thing `pickByDomain` reads; the practice question uses `DATA.samples`. There is no selector: the Standard/Heavy one was retired, and its old localStorage key (`ccarf-bank`) is removed on load.
- **Exam style** (`state.examStyle`: `real` | `modern`, saved in localStorage): `showScreen()` adds the `exam-real` class to `<body>` only on `test-sample` and `test-exam`; the `body.exam-real` CSS redefines the tokens (black/white, Arial, no radii) and hides the topbar, footer, hints and navigation panel. Text on those screens comes from the `UI` dictionary via `tx()`: both styles are in English, but `real` imitates the official exam's wording ("End Exam", "Mark for review") and `modern` uses the simulator's ("Finish exam", "⚐ Flag for review"). Static labels use `data-t="<key>"` + `applyStaticLabels()`. When adding text to the exam screen, add it to both styles in `UI`.
- **Review before finishing**: a view inside `screen-test-exam` (`#exam-review-view`, toggled with `#exam-question-view` via `showView()`), so it shares the bar and the clock. Finishing the exam always goes through it (`openReview` → `requestFinish`).
- **Credits**: in the `<footer>` (two lines, with links to the repo, to Matthew Purcell and to Issues) and in the README's Credits section, with per-source counts written by hand. If a source (`src`) is added or removed or the counts change, update both. The footer is hidden in the "real" exam style.
- **`[hidden]` has a global `display: none !important`**: without it, rules like `.btn { display: inline-flex }` override it.
- **Screens**: `.screen` sections with id `screen-<name>`; navigation through `showScreen()` or `data-nav="<name>"` attributes. Keyboard shortcuts are centralized in a single `keydown` handler per screen.

## Status

- Done: home screen, full Test mode (selection + real/modern style, practice question, exam, review before finishing, results by domain, review with filters) and Knowledge mode (setup, question with immediate feedback and a 2-minute clock per question, summary by domain).
- **Knowledge**: always modern style (doesn't use `tx()`; its text is directly in the code); options **not shuffled** (product decision, because of the letters in the explanations); state in `state.k`, its own clock (`startKTimer`/`kTick`) independent of the exam's. Selection with `pickByDomain(kDist(n, domain))`, without the scenario rule, in random order. Domain filter in the setup (`k-domain` radios, generated from `DOMAINS`): `'all'` uses `KNOWLEDGE_SIZES`; a single domain puts all n questions in it (`state.k.domain`) and the summary shows only that row.

## Verification

There are no automated tests. To verify:

- Syntax: extract the main `<script>` and run `node --check`.
- Flow: copy `index.html` to the scratchpad with a test script injected before `</body>` that fires clicks/keyboard events, and run headless Chrome (`--headless=new --dump-dom` or `--screenshot`). For the mobile view, load the page in a 390 px `<iframe>` (headless Chrome won't shrink the window below ~500 px).
- Don't leave test files inside the project.
