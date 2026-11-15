# Google Sites & GitHub Pages Setup Guide — Integrated Study Helper

This guide covers publishing **Integrated Study Helper** to GitHub Pages (`https://lenir67.github.io/integrated-study-helper/`), embedding it cleanly inside Google Sites, using direct deep links, and keeping everything automatically synchronized whenever you edit any chapter game, EPA 608 study hub, simulator, or student handout.

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
# 1. Sync all modules, student handouts, manifests, and H: Drive copy
..\cte-program-tracker-standalone\.venv\Scripts\python.exe sync_and_publish.py --local-only

# 2. Initialize Git on branch 'main' and link your new GitHub repo
git init -b main
git remote add origin https://github.com/lenir67/integrated-study-helper.git

# 3. Commit and push to GitHub
.\publish_update.bat
```

> **Note:** On future updates, you only need to double-click `publish_update.bat` (or let the automatic build hooks handle it).

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
5. Drag the embed container edges full-width across the page grid and stretch its height vertically so students have ample viewport space (the hub automatically enters a locked full-height stage when a module is open to avoid nested scrollbars, and includes a **⤢ Focus** mode plus a **↗ Full Tab** button).
6. Click **Publish** in Google Sites.

---

## 5. Optional Deep Links (Unit / Topic / Lab-Specific Google Sites Pages)

You can embed or link directly to any module or pre-configured simulator state using URL hashes:

| Module / Preset | Direct Embed / Bookmark URL |
|---|---|
| **Master Hub (All 52 Chapters + Labs)** | `https://lenir67.github.io/integrated-study-helper/` |
| **EPA Section 608 Certification Hub (v10 / v9)** | `https://lenir67.github.io/integrated-study-helper/#epa608` |
| **Electrical Theory Display Board** | `https://lenir67.github.io/integrated-study-helper/#electrical-board` |
| **Electrical Board — Motors, C-S-R & Capacitors** | `https://lenir67.github.io/integrated-study-helper/#electrical-board?tab=motors_caps` |
| **Refrigerant Cycle Lab** | `https://lenir67.github.io/integrated-study-helper/#refrigerant-cycle` |
| **Cycle Lab — Heat Pump Heating (R-410A)** | `https://lenir67.github.io/integrated-study-helper/#refrigerant-cycle?mode=heating&ref=R410A` |
| **Chapter 11 Study & Game (Example)** | `https://lenir67.github.io/integrated-study-helper/#ch11` |

*Any chapter (`#ch01` through `#ch52`) works the same way.*

---

## 6. How Automatic Updates Work

Integrated Study Helper is wired to your individual upstream projects so edits flow into the hub automatically:

1. **MRAC 2025 Chapter Builders (`cte-program-tracker-standalone`):**
   - Running `scripts/build_chapter_study_games.py` automatically invokes `sync_and_publish.py --auto-hook --source chapters` after building.
   - Pass `--no-hub-sync` if you temporarily want to skip hub syncing.
2. **EPA Section 608 Builder (`cte-program-tracker-standalone`):**
   - Running `scripts/build_epa608_study_game.py` automatically invokes `sync_and_publish.py --auto-hook --source epa608` after building.
   - Pass `--no-hub-sync` if you temporarily want to skip hub syncing.
3. **Electrical Display Board (`Electrical Display Board`):**
   - Running `node build_classroom_bundle.js` (or `publish_update.bat`) automatically invokes `sync_and_publish.py --auto-hook --source electrical-board` (unless `SKIP_HUB_SYNC=1`).
4. **Animated Refrigerant Cycle Lab (`animated refrigerant cycle`):**
   - Running `node build_classroom_bundle.js` (or `publish_update.bat`) automatically invokes `sync_and_publish.py --auto-hook --source refrigerant-cycle` (unless `SKIP_HUB_SYNC=1`).
5. **Real-Time Watcher (`watch_for_updates.bat`):**
   - Double-click `watch_for_updates.bat` while editing any project or exporting new Student Handouts. It polls upstream files every 2.5 seconds, rebuilds stale simulator bundles, regenerates `manifest.json` + `js/catalog_manifest.js`, mirrors to your `My Drive` `Projects\Integrated Study Helper` folder, and pushes updates if `origin/main` is configured.
6. **Manual One-Click Sync & Publish (`publish_update.bat`):**
   - Checks simulator source freshness (running unit tests + rebuilding if needed), copies only changed files atomically (SHA-256 checked), updates `manifest.json` & `js/catalog_manifest.js`, syncs safely to `My Drive`, commits, and pushes to GitHub Pages.
   - Every module iframe URL appends `?v=<10-char-sha256>` from the manifest so student Chromebooks immediately load fresh code without browser cache issues.

> **Classroom Security Guardrail:** Only student-facing HTML modules and files matching `*student_handout*.html` are synced into the hub. Presentation decks, instructor guides, teacher editions, and answer keys are strictly blocked from copying.
