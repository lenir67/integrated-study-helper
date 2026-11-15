# Google Sites & GitHub Pages Setup Guide — Integrated Study Helper

This guide covers publishing **Integrated Study Helper** to GitHub Pages (`https://lenir67.github.io/integrated-study-helper/`), embedding it cleanly inside Google Sites, using direct deep links, and keeping Desktop projects, Study Guides (Ch 01–52 + EPA 608 + Printable Student Handouts with embedded Vocabulary), `G:` School Drive, `H:` Personal Drive, and both GitHub Pages sites automatically synchronized.

---

## 1. First-Time GitHub Repository Setup

1. Sign in to GitHub (`lenir67`) and open **https://github.com/new**.
2. Set:
   - **Repository name:** `integrated-study-helper`
   - **Visibility:** **Public** *(required for free GitHub Pages hosting and Google Sites embedding)*
   - Leave *Add a README file*, *.gitignore*, and *license* **unchecked** (they are already in this folder).
3. Click **Create repository**.

---

## 2. Initial Local Sync & Push

Open PowerShell or Command Prompt inside `C:\Users\dkala\OneDrive\Desktop\Projects\Integrated Study Helper`:

```powershell
# 1. Rebuild stale bundles/guides, sync all 52 chapters, EPA 608, handouts, Drives & H: Projects
..\cte-program-tracker-standalone\.venv\Scripts\python.exe sync_and_publish.py --local-only

# 2. Initialize Git on branch 'main' and link your new GitHub repo (first time only)
git init -b main
git remote add origin https://github.com/lenir67/integrated-study-helper.git

# 3. Commit and push to GitHub Pages (Integrated Study Helper + hvac-cycle-lab)
.\publish_update.bat
```

> **Note:** On future updates, double-click `publish_update.bat` (or keep `watch_for_updates.bat` running while you work).

---

## 3. Enable GitHub Pages

1. Open **https://github.com/lenir67/integrated-study-helper/settings/pages**.
2. Under **Build and deployment**:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main`
   - **Folder:** `/ (root)`
3. Click **Save**.
4. Wait ~30–60 seconds, then verify the live site loads at:
   - **https://lenir67.github.io/integrated-study-helper/**

> Because `.nojekyll` is present in the root folder, GitHub Pages serves static HTML/JS/JSON files directly without Jekyll processing.

---

## 4. Embed into Google Sites

1. Open your Google Site in edit mode and navigate to the target page (e.g., *HVAC/R Study Hub*).
2. In the right sidebar, choose **Insert → Embed → By URL**.
3. Paste the live GitHub Pages URL:
   ```text
   https://lenir67.github.io/integrated-study-helper/
   ```
4. Select **Whole Page** (recommended instead of Preview card) and click **Insert**.
5. Drag the embed container edges full-width across the page grid and stretch its height vertically (by default, the embedded hub runs in **Full Tab Default** mode: it attempts to open in a full browser tab and routes any card click or first click directly to a full browser tab, while also offering a banner toggle to stay inline if desired; inline mode includes a locked full-height stage, **⤢ Focus** mode, and a **↗ Full Tab** button).
6. Click **Publish** in Google Sites.

---

## 5. What Gets Embedded & Synced

1. **Chapters 01–52 Interactive Study & HVAC Games:**
   - Every chapter game (`Ch 01` through `Ch 52`) now includes an embedded **Vocabulary Study Guide** tab alongside Flip Cards, Practice Exams, Blitz, Tower Defense, and Podium Arena.
   - `manifest.json` and `js/catalog_manifest.js` index all 52 chapter vocabularies so students can browse and search terms directly from the Hub's Vocabulary Explorer.
2. **Printable Student Handouts (`*student_handout*.html`):**
   - Student handouts (such as `Ch11_Exam_Study_Guide_Student_Handout.html`) automatically receive an embedded, printable 2-column **Key Vocabulary Study Guide** section (`#autoSyncedVocabSection`) and a **Toggle Vocabulary** toolbar button.
   - Original filenames (`Ch11_Exam_Study_Guide_Student_Handout.html`) stay identical across `My Drive`, Desktop `Curiculium data\chXX\`, Personal Drive `HVAC Class Chapters\Ch XX...`, and School Drive `HVAC Class Chapters\Ch XX...`, while the Hub web stage serves `./modules/handouts/chXX_handout.html`.
3. **EPA Section 608 Certification Hub (ESCO v10.1 / v9):**
   - Kept **exam-clean with no chapter vocabulary section**, preserving focused EPA 608 Core / Type I / Type II / Type III / Universal test prep.
4. **Interactive Simulators:**
   - **Electrical Theory Display Board** (`#electrical-board`), **HVAC/R Interactive Electrical Trainer** (`#electrical-simulator`), and **Animated Refrigerant Cycle Lab** (`#refrigerant-cycle`, also deployed standalone at `https://lenir67.github.io/hvac-cycle-lab/`).

---

## 6. Optional Deep Links (Unit / Topic / Lab-Specific Google Sites Pages)

