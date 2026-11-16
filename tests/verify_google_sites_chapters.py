#!/usr/bin/env python3
"""Standalone verification suite for filter-proof Google Sites Chromebook single-HTML chapters."""

from __future__ import annotations

import argparse
import functools
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple
import urllib.request

HUB_DIR = Path(__file__).resolve().parent.parent
GS_CHAPTERS_DIR = HUB_DIR / "google_sites_chapters"
DASHBOARD_PATH = HUB_DIR / "Google_Sites_Chromebook_Chapters.html"

MAX_EMBED_CHARS = 195_000
URL_RE = re.compile(r"https?://", re.IGNORECASE)
FORBIDDEN_NAME_RE = re.compile(r"(?i)(presentation|instructor|answer|teacher)")
DEFAULT_BROWSER_SPOTCHECKS = (1, 11, 22, 33, 50)


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            except Exception:
                pass


def _parse_chapters_arg(raw: Optional[str]) -> List[int]:
    if not raw:
        return list(range(1, 53))
    cleaned = raw.strip().lower()
    if cleaned in ("all", "*"):
        return list(range(1, 53))
    out: List[int] = []
    for part in cleaned.split(","):
        tok = part.strip()
        if not tok:
            continue
        if "-" in tok:
            a, b = tok.split("-", 1)
            lo, hi = int(a.strip()), int(b.strip())
            if lo > hi:
                lo, hi = hi, lo
            for ch in range(lo, hi + 1):
                if 1 <= ch <= 52:
                    out.append(ch)
        else:
            ch = int(tok)
            if 1 <= ch <= 52:
                out.append(ch)
    return sorted(set(out))


def _find_browser_binary() -> Optional[Path]:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    for cmd in ("chrome", "google-chrome", "msedge", "chromium"):
        found = shutil.which(cmd)
        if found:
            return Path(found)
    return None


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def check_files_urls_and_limits(
    chapters: Sequence[int],
    *,
    allow_over_limit: bool,
) -> Dict[int, int]:
    """Verify files exist, zero forbidden names, zero http(s):// URLs, and <195k chars."""
    assert DASHBOARD_PATH.is_file(), f"Missing dashboard: {DASHBOARD_PATH}"
    dash_text = DASHBOARD_PATH.read_text(encoding="utf-8")
    dash_urls = URL_RE.findall(dash_text)
    assert not dash_urls, f"{DASHBOARD_PATH.name} contains external URL(s): {dash_urls[:3]}"

    # Check filenames for forbidden words
    paths_to_check: List[Path] = [
        DASHBOARD_PATH,
        HUB_DIR / "build_google_sites_chapters.py",
        Path(__file__).resolve(),
    ]
    if GS_CHAPTERS_DIR.is_dir():
        paths_to_check.append(GS_CHAPTERS_DIR)
        paths_to_check.extend(GS_CHAPTERS_DIR.iterdir())
    for p in paths_to_check:
        rel = p.relative_to(HUB_DIR).as_posix()
        assert not FORBIDDEN_NAME_RE.search(rel), f"Forbidden filename pattern in {rel!r}"

    char_counts: Dict[int, int] = {}
    over_limit: List[Tuple[int, int]] = []
    for ch in chapters:
        p = GS_CHAPTERS_DIR / f"Ch_{ch:02d}_Google_Sites_Chromebook.html"
        assert p.is_file(), f"Missing single-HTML chapter file: {p}"
        text = p.read_text(encoding="utf-8")
        urls = URL_RE.findall(text)
        assert not urls, f"{p.name} contains external URL(s): {urls[:3]}"
        n_chars = len(text)
        assert n_chars > 10_000, f"{p.name} unexpectedly small ({n_chars} chars)"
        char_counts[ch] = n_chars
        if n_chars >= MAX_EMBED_CHARS:
            over_limit.append((ch, n_chars))

    vals = list(char_counts.values())
    min_c = min(vals)
    med_c = int(statistics.median(vals))
    max_c = max(vals)

    if over_limit:
        summary = ", ".join(f"ch{ch:02d}={n:,}" for ch, n in over_limit[:10])
        msg = f"{len(over_limit)} chapter(s) >= {MAX_EMBED_CHARS:,} chars: {summary}"
        if not allow_over_limit:
            raise AssertionError(msg)
        print(f"[WARN] {msg} (--allow-over-limit active)")

    print(
        f"[PASS] Files, zero-URL, and filename checks passed for {len(chapters)} chapter(s) + dashboard "
        f"(chars: min={min_c:,}, median={med_c:,}, max={max_c:,})."
    )
    return char_counts


