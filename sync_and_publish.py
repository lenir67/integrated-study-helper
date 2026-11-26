#!/usr/bin/env python3
"""Bidirectional sync, freshness-rebuild, handout vocab injection, manifest, H: drive mirror, and GitHub publisher."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

HUB_DIR = Path(__file__).resolve().parent
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

PROJECTS_DIR = HUB_DIR.parent
PHYSICS_LIB_DIR = PROJECTS_DIR / "Physics Library"
PHYSICS_DIST_DIR = PHYSICS_LIB_DIR / "web" / "dist"
VENDOR_PHYSICS_DIR = HUB_DIR / "js" / "vendor"
TRACKER_DIR = PROJECTS_DIR / "cte-program-tracker-standalone"
CURRICULUM_DIR = TRACKER_DIR / "Curiculium data"
ELEC_DIR = PROJECTS_DIR / "Electrical Display Board"
ELEC_SIM_DIR = PROJECTS_DIR / "Electrical Simulator"
CYCLE_DIR = PROJECTS_DIR / "animated refrigerant cycle"
TRACKER_VENV_PYTHON = TRACKER_DIR / ".venv" / "Scripts" / "python.exe"

MY_DRIVE_ROOT = Path.home() / "My Drive (dkalasz@gmail.com)"
SCHOOL_DRIVE_ROOT = Path("G:/My Drive")
PERSONAL_CHAPTERS_DIR = MY_DRIVE_ROOT / "HVAC Class Chapters"
SCHOOL_CHAPTERS_DIR = SCHOOL_DRIVE_ROOT / "HVAC Class Chapters"
H_DRIVE_PROJECTS_DIR = MY_DRIVE_ROOT / "Projects"
H_DRIVE_HUB_DIR = H_DRIVE_PROJECTS_DIR / "Integrated Study Helper"

SYNCED_PROJECTS: List[Path] = [
    HUB_DIR,
    TRACKER_DIR,
    ELEC_DIR,
    ELEC_SIM_DIR,
    CYCLE_DIR,
]

MANIFEST_JSON_PATH = HUB_DIR / "manifest.json"
MANIFEST_JS_PATH = HUB_DIR / "js" / "catalog_manifest.js"

HUB_TITLE = "Integrated HVAC/R Study Helper"
HUB_SUBTITLE = (
    "MRAC 2025 Chapters 01–52 • EPA Section 608 (v10 / v9) • "
    "Electrical Theory Board • Electrical Wiring Trainer • Refrigerant Cycle Lab"
)
LIVE_HUB_URL = "https://lenir67.github.io/integrated-study-helper/"
LIVE_CYCLE_LAB_URL = "https://lenir67.github.io/hvac-cycle-lab/"

ENGINE_LABELS: Dict[str, str] = {
    "dispatch_bench": "Dispatch & Bench Sim",
    "refrig_manifold": "Manifold & Refrigerant Sim",
    "electrical_meter": "Electrical & Meter Sim",
    "airflow_duct": "Airflow & Duct Sim",
    "heating_sequence": "Heating & Cycle Sequence",
    "commercial_walkin": "Commercial Walk-In Sim",
}

UNIT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "unit1",
        "label": "Unit 1: Trade, Safety & Tools",
        "short_label": "Ch 1–5",
        "chapters": list(range(1, 6)),
    },
    {
        "id": "unit2",
        "label": "Unit 2: Thermodynamics, Gases & Refrigerants",
        "short_label": "Ch 6–12",
        "chapters": list(range(6, 13)),
    },
    {
        "id": "unit3",
        "label": "Unit 3: Electricity, Electronics, Motors & Controls",
        "short_label": "Ch 13–19",
        "chapters": list(range(13, 20)),
    },
    {
        "id": "unit4",
        "label": "Unit 4: Domestic Refrigeration & Residential A/C",
        "short_label": "Ch 20–24",
        "chapters": list(range(20, 25)),
    },
    {
        "id": "unit5",
        "label": "Unit 5: Commercial A/C, Airflow & Load Calc",
        "short_label": "Ch 25–32",
        "chapters": list(range(25, 33)),
    },
    {
        "id": "unit6",
        "label": "Unit 6: Heating Systems, Heat Pumps & Energy",
        "short_label": "Ch 33–40",
        "chapters": list(range(33, 41)),
    },
    {
        "id": "unit7",
        "label": "Unit 7: Commercial Refrigeration Systems & Service",
        "short_label": "Ch 41–52",
        "chapters": list(range(41, 53)),
    },
]

CHAPTER_TO_UNIT: Dict[int, str] = {
    ch: unit["id"] for unit in UNIT_DEFINITIONS for ch in unit["chapters"]
}

SIMULATOR_SPECS: List[Dict[str, Any]] = [
    {
        "id": "electrical-board",
        "dir": ELEC_DIR,
        "vendor_bundle": "hvac-physics.electrical.bundle.js",
        "sources": [
            "index.html",
            "styles.css",
            "js/vendor/hvac-physics.electrical.bundle.js",
            "js/theory_engine.js",
            "js/curriculum_data.js",
            "js/board_renderer.js",
            "js/app.js",
        ],
        "bundle": "HVAC_Electrical_Theory_Board.html",
        "test_script": "tests/verify_theory.js",
        "build_script": "build_classroom_bundle.js",
        "dest_rel": "modules/electrical-board/index.html",
    },
    {
        "id": "electrical-simulator",
        "dir": ELEC_SIM_DIR,
        "vendor_bundle": "hvac-physics.electrical.bundle.js",
        "sources": [
            "index.html",
            "css/styles.css",
            "js/vendor/hvac-physics.electrical.bundle.js",
            "js/modules.js",
            "js/engine.js",
            "js/multimeter.js",
            "js/labs.js",
            "js/app.js",
        ],
        "bundle": "HVAC_Electrical_Trainer_Standalone.html",
        "test_script": "tests/verify_simulator.js",
        "build_script": "build_classroom_bundle.js",
        "dest_rel": "modules/electrical-simulator/index.html",
    },
    {
        "id": "refrigerant-cycle",
        "dir": CYCLE_DIR,
        "vendor_bundle": "hvac-physics.hub.bundle.js",
        "sources": [
            "index.html",
            "styles.css",
            "js/vendor/hvac-physics.hub.bundle.js",
            "js/refrigerants.js",
            "js/physics.js",
            "js/ph_diagram.js",
            "js/renderer.js",
            "js/tour_and_lab.js",
            "js/app.js",
        ],
        "bundle": "HVAC_Refrigerant_Cycle_Lab.html",
        "test_script": "tests/verify_physics.js",
        "build_script": "build_classroom_bundle.js",
        "dest_rel": "modules/refrigerant-cycle/index.html",
    },
]

CYCLE_COMPANION_CHAPTERS = (
    set(range(6, 13))
    | set(range(20, 24))
    | {25, 27, 36, 37}
    | set(range(41, 53))
)

ELECTRICAL_COMPANION_TABS: Dict[int, str] = {
    13: "tab=ohm_watt",
    14: "tab=ac_3phase",
    15: "tab=controls_starters",
    16: "tab=motors_caps",
    17: "tab=controls_starters",
    18: "tab=circuits_hopscotch",
    19: "tab=motors_caps",
    26: "tab=controls_starters",
    35: "tab=ohm_watt",
}

ELECTRICAL_SIM_COMPANION_MODULES: Dict[int, str] = {
    13: "module=mod1_relay&mode=wiring",
    14: "module=mod1_relay&mode=wiring",
    15: "module=mod3_furnace&mode=sequence",
    16: "module=mod2_split_ac&mode=wiring",
    17: "module=mod1_relay&mode=wiring",
    18: "module=mod1_relay&mode=troubleshoot",
    19: "module=mod2_split_ac&mode=troubleshoot",
    22: "module=mod2_split_ac&mode=wiring",
    23: "module=mod2_split_ac&mode=wiring",
    25: "module=mod4_commercial&mode=wiring",
    26: "module=mod4_commercial&mode=wiring",
    33: "module=mod3_furnace&mode=sequence",
    34: "module=mod3_furnace&mode=sequence",
    35: "module=mod4_commercial&mode=wiring",
    49: "module=mod4_commercial&mode=troubleshoot",
}

FORBIDDEN_HANDOUT_RE = re.compile(r"(?i)(presentation|instructor|answer|teacher)")
# Use negative lookahead (?!\d) rather than \b because filenames like Ch11_... have '_' (\w) after digits.
HANDOUT_NAME_RE = re.compile(
    r"(?i)^ch[.\s_-]*0?(\d{1,2})(?!\d).*student[_\s-]*handout.*\.html$"
)
HUB_HANDOUT_NAME_RE = re.compile(r"(?i)^ch(\d{2})_handout\.html$")
DRIVE_CHAPTER_DIR_RE = re.compile(r"(?i)^ch\s*0?(\d{1,2})\b")
DRIVE_EPA_DIR_RE = re.compile(r"(?i)^608\s+study\s+mater")
TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

VOCAB_CSS_START = "/* BEGIN AUTO-SYNCED VOCAB CSS */"
VOCAB_CSS_END = "/* END AUTO-SYNCED VOCAB CSS */"
VOCAB_BTN_START = "<!-- BEGIN AUTO-SYNCED VOCAB BTN -->"
VOCAB_BTN_END = "<!-- END AUTO-SYNCED VOCAB BTN -->"
VOCAB_SEC_START = "<!-- BEGIN AUTO-SYNCED VOCABULARY GUIDE -->"
VOCAB_SEC_END = "<!-- END AUTO-SYNCED VOCABULARY GUIDE -->"

H_DRIVE_EXCLUDE_DIRS = [
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "build",
    "dist",
    ".tmp.drivedownload",
    ".tmp.driveupload",
]
H_DRIVE_EXCLUDE_FILES = [
    "recent_databases.json",
    "*.pyc",
    "*.db-wal",
    "*.db-shm",
    "*.db-journal",
    "*.tmp",
    "*.tmp.*",
]

WATCH_POLL_INTERVAL_SEC = 2.5
WATCH_DEBOUNCE_SEC = 1.5
MTIME_TOLERANCE_SEC = 1.0


def _configure_stdio() -> None:
    """Ensure UTF-8 unbuffered console output on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            except Exception:
                pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_iso_from_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _win_long_path(path: Path, *, threshold: int = 220) -> Path:
    """Apply Windows extended-length prefix (\\\\?\\) when paths approach MAX_PATH."""
    if os.name != "nt":
        return path
    raw = str(path)
    if raw.startswith("\\\\?\\"):
        return path
    abs_raw = os.path.abspath(raw)
    if len(abs_raw) < threshold:
        return path
    if abs_raw.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + abs_raw.lstrip("\\"))
    return Path("\\\\?\\" + abs_raw)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with _win_long_path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_cloud_drive_path(path: Path) -> bool:
    """Return True if path resides inside Google Drive (G: or My Drive)."""
    parts_lower = [p.lower() for p in path.parts]
    drive_lower = path.drive.lower()
    if drive_lower in ("g:", "\\\\?\\g:"):
        return True
    return any("my drive" in part for part in parts_lower)


def _is_retryable_fs_error(exc: OSError) -> bool:
    if isinstance(exc, PermissionError):
        return True
    winerr = getattr(exc, "winerror", None)
    return winerr in (5, 32, 33)


