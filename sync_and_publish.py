#!/usr/bin/env python3
"""Sync, bundle-check, manifest-generate, H:-drive mirror, and publish Integrated Study Helper."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
PROJECTS_DIR = HUB_DIR.parent
TRACKER_DIR = PROJECTS_DIR / "cte-program-tracker-standalone"
CURRICULUM_DIR = TRACKER_DIR / "Curiculium data"
ELEC_DIR = PROJECTS_DIR / "Electrical Display Board"
CYCLE_DIR = PROJECTS_DIR / "animated refrigerant cycle"
MY_DRIVE_ROOT = Path.home() / "My Drive (dkalasz@gmail.com)"
H_DRIVE_HUB_DIR = MY_DRIVE_ROOT / "Projects" / "Integrated Study Helper"

MANIFEST_JSON_PATH = HUB_DIR / "manifest.json"
MANIFEST_JS_PATH = HUB_DIR / "js" / "catalog_manifest.js"

HUB_TITLE = "Integrated HVAC/R Study Helper"
HUB_SUBTITLE = (
    "MRAC 2025 Chapters 01–52 • EPA Section 608 (v10 / v9) • "
    "Electrical Theory Board • Refrigerant Cycle Lab"
)
LIVE_HUB_URL = "https://lenir67.github.io/integrated-study-helper/"

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
        "sources": [
            "index.html",
            "styles.css",
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
        "id": "refrigerant-cycle",
        "dir": CYCLE_DIR,
        "sources": [
            "index.html",
            "styles.css",
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

FORBIDDEN_HANDOUT_RE = re.compile(r"(?i)(presentation|instructor|answer|teacher)")
# Use negative lookahead (?!\d) rather than \b because filenames like Ch11_... have '_' (\w) after digits.
HANDOUT_NAME_RE = re.compile(
    r"(?i)^ch[.\s_-]*0?(\d{1,2})(?!\d).*student[_\s-]*handout.*\.html$"
)
TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_replace_with_retry(
    tmp_path: Path,
    target_path: Path,
    attempts: int = 6,
    delay: float = 0.2,
) -> None:
    """Replace target_path with tmp_path atomically, retrying transient Windows file locks."""
    for attempt in range(max(1, attempts)):
        try:
            os.replace(tmp_path, target_path)
            return
        except PermissionError:
            if attempt >= attempts - 1:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            time.sleep(delay * (attempt + 1))
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def _atomic_write_text(dest_path: Path, text: str) -> None:
    """Write UTF-8 text atomically via a sibling temporary file."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_name(
        f".{dest_path.name}.tmp.{os.getpid()}.{threading.get_ident()}"
    )
    tmp_path.write_text(text, encoding="utf-8", newline="\n")
    _atomic_replace_with_retry(tmp_path, dest_path)


def atomic_copy_if_changed(src: Path, dst: Path) -> Tuple[bool, str, int, str]:
    """Copy src to dst atomically only when dst is missing or SHA-256 differs."""
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    src_hash = _sha256_file(src)
    dst_hash = _sha256_file(dst) if dst.exists() else ""

    if dst_hash != src_hash:
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = dst.with_name(
            f".{dst.name}.tmp.{os.getpid()}.{threading.get_ident()}"
        )
        shutil.copyfile(src, tmp_path)
        _atomic_replace_with_retry(tmp_path, dst)
        changed = True
    else:
        changed = False

    stat = dst.stat()
    return changed, src_hash, stat.st_size, _utc_iso_from_timestamp(stat.st_mtime)


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


def _any_source_newer(sources: Sequence[Path], bundle: Path) -> bool:
    if not bundle.exists():
        return True
    bundle_mtime = bundle.stat().st_mtime
    return any(src.exists() and src.stat().st_mtime > bundle_mtime for src in sources)


