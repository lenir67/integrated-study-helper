#!/usr/bin/env python3
"""Comprehensive end-to-end verification suite for Integrated Study Helper."""

from __future__ import annotations

import argparse
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Tuple
import urllib.request

HUB_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = HUB_DIR.parent
ELEC_DIR = PROJECTS_DIR / "Electrical Display Board"
CYCLE_DIR = PROJECTS_DIR / "animated refrigerant cycle"
TRACKER_DIR = PROJECTS_DIR / "cte-program-tracker-standalone"

MANIFEST_JSON_PATH = HUB_DIR / "manifest.json"
MANIFEST_JS_PATH = HUB_DIR / "js" / "catalog_manifest.js"

FORBIDDEN_FILENAME_RE = re.compile(r"(?i)(presentation|instructor|answer_key|answerkey)")
MIN_MODULE_SIZE_BYTES = 10 * 1024
MAX_REPO_SIZE_BYTES = 150 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 50 * 1024 * 1024

MIN_TOTAL_VOCAB_TERMS = 1300
MIN_CHAPTER_VOCAB_TERMS = 12
MIN_VOCAB_DEF_LEN = 20
VOCAB_SPOTCHECK_CHAPTERS = ("ch01", "ch11", "ch24", "ch52")
INLINE_JS_CHECK_HTMLS = (
    "modules/chapters/ch01.html",
    "modules/chapters/ch52.html",
    "modules/epa608/index.html",
)
INLINE_SCRIPT_RE = re.compile(
    r"<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)

EXPECTED_FEATURED_IDS = ["epa608", "electrical-board", "refrigerant-cycle"]
HTTP_CHECK_ROUTES = [
    "/",
    "/manifest.json",
    "/js/app.js",
    "/js/catalog_manifest.js",
    "/modules/epa608/index.html",
    "/modules/electrical-board/index.html",
    "/modules/refrigerant-cycle/index.html",
    "/modules/chapters/ch01.html",
    "/modules/chapters/ch52.html",
    "/modules/handouts/ch11_handout.html",
]


def _configure_stdio() -> None:
    """Ensure UTF-8 unbuffered console output on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            except Exception:
                pass


def _sha256_prefix(path: Path, length: int = 10) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def _resolve_hub_rel_path(rel_url_path: str) -> Path:
    cleaned = rel_url_path.lstrip("./").replace("/", os.sep)
    resolved = (HUB_DIR / cleaned).resolve()
    hub_resolved = HUB_DIR.resolve()
    if hub_resolved != resolved and hub_resolved not in resolved.parents:
        raise AssertionError(f"Path escaped HUB_DIR: {rel_url_path}")
    return resolved


def _load_manifest_json() -> Dict[str, Any]:
    assert MANIFEST_JSON_PATH.is_file(), f"Missing {MANIFEST_JSON_PATH}"
    data = json.loads(MANIFEST_JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "manifest.json root must be a JSON object"
    return data


def _load_catalog_manifest_js() -> Dict[str, Any]:
    assert MANIFEST_JS_PATH.is_file(), f"Missing {MANIFEST_JS_PATH}"
    raw = MANIFEST_JS_PATH.read_text(encoding="utf-8").strip()
    prefix = "window.INTEGRATED_STUDY_MANIFEST = "
    assert raw.startswith(prefix), (
        f"catalog_manifest.js missing expected prefix {prefix!r}"
    )
    assert raw.endswith(";"), "catalog_manifest.js missing trailing semicolon"
    payload = raw[len(prefix) : -1].strip()
    data = json.loads(payload)
    assert isinstance(data, dict), "catalog_manifest.js payload must be a JSON object"
    return data


def check_manifest_parity() -> Dict[str, Any]:
    """Check 1: manifest.json and js/catalog_manifest.js parse and match exactly."""
    manifest_json = _load_manifest_json()
    manifest_js = _load_catalog_manifest_js()
    assert manifest_json == manifest_js, (
        "manifest.json and js/catalog_manifest.js do not match!"
    )
    print(
        f"[PASS] Check 1: manifest.json == js/catalog_manifest.js "
        f"(generated_at_utc={manifest_json.get('generated_at_utc')})"
    )
    return manifest_json


def check_manifest_structure(manifest: Dict[str, Any]) -> None:
    """Check 2: Verify featured_labs (3), chapters (52), and ch11 handout metadata."""
    featured = manifest.get("featured_labs")
    assert isinstance(featured, list) and len(featured) == 3, (
        f"Expected 3 featured_labs, got {len(featured) if isinstance(featured, list) else type(featured)}"
    )
    featured_ids = [item.get("id") for item in featured]
    assert featured_ids == EXPECTED_FEATURED_IDS, (
        f"Expected featured_labs ids {EXPECTED_FEATURED_IDS}, got {featured_ids}"
    )

    chapters = manifest.get("chapters")
    assert isinstance(chapters, list) and len(chapters) == 52, (
        f"Expected 52 chapters, got {len(chapters) if isinstance(chapters, list) else type(chapters)}"
    )
    expected_ch_ids = [f"ch{i:02d}" for i in range(1, 53)]
    actual_ch_ids = [ch.get("id") for ch in chapters]
    assert actual_ch_ids == expected_ch_ids, "Chapter IDs do not match ch01..ch52"

    actual_ch_nums = [ch.get("chapter_num") for ch in chapters]
    assert actual_ch_nums == list(range(1, 53)), "chapter_num values do not match 1..52"

    ch11_list = [ch for ch in chapters if ch.get("chapter_num") == 11]
    assert len(ch11_list) == 1, "Missing ch11 entry"
    ch11_handout = ch11_list[0].get("handout")
    assert isinstance(ch11_handout, dict), f"ch11 handout must be populated, got {ch11_handout!r}"
    assert ch11_handout.get("path") == "./modules/handouts/ch11_handout.html", (
        f"Unexpected ch11 handout path: {ch11_handout.get('path')!r}"
    )

    totals = manifest.get("totals", {})
    print(
        f"[PASS] Check 2: 3 featured_labs, 52 chapters (ch01..ch52), ch11 handout populated. "
        f"Totals={json.dumps(totals)}"
    )


def _verify_entry_file(label: str, entry: Dict[str, Any], check_recorded_size: bool) -> int:
    rel_path = entry.get("path")
    assert isinstance(rel_path, str) and rel_path, f"{label}: missing path"
    expected_ver = entry.get("version")
    assert isinstance(expected_ver, str) and len(expected_ver) == 10, (
        f"{label}: invalid version {expected_ver!r}"
    )

    target = _resolve_hub_rel_path(rel_path)
    assert target.is_file(), f"{label}: missing file on disk: {target}"

    actual_size = target.stat().st_size
    assert actual_size > MIN_MODULE_SIZE_BYTES, (
        f"{label}: file too small ({actual_size} bytes <= {MIN_MODULE_SIZE_BYTES}): {target}"
    )
    if check_recorded_size:
        assert actual_size == entry.get("size_bytes"), (
            f"{label}: size mismatch disk={actual_size} vs manifest={entry.get('size_bytes')}"
        )

    actual_ver = _sha256_prefix(target, 10)
    assert actual_ver == expected_ver, (
        f"{label}: SHA-256 prefix mismatch disk={actual_ver} vs manifest={expected_ver} ({target})"
    )
    return actual_size


def check_module_files(manifest: Dict[str, Any]) -> None:
    """Check 3: Every featured lab, chapter, and handout exists, >10 KB, and SHA-256 matches."""
    featured_summaries: List[str] = []
    for lab in manifest["featured_labs"]:
        size = _verify_entry_file(f"featured:{lab['id']}", lab, check_recorded_size=True)
        featured_summaries.append(f"{lab['id']}(v={lab['version']}, {size:,} B)")

    handout_sizes: List[Tuple[str, int, str]] = []
    for ch in manifest["chapters"]:
        _verify_entry_file(f"chapter:{ch['id']}", ch, check_recorded_size=True)
        handout = ch.get("handout")
        if handout is not None:
            h_size = _verify_entry_file(
                f"handout:{ch['id']}", handout, check_recorded_size=False
            )
            handout_sizes.append((ch["id"], h_size, handout["version"]))

    print(
        f"[PASS] Check 3: All 3 featured labs, 52 chapters, and {len(handout_sizes)} handout(s) "
        f"verified (>10 KB & SHA-256 matched)."
    )
    print(f"       Featured labs: {', '.join(featured_summaries)}")
    for ch_id, h_size, h_ver in handout_sizes:
        print(f"       Handout {ch_id}: v={h_ver}, size={h_size:,} bytes ({h_size / 1024:.2f} KB)")


def check_no_forbidden_filenames() -> None:
    """Check 4: Walk Integrated Study Helper (excl. .git) and assert zero forbidden filenames."""
    matches: List[str] = []
    for root, dirs, files in os.walk(HUB_DIR):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel_root = Path(root).relative_to(HUB_DIR)
        for dname in dirs:
            rel_dir = (rel_root / dname).as_posix()
            if FORBIDDEN_FILENAME_RE.search(dname) or FORBIDDEN_FILENAME_RE.search(rel_dir):
                matches.append(rel_dir)
        for fname in files:
            rel_file = (rel_root / fname).as_posix()
            if FORBIDDEN_FILENAME_RE.search(fname) or FORBIDDEN_FILENAME_RE.search(rel_file):
                matches.append(rel_file)

    assert not matches, f"Forbidden instructor/presentation/answer files found: {matches}"
    print("[PASS] Check 4: Zero files/dirs match forbidden instructor/presentation/answer patterns.")


def check_js_syntax() -> None:
    """Check 5: Validate JS syntax for js/app.js and js/catalog_manifest.js via node --check."""
    node_bin = shutil.which("node") or "node"
    for rel in ("js/app.js", "js/catalog_manifest.js"):
        proc = subprocess.run(
            [node_bin, "--check", rel],
            cwd=str(HUB_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 0, (
            f"node --check {rel} failed (exit {proc.returncode}): {proc.stderr or proc.stdout}"
        )
    print("[PASS] Check 5: node --check passed for js/app.js and js/catalog_manifest.js.")


def _run_hook_and_assert_manifest_updated(
    label: str,
    cmd: List[str],
    cwd: Path,
    clean_env_keys: Tuple[str, ...] = ("SKIP_HUB_SYNC",),
) -> str:
    before_ts = _load_manifest_json()["generated_at_utc"]
    time.sleep(1.2)

    env = os.environ.copy()
    for key in clean_env_keys:
        env.pop(key, None)

    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, (
        f"{label} failed (exit {proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    after_ts = _load_manifest_json()["generated_at_utc"]
    assert after_ts != before_ts and after_ts > before_ts, (
        f"{label} did not update manifest.json generated_at_utc "
        f"(before={before_ts}, after={after_ts})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    print(f"       {label}: exit=0, generated_at_utc {before_ts} -> {after_ts}")
    return after_ts


def check_live_auto_update_hooks() -> None:
    """Check 6: Exercise upstream build hooks and verify manifest.json auto-updates."""
    node_bin = shutil.which("node") or "node"
    venv_py = TRACKER_DIR / ".venv" / "Scripts" / "python.exe"
    tracker_py = str(venv_py) if venv_py.is_file() else sys.executable
    study_games_script = TRACKER_DIR / "scripts" / "build_chapter_study_games.py"
    if not study_games_script.is_file():
        fallback = TRACKER_DIR / "build_chapter_study_games.py"
        if fallback.is_file():
            study_games_script = fallback
    assert study_games_script.is_file(), f"Missing {study_games_script}"

    print("[INFO] Check 6: Running live auto-update hook verification...")
    _run_hook_and_assert_manifest_updated(
        "Electrical Display Board (build_classroom_bundle.js)",
        [node_bin, "build_classroom_bundle.js"],
        cwd=ELEC_DIR,
    )
    _run_hook_and_assert_manifest_updated(
        "CTE Tracker Ch 11 (scripts/build_chapter_study_games.py --chapters 11 --local-only)",
        [tracker_py, str(study_games_script), "--chapters", "11", "--local-only"],
        cwd=TRACKER_DIR,
    )
    _run_hook_and_assert_manifest_updated(
        "Refrigerant Cycle Lab (build_classroom_bundle.js)",
        [node_bin, "build_classroom_bundle.js"],
        cwd=CYCLE_DIR,
    )
    print("[PASS] Check 6: All 3 live upstream auto-update hooks updated manifest.json.")


class _QuietHandler(SimpleHTTPRequestHandler):
    """Static file handler that suppresses per-request stdout spam."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


def check_http_routes() -> None:
    """Check 7: Serve Integrated Study Helper over HTTP and verify 200 OK on all routes."""
    handler_cls = functools.partial(_QuietHandler, directory=str(HUB_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        results: List[str] = []
        for route in HTTP_CHECK_ROUTES:
            url = f"http://127.0.0.1:{port}{route}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                status = resp.status
                body = resp.read()
                assert status == 200, f"HTTP {status} for {route}"
                assert len(body) > 0, f"Empty HTTP response for {route}"
                if route == "/manifest.json":
                    parsed = json.loads(body.decode("utf-8"))
                    assert parsed.get("totals", {}).get("chapter_count") == 52
                results.append(f"{route} ({status}, {len(body):,} B)")
        print(f"[PASS] Check 7: All {len(HTTP_CHECK_ROUTES)} HTTP routes returned 200 OK:")
        for item in results:
            print(f"       GET {item}")
    finally:
        server.shutdown()
        server.server_close()


def check_repo_size() -> None:
    """Check 8: Verify total repository size (< 150 MB) and largest single file (< 50 MB)."""
    total_bytes = 0
    file_count = 0
    max_bytes = -1
    max_rel_path = ""

    for root, dirs, files in os.walk(HUB_DIR):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel_root = Path(root).relative_to(HUB_DIR)
        for fname in files:
            fpath = Path(root) / fname
            size = fpath.stat().st_size
            total_bytes += size
            file_count += 1
            if size > max_bytes:
                max_bytes = size
                max_rel_path = (rel_root / fname).as_posix()

    total_mb = total_bytes / (1024 * 1024)
    max_mb = max_bytes / (1024 * 1024)

    assert total_bytes < MAX_REPO_SIZE_BYTES, (
        f"Repository size {total_mb:.2f} MB exceeds 150 MB limit"
    )
    assert max_bytes < MAX_SINGLE_FILE_BYTES, (
        f"Largest file {max_rel_path} ({max_mb:.2f} MB) exceeds 50 MB limit"
    )

    print(
        f"[PASS] Check 8: Repo size = {total_mb:.2f} MB ({total_bytes:,} bytes across {file_count} files, < 150 MB); "
        f"largest file = {max_rel_path} ({max_mb:.2f} MB, {max_bytes:,} bytes, < 50 MB)."
    )


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


def _verify_inline_scripts_node_check(rel_paths: Tuple[str, ...]) -> int:
    """Extract inline <script> blocks into temp JS files and validate syntax with node --check."""
    node_bin = shutil.which("node") or "node"
    checked_blocks = 0

    with tempfile.TemporaryDirectory(prefix="ish_js_check_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        for rel_path in rel_paths:
            html_path = HUB_DIR / rel_path
            assert html_path.is_file(), f"Missing HTML for inline JS check: {html_path}"
            html_text = html_path.read_text(encoding="utf-8", errors="replace")
            scripts = [
                block
                for block in INLINE_SCRIPT_RE.findall(html_text)
                if block and block.strip()
            ]
            assert scripts, f"No inline <script> blocks found in {rel_path}"

            safe_stem = rel_path.replace("/", "_").replace(".", "_")
            for idx, script_body in enumerate(scripts, start=1):
                temp_js = tmp_root / f"{safe_stem}_script_{idx}.js"
                temp_js.write_text(script_body, encoding="utf-8")
                proc = subprocess.run(
                    [node_bin, "--check", str(temp_js)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert proc.returncode == 0, (
                    f"node --check failed for {rel_path} inline <script> #{idx} "
                    f"(exit {proc.returncode}): {proc.stderr or proc.stdout}"
                )
                checked_blocks += 1

    return checked_blocks


def check_vocabulary_integration(manifest: Dict[str, Any]) -> None:
    """Check 9: Verify Chapters 1-52 vocabulary data, chapter UI, EPA 608 guard, inline JS, and hub UI."""
    totals = manifest.get("totals", {})
    total_vocab = totals.get("total_vocab_terms")
    assert isinstance(total_vocab, int) and total_vocab >= MIN_TOTAL_VOCAB_TERMS, (
        f"Expected total_vocab_terms >= {MIN_TOTAL_VOCAB_TERMS}, got {total_vocab!r}"
    )

    chapters = manifest.get("chapters", [])
    sum_vocab = 0
    min_vocab_ch = ("", 10**9)
    max_vocab_ch = ("", -1)

    for ch in chapters:
        ch_id = str(ch.get("id") or "")
        vocab_count = ch.get("vocab_count")
        vocab_list = ch.get("vocabulary")
        assert isinstance(vocab_count, int) and vocab_count >= MIN_CHAPTER_VOCAB_TERMS, (
            f"{ch_id}: expected vocab_count >= {MIN_CHAPTER_VOCAB_TERMS}, got {vocab_count!r}"
        )
        assert isinstance(vocab_list, list) and len(vocab_list) == vocab_count, (
            f"{ch_id}: len(vocabulary)={len(vocab_list) if isinstance(vocab_list, list) else type(vocab_list)} "
            f"!= vocab_count={vocab_count}"
        )
        sum_vocab += vocab_count
        if vocab_count < min_vocab_ch[1]:
            min_vocab_ch = (ch_id, vocab_count)
        if vocab_count > max_vocab_ch[1]:
            max_vocab_ch = (ch_id, vocab_count)

        for idx, entry in enumerate(vocab_list, start=1):
            assert isinstance(entry, dict), f"{ch_id} vocab[{idx}] is not a dict"
            vid = entry.get("id")
            term = entry.get("term")
            definition = entry.get("definition")
            sec_id = entry.get("section_id")
            sec_title = entry.get("section_title")

            assert isinstance(vid, str) and vid.strip(), f"{ch_id} vocab[{idx}] missing id"
            assert isinstance(term, str) and len(term.strip()) >= 2, (
                f"{ch_id} vocab[{idx}] ({vid}) invalid term: {term!r}"
            )
            assert isinstance(definition, str) and len(definition.strip()) >= MIN_VOCAB_DEF_LEN, (
                f"{ch_id} vocab[{idx}] ({vid}) definition too short (< {MIN_VOCAB_DEF_LEN}): {definition!r}"
            )
            assert "____" not in definition, (
                f"{ch_id} vocab[{idx}] ({vid}) contains blank placeholder '____': {definition!r}"
            )
            assert isinstance(sec_id, str) and sec_id.strip(), (
                f"{ch_id} vocab[{idx}] ({vid}) missing section_id"
            )
            assert isinstance(sec_title, str) and sec_title.strip(), (
                f"{ch_id} vocab[{idx}] ({vid}) missing section_title"
            )

    assert total_vocab == sum_vocab, (
        f"totals.total_vocab_terms ({total_vocab}) != sum of chapter vocab_count ({sum_vocab})"
    )

    for ch_id in VOCAB_SPOTCHECK_CHAPTERS:
        ch_path = HUB_DIR / "modules" / "chapters" / f"{ch_id}.html"
        assert ch_path.is_file(), f"Missing chapter HTML: {ch_path}"
        ch_html = ch_path.read_text(encoding="utf-8", errors="replace")
        for marker in ('id="subtab-vocab"', 'data-subtab="subtab-vocab"', "renderVocabulary"):
            assert marker in ch_html, f"{ch_id}.html missing required vocabulary marker {marker!r}"
        ch_data = _extract_js_json_var(ch_html, "CHAPTER_DATA")
        assert isinstance(ch_data, dict), f"{ch_id}.html missing parseable window.CHAPTER_DATA"
        ch_vocab = ch_data.get("vocabulary")
        assert isinstance(ch_vocab, list) and len(ch_vocab) >= MIN_CHAPTER_VOCAB_TERMS, (
            f"{ch_id}.html CHAPTER_DATA.vocabulary empty or < {MIN_CHAPTER_VOCAB_TERMS}"
        )

    epa_path = HUB_DIR / "modules" / "epa608" / "index.html"
    assert epa_path.is_file(), f"Missing EPA 608 module: {epa_path}"
    epa_html = epa_path.read_text(encoding="utf-8", errors="replace")
    epa_editions = _extract_js_json_var(epa_html, "STUDY_EDITIONS")
    assert isinstance(epa_editions, dict) and epa_editions, (
        "modules/epa608/index.html missing parseable window.STUDY_EDITIONS"
    )
    for ed_key, ed_data in epa_editions.items():
        assert isinstance(ed_data, dict), f"EPA 608 edition {ed_key!r} is not a dict"
        ed_vocab = ed_data.get("vocabulary")
        assert not ed_vocab, (
            f"EPA 608 edition {ed_key!r} unexpectedly defines chapter-only vocabulary entries"
        )
    assert 'id="subtab-vocab"' not in epa_html, (
        "modules/epa608/index.html unexpectedly includes chapter subtab-vocab"
    )

    inline_blocks = _verify_inline_scripts_node_check(INLINE_JS_CHECK_HTMLS)

    index_path = HUB_DIR / "index.html"
    assert index_path.is_file(), f"Missing {index_path}"
    index_html = index_path.read_text(encoding="utf-8", errors="replace")
    for elem_id in (
        "btn-view-vocab",
        "vocab-explorer-panel",
        "vocab-explorer-list",
        "vocab-chapter-select",
    ):
        assert f'id="{elem_id}"' in index_html, f"index.html missing #{elem_id}"

    print(
        f"[PASS] Check 9: Vocabulary verified across 52 chapters "
        f"(total={total_vocab} terms, min={min_vocab_ch[0]}:{min_vocab_ch[1]}, "
        f"max={max_vocab_ch[0]}:{max_vocab_ch[1]}), spotchecks={list(VOCAB_SPOTCHECK_CHAPTERS)}, "
        f"EPA 608 clean, node --check passed on {inline_blocks} inline <script> blocks, "
        f"and index.html vocabulary explorer controls present."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Integrated Study Helper manifests, modules, hooks, HTTP serving, and size."
    )
    parser.add_argument(
        "--skip-live-hooks",
        action="store_true",
        help="Skip Check 6 live upstream auto-update hook execution.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    _configure_stdio()
    args = build_arg_parser().parse_args(argv)

    manifest = check_manifest_parity()
    check_manifest_structure(manifest)
    check_module_files(manifest)
    check_no_forbidden_filenames()
    check_js_syntax()

    if not args.skip_live_hooks:
        check_live_auto_update_hooks()
        # Re-verify manifest parity, file hashes, and JS syntax after live hooks wrote updates.
        manifest = check_manifest_parity()
        check_manifest_structure(manifest)
        check_module_files(manifest)
        check_js_syntax()
    else:
        print("[SKIP] Check 6: Live auto-update hook tests skipped (--skip-live-hooks).")

    check_http_routes()
    check_repo_size()
    check_vocabulary_integration(manifest)

    print("[SUCCESS] All Integrated Study Helper verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