def _atomic_replace_with_retry(
    tmp_path: Path,
    target_path: Path,
    attempts: int = 6,
    delay: float = 0.2,
) -> None:
    """Replace target_path with tmp_path atomically, retrying transient Windows file locks."""
    tmp_fs = _win_long_path(tmp_path)
    target_fs = _win_long_path(target_path)
    for attempt in range(max(1, attempts)):
        try:
            os.replace(tmp_fs, target_fs)
            return
        except OSError as exc:
            if not _is_retryable_fs_error(exc) or attempt >= attempts - 1:
                try:
                    tmp_fs.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            time.sleep(delay * (attempt + 1))


def _atomic_write_text(dest_path: Path, text: str) -> None:
    """Write UTF-8 text atomically via a sibling temporary file."""
    dest_fs = _win_long_path(dest_path)
    dest_fs.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_name(
        f".{dest_path.name}.tmp.{os.getpid()}.{threading.get_ident()}"
    )
    tmp_fs = _win_long_path(tmp_path)
    tmp_fs.write_text(text, encoding="utf-8", newline="\n")
    _atomic_replace_with_retry(tmp_fs, dest_fs)


def _safe_copystat(src: Path, dst: Path) -> None:
    """Best-effort metadata copy (st_mtime) guarded against Drive virtual FS lock quirks."""
    src_fs = _win_long_path(src)
    dst_fs = _win_long_path(dst)
    try:
        shutil.copystat(src_fs, dst_fs)
    except OSError as exc:
        try:
            st = src_fs.stat()
            os.utime(dst_fs, (st.st_atime, st.st_mtime))
        except OSError:
            if not _is_cloud_drive_path(dst):
                print(f"[WARN] Could not copy timestamps to {dst}: {exc}")


def fast_sync_file(src: Path, dst: Path) -> bool:
    """Idempotently sync src -> dst via size+mtime shortcut, SHA-256 check, atomic replace, and copystat.

    Returns True only when dst content was created or updated.
    """
    src_fs = _win_long_path(src)
    dst_fs = _win_long_path(dst)
    if not src_fs.is_file():
        raise FileNotFoundError(f"Source file not found: {src}")

    src_stat = src_fs.stat()
    dst_stat: Optional[os.stat_result] = None
    if dst_fs.exists():
        try:
            dst_stat = dst_fs.stat()
            if (
                dst_stat.st_size == src_stat.st_size
                and abs(dst_stat.st_mtime - src_stat.st_mtime) <= MTIME_TOLERANCE_SEC
            ):
                return False
        except OSError as exc:
            if _is_cloud_drive_path(dst) or _is_retryable_fs_error(exc):
                print(f"[WARN] Cloud Drive stat lock on {dst}; skipping: {exc}")
                return False
            raise

        try:
            if _sha256_file(src_fs) == _sha256_file(dst_fs):
                if dst_stat is None or abs(dst_stat.st_mtime - src_stat.st_mtime) > MTIME_TOLERANCE_SEC:
                    _safe_copystat(src_fs, dst_fs)
                return False
        except OSError as exc:
            if _is_cloud_drive_path(dst) or _is_cloud_drive_path(src) or _is_retryable_fs_error(exc):
                print(f"[WARN] File lock while hashing {src} / {dst}; skipping: {exc}")
                return False
            raise

    tmp_path = dst.with_name(
        f".{dst.name}.tmp.{os.getpid()}.{threading.get_ident()}"
    )
    tmp_fs = _win_long_path(tmp_path)
    try:
        dst_fs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_fs, tmp_fs)
        _safe_copystat(src_fs, tmp_fs)
        _atomic_replace_with_retry(tmp_fs, dst_fs)
        _safe_copystat(src_fs, dst_fs)
        return True
    except OSError as exc:
        try:
            tmp_fs.unlink(missing_ok=True)
        except OSError:
            pass
        if _is_cloud_drive_path(dst) or _is_retryable_fs_error(exc):
            print(f"[WARN] Cloud Drive / lock prevented syncing {dst}: {exc}")
            return False
        raise


def sync_equivalence_group(
    paths: Sequence[Path],
    authoritative: Optional[Path] = None,
) -> Tuple[Optional[Path], int]:
    """Synchronize an equivalence group of equivalent files bidirectionally.

    Selects `authoritative` if provided and existing; otherwise picks the existing
    file with newest `st_mtime` (ties broken by earliest index in `paths`).
    Copies winner to every other path in `paths` via `fast_sync_file`.
    Returns `(winner_path, changed_count)`.
    """
    unique_paths: List[Path] = []
    seen_norm: set[str] = set()
    for p in paths:
        if p is None:
            continue
        key = os.path.normcase(os.path.abspath(str(p)))
        if key not in seen_norm:
            seen_norm.add(key)
            unique_paths.append(p)

    if not unique_paths:
        return None, 0

    winner: Optional[Path] = None
    if authoritative is not None and authoritative.is_file():
        winner = authoritative
    else:
        best_key: Optional[Tuple[float, int]] = None
        for idx, candidate in enumerate(unique_paths):
            try:
                if not candidate.is_file():
                    continue
                mtime = candidate.stat().st_mtime
            except OSError as exc:
                print(f"[WARN] Could not stat equivalence candidate {candidate}: {exc}")
                continue
            cand_key = (mtime, -idx)
            if best_key is None or cand_key > best_key:
                best_key = cand_key
                winner = candidate

    if winner is None:
        return None, 0

    winner_norm = os.path.normcase(os.path.abspath(str(winner)))
    changed_count = 0
    for target in unique_paths:
        target_norm = os.path.normcase(os.path.abspath(str(target)))
        if target_norm == winner_norm:
            continue
        if fast_sync_file(winner, target):
            changed_count += 1

    return winner, changed_count


def atomic_copy_if_changed(src: Path, dst: Path) -> Tuple[bool, str, int, str]:
    """Copy src to dst atomically only when dst is missing or SHA-256 differs, preserving mtime."""
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    changed = fast_sync_file(src, dst)
    hash_target = dst if dst.exists() else src
    file_hash = _sha256_file(hash_target)
    stat = hash_target.stat()
    return changed, file_hash, stat.st_size, _utc_iso_from_timestamp(stat.st_mtime)