You can embed or link directly to any module or pre-configured simulator state using URL hashes:

| Module / Preset | Direct Embed / Bookmark URL |
|---|---|
| **Master Hub (All 52 Chapters + Labs)** | `https://lenir67.github.io/integrated-study-helper/` |
| **EPA Section 608 Certification Hub (v10 / v9)** | `https://lenir67.github.io/integrated-study-helper/#epa608` |
| **Electrical Theory Display Board** | `https://lenir67.github.io/integrated-study-helper/#electrical-board` |
| **Electrical Board — Motors, C-S-R & Capacitors** | `https://lenir67.github.io/integrated-study-helper/#electrical-board?tab=motors_caps` |
| **HVAC/R Interactive Electrical Trainer** | `https://lenir67.github.io/integrated-study-helper/#electrical-simulator` |
| **Electrical Trainer — Split A/C & Dual Cap Wiring** | `https://lenir67.github.io/integrated-study-helper/#electrical-simulator?module=mod2_split_ac&mode=wiring` |
| **Electrical Trainer — Gas Furnace Sequence** | `https://lenir67.github.io/integrated-study-helper/#electrical-simulator?module=mod3_furnace&mode=sequence` |
| **Refrigerant Cycle Lab** | `https://lenir67.github.io/integrated-study-helper/#refrigerant-cycle` |
| **Cycle Lab — Heat Pump Heating (R-410A)** | `https://lenir67.github.io/integrated-study-helper/#refrigerant-cycle?mode=heating&ref=R410A` |
| **Chapter 11 Study & Game (Example)** | `https://lenir67.github.io/integrated-study-helper/#ch11` |

*Any chapter (`#ch01` through `#ch52`) works the same way.*

---

## 7. Bidirectional Multi-Target Sync Workflow

`sync_and_publish.py` is a **bidirectional, idempotent, non-destructive** orchestrator:

1. **Edit Anywhere — Upstream or Classroom Copy:**
   - Edit source files in `cte-program-tracker-standalone` (`scripts/`, `.xlsx`, `.docx`), `Electrical Display Board`, `Electrical Simulator`, `animated refrigerant cycle`, or `Integrated Study Helper`, **or** edit any synced HTML module / Student Handout directly on:
     - Desktop `Curiculium data\chXX\` or `Curiculium data\608 Study Material\`
     - Integrated Study Helper `modules\`
     - **Personal Google Drive** (`H:\My Drive\HVAC Class Chapters\...` and `H:\My Drive\Projects\...`)
     - **School Google Drive** (`G:\My Drive\HVAC Class Chapters\...`, including `608 Study Materal`)
2. **Freshness Rebuilds (Authoritative Source Priority):**
   - When Python study-game generators, chapter `.xlsx`/`.docx` files, or simulator `js/`/`css/`/`index.html` sources are newer than their rendered HTML bundles, `sync_and_publish.py` automatically runs unit tests / rebuilds only what is stale (pass `--skip-rebuild` to bypass rebuild checks).
   - Otherwise, the newest `st_mtime` across Desktop, Hub, Personal Drive, and School Drive wins and propagates cleanly using SHA-256 + timestamp checks (`0` ping-pong on repeated runs).
3. **Safe Drive & Project Mirroring (`H:\My Drive\Projects\*`):**
   - Automatically syncs `Integrated Study Helper`, `cte-program-tracker-standalone`, `Electrical Display Board`, `Electrical Simulator`, and `animated refrigerant cycle` non-destructively (excluding `.venv`, `node_modules`, `.git`, `__pycache__`, `.db-wal`, etc., and never deleting existing Drive files).
   - School Drive `_Backup_*` folders and student `Block *` / `_Completed*` folders are never touched.
4. **Live Watcher & One-Click Dual Publish:**
   - **`watch_for_updates.bat`** (`sync_and_publish.py --watch`): Polls every 2.5 seconds (1.5s debounce), rebuilds stale bundles, injects/updates handout vocabulary, syncs `G:`, `H:`, `Projects\*`, and auto-pushes both `integrated-study-helper` and `hvac-cycle-lab`.
   - **`publish_update.bat`** (`sync_and_publish.py --push`): One-click full sync, manifest rebuild, `H:` Projects mirror, and dual push to GitHub Pages (`integrated-study-helper` + `hvac-cycle-lab`).
   - Individual project build scripts (`build_chapter_study_games.py`, `build_epa608_study_game.py`, and `build_classroom_bundle.js`) also trigger `sync_and_publish.py --auto-hook` unless `--no-hub-sync` / `SKIP_HUB_SYNC=1` is set.
   - Every module iframe URL appends `?v=<10-char-sha256>` from the manifest so student Chromebooks immediately load fresh code without cache issues.

> **Classroom Security Guardrail:** Only student-facing HTML modules and files matching `*student_handout*.html` are synced into the hub. Presentation decks, instructor guides, teacher editions, and answer keys are strictly blocked from copying.