class _QuietThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        return


class _GoogleSitesTestHandler(SimpleHTTPRequestHandler):
    """Serves HUB_DIR plus synthetic sandboxed srcdoc test wrappers under /__gs_sandbox__/chXX."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        match = re.match(r"^/__gs_sandbox__/(\d{1,2})$", self.path.split("?", 1)[0])
        if match:
            ch_num = int(match.group(1))
            ch_file = GS_CHAPTERS_DIR / f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html"
            if not ch_file.is_file():
                self.send_error(404, f"Missing chapter {ch_num}")
                return
            ch_html = ch_file.read_text(encoding="utf-8")
            escaped_srcdoc = html.escape(ch_html, quote=True)
            wrapper = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>Google Sites Sandbox Wrapper Ch {ch_num:02d}</title></head>"
                "<body style='margin:0;background:#000;'>"
                f'<iframe id="gs-frame" sandbox="allow-scripts" '
                f'style="width:1280px;height:900px;border:0;display:block;" '
                f'srcdoc="{escaped_srcdoc}"></iframe>'
                "</body></html>"
            )
            body = wrapper.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


class _CDPSession:
    """Minimal synchronous Chrome DevTools Protocol client over websocket-client."""

    def __init__(self, ws_url: str) -> None:
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=20)
        self.next_id = 1
        self.exceptions: List[str] = []
        self.console_errors: List[str] = []
        self.iframe_sessions: List[str] = []

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass

    def reset_logs(self) -> None:
        self.exceptions.clear()
        self.console_errors.clear()
        self.iframe_sessions.clear()

    def _handle_event(self, msg: Dict[str, Any]) -> None:
        method = msg.get("method")
        params = msg.get("params") or {}
        if method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails") or {}
            exc = details.get("exception") or {}
            desc = exc.get("description") or details.get("text") or json.dumps(details)
            self.exceptions.append(str(desc))
        elif method == "Runtime.consoleAPICalled":
            if params.get("type") == "error":
                args = params.get("args") or []
                txt = " ".join(str(a.get("value") or a.get("description") or "") for a in args)
                self.console_errors.append(txt or "console.error")
        elif method == "Target.attachedToTarget":
            tinfo = params.get("targetInfo") or {}
            sid = params.get("sessionId")
            if sid and tinfo.get("type") == "iframe":
                self.iframe_sessions.append(str(sid))

    def call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        req_id = self.next_id
        self.next_id += 1
        payload: Dict[str, Any] = {"id": req_id, "method": method, "params": params or {}}
        if session_id:
            payload["sessionId"] = session_id
        self.ws.send(json.dumps(payload))
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            raw = self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} failed: {msg['error']}")
                return msg.get("result") or {}
            self._handle_event(msg)
        raise TimeoutError(f"CDP {method} timed out")

    def pump_events(self, wait_sec: float = 0.05) -> None:
        prev_timeout = self.ws.gettimeout()
        self.ws.settimeout(wait_sec)
        try:
            while True:
                raw = self.ws.recv()
                msg = json.loads(raw)
                self._handle_event(msg)
        except Exception:
            pass
        finally:
            self.ws.settimeout(prev_timeout)

    def eval_js(self, expr: str, session_id: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True,
        }
        res = self.call("Runtime.evaluate", params, session_id=session_id)
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS eval exception: {res['exceptionDetails']}")
        return (res.get("result") or {}).get("value")


_INSPECT_CHAPTER_JS = r"""
(function () {
  var boot = document.getElementById("gs-boot");
  var data = window.CHAPTER_DATA;
  var titleEl = document.querySelector("h1, .hero-title, .chapter-title, #chapter-title");
  var studyTab = document.getElementById("tab-study");
  var vocabBtn = document.getElementById("btn-subtab-vocab");
  var arenaTab = document.getElementById("tab-arena");
  var bodyText = document.body ? document.body.innerText : "";
  var figs = (data && data.figures && typeof data.figures === "object") ? data.figures : {};
  var figKeys = Object.keys(figs);
  var hydratedFigs = 0;
  var unhydratedFigs = [];
  for (var i = 0; i < figKeys.length; i++) {
    var k = figKeys[i];
    var e = figs[k];
    var u = (typeof e === "string") ? e : (e && e.data_uri ? e.data_uri : "");
    if (typeof u === "string" && u.indexOf("data:image/") === 0 && u.length > 64) {
      hydratedFigs++;
    } else {
      unhydratedFigs.push(k);
    }
  }
  var imgs = Array.prototype.slice.call(document.querySelectorAll("img"));
  var imgStats = imgs.filter(function (im) {
    var s = im.getAttribute("src") || "";
    return s.trim().length > 0;
  }).map(function (im) {
    return { complete: Boolean(im.complete), naturalWidth: Number(im.naturalWidth || 0) };
  });
  return {
    bootPresent: Boolean(boot),
    ready: Boolean(data && typeof data === "object" && studyTab && !boot && bodyText.trim().length > 80),
    chapterNum: data ? Number(data.chapter_num) : null,
    chapterTitle: data ? String(data.chapter_title || "") : "",
    domTitleText: titleEl ? titleEl.textContent.trim() : "",
    bodyHasTitle: Boolean(data && data.chapter_title && bodyText.indexOf(data.chapter_title) !== -1),
    hasStudyTab: Boolean(studyTab),
    hasVocabBtn: Boolean(vocabBtn),
    hasArenaTab: Boolean(arenaTab),
    studyItemCount: data && Array.isArray(data.study_items) ? data.study_items.length : 0,
    figKeyCount: figKeys.length,
    hydratedFigs: hydratedFigs,
    unhydratedFigs: unhydratedFigs,
    imgStats: imgStats
  };
})()
"""


def _wait_for_chapter_render(
    cdp: _CDPSession,
    expected_ch: int,
    *,
    session_id: Optional[str] = None,
    timeout_sec: float = 12.0,
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout_sec
    last_state: Any = None
    while time.monotonic() < deadline:
        cdp.pump_events(0.05)
        try:
            state = cdp.eval_js(_INSPECT_CHAPTER_JS, session_id=session_id)
            last_state = state
            if isinstance(state, dict) and state.get("ready"):
                # Wait briefly for any <img> elements to decode
                img_stats = state.get("imgStats") or []
                if all(im.get("complete") for im in img_stats):
                    return state
        except Exception:
            pass
        time.sleep(0.15)
    raise AssertionError(
        f"Chapter {expected_ch:02d} failed to finish rendering within {timeout_sec}s; last_state={last_state!r}"
    )


def _assert_chapter_dom_ok(ch_num: int, mode: str, state: Dict[str, Any], cdp: _CDPSession) -> None:
    assert not cdp.exceptions, f"ch{ch_num:02d} ({mode}) uncaught exceptions: {cdp.exceptions}"
    assert state.get("chapterNum") == ch_num, (
        f"ch{ch_num:02d} ({mode}) CHAPTER_DATA.chapter_num mismatch: {state.get('chapterNum')}"
    )
    assert state.get("bodyHasTitle"), (
        f"ch{ch_num:02d} ({mode}) rendered DOM missing title {state.get('chapterTitle')!r}"
    )
    assert state.get("hasStudyTab") and state.get("hasVocabBtn") and state.get("hasArenaTab"), (
        f"ch{ch_num:02d} ({mode}) missing study/vocab/arena controls: {state}"
    )
    assert state.get("studyItemCount", 0) > 0, f"ch{ch_num:02d} ({mode}) has 0 study items"

    fig_count = int(state.get("figKeyCount") or 0)
    assert not state.get("unhydratedFigs"), (
        f"ch{ch_num:02d} ({mode}) unhydrated figures: {state.get('unhydratedFigs')}"
    )
    if ch_num in (22, 50):
        assert fig_count > 0 and state.get("hydratedFigs") == fig_count, (
            f"ch{ch_num:02d} ({mode}) expected hydrated figures, got {state}"
        )
    for idx, im in enumerate(state.get("imgStats") or []):
        assert im.get("complete") and im.get("naturalWidth", 0) > 0, (
            f"ch{ch_num:02d} ({mode}) broken <img> #{idx}: {im}"
        )


def _verify_figures_modal_renders(
    ch_num: int,
    mode: str,
    cdp: _CDPSession,
    session_id: Optional[str] = None,
) -> int:
    """Click #btn-open-figures and verify every rendered .figure-ref-img loads cleanly."""
    opened = cdp.eval_js(
        """(function(){
          var btn = document.getElementById("btn-open-figures");
          if (!btn) return false;
          btn.click();
          return true;
        })()""",
        session_id=session_id,
    )
    assert opened, f"ch{ch_num:02d} ({mode}) missing #btn-open-figures"
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        cdp.pump_events(0.05)
        res = cdp.eval_js(
            """(function(){
              var imgs = Array.prototype.slice.call(document.querySelectorAll("#figures-modal-grid img.figure-ref-img"));
              return imgs.map(function(im){
                return { srcOk: (im.src || "").indexOf("data:image/") === 0, complete: im.complete, w: im.naturalWidth };
              });
            })()""",
            session_id=session_id,
        )
        if res and all(r.get("complete") for r in res):
            assert all(r.get("srcOk") and r.get("w", 0) > 0 for r in res), (
                f"ch{ch_num:02d} ({mode}) failed figure modal image decode: {res}"
            )
            return len(res)
        time.sleep(0.1)
    raise AssertionError(f"ch{ch_num:02d} ({mode}) figures modal images did not finish loading")