def _resolve_drive_chapter_dirs(root: Path) -> Tuple[Dict[int, Path], Optional[Path]]:
    """Resolve Chapter 1..52 directories and EPA 608 directory inside a Drive chapters root.

    Degrades cleanly with a warning log if `root` is unmounted or inaccessible.
    Strictly skips `_Backup_*`, hidden folders, and unrelated subdirectories.
    """
    ch_dirs: Dict[int, Path] = {}
    epa_dir: Optional[Path] = None

    if not root.exists():
        print(f"[WARN] Drive chapters directory not available (skipping): {root}")
        return ch_dirs, epa_dir

    try:
        with os.scandir(root) as it:
            entries = sorted(
                (e for e in it if e.is_dir(follow_symlinks=False)),
                key=lambda e: e.name.lower(),
            )
    except OSError as exc:
        print(f"[WARN] Could not list Drive chapters directory {root}: {exc}")
        return ch_dirs, epa_dir

    for entry in entries:
        name = entry.name
        if name.startswith(("_", ".")):
            continue
        ch_match = DRIVE_CHAPTER_DIR_RE.match(name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            if 1 <= ch_num <= 52 and ch_num not in ch_dirs:
                ch_dirs[ch_num] = Path(entry.path)
            continue
        if epa_dir is None and DRIVE_EPA_DIR_RE.match(name):
            epa_dir = Path(entry.path)

    return ch_dirs, epa_dir


def _extract_js_json_var(html_text: str, var_name: str) -> Any:
    """Decode JSON assigned to `window.<var_name> = ...` using JSONDecoder.raw_decode."""
    decoder = json.JSONDecoder()
    pattern = re.compile(rf"\bwindow\.{re.escape(var_name)}\s*=\s*")
    for match in pattern.finditer(html_text):
        try:
            obj, _ = decoder.raw_decode(html_text, idx=match.end())
            return obj
        except json.JSONDecodeError:
            continue
    return None


def _first_card_list(data: Dict[str, Any]) -> List[Any]:
    """Select study/flashcard list following study_game_pkg priority."""
    for key in ("flip_cards", "flashcards", "cards", "study_items"):
        val = data.get(key)
        if isinstance(val, list):
            return val
    return []


def _any_source_newer(sources: Sequence[Path], bundle: Path, tolerance: float = 0.0) -> bool:
    if not bundle.exists():
        return True
    bundle_mtime = bundle.stat().st_mtime
    return any(
        src.exists() and (src.stat().st_mtime - bundle_mtime) > tolerance
        for src in sources
    )


def _list_chapter_doc_inputs(ch_dir: Path) -> List[Path]:
    """Return .xlsx and .docx curriculum inputs inside a chapter directory (ignoring Office lockfiles)."""
    if not ch_dir.is_dir():
        return []
    docs: List[Path] = []
    try:
        for item in sorted(ch_dir.iterdir()):
            if not item.is_file():
                continue
            if item.name.startswith("~$"):
                continue
            if item.suffix.lower() in (".xlsx", ".docx"):
                docs.append(item)
    except OSError:
        pass
    return docs


def ensure_study_guides_fresh(
    source_tag: Optional[str] = None,
    skip_rebuild: bool = False,
) -> Dict[str, Any]:
    """Rebuild stale Chapters 1–52 or EPA 608 study games if Python/data inputs are >1s newer."""
    result: Dict[str, Any] = {
        "chapters_rebuilt": [],
        "epa_rebuilt": False,
    }
    if skip_rebuild or not TRACKER_DIR.exists():
        return result

    tracker_py = str(TRACKER_VENV_PYTHON) if TRACKER_VENV_PYTHON.is_file() else sys.executable
    child_env = os.environ.copy()
    child_env["SKIP_HUB_SYNC"] = "1"

    chapter_script = TRACKER_DIR / "scripts" / "build_chapter_study_games.py"
    study_pkg_dir = TRACKER_DIR / "scripts" / "study_game_pkg"
    study_pkg_py = sorted(study_pkg_dir.glob("*.py")) if study_pkg_dir.is_dir() else []

    # 1. MRAC Chapters 01–52 freshness check (skip when caller itself is `chapters`)
    if source_tag != "chapters" and chapter_script.is_file():
        code_inputs = [chapter_script, *study_pkg_py]
        max_code_mtime = max(
            (p.stat().st_mtime for p in code_inputs if p.exists()),
            default=0.0,
        )

        any_code_stale = False
        stale_data_chapters: List[int] = []
        for ch_num in range(1, 53):
            ch_dir = CURRICULUM_DIR / f"ch{ch_num:02d}"
            html_path = ch_dir / f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html"
            if not html_path.exists():
                any_code_stale = True
                break
            html_mtime = html_path.stat().st_mtime
            if (max_code_mtime - html_mtime) > MTIME_TOLERANCE_SEC:
                any_code_stale = True
                break
            doc_inputs = _list_chapter_doc_inputs(ch_dir)
            if any((doc.stat().st_mtime - html_mtime) > MTIME_TOLERANCE_SEC for doc in doc_inputs):
                stale_data_chapters.append(ch_num)

        if any_code_stale:
            print("[BUILD] Chapter generator/package updated; rebuilding Chapters 01–52...")
            subprocess.run(
                [
                    tracker_py,
                    str(chapter_script),
                    "--local-only",
                    "--no-hub-sync",
                    "--workers",
                    "4",
                ],
                cwd=str(TRACKER_DIR),
                env=child_env,
                check=True,
            )
            result["chapters_rebuilt"] = list(range(1, 53))
        elif stale_data_chapters:
            ch_spec = ",".join(str(c) for c in stale_data_chapters)
            print(f"[BUILD] Rebuilding stale chapter study game(s): {ch_spec}...")
            subprocess.run(
                [
                    tracker_py,
                    str(chapter_script),
                    "--local-only",
                    "--no-hub-sync",
                    "--workers",
                    "4",
                    "--chapters",
                    ch_spec,
                ],
                cwd=str(TRACKER_DIR),
                env=child_env,
                check=True,
            )
            result["chapters_rebuilt"] = stale_data_chapters

    # 2. EPA 608 freshness check (skip when caller itself is `epa608`)
    epa_script = TRACKER_DIR / "scripts" / "build_epa608_study_game.py"
    if source_tag != "epa608" and epa_script.is_file():
        epa_pkg_dir = TRACKER_DIR / "scripts" / "epa608_game_pkg"
        epa_pkg_files = (
            [*sorted(epa_pkg_dir.glob("*.py")), *sorted(epa_pkg_dir.glob("*.json"))]
            if epa_pkg_dir.is_dir()
            else []
        )
        epa_dir = CURRICULUM_DIR / "608 Study Material"
        epa_html = epa_dir / "EPA 608 - Interactive Study & HVAC Game.html"
        epa_sources = [
            epa_script,
            *study_pkg_py,
            *epa_pkg_files,
            *_list_chapter_doc_inputs(epa_dir),
        ]
        if not epa_html.exists() or _any_source_newer(
            epa_sources, epa_html, tolerance=MTIME_TOLERANCE_SEC
        ):
            print("[BUILD] Rebuilding EPA 608 Interactive Study & HVAC Game...")
            subprocess.run(
                [tracker_py, str(epa_script), "--local-only", "--no-hub-sync"],
                cwd=str(TRACKER_DIR),
                env=child_env,
                check=True,
            )
            result["epa_rebuilt"] = True

    return result


def _sync_physics_vendor() -> int:
    """Sync prebuilt HVACPhysicsLib IIFE bundles into Hub js/vendor/ and simulator js/vendor/."""
    if not PHYSICS_DIST_DIR.is_dir():
        return 0
    changed = 0
    for bundle_name in ("hvac-physics.hub.bundle.js", "hvac-physics.electrical.bundle.js"):
        src = PHYSICS_DIST_DIR / bundle_name
        if src.is_file() and fast_sync_file(src, VENDOR_PHYSICS_DIR / bundle_name):
            changed += 1
    for spec in SIMULATOR_SPECS:
        vb = spec.get("vendor_bundle")
        sim_dir: Path = spec["dir"]
        if not vb or not sim_dir.is_dir():
            continue
        src = PHYSICS_DIST_DIR / vb
        if src.is_file() and fast_sync_file(src, sim_dir / "js" / "vendor" / vb):
            changed += 1
    return changed


def _sync_simulator_bundles(
    source_tag: Optional[str],
    force_rebuild: bool,
    skip_rebuild: bool = False,
) -> Tuple[List[str], int]:
    """Verify/rebuild simulator bundles if source files are newer, then bidirectionally sync bundles."""
    rebuilt: List[str] = []
    changed_count = _sync_physics_vendor()
    node_bin = shutil.which("node") or "node"
    child_env = os.environ.copy()
    child_env["SKIP_HUB_SYNC"] = "1"
    h_drive_ok = MY_DRIVE_ROOT.exists()

    for spec in SIMULATOR_SPECS:
        sim_dir: Path = spec["dir"]
        if not sim_dir.exists():
            print(f"[WARN] Simulator directory missing, skipping: {sim_dir}")
            continue

        bundle_path = sim_dir / spec["bundle"]
        source_paths = [sim_dir / rel for rel in spec["sources"]]
        is_caller_source = source_tag == spec["id"]

        if not skip_rebuild:
            needs_rebuild = (
                force_rebuild
                or not bundle_path.exists()
                or (not is_caller_source and _any_source_newer(source_paths, bundle_path))
            )
            if needs_rebuild:
                print(f"[BUILD] Rebuilding {spec['id']} ({sim_dir.name})...")
                subprocess.run(
                    [node_bin, spec["test_script"]],
                    cwd=str(sim_dir),
                    env=child_env,
                    check=True,
                )
                subprocess.run(
                    [node_bin, spec["build_script"]],
                    cwd=str(sim_dir),
                    env=child_env,
                    check=True,
                )
                rebuilt.append(spec["id"])

        hub_bundle = HUB_DIR / spec["dest_rel"]
        bundle_group: List[Path] = [bundle_path, hub_bundle]
        if h_drive_ok:
            bundle_group.append(H_DRIVE_PROJECTS_DIR / sim_dir.name / spec["bundle"])

        authoritative = (
            bundle_path
            if (spec["id"] in rebuilt or is_caller_source) and bundle_path.is_file()
            else None
        )
        _, sim_changed = sync_equivalence_group(bundle_group, authoritative=authoritative)
        changed_count += sim_changed

    return rebuilt, changed_count


def ensure_simulator_bundles_fresh(
    source_tag: Optional[str],
    force_rebuild: bool,
    skip_rebuild: bool = False,
) -> List[str]:
    """Verify, rebuild if stale/forced, and bidirectionally sync simulator bundles."""
    rebuilt, _ = _sync_simulator_bundles(source_tag, force_rebuild, skip_rebuild=skip_rebuild)
    return rebuilt


def _is_valid_student_handout(path: Path) -> Optional[int]:
    """Return chapter number (1..52) if path is an approved Student Handout HTML, else None."""
    if not path.is_file():
        return None
    name = path.name
    if FORBIDDEN_HANDOUT_RE.search(name):
        return None
    match = HANDOUT_NAME_RE.match(name)
    if not match:
        return None
    ch_num = int(match.group(1))
    if 1 <= ch_num <= 52:
        return ch_num
    return None


def _scan_dir_for_handouts(
    directory: Path,
    consider_fn: Any,
    *,
    allow_hub_name: bool = False,
) -> None:
    """Scan top-level files of a single directory for approved Student Handouts."""
    if not directory.is_dir():
        return
    try:
        for item in sorted(directory.iterdir()):
            if not item.is_file():
                continue
            if FORBIDDEN_HANDOUT_RE.search(item.name):
                continue
            ch_num = _is_valid_student_handout(item)
            if ch_num is None and allow_hub_name:
                hub_match = HUB_HANDOUT_NAME_RE.match(item.name)
                if hub_match:
                    candidate_num = int(hub_match.group(1))
                    if 1 <= candidate_num <= 52:
                        ch_num = candidate_num
            if ch_num is not None:
                consider_fn(ch_num, item)
    except OSError as exc:
        print(f"[WARN] Could not scan handouts in {directory}: {exc}")


def discover_student_handouts(
    personal_ch_dirs: Optional[Dict[int, Path]] = None,
    school_ch_dirs: Optional[Dict[int, Path]] = None,
) -> Dict[int, Path]:
    """Discover newest approved Student Handout HTML per chapter without touching instructor files."""
    candidates: Dict[int, Path] = {}

    def _consider(ch_num: int, path: Path) -> None:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        prev = candidates.get(ch_num)
        if prev is None:
            candidates[ch_num] = path
            return
        try:
            if mtime > prev.stat().st_mtime:
                candidates[ch_num] = path
        except OSError:
            candidates[ch_num] = path

    if MY_DRIVE_ROOT.exists():
        _scan_dir_for_handouts(MY_DRIVE_ROOT, _consider)

    if CURRICULUM_DIR.is_dir():
        for ch_num in range(1, 53):
            _scan_dir_for_handouts(CURRICULUM_DIR / f"ch{ch_num:02d}", _consider)

    if personal_ch_dirs is None and PERSONAL_CHAPTERS_DIR.exists():
        personal_ch_dirs, _ = _resolve_drive_chapter_dirs(PERSONAL_CHAPTERS_DIR)
    for ch_dir in (personal_ch_dirs or {}).values():
        _scan_dir_for_handouts(ch_dir, _consider)

    if school_ch_dirs is None and SCHOOL_CHAPTERS_DIR.exists():
        school_ch_dirs, _ = _resolve_drive_chapter_dirs(SCHOOL_CHAPTERS_DIR)
    for ch_dir in (school_ch_dirs or {}).values():
        _scan_dir_for_handouts(ch_dir, _consider)

    hub_handouts_dir = HUB_DIR / "modules" / "handouts"
    if hub_handouts_dir.is_dir():
        _scan_dir_for_handouts(hub_handouts_dir, _consider, allow_hub_name=False)

    return candidates


def _collect_handout_groups(
    personal_ch_dirs: Dict[int, Path],
    school_ch_dirs: Dict[int, Path],
) -> Dict[int, Dict[str, Any]]:
    """Collect per-chapter Student Handout candidate paths, canonical filename, and equivalence paths."""
    by_ch: Dict[int, Dict[str, Any]] = {}

    def _record(ch_num: int, path: Path, *, is_named_student_handout: bool) -> None:
        if FORBIDDEN_HANDOUT_RE.search(path.name):
            return
        bucket = by_ch.setdefault(
            ch_num,
            {
                "existing": [],
                "orig_filename": "",
            },
        )
        bucket["existing"].append(path)
        if is_named_student_handout and not bucket["orig_filename"]:
            bucket["orig_filename"] = path.name

    # Scan in preferred order so orig_filename resolves predictably
    if CURRICULUM_DIR.is_dir():
        for ch_num in range(1, 53):
            _scan_dir_for_handouts(
                CURRICULUM_DIR / f"ch{ch_num:02d}",
                lambda c, p: _record(c, p, is_named_student_handout=True),
            )

    if MY_DRIVE_ROOT.exists():
        _scan_dir_for_handouts(
            MY_DRIVE_ROOT,
            lambda c, p: _record(c, p, is_named_student_handout=True),
        )

    for ch_dir in personal_ch_dirs.values():
        _scan_dir_for_handouts(
            ch_dir,
            lambda c, p: _record(c, p, is_named_student_handout=True),
        )

    for ch_dir in school_ch_dirs.values():
        _scan_dir_for_handouts(
            ch_dir,
            lambda c, p: _record(c, p, is_named_student_handout=True),
        )

    hub_handouts_dir = HUB_DIR / "modules" / "handouts"
    if hub_handouts_dir.is_dir():
        _scan_dir_for_handouts(
            hub_handouts_dir,
            lambda c, p: _record(c, p, is_named_student_handout=_is_valid_student_handout(p) is not None),
            allow_hub_name=True,
        )

    groups: Dict[int, Dict[str, Any]] = {}
    for ch_num, info in sorted(by_ch.items()):
        orig_filename = info["orig_filename"] or f"Ch{ch_num:02d}_Exam_Study_Guide_Student_Handout.html"
        if FORBIDDEN_HANDOUT_RE.search(orig_filename):
            continue

        group_paths: List[Path] = []
        ch_curr_dir = CURRICULUM_DIR / f"ch{ch_num:02d}"
        if ch_curr_dir.is_dir():
            group_paths.append(ch_curr_dir / orig_filename)
        group_paths.append(HUB_DIR / "modules" / "handouts" / f"ch{ch_num:02d}_handout.html")
        if MY_DRIVE_ROOT.exists():
            group_paths.append(MY_DRIVE_ROOT / orig_filename)
        if ch_num in personal_ch_dirs:
            group_paths.append(personal_ch_dirs[ch_num] / orig_filename)
        if ch_num in school_ch_dirs:
            group_paths.append(school_ch_dirs[ch_num] / orig_filename)

        # Include any existing files discovered under non-standard paths as candidates too
        all_candidates = list(group_paths)
        existing_set = {os.path.normcase(os.path.abspath(str(p))) for p in group_paths}
        for extra in info["existing"]:
            norm = os.path.normcase(os.path.abspath(str(extra)))
            if norm not in existing_set:
                existing_set.add(norm)
                all_candidates.append(extra)

        newest_path: Optional[Path] = None
        newest_key: Optional[Tuple[float, int]] = None
        for idx, cand in enumerate(all_candidates):
            try:
                if not cand.is_file():
                    continue
                mtime = cand.stat().st_mtime
            except OSError:
                continue
            cand_key = (mtime, -idx)
            if newest_key is None or cand_key > newest_key:
                newest_key = cand_key
                newest_path = cand

        if newest_path is not None:
            groups[ch_num] = {
                "orig_filename": orig_filename,
                "newest_path": newest_path,
                "group_paths": group_paths,
            }

    return groups


def _inject_or_update_handout_vocab_html(
    html_text: str,
    ch_num: int,
    ch_title: str,
    vocab_items: List[Dict[str, Any]],
) -> str:
    """Idempotently inject or update CSS, Toggle Vocabulary button, and 2-column Vocabulary Study Guide."""
    if not vocab_items:
        return html_text

    clean_items: List[Dict[str, Any]] = []
    for item in vocab_items:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or "").strip()
        definition = str(item.get("definition") or "").strip()
        if not term:
            continue
        sec_id = str(item.get("section_id") or "").strip()
        try:
            page = int(item.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        clean_items.append(
            {
                "term": term,
                "definition": definition,
                "section_id": sec_id,
                "page": page,
                "is_epa_608": bool(item.get("is_epa_608")),
            }
        )

    if not clean_items:
        return html_text

    css_block = "\n".join(
        [
            f"    {VOCAB_CSS_START}",
            "    .vocab-guide-section {",
            "      margin-top: 14px;",
            "    }",
            "    .vocab-guide-intro {",
            "      margin: 0 0 8px 0;",
            "      font-size: 9pt;",
            "      color: var(--muted, #4b5563);",
            "    }",
            "    .vocab-grid {",
            "      display: grid;",
            "      grid-template-columns: repeat(2, minmax(0, 1fr));",
            "      gap: 7px 12px;",
            "    }",
            "    .vocab-item {",
            "      border: 1px solid var(--border, #d1d5db);",
            "      border-left: 3px solid var(--accent, #0f4c81);",
            "      border-radius: 4px;",
            "      padding: 6px 8px;",
            "      background: var(--bg-soft, #f8fafc);",
            "      break-inside: avoid;",
            "      page-break-inside: avoid;",
            "    }",
            "    .vocab-item-head {",
            "      display: flex;",
            "      flex-wrap: wrap;",
            "      align-items: baseline;",
            "      gap: 5px;",
            "      margin-bottom: 2px;",
            "    }",
            "    .vocab-term {",
            "      font-weight: 700;",
            "      color: #0f172a;",
            "      font-size: 9.5pt;",
            "    }",
            "    .vocab-meta-badge {",
            "      font-size: 7.5pt;",
            "      font-weight: 600;",
            "      color: var(--accent, #0f4c81);",
            "      background: #e0f2fe;",
            "      border-radius: 3px;",
            "      padding: 0 4px;",
            "    }",
            "    .vocab-epa-badge {",
            "      font-size: 7pt;",
            "      font-weight: 700;",
            "      color: #92400e;",
            "      background: #fef3c7;",
            "      border: 1px solid #f59e0b;",
            "      border-radius: 3px;",
            "      padding: 0 4px;",
            "      text-transform: uppercase;",
            "      letter-spacing: 0.03em;",
            "    }",
            "    .vocab-def {",
            "      font-size: 8.6pt;",
            "      line-height: 1.4;",
            "      color: #1f2937;",
            "    }",
            "    @media screen and (max-width: 768px) {",
            "      body {",
            "        padding: 10px;",
            "      }",
            "      .toolbar {",
            "        flex-wrap: wrap;",
            "        padding: 10px 12px;",
            "      }",
            "      .toolbar-actions {",
            "        flex-wrap: wrap;",
            "        width: 100%;",
            "        gap: 8px;",
            "      }",
            "      .toolbar-actions .btn {",
            "        flex: 1 1 auto;",
            "        min-height: 38px;",
            "        text-align: center;",
            "      }",
            "      .page {",
            "        padding: 16px 14px;",
            "      }",
            "      h1 {",
            "        font-size: 13pt;",
            "      }",
            "      .student-meta {",
            "        grid-template-columns: 1fr;",
            "        gap: 8px;",
            "      }",
            "      .blank,",
            "      .blank.short,",
            "      .blank.long {",
            "        min-width: 72px;",
            "        max-width: 100%;",
            "      }",
            "      table.match-table {",
            "        display: block;",
            "        width: 100%;",
            "        overflow-x: auto;",
            "        -webkit-overflow-scrolling: touch;",
            "      }",
            "      table.match-table th:first-child,",
            "      table.match-table td:first-child {",
            "        width: 56px !important;",
            "        min-width: 56px;",
            "      }",
            "      table.match-table th:nth-child(2),",
            "      table.match-table td:nth-child(2) {",
            "        min-width: 180px;",
            "      }",
            "      table.match-table th:nth-child(3),",
            "      table.match-table td:nth-child(3) {",
            "        width: 150px !important;",
            "        min-width: 135px;",
            "      }",
            "      .vocab-grid {",
            "        grid-template-columns: 1fr;",
            "      }",
            "    }",
            "    @media print {",
            "      .vocab-guide-section {",
            "        margin-top: 10px;",
            "      }",
            "      .vocab-grid {",
            "        grid-template-columns: repeat(2, minmax(0, 1fr));",
            "        gap: 5px 10px;",
            "      }",
            "      .vocab-item {",
            "        background: #fff;",
            "        padding: 4px 6px;",
            "        break-inside: avoid;",
            "        page-break-inside: avoid;",
            "      }",
            "      .vocab-term {",
            "        font-size: 8.8pt;",
            "      }",
            "      .vocab-def {",
            "        font-size: 8pt;",
            "        line-height: 1.32;",
            "      }",
            "    }",
            f"    {VOCAB_CSS_END}",
        ]
    )

    btn_block = (
        f'{VOCAB_BTN_START}<button type="button" class="btn secondary" '
        'onclick="var el=document.getElementById(\'autoSyncedVocabSection\');'
        'if(el){el.style.display=el.style.display===\'none\'?\'block\':\'none\';}">'
        f"Toggle Vocabulary</button>{VOCAB_BTN_END}"
    )

    safe_title = html.escape(ch_title.strip() or f"Chapter {ch_num:02d}", quote=True)
    has_epa = any(item["is_epa_608"] for item in clean_items)
    epa_note = (
        ' Terms marked <span class="vocab-epa-badge">EPA 608</span> also reinforce EPA Section 608 certification topics.'
        if has_epa
        else ""
    )

    item_blocks: List[str] = []
    for item in clean_items:
        meta_parts: List[str] = []
        if item["section_id"]:
            sec_text = f"§{item['section_id']}"
            if item["page"] > 0:
                sec_text += f" · p.{item['page']}"
            meta_parts.append(f'<span class="vocab-meta-badge">{html.escape(sec_text, quote=True)}</span>')
        elif item["page"] > 0:
            meta_parts.append(f'<span class="vocab-meta-badge">p.{item["page"]}</span>')
        if item["is_epa_608"]:
            meta_parts.append('<span class="vocab-epa-badge">EPA 608</span>')
        head_meta = "".join(meta_parts)
        item_blocks.append(
            "\n".join(
                [
                    '        <div class="vocab-item">',
                    f'          <div class="vocab-item-head"><span class="vocab-term">{html.escape(item["term"], quote=True)}</span>{head_meta}</div>',
                    f'          <div class="vocab-def">{html.escape(item["definition"], quote=True)}</div>',
                    "        </div>",
                ]
            )
        )

    vocab_section_block = "\n".join(
        [
            VOCAB_SEC_START,
            '    <section class="vocab-guide-section" id="autoSyncedVocabSection">',
            f"      <h2>Key Vocabulary Study Guide: Ch. {ch_num:02d} — {safe_title} ({len(clean_items)} Terms)</h2>",
            f'      <p class="vocab-guide-intro"><strong>Textbook Key Terms ({len(clean_items)}):</strong> Review each term and definition alongside your study guide blanks.{epa_note}</p>',
            '      <div class="vocab-grid">',
            *item_blocks,
            "      </div>",
            "    </section>",
            f"    {VOCAB_SEC_END}",
        ]
    )

    updated = html_text

    # 1. CSS injection/update
    css_marker_re = re.compile(
        rf"[ \t]*{re.escape(VOCAB_CSS_START)}.*?{re.escape(VOCAB_CSS_END)}",
        re.DOTALL,
    )
    if css_marker_re.search(updated):
        updated = css_marker_re.sub(lambda _: css_block, updated, count=1)
    elif re.search(r"</style\s*>", updated, re.IGNORECASE):
        updated = re.sub(
            r"([ \t]*</style\s*>)",
            lambda m: f"{css_block}\n{m.group(1)}",
            updated,
            count=1,
            flags=re.IGNORECASE,
        )
    elif re.search(r"</head\s*>", updated, re.IGNORECASE):
        updated = re.sub(
            r"([ \t]*</head\s*>)",
            lambda m: f"  <style>\n{css_block}\n  </style>\n{m.group(1)}",
            updated,
            count=1,
            flags=re.IGNORECASE,
        )

    # 2. Toolbar Toggle Vocabulary button injection/update
    btn_marker_re = re.compile(
        rf"{re.escape(VOCAB_BTN_START)}.*?{re.escape(VOCAB_BTN_END)}",
        re.DOTALL,
    )
    if btn_marker_re.search(updated):
        updated = btn_marker_re.sub(lambda _: btn_block, updated, count=1)
    else:
        print_btn_re = re.compile(
            r'([ \t]*)(<button\b[^>]*window\.print\s*\([^>]*>)',
            re.IGNORECASE,
        )
        toolbar_actions_re = re.compile(
            r'(<div\b[^>]*class=["\'][^"\']*\btoolbar-actions\b[^"\']*["\'][^>]*>)(.*?)(</div>)',
            re.IGNORECASE | re.DOTALL,
        )
        m_tb = toolbar_actions_re.search(updated)
        if m_tb:
            tb_inner = m_tb.group(2)
            if print_btn_re.search(tb_inner):
                new_tb_inner = print_btn_re.sub(
                    lambda m: f"{m.group(1)}{btn_block}\n{m.group(1)}{m.group(2)}",
                    tb_inner,
                    count=1,
                )
            else:
                new_tb_inner = tb_inner.rstrip() + f"\n      {btn_block}\n    "
            updated = (
                updated[: m_tb.start(2)]
                + new_tb_inner
                + updated[m_tb.end(2) :]
            )
        elif print_btn_re.search(updated):
            updated = print_btn_re.sub(
                lambda m: f"{m.group(1)}{btn_block}\n{m.group(1)}{m.group(2)}",
                updated,
                count=1,
            )

    # 3. Vocabulary section injection/update
    sec_marker_re = re.compile(
        rf"{re.escape(VOCAB_SEC_START)}.*?{re.escape(VOCAB_SEC_END)}",
        re.DOTALL,
    )
    if sec_marker_re.search(updated):
        updated = sec_marker_re.sub(lambda _: vocab_section_block, updated, count=1)
    else:
        word_bank_re = re.compile(
            r'([ \t]*)(<div\b[^>]*(?:\bid=["\']wordBankBox["\']|\bclass=["\'][^"\']*\bword-bank\b[^"\']*["\'])[^>]*>)',
            re.IGNORECASE,
        )
        if word_bank_re.search(updated):
            updated = word_bank_re.sub(
                lambda m: f"{m.group(1)}{vocab_section_block}\n\n{m.group(1)}{m.group(2)}",
                updated,
                count=1,
            )
        else:
            page_end_re = re.compile(r"([ \t]*</div>\s*</body>)", re.IGNORECASE)
            if page_end_re.search(updated):
                updated = page_end_re.sub(
                    lambda m: f"    {vocab_section_block}\n{m.group(1)}",
                    updated,
                    count=1,
                )
            elif re.search(r"</body\s*>", updated, re.IGNORECASE):
                updated = re.sub(
                    r"([ \t]*</body\s*>)",
                    lambda m: f"  {vocab_section_block}\n{m.group(1)}",
                    updated,
                    count=1,
                    flags=re.IGNORECASE,
                )

    if updated == html_text:
        return html_text
    return updated


def _extract_html_title(html_path: Path, fallback: str) -> str:
    try:
        head = html_path.read_text(encoding="utf-8", errors="replace")[:8192]
        match = TITLE_TAG_RE.search(head)
        if match:
            cleaned = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
            if cleaned:
                return cleaned
    except OSError:
        pass
    return fallback


def _normalize_vocabulary(raw_vocab: Any) -> List[Dict[str, Any]]:
    """Normalize chapter vocabulary items preserving hub manifest fields."""
    if not isinstance(raw_vocab, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_vocab, start=1):
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or "").strip()
        if not term:
            continue
        definition = str(item.get("definition") or "").strip()
        raw_page = item.get("page")
        try:
            page = int(raw_page) if raw_page not in (None, "") else 0
        except (TypeError, ValueError):
            page = 0
        normalized.append(
            {
                "id": str(item.get("id") or f"v{idx}").strip(),
                "term": term,
                "definition": definition,
                "section_id": str(item.get("section_id") or "").strip(),
                "section_title": str(item.get("section_title") or "").strip(),
                "page": page,
                "is_epa_608": bool(item.get("is_epa_608")),
            }
        )
    return normalized