def ensure_simulator_bundles_fresh(
    source_tag: Optional[str],
    force_rebuild: bool,
) -> List[str]:
    """Verify and rebuild Electrical Board / Refrigerant Cycle bundles if stale or forced."""
    rebuilt: List[str] = []
    node_bin = shutil.which("node") or "node"
    child_env = os.environ.copy()
    child_env["SKIP_HUB_SYNC"] = "1"

    for spec in SIMULATOR_SPECS:
        sim_dir: Path = spec["dir"]
        if not sim_dir.exists():
            print(f"[WARN] Simulator directory missing, skipping: {sim_dir}")
            continue

        bundle_path = sim_dir / spec["bundle"]
        source_paths = [sim_dir / rel for rel in spec["sources"]]
        is_caller_source = source_tag == spec["id"]
        needs_rebuild = (
            force_rebuild
            or not bundle_path.exists()
            or (not is_caller_source and _any_source_newer(source_paths, bundle_path))
        )
        if not needs_rebuild:
            continue

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


def discover_student_handouts() -> Dict[int, Path]:
    """Discover newest approved Student Handout HTML per chapter without touching instructor files."""
    candidates: Dict[int, Path] = {}

    def _consider(path: Path) -> None:
        ch_num = _is_valid_student_handout(path)
        if ch_num is None:
            return
        prev = candidates.get(ch_num)
        if prev is None or path.stat().st_mtime > prev.stat().st_mtime:
            candidates[ch_num] = path

    if MY_DRIVE_ROOT.exists():
        try:
            for item in MY_DRIVE_ROOT.iterdir():
                if item.is_file():
                    _consider(item)
        except OSError as exc:
            print(f"[WARN] Could not scan {MY_DRIVE_ROOT}: {exc}")

        hvac_chapters_dir = MY_DRIVE_ROOT / "HVAC Class Chapters"
        if hvac_chapters_dir.exists():
            for root, dirs, files in os.walk(hvac_chapters_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    _consider(Path(root) / fname)

    if CURRICULUM_DIR.exists():
        for root, dirs, files in os.walk(CURRICULUM_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                _consider(Path(root) / fname)

    return candidates


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


def _sync_h_drive() -> None:
    """Mirror Integrated Study Helper safely to H: drive Projects folder without deleting files."""
    if not MY_DRIVE_ROOT.exists():
        print(f"[INFO] My Drive root not present ({MY_DRIVE_ROOT}); skipping H: drive sync.")
        return

    H_DRIVE_HUB_DIR.mkdir(parents=True, exist_ok=True)
    robocopy_bin = shutil.which("robocopy")
    if robocopy_bin:
        cmd = [
            robocopy_bin,
            str(HUB_DIR),
            str(H_DRIVE_HUB_DIR),
            "/E",
            "/R:2",
            "/W:1",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/NC",
            "/NS",
            "/NP",
            "/XD",
            *H_DRIVE_EXCLUDE_DIRS,
            "/XF",
            *H_DRIVE_EXCLUDE_FILES,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode >= 8:
            raise RuntimeError(
                f"robocopy to H: drive failed (exit {proc.returncode}): "
                f"{(proc.stdout or proc.stderr).strip()}"
            )
        print(f"[OK] H: drive synced -> {H_DRIVE_HUB_DIR} (robocopy exit {proc.returncode})")
        return

    # Pure-Python non-destructive fallback if robocopy is unavailable
    exclude_dirs_set = set(H_DRIVE_EXCLUDE_DIRS)
    copied = 0
    for root, dirs, files in os.walk(HUB_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
        rel_root = Path(root).relative_to(HUB_DIR)
        for fname in files:
            if (
                fname == "recent_databases.json"
                or fname.endswith((".pyc", ".db-wal", ".db-shm", ".db-journal", ".tmp"))
                or ".tmp." in fname
            ):
                continue
            src_file = Path(root) / fname
            dst_file = H_DRIVE_HUB_DIR / rel_root / fname
            changed, _, _, _ = atomic_copy_if_changed(src_file, dst_file)
            if changed:
                copied += 1
    print(f"[OK] H: drive synced -> {H_DRIVE_HUB_DIR} ({copied} file(s) updated)")


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
) -> Dict[str, Any]:
    """Run upstream checks, atomic module/handout sync, manifest generation, and H: drive sync."""
    rebuilt_sims = ensure_simulator_bundles_fresh(source_tag, force_rebuild)
    if rebuilt_sims:
        print(f"[OK] Rebuilt simulator bundle(s): {', '.join(rebuilt_sims)}")

    changed_files = 0

    # 1. Sync featured labs
    epa_src = CURRICULUM_DIR / "608 Study Material" / "EPA 608 - Interactive Study & HVAC Game.html"
    epa_dst = HUB_DIR / "modules" / "epa608" / "index.html"
    epa_changed, epa_sha, epa_size, epa_updated = atomic_copy_if_changed(epa_src, epa_dst)
    if epa_changed:
        changed_files += 1
    epa_storage_keys, epa_card_totals = _extract_epa608_metadata(epa_dst)
    total_epa_cards = sum(epa_card_totals.values())

    elec_src = ELEC_DIR / "HVAC_Electrical_Theory_Board.html"
    elec_dst = HUB_DIR / "modules" / "electrical-board" / "index.html"
    elec_changed, elec_sha, elec_size, elec_updated = atomic_copy_if_changed(elec_src, elec_dst)
    if elec_changed:
        changed_files += 1

    cycle_src = CYCLE_DIR / "HVAC_Refrigerant_Cycle_Lab.html"
    cycle_dst = HUB_DIR / "modules" / "refrigerant-cycle" / "index.html"
    cycle_changed, cycle_sha, cycle_size, cycle_updated = atomic_copy_if_changed(cycle_src, cycle_dst)
    if cycle_changed:
        changed_files += 1

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
            "standalone_live_url": "https://lenir67.github.io/hvac-cycle-lab/",
        },
    ]

    # 2. Discover and sync Student Handouts (strictly excluding presentation/instructor/answer/teacher)
    handout_sources = discover_student_handouts()
    synced_handouts: Dict[int, Dict[str, str]] = {}
    for ch_num, handout_src in sorted(handout_sources.items()):
        if FORBIDDEN_HANDOUT_RE.search(handout_src.name):
            raise RuntimeError(f"Safety abort: refused forbidden filename {handout_src.name}")
        handout_dst = HUB_DIR / "modules" / "handouts" / f"ch{ch_num:02d}_handout.html"
        h_changed, h_sha, _, _ = atomic_copy_if_changed(handout_src, handout_dst)
        if h_changed:
            changed_files += 1
        h_title = _extract_html_title(handout_dst, f"Ch {ch_num:02d} Student Study Guide")
        synced_handouts[ch_num] = {
            "title": h_title,
            "path": f"./modules/handouts/ch{ch_num:02d}_handout.html",
            "version": h_sha[:10],
        }

    # 3. Sync MRAC Chapters 01-52 and extract metadata
    chapters: List[Dict[str, Any]] = []
    for ch_num in range(1, 53):
        ch_src = (
            CURRICULUM_DIR
            / f"ch{ch_num:02d}"
            / f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html"
        )
        ch_dst = HUB_DIR / "modules" / "chapters" / f"ch{ch_num:02d}.html"
        ch_changed, ch_sha, ch_size, ch_updated = atomic_copy_if_changed(ch_src, ch_dst)
        if ch_changed:
            changed_files += 1

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
                "handout": synced_handouts.get(ch_num),
                "companions": _build_chapter_companions(ch_num, epa_608_count),
            }
        )

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
    need_manifest_write = (
        not MANIFEST_JSON_PATH.exists()
        or not MANIFEST_JS_PATH.exists()
        or changed_files > 0
        or body_changed
        or force_rebuild
        or bool(source_tag)
    )

    if need_manifest_write:
        _atomic_write_text(
            MANIFEST_JSON_PATH,
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
        _atomic_write_text(MANIFEST_JS_PATH, _serialize_catalog_js(manifest))
        print(
            f"[OK] Manifest updated ({manifest['totals']['total_modules']} modules, "
            f"{handout_count} handout(s), {changed_files} file(s) copied)."
        )
    else:
        print(
            f"[OK] All {manifest['totals']['total_modules']} modules and manifest up to date "
            f"(0 file(s) changed)."
        )

    if not no_h_drive:
        _sync_h_drive()

    return {
        "changed_files": changed_files,
        "manifest_written": need_manifest_write,
        "rebuilt_sims": rebuilt_sims,
        "totals": manifest["totals"],
    }


def _run_git(args: List[str], *, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git") or "git"
    return subprocess.run(
        [git_bin, *args],
        cwd=str(HUB_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=check,
    )


def _git_stage_and_commit(source_tag: Optional[str], custom_msg: Optional[str]) -> bool:
    """Stage all changes in HUB_DIR and commit if staged diff is non-empty. Returns True if committed."""
    _run_git(["add", "-A"])
    diff_proc = _run_git(["diff", "--cached", "--quiet"], check=False)
    if diff_proc.returncode == 0:
        print("[INFO] Git working tree clean; no new changes to commit.")
        return False
    if diff_proc.returncode != 1:
        raise RuntimeError(f"git diff --cached --quiet failed: {diff_proc.stderr.strip()}")

    label = source_tag or "hub"
    commit_msg = custom_msg or f"Update Integrated Study Helper ({label} @ {_utc_now_iso()})"
    _run_git(["commit", "-m", commit_msg])
    print(f"[OK] Committed changes: {commit_msg}")
    return True


def publish_git_push(source_tag: Optional[str], custom_msg: Optional[str]) -> int:
    """Commit and push changes to origin/main (--push mode)."""
    if not (HUB_DIR / ".git").exists():
        print(
            f"[ERROR] No .git repository found in {HUB_DIR}.\n"
            f"        Follow GOOGLE_SITES_SETUP.md to initialize git and create "
            f"https://github.com/new (repository name: integrated-study-helper).",
            file=sys.stderr,
        )
        return 1

    try:
        _git_stage_and_commit(source_tag, custom_msg)
    except Exception as exc:
        print(f"[ERROR] Git commit failed: {exc}", file=sys.stderr)
        return 1

    remote_check = _run_git(["remote", "get-url", "origin"], check=False)
    if remote_check.returncode != 0:
        print(
            "[ERROR] Git remote 'origin' is not configured.\n"
            "        Create a Public GitHub repo at https://github.com/new "
            "(name: integrated-study-helper),\n"
            "        then run: git remote add origin https://github.com/lenir67/integrated-study-helper.git",
            file=sys.stderr,
        )
        return 1

    push_proc = _run_git(["push", "-u", "origin", "main"], check=False, timeout=120)
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
    if not (HUB_DIR / ".git").exists():
        print("[INFO] Hub synced locally (.git not initialized yet; skipping auto-commit/push).")
        return 0

    try:
        _git_stage_and_commit(source_tag, custom_msg)
    except Exception as exc:
        print(f"[WARN] Auto-hook git commit skipped: {exc}")
        return 0

    verify_remote = _run_git(
        ["rev-parse", "--verify", "refs/remotes/origin/main"],
        check=False,
    )
    if verify_remote.returncode != 0:
        print("[INFO] Remote branch refs/remotes/origin/main not found; committed locally only.")
        return 0

    try:
        push_proc = _run_git(["push", "origin", "main"], check=False, timeout=60)
        if push_proc.returncode != 0:
            detail = (push_proc.stderr or push_proc.stdout or "").strip()
            print(f"[WARN] Auto-hook git push failed (continuing offline): {detail}")
        else:
            print(f"[OK] Auto-hook pushed update to origin/main -> {LIVE_HUB_URL}")
    except Exception as exc:
        print(f"[WARN] Auto-hook git push failed (continuing offline): {exc}")
    return 0


def _scan_source_mtimes() -> Dict[str, float]:
    """Snapshot modification times across all upstream HTML, simulator, and handout sources."""
    mtimes: Dict[str, float] = {}

    for spec in SIMULATOR_SPECS:
        sim_dir: Path = spec["dir"]
        if not sim_dir.exists():
            continue
        for rel in [*spec["sources"], spec["bundle"]]:
            p = sim_dir / rel
            if p.exists():
                mtimes[str(p)] = p.stat().st_mtime

    epa_src = CURRICULUM_DIR / "608 Study Material" / "EPA 608 - Interactive Study & HVAC Game.html"
    if epa_src.exists():
        mtimes[str(epa_src)] = epa_src.stat().st_mtime

    for ch_num in range(1, 53):
        ch_src = (
            CURRICULUM_DIR
            / f"ch{ch_num:02d}"
            / f"Ch {ch_num:02d} - Interactive Study & HVAC Game.html"
        )
        if ch_src.exists():
            mtimes[str(ch_src)] = ch_src.stat().st_mtime

    for handout_path in discover_student_handouts().values():
        if handout_path.exists():
            mtimes[str(handout_path)] = handout_path.stat().st_mtime

    return mtimes


def run_watch_loop(
    *,
    force_rebuild: bool,
    no_h_drive: bool,
    custom_msg: Optional[str],
) -> int:
    """Poll upstream sources every 2.5s, debounce 1.5s, and run sync + auto-hook on changes."""
    print(
        f"[WATCH] Monitoring MRAC chapters, EPA 608, Electrical Board, Cycle Lab, and handouts "
        f"(poll={WATCH_POLL_INTERVAL_SEC}s, debounce={WATCH_DEBOUNCE_SEC}s)..."
    )
    print("[WATCH] Press Ctrl+C to stop.")
    try:
        sync_hub(source_tag="watch", force_rebuild=force_rebuild, no_h_drive=no_h_drive)
        auto_hook_git("watch", custom_msg)
    except Exception as exc:
        print(f"[WARN] Initial watch sync encountered an error: {exc}")

    last_snapshot = _scan_source_mtimes()
    try:
        while True:
            time.sleep(WATCH_POLL_INTERVAL_SEC)
            current = _scan_source_mtimes()
            if current == last_snapshot:
                continue

            print("[WATCH] Upstream change detected; waiting for writes to settle...")
            settled = current
            for _ in range(3):
                time.sleep(WATCH_DEBOUNCE_SEC)
                newer = _scan_source_mtimes()
                if newer == settled:
                    break
                settled = newer

            try:
                sync_hub(source_tag="watch", force_rebuild=False, no_h_drive=no_h_drive)
                auto_hook_git("watch", custom_msg)
            except Exception as exc:
                print(f"[WARN] Watch sync failed (will retry on next change): {exc}")
            last_snapshot = _scan_source_mtimes()
    except KeyboardInterrupt:
        print("\n[WATCH] Stopped by user.")
        return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync Integrated Study Helper modules, manifests, H: drive mirror, and GitHub Pages."
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Sync modules, regenerate manifests, and sync H: drive without git commit/push.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Sync modules, regenerate manifests, sync H: drive, git commit, and push to origin/main.",
    )
    parser.add_argument(
        "--auto-hook",
        action="store_true",
        help="Post-build hook mode: sync, commit if .git exists, and push only if origin/main exists (warns offline).",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously poll upstream source mtimes every 2.5s (1.5s debounce) and run sync + auto-hook.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuilding Electrical Display Board and Refrigerant Cycle bundles even if up to date.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional upstream source label (e.g. chapters, epa608, electrical-board, refrigerant-cycle).",
    )
    parser.add_argument(
        "--no-h-drive",
        action="store_true",
        help="Skip mirroring Integrated Study Helper to My Drive Projects folder.",
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
            custom_msg=args.message,
        )

    sync_hub(
        source_tag=args.source,
        force_rebuild=args.force_rebuild,
        no_h_drive=args.no_h_drive,
    )

    if args.push:
        return publish_git_push(args.source, args.message)
    if args.auto_hook:
        return auto_hook_git(args.source, args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