def check_browser_rendering(spotcheck_chapters: Sequence[int]) -> None:
    """Verify representative chapters in headless Chrome/Edge directly and in sandboxed srcdoc iframe."""
    browser_bin = _find_browser_binary()
    assert browser_bin is not None, "Could not locate Chrome or Edge binary for headless verification"

    handler_cls = functools.partial(_GoogleSitesTestHandler, directory=str(HUB_DIR))
    server = _QuietThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    http_port = server.server_address[1]
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    dbg_port = _pick_free_port()
    with tempfile.TemporaryDirectory(prefix="ish_gs_chrome_", ignore_cleanup_errors=True) as tmp_profile:
        proc = subprocess.Popen(
            [
                str(browser_bin),
                "--headless=new",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--disable-extensions",
                f"--remote-debugging-port={dbg_port}",
                f"--user-data-dir={tmp_profile}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cdp: Optional[_CDPSession] = None
        try:
            ws_url = ""
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{dbg_port}/json/list", timeout=2) as r:
                        targets = json.loads(r.read().decode("utf-8"))
                        page_targets = [t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
                        if page_targets:
                            ws_url = page_targets[0]["webSocketDebuggerUrl"]
                            break
                except Exception:
                    time.sleep(0.15)
            assert ws_url, f"Headless browser did not expose CDP target on port {dbg_port}"

            cdp = _CDPSession(ws_url)
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            cdp.call(
                "Target.setAutoAttach",
                {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True},
            )

            # Verify dashboard renders cleanly with 52 cards
            cdp.reset_logs()
            dash_url = f"http://127.0.0.1:{http_port}/Google_Sites_Chromebook_Chapters.html"
            cdp.call("Page.navigate", {"url": dash_url})
            dash_deadline = time.monotonic() + 10.0
            dash_cards = 0
            while time.monotonic() < dash_deadline:
                cdp.pump_events(0.05)
                dash_cards = cdp.eval_js("document.querySelectorAll('#chapters-grid .card').length") or 0
                if dash_cards == 52:
                    break
                time.sleep(0.1)
            assert dash_cards == 52, f"Dashboard expected 52 chapter cards, rendered {dash_cards}"
            assert not cdp.exceptions, f"Dashboard uncaught exceptions: {cdp.exceptions}"
            print("[PASS] Browser dashboard check: Google_Sites_Chromebook_Chapters.html rendered 52 cards with 0 errors.")

            for ch_num in spotcheck_chapters:
                # 1. Direct HTTP navigation
                cdp.reset_logs()
                direct_url = (
                    f"http://127.0.0.1:{http_port}/google_sites_chapters/"
                    f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html"
                )
                cdp.call("Page.navigate", {"url": direct_url})
                direct_state = _wait_for_chapter_render(cdp, ch_num)
                _assert_chapter_dom_ok(ch_num, "direct", direct_state, cdp)
                if direct_state.get("figKeyCount", 0) > 0:
                    _verify_figures_modal_renders(ch_num, "direct", cdp)

                # 2. Sandboxed srcdoc iframe (opaque null origin mimicking Google Sites!)
                cdp.reset_logs()
                sandbox_url = f"http://127.0.0.1:{http_port}/__gs_sandbox__/{ch_num}"
                cdp.call("Page.navigate", {"url": sandbox_url})

                child_sid: Optional[str] = None
                wait_end = time.monotonic() + 10.0
                while time.monotonic() < wait_end:
                    cdp.pump_events(0.05)
                    if cdp.iframe_sessions:
                        child_sid = cdp.iframe_sessions[-1]
                        break
                    time.sleep(0.1)

                assert child_sid is not None, (
                    f"ch{ch_num:02d} (sandboxed srcdoc) failed to attach to child iframe target"
                )
                cdp.call("Runtime.enable", session_id=child_sid)
                sb_state = _wait_for_chapter_render(cdp, ch_num, session_id=child_sid)
                _assert_chapter_dom_ok(ch_num, "sandboxed-srcdoc", sb_state, cdp)
                if sb_state.get("figKeyCount", 0) > 0:
                    _verify_figures_modal_renders(ch_num, "sandboxed-srcdoc", cdp, session_id=child_sid)

                print(
                    f"[PASS] Browser Ch {ch_num:02d}: direct + sandboxed srcdoc verified "
                    f"(items={sb_state['studyItemCount']}, figs={sb_state['hydratedFigs']}/{sb_state['figKeyCount']}, 0 errors)."
                )
        finally:
            if cdp is not None:
                cdp.close()
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            server.shutdown()
            server.server_close()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Google Sites single-HTML Chromebook chapters and browser rendering."
    )
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Comma/range list of chapters to verify (default: 1-52).",
    )
    parser.add_argument(
        "--allow-over-limit",
        action="store_true",
        help="Warn instead of failing if any file is >= 195,000 chars (pre-upstream-rebuild mode).",
    )
    parser.add_argument(
        "--skip-browser",
        action="store_true",
        help="Skip headless Chrome/Edge rendering verification.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_stdio()
    args = build_arg_parser().parse_args(list(argv) if argv is not None else None)
    chapters = _parse_chapters_arg(args.chapters)
    check_files_urls_and_limits(chapters, allow_over_limit=args.allow_over_limit)

    if not args.skip_browser:
        if len(chapters) <= 6:
            spotchecks = list(chapters)
        else:
            spotchecks = [ch for ch in DEFAULT_BROWSER_SPOTCHECKS if ch in chapters]
            if not spotchecks:
                spotchecks = list(chapters[:3])
        check_browser_rendering(spotchecks)
    else:
        print("[SKIP] Browser rendering check skipped (--skip-browser).")

    print("[SUCCESS] Google Sites Chromebook verification completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