def _build_chapter_keywords(
    title: str,
    sections: List[Dict[str, str]],
    engine_label: str,
    match_pairs: List[Any],
    vocabulary: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Build deduplicated lowercase search keywords from title, sections, engine, terms, and vocabulary."""
    seen: set[str] = set()
    keywords: List[str] = []

    def _add(raw: str) -> None:
        tok = re.sub(r"\s+", " ", (raw or "").strip().lower())
        if tok and tok not in seen:
            seen.add(tok)
            keywords.append(tok)

    _add(title)
    for word in re.findall(r"[a-z0-9/+-]{2,}", title.lower()):
        _add(word)
    _add(engine_label)
    for sec in sections:
        _add(sec.get("title", ""))

    term_count = 0
    for pair in match_pairs:
        if term_count >= 25:
            break
        if not isinstance(pair, dict):
            continue
        raw_term = ""
        for field in ("term", "left", "word", "prompt"):
            val = pair.get(field)
            if isinstance(val, str) and val.strip():
                raw_term = val.strip()
                break
        if raw_term:
            _add(raw_term)
            term_count += 1

    if vocabulary:
        for vocab_item in vocabulary:
            if not isinstance(vocab_item, dict):
                continue
            raw_vocab_term = vocab_item.get("term")
            if isinstance(raw_vocab_term, str) and raw_vocab_term.strip():
                _add(raw_vocab_term)

    return keywords


def _build_chapter_companions(ch_num: int, epa_608_count: int) -> List[Dict[str, str]]:
    """Build contextual interactive simulator and EPA 608 companion links for a chapter."""
    companions: List[Dict[str, str]] = []

    if ch_num in CYCLE_COMPANION_CHAPTERS:
        if ch_num in (36, 37):
            query = "mode=heating&ref=R410A&valve=txv"
        elif ch_num == 10:
            query = "mode=cooling&ref=R454B&valve=txv"
        elif ch_num in (20, 21):
            query = "mode=cooling&ref=R134A&valve=fxo"
        elif 41 <= ch_num <= 52:
            query = "mode=cooling&ref=R404A&valve=txv"
        else:
            query = "mode=cooling&ref=R410A&valve=txv"
        companions.append(
            {
                "target_id": "refrigerant-cycle",
                "label": "❄️ Cycle Lab",
                "query": query,
            }
        )

    if ch_num in ELECTRICAL_COMPANION_TABS:
        companions.append(
            {
                "target_id": "electrical-board",
                "label": "⚡ Electrical Board",
                "query": ELECTRICAL_COMPANION_TABS[ch_num],
            }
        )

    if ch_num in ELECTRICAL_SIM_COMPANION_MODULES:
        companions.append(
            {
                "target_id": "electrical-simulator",
                "label": "🔌 Wiring Trainer",
                "query": ELECTRICAL_SIM_COMPANION_MODULES[ch_num],
            }
        )

    if epa_608_count > 0:
        companions.append(
            {
                "target_id": "epa608",
                "label": "🛡️ EPA 608 Prep",
                "query": "",
            }
        )

    return companions


def _extract_epa608_metadata(epa_dest: Path) -> Tuple[List[str], Dict[str, int]]:
    """Extract edition storage keys and card totals from EPA 608 HTML."""
    html_text = epa_dest.read_text(encoding="utf-8", errors="replace")
    editions = _extract_js_json_var(html_text, "STUDY_EDITIONS")
    storage_keys: List[str] = []
    card_totals: Dict[str, int] = {}

    if isinstance(editions, dict) and editions:
        ordered_keys = [k for k in ("v10", "v9") if k in editions]
        for extra_k in editions.keys():
            if extra_k not in ordered_keys:
                ordered_keys.append(extra_k)
        for ed_key in ordered_keys:
            ed_data = editions.get(ed_key)
            if not isinstance(ed_data, dict):
                continue
            s_key = str(ed_data.get("storage_key") or f"cte_epa608_esco_{ed_key}")
            count = len(_first_card_list(ed_data))
            if s_key not in storage_keys:
                storage_keys.append(s_key)
            card_totals[s_key] = count
        return storage_keys, card_totals

    single = _extract_js_json_var(html_text, "CHAPTER_DATA")
    if isinstance(single, dict):
        s_key = str(single.get("storage_key") or "cte_epa608_esco_v10")
        storage_keys.append(s_key)
        card_totals[s_key] = len(_first_card_list(single))
    return storage_keys, card_totals


def _is_h_drive_excluded_file(fname: str) -> bool:
    if fname.startswith(".") and ".tmp." in fname:
        return True
    lower = fname.lower()
    return any(fnmatch.fnmatch(lower, pat.lower()) for pat in H_DRIVE_EXCLUDE_FILES)


def _sync_project_to_h_drive(src_dir: Path, dst_dir: Path) -> int:
    """Non-destructively sync a Desktop project folder to H: drive Projects without deleting destination files."""
    if not src_dir.is_dir():
        return 0
    exclude_dirs = set(H_DRIVE_EXCLUDE_DIRS)
    changed = 0
    _win_long_path(dst_dir).mkdir(parents=True, exist_ok=True)

    stack: List[Path] = [src_dir]
    while stack:
        cur_dir = stack.pop()
        rel_dir = cur_dir.relative_to(src_dir)
        target_dir = dst_dir if str(rel_dir) == "." else dst_dir / rel_dir
        try:
            with os.scandir(_win_long_path(cur_dir)) as it:
                entries = list(it)
        except OSError as exc:
            print(f"[WARN] Could not scan project dir {cur_dir}: {exc}")
            continue

        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in exclude_dirs:
                    stack.append(cur_dir / entry.name)
            elif entry.is_file(follow_symlinks=False):
                if _is_h_drive_excluded_file(entry.name):
                    continue
                if fast_sync_file(cur_dir / entry.name, target_dir / entry.name):
                    changed += 1

    return changed


def _sync_h_drive() -> int:
    """Mirror all Desktop Projects safely to H: drive Projects folder without deleting files."""
    if not MY_DRIVE_ROOT.exists():
        print(f"[INFO] My Drive root not present ({MY_DRIVE_ROOT}); skipping H: drive sync.")
        return 0

    H_DRIVE_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    total_changed = 0
    project_counts: List[str] = []

    for proj_dir in SYNCED_PROJECTS:
        if not proj_dir.is_dir():
            continue
        dst_dir = H_DRIVE_PROJECTS_DIR / proj_dir.name
        proj_changed = _sync_project_to_h_drive(proj_dir, dst_dir)
        total_changed += proj_changed
        project_counts.append(f"{proj_dir.name}={proj_changed}")

    print(
        f"[OK] H: drive Projects synced -> {H_DRIVE_PROJECTS_DIR} "
        f"({total_changed} file(s) updated; {', '.join(project_counts)})"
    )
    return total_changed


def _strip_generated_ts(data: Dict[str, Any]) -> Dict[str, Any]:
    copied = dict(data)
    copied.pop("generated_at_utc", None)
    return copied


def _serialize_catalog_js(manifest: Dict[str, Any]) -> str:
    payload = json.dumps(manifest, indent=2, ensure_ascii=False)
    # Escape Unicode line/paragraph separators so JS parser stays valid across all engines.
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f"window.INTEGRATED_STUDY_MANIFEST = {payload};\n"


def sync_hub(
    *,
    source_tag: Optional[str] = None,
    force_rebuild: bool = False,
    no_h_drive: bool = False,
    skip_rebuild: bool = False,
) -> Dict[str, Any]:
    """Run freshness rebuilds, bidirectional Drive/Hub/Desktop sync, handout vocab injection, manifest & H: mirror."""
    freshness = ensure_study_guides_fresh(source_tag=source_tag, skip_rebuild=skip_rebuild)
    chapters_rebuilt_set = set(freshness.get("chapters_rebuilt") or [])
    epa_rebuilt = bool(freshness.get("epa_rebuilt"))

    rebuilt_sims, sim_changed = _sync_simulator_bundles(
        source_tag, force_rebuild, skip_rebuild=skip_rebuild
    )
    if rebuilt_sims:
        print(f"[OK] Rebuilt simulator bundle(s): {', '.join(rebuilt_sims)}")

    personal_ch_dirs, personal_epa_dir = _resolve_drive_chapter_dirs(PERSONAL_CHAPTERS_DIR)
    school_ch_dirs, school_epa_dir = _resolve_drive_chapter_dirs(SCHOOL_CHAPTERS_DIR)

    changed_files = sim_changed

    # 1. Sync Featured Labs (EPA 608 bidirectional + Electrical Board + Electrical Simulator + Cycle Lab metadata)
    epa_filename = "EPA 608 - Interactive Study & HVAC Game.html"
    epa_desktop = CURRICULUM_DIR / "608 Study Material" / epa_filename
    epa_dst = HUB_DIR / "modules" / "epa608" / "index.html"
    epa_group: List[Path] = [epa_desktop, epa_dst]
    if personal_epa_dir is not None:
        epa_group.append(personal_epa_dir / epa_filename)
    if school_epa_dir is not None:
        epa_group.append(school_epa_dir / epa_filename)

    _, epa_changed_cnt = sync_equivalence_group(
        epa_group,
        authoritative=epa_desktop if epa_rebuilt and epa_desktop.is_file() else None,
    )
    changed_files += epa_changed_cnt
    epa_sha = _sha256_file(epa_dst)
    epa_stat = epa_dst.stat()
    epa_size = epa_stat.st_size
    epa_updated = _utc_iso_from_timestamp(epa_stat.st_mtime)
    epa_storage_keys, epa_card_totals = _extract_epa608_metadata(epa_dst)
    total_epa_cards = sum(epa_card_totals.values())

    elec_dst = HUB_DIR / "modules" / "electrical-board" / "index.html"
    elec_sha = _sha256_file(elec_dst)
    elec_stat = elec_dst.stat()
    elec_size = elec_stat.st_size
    elec_updated = _utc_iso_from_timestamp(elec_stat.st_mtime)

    elec_sim_dst = HUB_DIR / "modules" / "electrical-simulator" / "index.html"
    elec_sim_sha = _sha256_file(elec_sim_dst)
    elec_sim_stat = elec_sim_dst.stat()
    elec_sim_size = elec_sim_stat.st_size
    elec_sim_updated = _utc_iso_from_timestamp(elec_sim_stat.st_mtime)

    cycle_dst = HUB_DIR / "modules" / "refrigerant-cycle" / "index.html"
    cycle_sha = _sha256_file(cycle_dst)
    cycle_stat = cycle_dst.stat()
    cycle_size = cycle_stat.st_size
    cycle_updated = _utc_iso_from_timestamp(cycle_stat.st_mtime)

    featured_labs: List[Dict[str, Any]] = [
        {
            "id": "epa608",
            "kind": "certification",
            "badge": "Certification Prep",
            "icon": "🛡️",
            "accent": "amber",
            "title": "EPA Section 608 Certification Hub",
            "subtitle": "Switchable ESCO 10th Edition (v10.1) & 9th Edition (V2) — Core, Type I, II, III & Universal",
            "path": "./modules/epa608/index.html",
            "version": epa_sha[:10],
            "updated_at_utc": epa_updated,
            "size_bytes": epa_size,
            "storage_keys": epa_storage_keys,
            "card_totals": epa_card_totals,
            "highlights": [
                "ESCO v10.1 & v9",
                f"{total_epa_cards} Study Cards",
                "Core + Type I/II/III",
                "Blooket & Podium Arena",
            ],
            "keywords": [
                "epa",
                "608",
                "epa 608",
                "certification",
                "esco",
                "v10",
                "v9",
                "core",
                "type i",
                "type ii",
                "type iii",
                "universal",
                "recovery",
                "a2l",
                "aim act",
            ],
            "quick_presets": [],
        },
        {
            "id": "electrical-board",
            "kind": "simulator",
            "badge": "Interactive Board",
            "icon": "⚡",
            "accent": "cyan",
            "title": "HVAC/R Electrical Theory Board",
            "subtitle": "Ohm's & Watt's Law, Series/Parallel Hopscotch, Circuit Builder & DMM, 3-Phase, Motors & NEC 430",
            "path": "./modules/electrical-board/index.html",
            "version": elec_sha[:10],
            "updated_at_utc": elec_updated,
            "size_bytes": elec_size,
            "storage_keys": [],
            "highlights": [
                "7 Interactive Boards",
                "Live DMM Probes",
                "10-Slide Walkthrough",
                "MRAC Ch. 13–19",
            ],
            "keywords": [
                "electrical",
                "ohm",
                "watt",
                "series",
                "parallel",
                "hopscotch",
                "circuit builder",
                "dmm",
                "multimeter",
                "3-phase",
                "three phase",
                "motors",
                "capacitors",
                "megger",
                "starters",
                "nec 430",
                "controls",
            ],
            "quick_presets": [
                {"label": "Ohm & Watt's Law", "query": "tab=ohm_watt"},
                {"label": "Hopscotch Circuits", "query": "tab=circuits_hopscotch"},
                {"label": "Circuit Builder & DMM", "query": "tab=circuit_builder"},
                {"label": "AC & 3-Phase", "query": "tab=ac_3phase"},
                {"label": "Motors & Capacitors", "query": "tab=motors_caps"},
                {"label": "Controls & NEC 430", "query": "tab=controls_starters"},
                {"label": "Guided Walkthrough", "query": "tab=ohm_watt&walkthrough=1"},
            ],
        },
        {
            "id": "electrical-simulator",
            "kind": "simulator",
            "badge": "Wiring & DMM Trainer",
            "icon": "🔌",
            "accent": "cyan",
            "title": "HVAC/R Interactive Electrical Trainer",
            "subtitle": "Point-to-Point Component Wiring, Live Ladder Schematics, Fluke DMM Diagnostics & 8 Guided Labs",
            "path": "./modules/electrical-simulator/index.html",
            "version": elec_sim_sha[:10],
            "updated_at_utc": elec_sim_updated,
            "size_bytes": elec_sim_size,
            "storage_keys": [],
            "highlights": [
                "4 Wiring Workbenches",
                "Live Ladder Schematic",
                "Virtual Fluke DMM",
                "8 Guided Student Labs",
            ],
            "keywords": [
                "electrical",
                "simulator",
                "trainer",
                "wiring",
                "workbench",
                "ladder",
                "schematic",
                "relay",
                "90-340",
                "contactor",
                "capacitor",
                "dual run capacitor",
                "compressor",
                "furnace",
                "ignition",
                "hsi",
                "flame sensor",
                "pressure switch",
                "rollout",
                "high limit",
                "sequencer",
                "heat strip",
                "time delay",
                "tdr",
                "ss2",
                "dmm",
                "multimeter",
                "troubleshooting",
                "labs",
            ],
            "quick_presets": [
                {"label": "Mod 1: 24V Relay Logic", "query": "module=mod1_relay&mode=wiring"},
                {"label": "Mod 2: Split A/C & Dual Cap", "query": "module=mod2_split_ac&mode=wiring"},
                {"label": "Mod 3: Gas Furnace Sequence", "query": "module=mod3_furnace&mode=sequence"},
                {"label": "Mod 4: Commercial & Heat Strip", "query": "module=mod4_commercial&mode=wiring"},
                {"label": "Troubleshooting & Faults", "query": "module=mod2_split_ac&mode=troubleshoot"},
                {"label": "8 Student Labs", "query": "module=mod1_relay&mode=labs"},
            ],
        },
        {
            "id": "refrigerant-cycle",
            "kind": "simulator",
            "badge": "Cycle Simulator",
            "icon": "❄️",
            "accent": "emerald",
            "title": "HVAC/R Interactive Refrigerant Cycle Lab",
            "subtitle": "Live Subcooling & Superheat Physics, P-h Enthalpy Diagram, TXV/FXO/EEV Metering & Fault Lab",
            "path": "./modules/refrigerant-cycle/index.html",
            "version": cycle_sha[:10],
            "updated_at_utc": cycle_updated,
            "size_bytes": cycle_size,
            "storage_keys": [],
            "highlights": [
                "6 Refrigerants (A2L/A1)",
                "Live P-h Diagram",
                "Cooling & Heating Modes",
                "Mystery Fault Trainer",
            ],
            "keywords": [
                "refrigerant",
                "cycle",
                "superheat",
                "subcooling",
                "enthalpy",
                "p-h diagram",
                "txv",
                "fxo",
                "eev",
                "r410a",
                "r-410a",
                "r454b",
                "r-454b",
                "r32",
                "r22",
                "r134a",
                "r404a",
                "heat pump",
                "fault",
            ],
            "quick_presets": [
                {"label": "R-410A Cooling (TXV)", "query": "mode=cooling&ref=R410A&valve=txv"},
                {"label": "R-454B A2L Cooling", "query": "mode=cooling&ref=R454B&valve=txv"},
                {"label": "Heat Pump Heating", "query": "mode=heating&ref=R410A&valve=txv"},
                {"label": "Fixed Orifice (FXO)", "query": "mode=cooling&ref=R410A&valve=fxo"},
                {"label": "Commercial R-404A", "query": "mode=cooling&ref=R404A&valve=txv"},
                {"label": "Guided Cycle Tour", "query": "mode=cooling&ref=R410A&valve=txv&tour=1"},
            ],
            "standalone_live_url": LIVE_CYCLE_LAB_URL,
        },
    ]

    # 2. Bidirectional sync for MRAC Chapters 01–52 BEFORE handouts so chapter vocabularies are ready!
    chapters: List[Dict[str, Any]] = []
    chapter_vocab_map: Dict[int, List[Dict[str, Any]]] = {}
    chapter_title_map: Dict[int, str] = {}

    for ch_num in range(1, 53):
        ch_filename = f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html"
        ch_desktop = CURRICULUM_DIR / f"ch{ch_num:02d}" / ch_filename
        ch_dst = HUB_DIR / "modules" / "chapters" / f"ch{ch_num:02d}.html"

        ch_group: List[Path] = [ch_desktop, ch_dst]
        if ch_num in personal_ch_dirs:
            ch_group.append(personal_ch_dirs[ch_num] / ch_filename)
        if ch_num in school_ch_dirs:
            ch_group.append(school_ch_dirs[ch_num] / ch_filename)

        _, ch_changed_cnt = sync_equivalence_group(
            ch_group,
            authoritative=ch_desktop if ch_num in chapters_rebuilt_set and ch_desktop.is_file() else None,
        )
        changed_files += ch_changed_cnt

        ch_sha = _sha256_file(ch_dst)
        ch_stat = ch_dst.stat()
        ch_size = ch_stat.st_size
        ch_updated = _utc_iso_from_timestamp(ch_stat.st_mtime)

        ch_html = ch_dst.read_text(encoding="utf-8", errors="replace")
        data = _extract_js_json_var(ch_html, "CHAPTER_DATA")
        if not isinstance(data, dict):
            raise ValueError(f"Could not decode window.CHAPTER_DATA JSON from {ch_dst}")

        title = str(data.get("chapter_title") or f"Chapter {ch_num:02d}").strip()
        engine_id = str(data.get("engine_id") or "").strip()
        engine_label = ENGINE_LABELS.get(
            engine_id,
            engine_id.replace("_", " ").title() if engine_id else "Interactive Study",
        )
        sections = [
            {"id": str(s.get("id", "")), "title": str(s.get("title", ""))}
            for s in (data.get("sections") or [])
            if isinstance(s, dict)
        ]
        match_pairs = data.get("match_pairs") if isinstance(data.get("match_pairs"), list) else []
        blitz_questions = (
            data.get("blitz_questions") if isinstance(data.get("blitz_questions"), list) else []
        )
        sim_missions = (
            data.get("sim_missions") if isinstance(data.get("sim_missions"), list) else []
        )
        vocabulary = _normalize_vocabulary(data.get("vocabulary"))
        chapter_vocab_map[ch_num] = vocabulary
        chapter_title_map[ch_num] = title
        study_items = _first_card_list(data)
        epa_608_count = int(data.get("epa_608_count") or 0)

        chapters.append(
            {
                "id": f"ch{ch_num:02d}",
                "chapter_num": ch_num,
                "chapter_code": f"Ch {ch_num:02d}",
                "title": title,
                "unit_id": CHAPTER_TO_UNIT[ch_num],
                "engine_id": engine_id,
                "engine_label": engine_label,
                "path": f"./modules/chapters/ch{ch_num:02d}.html",
                "version": ch_sha[:10],
                "updated_at_utc": ch_updated,
                "size_bytes": ch_size,
                "storage_key": str(data.get("storage_key") or f"mrac_study_ch{ch_num:02d}_v1"),
                "exam_question_count": int(data.get("exam_question_count") or 0),
                "study_item_count": len(study_items),
                "match_pair_count": len(match_pairs),
                "blitz_question_count": len(blitz_questions),
                "sim_mission_count": len(sim_missions),
                "epa_608_count": epa_608_count,
                "vocab_count": len(vocabulary),
                "sections": sections,
                "vocabulary": vocabulary,
                "keywords": _build_chapter_keywords(
                    title, sections, engine_label, match_pairs, vocabulary
                ),
                "handout": None,
                "companions": _build_chapter_companions(ch_num, epa_608_count),
            }
        )

    # 3. Discover Student Handouts, inject/update chapter Vocabulary on newest, and sync bidirectionally
    handout_groups = _collect_handout_groups(personal_ch_dirs, school_ch_dirs)
    synced_handouts: Dict[int, Dict[str, str]] = {}
    for ch_num, info in sorted(handout_groups.items()):
        orig_filename: str = info["orig_filename"]
        newest_path: Path = info["newest_path"]
        group_paths: List[Path] = info["group_paths"]

        if FORBIDDEN_HANDOUT_RE.search(orig_filename) or FORBIDDEN_HANDOUT_RE.search(newest_path.name):
            raise RuntimeError(f"Safety abort: refused forbidden filename {newest_path.name}")

        vocab_items = chapter_vocab_map.get(ch_num, [])
        ch_title = chapter_title_map.get(ch_num, f"Chapter {ch_num:02d}")
        authoritative_handout: Optional[Path] = None

        handout_dst = HUB_DIR / "modules" / "handouts" / f"ch{ch_num:02d}_handout.html"
        if vocab_items:
            raw_text = newest_path.read_text(encoding="utf-8", errors="replace")
            injected_text = _inject_or_update_handout_vocab_html(
                raw_text, ch_num, ch_title, vocab_items
            )
            if injected_text != raw_text:
                try:
                    _atomic_write_text(newest_path, injected_text)
                    authoritative_handout = newest_path
                except OSError as exc:
                    print(
                        f"[WARN] Could not update handout in-place ({newest_path}): {exc}; "
                        f"staging authoritative copy at {handout_dst}"
                    )
                    _atomic_write_text(handout_dst, injected_text)
                    authoritative_handout = handout_dst
                changed_files += 1

        _, handout_changed_cnt = sync_equivalence_group(
            group_paths,
            authoritative=authoritative_handout,
        )
        changed_files += handout_changed_cnt

        if not handout_dst.is_file():
            continue
        h_sha = _sha256_file(handout_dst)
        h_title = _extract_html_title(handout_dst, f"Ch {ch_num:02d} Student Study Guide")
        synced_handouts[ch_num] = {
            "title": h_title,
            "path": f"./modules/handouts/ch{ch_num:02d}_handout.html",
            "version": h_sha[:10],
        }

    for ch_entry in chapters:
        ch_entry["handout"] = synced_handouts.get(ch_entry["chapter_num"])

    handout_count = sum(1 for c in chapters if c["handout"] is not None)
    manifest: Dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _utc_now_iso(),
        "hub_title": HUB_TITLE,
        "hub_subtitle": HUB_SUBTITLE,
        "totals": {
            "total_modules": len(featured_labs) + len(chapters),
            "chapter_count": len(chapters),
            "handout_count": handout_count,
            "total_exam_questions": sum(c["exam_question_count"] for c in chapters),
            "total_study_items": sum(c["study_item_count"] for c in chapters),
            "total_epa608_tagged": sum(c["epa_608_count"] for c in chapters),
            "total_vocab_terms": sum(c["vocab_count"] for c in chapters),
        },
        "units": UNIT_DEFINITIONS,
        "featured_labs": featured_labs,
        "chapters": chapters,
    }

    # Determine whether manifest files need to be written
    existing_manifest: Optional[Dict[str, Any]] = None
    if MANIFEST_JSON_PATH.exists():
        try:
            loaded = json.loads(MANIFEST_JSON_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing_manifest = loaded
        except (OSError, json.JSONDecodeError):
            existing_manifest = None

    body_changed = (
        existing_manifest is None
        or _strip_generated_ts(existing_manifest) != _strip_generated_ts(manifest)
    )
    is_upstream_build_hook = source_tag not in (None, "watch")
    need_manifest_write = (
        not MANIFEST_JSON_PATH.exists()
        or not MANIFEST_JS_PATH.exists()
        or changed_files > 0
        or body_changed
        or force_rebuild
        or is_upstream_build_hook
    )

    if need_manifest_write:
        _atomic_write_text(
            MANIFEST_JSON_PATH,
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
        _atomic_write_text(MANIFEST_JS_PATH, _serialize_catalog_js(manifest))
        print(
            f"[OK] Manifest updated ({manifest['totals']['total_modules']} modules, "
            f"{handout_count} handout(s), {changed_files} file(s) synced)."
        )
    else:
        print(
            f"[OK] All {manifest['totals']['total_modules']} modules and manifest up to date "
            f"(0 file(s) changed)."
        )

    h_drive_changed = 0
    if not no_h_drive:
        h_drive_changed = _sync_h_drive()

    return {
        "changed_files": changed_files,
        "h_drive_changed": h_drive_changed,
        "manifest_written": need_manifest_write,
        "rebuilt_sims": rebuilt_sims,
        "chapters_rebuilt": freshness.get("chapters_rebuilt", []),
        "epa_rebuilt": epa_rebuilt,
        "totals": manifest["totals"],
    }


def _run_git(
    args: List[str],
    *,
    repo_dir: Path = HUB_DIR,
    check: bool = True,
    timeout: int = 120,
    extra_env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git") or "git"
    env = os.environ.copy()
    for var in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_QUARANTINE_PATH",
        "GIT_AUTHOR_DATE",
    ):
        env.pop(var, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [git_bin, *args],
        cwd=str(repo_dir),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=check,
    )


def _git_stage_and_commit(
    source_tag: Optional[str],
    custom_msg: Optional[str],
    *,
    repo_dir: Path = HUB_DIR,
) -> bool:
    """Stage all changes in repo_dir and commit if staged diff is non-empty. Returns True if committed."""
    _run_git(["add", "-A"], repo_dir=repo_dir)
    diff_proc = _run_git(["diff", "--cached", "--quiet"], repo_dir=repo_dir, check=False)
    if diff_proc.returncode == 0:
        print(f"[INFO] Git working tree clean ({repo_dir.name}); no new changes to commit.")
        return False
    if diff_proc.returncode != 1:
        raise RuntimeError(f"git diff --cached --quiet failed: {diff_proc.stderr.strip()}")

    label = source_tag or "hub"
    commit_msg = custom_msg or f"Update {repo_dir.name} ({label} @ {_utc_now_iso()})"
    _run_git(["commit", "-m", commit_msg], repo_dir=repo_dir)
    print(f"[OK] Committed changes in {repo_dir.name}: {commit_msg}")
    return True


def _sync_cycle_lab_git(*, auto_hook: bool = False) -> int:
    """Commit and push animated refrigerant cycle lab changes to origin/main if modified or ahead."""
    if not (CYCLE_DIR / ".git").exists():
        print(f"[INFO] Cycle lab .git not found ({CYCLE_DIR}); skipping hvac-cycle-lab push.")
        return 0

    if auto_hook and ((CYCLE_DIR / ".git" / "index.lock").exists() or "GIT_INDEX_FILE" in os.environ):
        print("[INFO] Cycle Lab commit already in progress; skipping nested Cycle Lab git sync.")
        return 0

    try:
        status_proc = _run_git(["status", "--porcelain"], repo_dir=CYCLE_DIR, check=False)
    except Exception as exc:
        print(f"[WARN] Could not inspect Cycle Lab git status: {exc}")
        return 0 if auto_hook else 1

    if status_proc.returncode != 0:
        print(f"[WARN] Cycle Lab git status returned {status_proc.returncode}: {status_proc.stderr.strip()}")
        return 0 if auto_hook else 1

    remote_check = _run_git(["remote", "get-url", "origin"], repo_dir=CYCLE_DIR, check=False)
    if remote_check.returncode != 0:
        print("[INFO] Cycle Lab remote 'origin' not configured; skipping push.")
        return 0

    dirty = bool(status_proc.stdout.strip())
    ahead_count = 0
    if not dirty:
        ahead_proc = _run_git(
            ["rev-list", "--count", "origin/main..HEAD"],
            repo_dir=CYCLE_DIR,
            check=False,
        )
        if ahead_proc.returncode == 0 and ahead_proc.stdout.strip().isdigit():
            ahead_count = int(ahead_proc.stdout.strip())

    if not dirty and ahead_count == 0:
        print("[INFO] Cycle Lab git working tree clean; nothing to push.")
        return 0

    try:
        if dirty:
            _run_git(["add", "-A"], repo_dir=CYCLE_DIR)
            diff_proc = _run_git(["diff", "--cached", "--quiet"], repo_dir=CYCLE_DIR, check=False)
            if diff_proc.returncode == 1:
                _run_git(
                    ["commit", "-m", "chore: sync animated refrigerant cycle lab"],
                    repo_dir=CYCLE_DIR,
                    extra_env={"SKIP_HUB_SYNC": "1"},
                )
                print("[OK] Committed changes in animated refrigerant cycle.")

        push_proc = _run_git(
            ["push", "origin", "main"],
            repo_dir=CYCLE_DIR,
            check=False,
            timeout=90,
        )
        if push_proc.returncode != 0:
            detail = (push_proc.stderr or push_proc.stdout or "").strip()
            print(f"[WARN] Cycle Lab git push failed (continuing): {detail}")
            return 0 if auto_hook else 1
        print(f"[OK] Pushed Cycle Lab update to origin/main -> {LIVE_CYCLE_LAB_URL}")
        return 0
    except Exception as exc:
        print(f"[WARN] Cycle Lab git sync failed: {exc}")
        return 0 if auto_hook else 1


def publish_git_push(source_tag: Optional[str], custom_msg: Optional[str]) -> int:
    """Commit and push changes to origin/main (--push mode) for Hub and Cycle Lab."""
    cycle_rc = _sync_cycle_lab_git(auto_hook=False)
    if cycle_rc != 0:
        print("[WARN] Continuing to Integrated Study Helper push despite Cycle Lab push warning.")

    if not (HUB_DIR / ".git").exists():
        print(
            f"[ERROR] No .git repository found in {HUB_DIR}.\n"
            f"        Initialize git and create "
            f"https://github.com/new (repository name: integrated-study-helper).",
            file=sys.stderr,
        )
        return 1

    try:
        _git_stage_and_commit(source_tag, custom_msg, repo_dir=HUB_DIR)
    except Exception as exc:
        print(f"[ERROR] Git commit failed: {exc}", file=sys.stderr)
        return 1

    remote_check = _run_git(["remote", "get-url", "origin"], repo_dir=HUB_DIR, check=False)
    if remote_check.returncode != 0:
        print(
            "[ERROR] Git remote 'origin' is not configured.\n"
            "        Create a Public GitHub repo at https://github.com/new "
            "(name: integrated-study-helper),\n"
            "        then run: git remote add origin https://github.com/lenir67/integrated-study-helper.git",
            file=sys.stderr,
        )
        return 1

    push_proc = _run_git(["push", "-u", "origin", "main"], repo_dir=HUB_DIR, check=False, timeout=120)
    if push_proc.returncode != 0:
        detail = (push_proc.stderr or push_proc.stdout or "").strip()
        print(
            f"[ERROR] git push -u origin main failed:\n{detail}\n"
            f"        Ensure the repo exists at https://github.com/new "
            f"(Repository name: integrated-study-helper, Public).",
            file=sys.stderr,
        )
        return 1

    print(f"[SUCCESS] Pushed to GitHub Pages (origin/main): {LIVE_HUB_URL}")
    return 0


def auto_hook_git(source_tag: Optional[str], custom_msg: Optional[str]) -> int:
    """Best-effort commit & push for upstream build hooks (never fails offline builds)."""
    _sync_cycle_lab_git(auto_hook=True)

    if not (HUB_DIR / ".git").exists():
        print("[INFO] Hub synced locally (.git not initialized yet; skipping auto-commit/push).")
        return 0

    try:
        committed = _git_stage_and_commit(source_tag, custom_msg, repo_dir=HUB_DIR)
    except Exception as exc:
        print(f"[WARN] Auto-hook git commit skipped: {exc}")
        return 0

    if not committed:
        return 0

    verify_remote = _run_git(
        ["rev-parse", "--verify", "refs/remotes/origin/main"],
        repo_dir=HUB_DIR,
        check=False,
    )
    if verify_remote.returncode != 0:
        print("[INFO] Remote branch refs/remotes/origin/main not found; committed locally only.")
        return 0

    try:
        push_proc = _run_git(["push", "origin", "main"], repo_dir=HUB_DIR, check=False, timeout=60)
        if push_proc.returncode != 0:
            detail = (push_proc.stderr or push_proc.stdout or "").strip()
            print(f"[WARN] Auto-hook git push failed (continuing offline): {detail}")
        else:
            print(f"[OK] Auto-hook pushed update to origin/main -> {LIVE_HUB_URL}")
    except Exception as exc:
        print(f"[WARN] Auto-hook git push failed (continuing offline): {exc}")
    return 0


def _scan_source_mtimes() -> Dict[str, Tuple[float, int, bool]]:
    """Snapshot (mtime, size, is_cloud) across upstream scripts, curriculum, simulators, Drives, and Hub modules.

    Deliberately excludes generated manifest.json / js/catalog_manifest.js and Drive _Backup_* folders
    so `--watch` never self-triggers.
    """
    snapshot: Dict[str, Tuple[float, int, bool]] = {}

    def _record(path: Path) -> None:
        try:
            if not path.is_file():
                return
            st = path.stat()
            snapshot[str(path)] = (st.st_mtime, st.st_size, _is_cloud_drive_path(path))
        except OSError:
            pass

    # 1. Simulators & Physics Library dist bundles (sources, Desktop bundles, Hub copies, H: Drive copies)
    for bundle_name in ("hvac-physics.hub.bundle.js", "hvac-physics.electrical.bundle.js"):
        _record(PHYSICS_DIST_DIR / bundle_name)
        _record(VENDOR_PHYSICS_DIR / bundle_name)
    h_drive_ok = MY_DRIVE_ROOT.exists()
    for spec in SIMULATOR_SPECS:
        sim_dir: Path = spec["dir"]
        if sim_dir.is_dir():
            for rel in [*spec["sources"], spec["bundle"]]:
                _record(sim_dir / rel)
        _record(HUB_DIR / spec["dest_rel"])
        if h_drive_ok:
            _record(H_DRIVE_PROJECTS_DIR / sim_dir.name / spec["bundle"])

    # 2. Tracker Python generator & package files
    scripts_dir = TRACKER_DIR / "scripts"
    if scripts_dir.is_dir():
        _record(scripts_dir / "build_chapter_study_games.py")
        _record(scripts_dir / "build_epa608_study_game.py")
        study_pkg_dir = scripts_dir / "study_game_pkg"
        if study_pkg_dir.is_dir():
            for py_file in study_pkg_dir.glob("*.py"):
                _record(py_file)
        epa_pkg_dir = scripts_dir / "epa608_game_pkg"
        if epa_pkg_dir.is_dir():
            for p in (*epa_pkg_dir.glob("*.py"), *epa_pkg_dir.glob("*.json")):
                _record(p)

    # 3. Curriculum data (Ch 1–52 HTML + .xlsx/.docx + handouts, EPA 608 HTML)
    epa_dir = CURRICULUM_DIR / "608 Study Material"
    if epa_dir.is_dir():
        _record(epa_dir / "EPA 608 - Interactive Study & HVAC Game.html")
        for doc in _list_chapter_doc_inputs(epa_dir):
            _record(doc)

    for ch_num in range(1, 53):
        ch_dir = CURRICULUM_DIR / f"ch{ch_num:02d}"
        if not ch_dir.is_dir():
            continue
        _record(ch_dir / f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html")
        for doc in _list_chapter_doc_inputs(ch_dir):
            _record(doc)
        for item in ch_dir.iterdir():
            if _is_valid_student_handout(item) is not None:
                _record(item)

    # 4. Hub web shell & modules (excluding generated catalog_manifest.js and manifest.json)
    _record(HUB_DIR / "index.html")
    _record(HUB_DIR / "styles.css")
    hub_js_dir = HUB_DIR / "js"
    if hub_js_dir.is_dir():
        for js_file in hub_js_dir.glob("*.js"):
            if js_file.name != "catalog_manifest.js":
                _record(js_file)
    for ch_num in range(1, 53):
        _record(HUB_DIR / "modules" / "chapters" / f"ch{ch_num:02d}.html")
    _record(HUB_DIR / "modules" / "epa608" / "index.html")
    hub_handouts_dir = HUB_DIR / "modules" / "handouts"
    if hub_handouts_dir.is_dir():
        for item in hub_handouts_dir.iterdir():
            if not item.is_file() or FORBIDDEN_HANDOUT_RE.search(item.name):
                continue
            if HUB_HANDOUT_NAME_RE.match(item.name) or _is_valid_student_handout(item) is not None:
                _record(item)

    # 5. MY_DRIVE_ROOT root Student Handouts
    if h_drive_ok:
        try:
            for item in MY_DRIVE_ROOT.iterdir():
                if _is_valid_student_handout(item) is not None:
                    _record(item)
        except OSError:
            pass

    # 6. Personal & School Drive synced HTMLs + handouts (resolved dirs only; ignores _Backup_*)
    for chapters_root in (PERSONAL_CHAPTERS_DIR, SCHOOL_CHAPTERS_DIR):
        if not chapters_root.exists():
            continue
        ch_dirs, drv_epa_dir = _resolve_drive_chapter_dirs(chapters_root)
        if drv_epa_dir is not None:
            _record(drv_epa_dir / "EPA 608 - Interactive Study & HVAC Game.html")
        for ch_num, drv_ch_dir in ch_dirs.items():
            _record(drv_ch_dir / f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html")
            try:
                for item in drv_ch_dir.iterdir():
                    if _is_valid_student_handout(item) is not None:
                        _record(item)
            except OSError:
                pass

    return snapshot


def _snapshots_differ(
    prev: Dict[str, Tuple[float, int, bool]],
    curr: Dict[str, Tuple[float, int, bool]],
) -> bool:
    if set(prev.keys()) != set(curr.keys()):
        return True
    for path_key, (curr_mtime, curr_size, is_cloud) in curr.items():
        prev_mtime, prev_size, _ = prev[path_key]
        if curr_size != prev_size:
            return True
        tol = MTIME_TOLERANCE_SEC if is_cloud else 0.01
        if abs(curr_mtime - prev_mtime) > tol:
            return True
    return False


def run_watch_loop(
    *,
    force_rebuild: bool,
    no_h_drive: bool,
    skip_rebuild: bool,
    custom_msg: Optional[str],
) -> int:
    """Poll upstream sources every 2.5s, debounce 1.5s, and run bidirectional sync + auto-hook on changes."""
    print(
        f"[WATCH] Monitoring MRAC Ch 01–52, EPA 608, Electrical Board, Electrical Simulator, Cycle Lab, Student Handouts, "
        f"Personal Drive & School Drive (poll={WATCH_POLL_INTERVAL_SEC}s, debounce={WATCH_DEBOUNCE_SEC}s)..."
    )
    print("[WATCH] Press Ctrl+C to stop.")
    try:
        sync_hub(
            source_tag="watch",
            force_rebuild=force_rebuild,
            no_h_drive=no_h_drive,
            skip_rebuild=skip_rebuild,
        )
        auto_hook_git("watch", custom_msg)
    except Exception as exc:
        print(f"[WARN] Initial watch sync encountered an error: {exc}")

    last_snapshot = _scan_source_mtimes()
    try:
        while True:
            time.sleep(WATCH_POLL_INTERVAL_SEC)
            current = _scan_source_mtimes()
            if not _snapshots_differ(last_snapshot, current):
                continue

            print("[WATCH] Upstream/Drive change detected; waiting for writes to settle...")
            settled = current
            for _ in range(3):
                time.sleep(WATCH_DEBOUNCE_SEC)
                newer = _scan_source_mtimes()
                if not _snapshots_differ(settled, newer):
                    break
                settled = newer

            try:
                sync_hub(
                    source_tag="watch",
                    force_rebuild=False,
                    no_h_drive=no_h_drive,
                    skip_rebuild=skip_rebuild,
                )
                auto_hook_git("watch", custom_msg)
            except Exception as exc:
                print(f"[WARN] Watch sync failed (will retry on next change): {exc}")
            last_snapshot = _scan_source_mtimes()
    except KeyboardInterrupt:
        print("\n[WATCH] Stopped by user.")
        return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bidirectionally sync Integrated Study Helper, Study Guides, Drives, H: Projects, and GitHub Pages."
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Sync modules, regenerate manifests, and sync Drives/H: Projects without git commit/push.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Sync modules, regenerate manifests, sync Drives/H: Projects, git commit, and push to origin/main.",
    )
    parser.add_argument(
        "--auto-hook",
        action="store_true",
        help="Post-build hook mode: sync, commit if .git exists, and push only if origin/main exists (warns offline).",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously poll upstream & Drive source mtimes every 2.5s (1.5s debounce) and run sync + auto-hook.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuilding Electrical Display Board, Electrical Simulator, and Refrigerant Cycle bundles even if up to date.",
    )
    parser.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Skip freshness rebuild checks for study guides and simulator bundles; perform fast copy/manifest/push only.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional upstream source label (e.g. chapters, epa608, electrical-board, electrical-simulator, refrigerant-cycle).",
    )
    parser.add_argument(
        "--no-h-drive",
        action="store_true",
        help="Skip mirroring Desktop Projects to My Drive Projects folder.",
    )
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        default=None,
        help="Optional git commit message when committing changes.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    _configure_stdio()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    mode_flags = sum(
        bool(flag) for flag in (args.local_only, args.push, args.auto_hook, args.watch)
    )
    if mode_flags > 1:
        parser.error("Use at most one of --local-only, --push, --auto-hook, or --watch.")

    if args.watch:
        return run_watch_loop(
            force_rebuild=args.force_rebuild,
            no_h_drive=args.no_h_drive,
            skip_rebuild=args.skip_rebuild,
            custom_msg=args.message,
        )

    sync_hub(
        source_tag=args.source,
        force_rebuild=args.force_rebuild,
        no_h_drive=args.no_h_drive,
        skip_rebuild=args.skip_rebuild,
    )

    if args.push:
        return publish_git_push(args.source, args.message)
    if args.auto_hook:
        return auto_hook_git(args.source, args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
