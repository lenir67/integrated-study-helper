#!/usr/bin/env python3
"""Build filter-proof single-HTML Google Sites Chromebook chapter files (< 195 KB each).

Packages each `modules/chapters/chXX.html` into a completely self-contained, zero-external-URL
HTML document at `google_sites_chapters/Ch_XX_Google_Sites_Chromebook.html` (and a copy/download
utility dashboard at `Google_Sites_Chromebook_Chapters.html`) that fits well beneath Google
Sites' 200,000-character custom embed limit.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import statistics
import sys
import threading
from typing import Any, Dict, List, Optional, Sequence, Tuple

HUB_DIR = Path(__file__).resolve().parent
CHAPTERS_SRC_DIR = HUB_DIR / "modules" / "chapters"
OUTPUT_DIR = HUB_DIR / "google_sites_chapters"
EMBED_MANIFEST_PATH = OUTPUT_DIR / "embed_manifest.json"
DASHBOARD_PATH = HUB_DIR / "Google_Sites_Chromebook_Chapters.html"

SCRIPT_VERSION = 1
MAX_EMBED_CHARS = 195_000
GOOGLE_SITES_CHAR_LIMIT = 200_000
MAX_IMAGE_DIM_PX = 440
JPEG_QUALITY = 50

# Exact 85-character HTML/JS-safe alphabet: printable ASCII 33..126 excluding " & ' / < > ? \ `
_EXCLUDED_ASCII = {34, 38, 39, 47, 60, 62, 63, 92, 96}
BASE85_ALPHABET = "".join(
    chr(c) for c in range(33, 127) if c not in _EXCLUDED_ASCII
)
assert len(BASE85_ALPHABET) == 85

URL_RE = re.compile(r"https?://", re.IGNORECASE)
STYLE_TAG_RE = re.compile(r"<style[^>]*>([\s\S]*?)</style>", re.IGNORECASE)
SCRIPT_TAG_RE = re.compile(r"<script[^>]*>([\s\S]*?)</script>", re.IGNORECASE)
TITLE_TAG_RE = re.compile(r"<title[^>]*>([\s\S]*?)</title>", re.IGNORECASE)
CHAPTER_DATA_ASSIGN_RE = re.compile(r"\bwindow\.CHAPTER_DATA\s*=\s*")
CLOSE_SCRIPT_RE = re.compile(r"</script", re.IGNORECASE)

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

ITEM_LIST_KEYS = (
    "study_items",
    "blitz_questions",
    "critical_thinking",
    "flip_cards",
    "flashcards",
    "cards",
    "questions",
)


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
            except Exception:
                pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write_text(dest_path: Path, text: str) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_name(
        f".{dest_path.name}.tmp.{os.getpid()}.{threading.get_ident()}"
    )
    tmp_path.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp_path, dest_path)


def _escape_inline_script_json(raw_json: str) -> str:
    """Escape JSON string so it is safe inside both HTML <script> and JS parsers."""
    return (
        raw_json.replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _recompress_image_data_uri(
    data_uri: str,
    *,
    fmt: str = "JPG",
    max_dim: int = MAX_IMAGE_DIM_PX,
    quality: int = JPEG_QUALITY,
) -> str:
    """Re-compress a data:image/*;base64,... URI to <=max_dim px in JPG/WEBP if smaller."""
    if not isinstance(data_uri, str) or not data_uri.startswith("data:image/"):
        return data_uri
    if "," not in data_uri:
        return data_uri
    _, b64_part = data_uri.split(",", 1)
    try:
        raw_bytes = base64.b64decode(b64_part)
    except Exception:
        return data_uri
    if not raw_bytes:
        return data_uri

    mime = "image/webp" if fmt.upper() == "WEBP" else "image/jpeg"

    # Lazy-import imaging libraries only when an image actually needs processing
    # so no-op builds remain sub-10ms.
    try:
        from PySide6.QtCore import QBuffer, QIODevice, Qt
        from PySide6.QtGui import QImage, QPainter

        img = QImage.fromData(raw_bytes)
        if not img.isNull():
            if max(img.width(), img.height()) > max_dim:
                img = img.scaled(
                    max_dim,
                    max_dim,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            if img.hasAlphaChannel():
                canvas = QImage(img.size(), QImage.Format.Format_RGB32)
                canvas.fill(Qt.GlobalColor.white)
                painter = QPainter(canvas)
                painter.drawImage(0, 0, img)
                painter.end()
                img = canvas
            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            if img.save(buf, fmt.upper(), quality):
                out_bytes = bytes(buf.data())
                if out_bytes:
                    candidate = f"data:{mime};base64," + base64.b64encode(out_bytes).decode("ascii")
                    return candidate if len(candidate) <= len(data_uri) else data_uri
    except Exception:
        pass

    try:
        from PIL import Image

        pil_fmt = "WEBP" if fmt.upper() == "WEBP" else "JPEG"
        with Image.open(io.BytesIO(raw_bytes)) as pil_img:
            if pil_img.mode in ("RGBA", "LA") or (
                pil_img.mode == "P" and "transparency" in pil_img.info
            ):
                rgba = pil_img.convert("RGBA")
                bg = Image.new("RGB", rgba.size, (255, 255, 255))
                bg.paste(rgba, mask=rgba.split()[3])
                pil_img = bg
            elif pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            if max(pil_img.width, pil_img.height) > max_dim:
                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            pil_img.save(out_buf, format=pil_fmt, quality=quality, optimize=True)
            out_bytes = out_buf.getvalue()
            if out_bytes:
                candidate = f"data:{mime};base64," + base64.b64encode(out_bytes).decode("ascii")
                return candidate if len(candidate) <= len(data_uri) else data_uri
    except Exception:
        pass

    return data_uri


def _extract_and_optimize_figures(data: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Deduplicate, recompress, and externalize chapter figures out of CHAPTER_DATA."""
    raw_to_fig_id: Dict[str, str] = {}
    gs_figs: Dict[str, str] = {}
    raw_figs_map: Dict[str, str] = {}

    raw_figs = data.get("figures")
    figures: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw_figs, dict):
        for fk, fv in raw_figs.items():
            fk_str = str(fk)
            if isinstance(fv, str):
                uri = fv
                caption = ""
                source = ""
            elif isinstance(fv, dict):
                uri = str(
                    fv.get("data_uri")
                    or fv.get("image_data_uri")
                    or fv.get("uri")
                    or fv.get("src")
                    or ""
                )
                caption = str(fv.get("caption") or fv.get("title") or fv.get("alt") or "")
                source = str(fv.get("source") or "")
            else:
                continue

            if uri.startswith("data:image/"):
                raw_figs_map[fk_str] = uri
                gs_figs[fk_str] = _recompress_image_data_uri(uri)
                raw_to_fig_id[uri] = fk_str
                entry: Dict[str, Any] = {
                    "data_uri": "__GS_FIG__:" + fk_str,
                    "caption": caption,
                }
                if source:
                    entry["source"] = source
                figures[fk_str] = entry
            elif uri:
                entry = {"data_uri": uri, "caption": caption}
                if source:
                    entry["source"] = source
                figures[fk_str] = entry

    next_idx = 1

    def _alloc_fig_id() -> str:
        nonlocal next_idx
        while True:
            cand = f"fig_{next_idx:02d}"
            next_idx += 1
            if cand not in figures and cand not in gs_figs:
                return cand

    for list_key in ITEM_LIST_KEYS:
        raw_list = data.get(list_key)
        if not isinstance(raw_list, list):
            continue
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            direct_uri = item.get("image_data_uri")
            if isinstance(direct_uri, str) and direct_uri.startswith("data:image/"):
                fig_id = raw_to_fig_id.get(direct_uri)
                if not fig_id:
                    existing_id = str(item.get("image_id") or item.get("figure_id") or "").strip()
                    fig_id = existing_id if (existing_id and existing_id not in gs_figs) else _alloc_fig_id()
                    raw_figs_map[fig_id] = direct_uri
                    gs_figs[fig_id] = _recompress_image_data_uri(direct_uri)
                    raw_to_fig_id[direct_uri] = fig_id
                    if fig_id not in figures:
                        figures[fig_id] = {
                            "data_uri": "__GS_FIG__:" + fig_id,
                            "caption": str(item.get("image_caption") or "").strip(),
                        }
                if not item.get("image_id") and not item.get("figure_id"):
                    item["image_id"] = fig_id
            # Strip raw/empty image_data_uri bloat from items; S3 resolves via figures[image_id].
            item.pop("image_data_uri", None)
            if item.get("image_caption") == "":
                item.pop("image_caption", None)

    if figures:
        data["figures"] = figures
    else:
        data.pop("figures", None)

    return gs_figs, raw_figs_map


def _minify_css(css: str) -> str:
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{:;,>~+])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


_REGEX_PREV_TOKENS = frozenset(
    {
        "",
        "(",
        "[",
        "{",
        ",",
        ";",
        ":",
        "=",
        "!",
        "&",
        "|",
        "?",
        "+",
        "-",
        "*",
        "%",
        "<",
        ">",
        "~",
        "^",
        "return",
        "case",
        "else",
        "throw",
        "typeof",
        "void",
        "delete",
        "in",
        "of",
    }
)


def _minify_js_safe(js: str) -> str:
    """Strip JS comments and redundant whitespace while preserving strings, regexes, and ASI."""
    out: List[str] = []
    i = 0
    n = len(js)
    prev_tok = ""
    while i < n:
        c = js[i]
        if c == "/" and i + 1 < n and js[i + 1] == "/":
            i += 2
            while i < n and js[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and js[i + 1] == "*":
            i += 2
            while i + 1 < n and not (js[i] == "*" and js[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c in ("'", '"', "`"):
            q = c
            start = i
            i += 1
            while i < n:
                ch = js[i]
                if ch == "\\":
                    i += 2
                    continue
                if ch == q:
                    i += 1
                    break
                i += 1
            out.append(js[start:i])
            prev_tok = "str"
            continue
        if c in " \t\r\n":
            has_nl = False
            while i < n and js[i] in " \t\r\n":
                if js[i] == "\n":
                    has_nl = True
                i += 1
            if has_nl:
                if out and out[-1] not in ("\n", "{", ";", ","):
                    out.append("\n")
            else:
                if out and out[-1] not in ("\n", " ") and i < n:
                    nxt = js[i]
                    if (out[-1][-1].isalnum() or out[-1][-1] in "_$") and (
                        nxt.isalnum() or nxt in "_$"
                    ):
                        out.append(" ")
                    elif out[-1][-1] in "+-" and nxt in "+-":
                        out.append(" ")
            continue
        if c == "/" and prev_tok in _REGEX_PREV_TOKENS:
            start = i
            i += 1
            in_cc = False
            while i < n:
                ch = js[i]
                if ch == "\\":
                    i += 2
                    continue
                if ch == "[":
                    in_cc = True
                elif ch == "]":
                    in_cc = False
                elif ch == "/" and not in_cc:
                    i += 1
                    while i < n and js[i].isalpha():
                        i += 1
                    break
                elif ch == "\n":
                    break
                i += 1
            out.append(js[start:i])
            prev_tok = "regex"
            continue
        if c.isalnum() or c in "_$":
            start = i
            while i < n and (js[i].isalnum() or js[i] in "_$"):
                i += 1
            tok = js[start:i]
            out.append(tok)
            prev_tok = tok
            continue
        out.append(c)
        prev_tok = c
        i += 1
    return CLOSE_SCRIPT_RE.sub("<\\/script", "".join(out))


def encode_safe_base85(data: bytes) -> Tuple[str, int]:
    """Encode arbitrary bytes into the 85-char HTML/JS-safe alphabet with big-endian uint32."""
    orig_len = len(data)
    if orig_len == 0:
        return "", 0
    rem = orig_len % 4
    padded = data if rem == 0 else data + b"\x00" * (4 - rem)

    alphabet = BASE85_ALPHABET
    chunks: List[str] = []
    for offset in range(0, len(padded), 4):
        val = int.from_bytes(padded[offset : offset + 4], "big")
        val, d4 = divmod(val, 85)
        val, d3 = divmod(val, 85)
        val, d2 = divmod(val, 85)
        d0, d1 = divmod(val, 85)
        chunks.append(
            alphabet[d0] + alphabet[d1] + alphabet[d2] + alphabet[d3] + alphabet[d4]
        )
    return "".join(chunks), orig_len


def _compact_chapter_html(src_html: str) -> Tuple[str, Dict[str, str], Dict[str, str], Dict[str, Any]]:
    """Parse CHAPTER_DATA, externalize figures, and compact HTML/CSS/JS."""
    decoder = json.JSONDecoder()
    scripts_found: List[str] = []

    def _replace_style(match: re.Match[str]) -> str:
        return "<style>" + _minify_css(match.group(1)) + "</style>"

    compacted = STYLE_TAG_RE.sub(_replace_style, src_html)

    extracted_data: Optional[Dict[str, Any]] = None
    gs_figs: Dict[str, str] = {}
    raw_figs_map: Dict[str, str] = {}

    script_idx = 0

    def _replace_script(match: re.Match[str]) -> str:
        nonlocal script_idx, extracted_data, gs_figs, raw_figs_map
        body = match.group(1)
        idx = script_idx
        script_idx += 1
        scripts_found.append(body)

        if idx == 0:
            assign_match = CHAPTER_DATA_ASSIGN_RE.search(body)
            if not assign_match:
                raise ValueError("Script #0 missing window.CHAPTER_DATA assignment")
            parsed_obj, end_idx = decoder.raw_decode(body, assign_match.end())
            if not isinstance(parsed_obj, dict):
                raise ValueError("window.CHAPTER_DATA did not decode to a JSON object")
            extracted_data = parsed_obj
            gs_figs, raw_figs_map = _extract_and_optimize_figures(extracted_data)
            compact_json = _escape_inline_script_json(
                json.dumps(extracted_data, separators=(",", ":"), ensure_ascii=False)
            )
            hydration_js = ""
            if gs_figs:
                hydration_js = (
                    'var _gf=window.__ISH_GS_FIGS__;'
                    'if(_gf&&window.CHAPTER_DATA.figures){'
                    'Object.keys(window.CHAPTER_DATA.figures).forEach(function(k){'
                    'var e=window.CHAPTER_DATA.figures[k];'
                    'if(e&&typeof e==="object"&&typeof e.data_uri==="string"&&'
                    'e.data_uri.indexOf("__GS_FIG__:")===0){'
                    'var fk=e.data_uri.slice(11);'
                    'if(_gf[fk])e.data_uri=_gf[fk];'
                    '}});}'
                )
            tail = body[end_idx:].lstrip()
            if tail.startswith(";"):
                tail = tail[1:]
            tail_min = _minify_js_safe(tail)
            prefix = _minify_js_safe(body[: assign_match.start()])
            prefix_part = (prefix + "\n") if prefix else ""
            tail_part = ("\n" + tail_min) if tail_min else ""
            return (
                "<script>"
                + prefix_part
                + "window.CHAPTER_DATA="
                + compact_json
                + ";"
                + hydration_js
                + tail_part
                + "</script>"
            )

        return "<script>" + _minify_js_safe(body) + "</script>"

    compacted = SCRIPT_TAG_RE.sub(_replace_script, compacted)
    if extracted_data is None:
        raise ValueError("Could not parse window.CHAPTER_DATA from chapter HTML")

    return compacted, gs_figs, raw_figs_map, extracted_data


def _render_bootstrap_shell(
    *,
    title: str,
    b85_payload: str,
    orig_len: int,
    gs_figs: Dict[str, str],
) -> str:
    safe_title = html.escape(title, quote=False)
    figs_stmt = ""
    if gs_figs:
        figs_json = _escape_inline_script_json(
            json.dumps(gs_figs, separators=(",", ":"), ensure_ascii=False)
        )
        figs_stmt = f"window.__ISH_GS_FIGS__={figs_json};"

    boot_js = (
        "(async function(){"
        + figs_stmt
        + f"var L={orig_len};"
        + f'var A="{BASE85_ALPHABET}";'
        + "function showErr(msg){"
        + 'var b=document.getElementById("gs-boot");'
        + 'if(!b){b=document.createElement("div");b.id="gs-boot";document.body.innerHTML="";document.body.appendChild(b);}'
        + 'b.innerHTML="<div style=\\"max-width:520px;padding:20px;border:1px solid #ef4444;border-radius:10px;background:#1e293b;color:#fecaca\\"><strong>Unable to Load Chapter</strong><p style=\\"margin:8px 0 0;font-size:14px;color:#f8fafc\\"></p></div>";'
        + 'var p=b.querySelector("p");if(p)p.textContent=msg;'
        + "}"
        + "try{"
        + 'if(typeof DecompressionStream==="undefined")throw new Error("DecompressionStream API is unsupported in this browser. Please update Chrome or Edge.");'
        + 'var el=document.getElementById("gs-d");'
        + 'var s=el?el.textContent.trim():"";'
        + "var t=new Int16Array(128);t.fill(-1);"
        + "for(var i=0;i<85;i++)t[A.charCodeAt(i)]=i;"
        + "var n=s.length;if(n%5!==0)throw new Error(\"Corrupt embedded payload length.\");"
        + "var u=new Uint8Array((n/5)*4);var p=0;"
        + "for(var i=0;i<n;i+=5){"
        + "var d0=t[s.charCodeAt(i)],d1=t[s.charCodeAt(i+1)],d2=t[s.charCodeAt(i+2)],d3=t[s.charCodeAt(i+3)],d4=t[s.charCodeAt(i+4)];"
        + "if(d0<0||d1<0||d2<0||d3<0||d4<0)throw new Error(\"Corrupt embedded character.\");"
        + "var v=(((d0*85+d1)*85+d2)*85+d3)*85+d4;"
        + "u[p++]=(v>>>24)&255;u[p++]=(v>>>16)&255;u[p++]=(v>>>8)&255;u[p++]=v&255;"
        + "}"
        + "var bytes=u.subarray(0,L);"
        + 'var ds=new DecompressionStream("gzip");'
        + "var htmlStr=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).text();"
        + 'var doc=(new DOMParser()).parseFromString(htmlStr,"text/html");'
        + "if(doc.title)document.title=doc.title;"
        + 'var styles=doc.querySelectorAll("style");'
        + "for(var j=0;j<styles.length;j++){"
        + 'var ns=document.createElement("style");ns.textContent=styles[j].textContent;document.head.appendChild(ns);'
        + "}"
        + 'var bootCss=document.getElementById("gs-boot-css");if(bootCss&&bootCss.parentNode)bootCss.parentNode.removeChild(bootCss);'
        + 'var scs=Array.prototype.slice.call(doc.querySelectorAll("script"));'
        + "for(var k=0;k<scs.length;k++){if(scs[k].parentNode)scs[k].parentNode.removeChild(scs[k]);}"
        + "if(doc.documentElement&&doc.documentElement.className)document.documentElement.className=doc.documentElement.className;"
        + 'document.body.className=(doc.body&&doc.body.className)||"";'
        + "document.body.innerHTML=doc.body?doc.body.innerHTML:\"\";"
        + "for(var k=0;k<scs.length;k++){"
        + 'var sc=document.createElement("script");sc.textContent=scs[k].textContent;document.body.appendChild(sc);'
        + "}"
        + "}catch(err){"
        + 'showErr(err&&err.message?err.message:String(err));'
        + "}"
        + "})();"
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"<title>{safe_title}</title>\n"
        '<style id="gs-boot-css">html,body{margin:0;padding:0;min-height:100%;background:#0b1120;color:#e2e8f0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;}#gs-boot{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:24px;text-align:center;}.gs-sub{color:#94a3b8;font-size:13.5px;}</style>\n'
        "</head>\n"
        "<body>\n"
        '<div id="gs-boot"><div>Loading interactive chapter…</div><div class="gs-sub">MRAC 2025 Self-Contained Study Module</div></div>\n'
        f'<script id="gs-d" type="text/plain">{b85_payload}</script>\n'
        f"<script>{boot_js}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def _extract_quick_chapter_meta(src_path: Path, ch_num: int) -> Tuple[str, str]:
    """Read chapter_title and engine_id cheaply from a chapter HTML."""
    raw = src_path.read_text(encoding="utf-8", errors="replace")
    decoder = json.JSONDecoder()
    assign_match = CHAPTER_DATA_ASSIGN_RE.search(raw)
    if assign_match:
        try:
            obj, _ = decoder.raw_decode(raw, assign_match.end())
            if isinstance(obj, dict):
                title = str(obj.get("chapter_title") or f"Chapter {ch_num:02d}").strip()
                engine_id = str(obj.get("engine_id") or "").strip()
                return title, engine_id
        except json.JSONDecodeError:
            pass
    t_match = TITLE_TAG_RE.search(raw[:4096])
    title = html.unescape(t_match.group(1)).strip() if t_match else f"Chapter {ch_num:02d}"
    return title, ""


def _render_dashboard_html(chapters_meta: Dict[str, Any]) -> str:
    """Build standalone Google_Sites_Chromebook_Chapters.html with zero external URLs."""
    rows: List[Dict[str, Any]] = []
    ready_count = 0
    max_chars = 0

    for ch_num in range(1, 53):
        key = str(ch_num)
        entry = chapters_meta.get(key) if isinstance(chapters_meta.get(key), dict) else {}
        out_file = OUTPUT_DIR / f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html"
        exists = out_file.is_file()
        chars = int(entry.get("chars") or 0)
        if exists and chars <= 0:
            chars = len(out_file.read_text(encoding="utf-8", errors="replace"))
        if not exists:
            chars = 0

        title = str(entry.get("title") or "").strip()
        engine_id = str(entry.get("engine_id") or "").strip()
        if not title:
            src_path = CHAPTERS_SRC_DIR / f"ch{ch_num:02d}.html"
            if src_path.is_file():
                title, engine_id = _extract_quick_chapter_meta(src_path, ch_num)
            else:
                title = f"Chapter {ch_num:02d}"

        if exists and chars > 0:
            ready_count += 1
            if chars > max_chars:
                max_chars = chars

        rows.append(
            {
                "num": ch_num,
                "code": f"Ch {ch_num:02d}",
                "title": title,
                "unit_id": CHAPTER_TO_UNIT[ch_num],
                "engine_label": ENGINE_LABELS.get(
                    engine_id,
                    engine_id.replace("_", " ").title() if engine_id else "Interactive Study",
                ),
                "filename": f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html",
                "href": f"./google_sites_chapters/Ch_{ch_num:02d}_Google_Sites_Chromebook.html",
                "chars": chars,
                "fig_count": int(entry.get("fig_count") or 0),
                "ready": exists and chars > 0,
            }
        )

    rows_json = _escape_inline_script_json(
        json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    )
    units_json = _escape_inline_script_json(
        json.dumps(
            [{"id": u["id"], "label": u["label"], "short_label": u["short_label"]} for u in UNIT_DEFINITIONS],
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )

    max_summary = (
        f"Max {max_chars:,} / {GOOGLE_SITES_CHAR_LIMIT:,} Chars"
        if max_chars > 0
        else f"Under {GOOGLE_SITES_CHAR_LIMIT:,} Chars Each"
    )
    status_banner = (
        f"{ready_count} / 52 Chapters Ready &bull; 0 External Links &bull; {max_summary}"
    )

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="dark light" />
  <title>Google Sites Chromebook Single-HTML Chapters — MRAC 2025</title>
  <script>
    (function () {
      try {
        var raw = window.localStorage.getItem("ish_gs_dash_theme");
        if (raw === "light") document.documentElement.classList.add("theme-light");
      } catch (_e) {}
    })();
  </script>
  <style>
    :root {
      --bg: #070d1a;
      --bg-elev: #0f172a;
      --card: #131f36;
      --card-alt: #182744;
      --border: #253659;
      --border-bright: #385182;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --cyan: #38bdf8;
      --cyan-strong: #0284c7;
      --amber: #f59e0b;
      --emerald: #10b981;
      --coral: #f43f5e;
      --font-sans: "Segoe UI", Roboto, system-ui, -apple-system, sans-serif;
      --font-mono: "Consolas", "SFMono-Regular", Menlo, monospace;
    }
    html.theme-light {
      --bg: #eef2f7;
      --bg-elev: #ffffff;
      --card: #ffffff;
      --card-alt: #f8fafc;
      --border: #cbd5e1;
      --border-bright: #94a3b8;
      --text: #0f172a;
      --muted: #475569;
      --cyan: #0284c7;
      --cyan-strong: #0369a1;
      --amber: #d97706;
      --emerald: #059669;
      --coral: #e11d48;
    }
    *, *::before, *::after { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      line-height: 1.45;
    }
    .wrap {
      max-width: 1380px;
      margin: 0 auto;
      padding: 20px 18px 48px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
      padding: 16px 18px;
      border-radius: 14px;
      background: var(--bg-elev);
      border: 1px solid var(--border);
    }
    .brand {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .kicker {
      font-size: 11.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--cyan);
    }
    h1 {
      margin: 0;
      font-size: clamp(1.2rem, 2.2vw, 1.65rem);
      font-weight: 800;
    }
    .stats-pill {
      display: inline-flex;
      align-items: center;
      padding: 5px 12px;
      border-radius: 999px;
      background: rgba(16, 185, 129, 0.14);
      border: 1px solid rgba(16, 185, 129, 0.42);
      color: var(--emerald);
      font-size: 12.5px;
      font-weight: 700;
      width: fit-content;
      margin-top: 4px;
    }
    .top-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .btn {
      height: 36px;
      padding: 0 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      text-decoration: none;
      white-space: nowrap;
      font-family: inherit;
    }
    .btn:hover { background: var(--card-alt); border-color: var(--border-bright); }
    .btn-primary {
      background: linear-gradient(135deg, var(--cyan), var(--cyan-strong));
      border-color: transparent;
      color: #061224;
    }
    html.theme-light .btn-primary { color: #ffffff; }
    .btn-primary:hover { filter: brightness(1.07); }
    .setup-box {
      padding: 16px 18px;
      border-radius: 12px;
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.12), rgba(16, 185, 129, 0.08));
      border: 1px solid rgba(56, 189, 248, 0.4);
    }
    .setup-box h2 {
      margin: 0 0 8px;
      font-size: 1rem;
      color: var(--text);
    }
    .setup-steps {
      margin: 0;
      padding-left: 20px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 8px 22px;
      font-size: 13px;
      color: var(--text);
    }
    .setup-steps li strong { color: var(--cyan); }
    .toolbar {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .toolbar-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .search-input {
      flex: 1 1 280px;
      max-width: 460px;
      height: 38px;
      padding: 0 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--text);
      font-size: 13.5px;
      font-family: inherit;
    }
    .search-input:focus {
      outline: none;
      border-color: var(--cyan);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16);
    }
    .match-pill {
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--card);
      border: 1px solid var(--border);
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
    }
    .unit-pills {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .unit-pill {
      padding: 6px 11px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--card);
      color: var(--muted);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      font-family: inherit;
    }
    .unit-pill.active {
      background: rgba(56, 189, 248, 0.16);
      border-color: var(--cyan);
      color: var(--cyan);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
      gap: 13px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 9px;
    }
    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      flex-wrap: wrap;
    }
    .badges {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .ch-code {
      padding: 2px 8px;
      border-radius: 6px;
      background: rgba(56, 189, 248, 0.16);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: var(--cyan);
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 800;
    }
    .engine-badge {
      padding: 2px 8px;
      border-radius: 6px;
      background: var(--card-alt);
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }
    .char-badge {
      padding: 2px 8px;
      border-radius: 999px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      border: 1px solid rgba(16, 185, 129, 0.42);
      background: rgba(16, 185, 129, 0.14);
      color: var(--emerald);
    }
    .char-badge.over {
      border-color: rgba(245, 158, 11, 0.55);
      background: rgba(245, 158, 11, 0.16);
      color: var(--amber);
    }
    .char-badge.pending {
      border-color: var(--border);
      background: var(--bg-elev);
      color: var(--muted);
    }
    .card-title {
      margin: 0;
      font-size: 15px;
      font-weight: 800;
      line-height: 1.3;
    }
    .card-meta {
      font-size: 12px;
      color: var(--muted);
      font-family: var(--font-mono);
    }
    .card-actions {
      margin-top: auto;
      padding-top: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .card-actions .btn-primary { flex: 1 1 140px; }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(2, 6, 23, 0.72);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 100;
    }
    .modal-backdrop.hidden { display: none; }
    .modal {
      width: min(760px, 100%);
      max-height: 90vh;
      background: var(--bg-elev);
      border: 1px solid var(--border-bright);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .modal-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .modal-head h3 { margin: 0; font-size: 1rem; }
    .modal textarea {
      width: 100%;
      min-height: 220px;
      resize: vertical;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 11.5px;
      padding: 10px;
    }
    .modal-note {
      margin: 0;
      font-size: 13px;
      color: var(--muted);
    }
    .modal-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .toast {
      position: fixed;
      bottom: 18px;
      right: 18px;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--card);
      border: 1px solid var(--border-bright);
      border-left: 4px solid var(--emerald);
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
      z-index: 120;
    }
    .toast.hidden { display: none; }
  </style>
</head>
<body>
  <div class="wrap">
    <header class="topbar">
      <div class="brand">
        <span class="kicker">School Chromebook Filter-Proof Embeds</span>
        <h1>Google Sites Single-HTML Chapters (Ch 01–52)</h1>
        <div class="stats-pill" id="stats-pill">__STATUS_BANNER__</div>
      </div>
      <div class="top-actions">
        <button type="button" class="btn" id="btn-theme">☀️ Light</button>
        <a class="btn" href="./index.html">← Back to Study Hub</a>
      </div>
    </header>

    <section class="setup-box" aria-label="Google Sites Chromebook Setup Guide">
      <h2>4-Step Google Sites Chromebook Setup (No github.io Domain Required)</h2>
      <ol class="setup-steps">
        <li><strong>1. Copy or Download:</strong> Click <em>📋 Copy Embed HTML</em> on any chapter card below (or click <em>⬇️ Download HTML</em>).</li>
        <li><strong>2. Add Google Sites Embed:</strong> Open your Google Site, choose <em>Pages → + → Full page embed → Add custom code</em> (or <em>Insert → Embed → Embed code</em>).</li>
        <li><strong>3. Paste &amp; Insert:</strong> Paste the single-file HTML code (under 200,000 characters) and click <em>Next → Insert</em>.</li>
        <li><strong>4. Publish:</strong> Publish your Google Site — every chapter runs 100% inline from Google Sites even when <code>github.io</code> is blocked on student Chromebooks.</li>
      </ol>
    </section>

    <section class="toolbar" aria-label="Filter and search chapters">
      <div class="toolbar-row">
        <input id="dash-search" class="search-input" type="search" placeholder="Search chapter number, title, or simulator..." aria-label="Search chapters" />
        <span id="dash-match" class="match-pill">52 of 52 chapters</span>
      </div>
      <div id="unit-pills" class="unit-pills" role="tablist" aria-label="Filter by curriculum unit"></div>
    </section>

    <main id="chapters-grid" class="grid"></main>
  </div>

  <div id="copy-modal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="copy-modal-title">
    <div class="modal">
      <div class="modal-head">
        <h3 id="copy-modal-title">Copy Google Sites Embed HTML</h3>
        <button type="button" class="btn" id="btn-modal-close">✕ Close</button>
      </div>
      <p id="copy-modal-note" class="modal-note"></p>
      <textarea id="copy-modal-text" readonly spellcheck="false" placeholder="HTML embed code appears here..."></textarea>
      <div class="modal-actions">
        <button type="button" class="btn btn-primary" id="btn-modal-copy">📋 Copy All Text</button>
        <a id="btn-modal-download" class="btn" href="#" download>⬇️ Download HTML File</a>
        <label class="btn" id="lbl-modal-file">
          📂 Load Downloaded File
          <input id="input-modal-file" type="file" accept=".html,text/html" hidden />
        </label>
      </div>
    </div>
  </div>

  <div id="toast" class="toast hidden" role="status" aria-live="polite"></div>

  <script>
    (function () {
      "use strict";
      var CHAPTERS = __ROWS_JSON__;
      var UNITS = __UNITS_JSON__;
      var LIMIT = __CHAR_LIMIT__;

      var activeUnit = "all";
      var searchText = "";
      var toastTimer = null;

      var gridEl = document.getElementById("chapters-grid");
      var unitPillsEl = document.getElementById("unit-pills");
      var searchEl = document.getElementById("dash-search");
      var matchEl = document.getElementById("dash-match");
      var themeBtn = document.getElementById("btn-theme");
      var modalEl = document.getElementById("copy-modal");
      var modalTitleEl = document.getElementById("copy-modal-title");
      var modalNoteEl = document.getElementById("copy-modal-note");
      var modalTextEl = document.getElementById("copy-modal-text");
      var modalCopyBtn = document.getElementById("btn-modal-copy");
      var modalDlLink = document.getElementById("btn-modal-download");
      var modalFileInput = document.getElementById("input-modal-file");
      var modalCloseBtn = document.getElementById("btn-modal-close");
      var toastEl = document.getElementById("toast");

      function esc(s) {
        return String(s == null ? "" : s)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }

      function showToast(msg) {
        toastEl.textContent = msg;
        toastEl.classList.remove("hidden");
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
          toastEl.classList.add("hidden");
        }, 3000);
      }

      function syncThemeBtn() {
        var isLight = document.documentElement.classList.contains("theme-light");
        themeBtn.textContent = isLight ? "🌙 Dark" : "☀️ Light";
      }

      themeBtn.addEventListener("click", function () {
        var isLight = document.documentElement.classList.toggle("theme-light");
        try {
          window.localStorage.setItem("ish_gs_dash_theme", isLight ? "light" : "dark");
        } catch (_e) {}
        syncThemeBtn();
      });
      syncThemeBtn();

      function renderUnitPills() {
        var html = [
          '<button type="button" class="unit-pill' + (activeUnit === "all" ? " active" : "") + '" data-unit="all">All (52)</button>'
        ];
        UNITS.forEach(function (u) {
          html.push(
            '<button type="button" class="unit-pill' + (activeUnit === u.id ? " active" : "") + '" data-unit="' + esc(u.id) + '" title="' + esc(u.label) + '">' + esc(u.short_label) + "</button>"
          );
        });
        unitPillsEl.innerHTML = html.join("");
      }

      function renderGrid() {
        var q = searchText.trim().toLowerCase();
        var filtered = CHAPTERS.filter(function (ch) {
          if (activeUnit !== "all" && ch.unit_id !== activeUnit) return false;
          if (!q) return true;
          var hay = (ch.code + " ch" + ch.num + " chapter " + ch.num + " " + ch.title + " " + ch.engine_label).toLowerCase();
          return hay.indexOf(q) !== -1;
        });

        matchEl.textContent = filtered.length + " of " + CHAPTERS.length + " chapters";

        gridEl.innerHTML = filtered.map(function (ch) {
          var badgeCls = !ch.ready ? "char-badge pending" : (ch.chars >= LIMIT ? "char-badge over" : "char-badge");
          var badgeText = !ch.ready
            ? "Not built yet"
            : (ch.chars.toLocaleString() + " / " + LIMIT.toLocaleString() + " chars");
          var figsNote = ch.fig_count > 0 ? (" • " + ch.fig_count + " figure" + (ch.fig_count === 1 ? "" : "s")) : "";

          return (
            '<article class="card">' +
              '<div class="card-top">' +
                '<div class="badges">' +
                  '<span class="ch-code">' + esc(ch.code) + "</span>" +
                  '<span class="engine-badge">' + esc(ch.engine_label) + "</span>" +
                "</div>" +
                '<span class="' + badgeCls + '">' + esc(badgeText) + "</span>" +
              "</div>" +
              '<h3 class="card-title">' + esc(ch.title) + "</h3>" +
              '<div class="card-meta">' + esc(ch.filename) + esc(figsNote) + "</div>" +
              '<div class="card-actions">' +
                '<button type="button" class="btn btn-primary" data-copy-ch="' + ch.num + '"' + (ch.ready ? "" : " disabled") + ">📋 Copy Embed HTML</button>" +
                '<a class="btn" href="' + esc(ch.href) + '" download="' + esc(ch.filename) + '">⬇️ Download HTML</a>' +
              "</div>" +
            "</article>"
          );
        }).join("");
      }

      function openCopyModal(ch, text, note) {
        modalTitleEl.textContent = ch.code + " — " + ch.title;
        modalNoteEl.textContent = note;
        modalTextEl.value = text || "";
        modalDlLink.href = ch.href;
        modalDlLink.setAttribute("download", ch.filename);
        modalEl.classList.remove("hidden");
        if (text) {
          modalTextEl.focus();
          modalTextEl.select();
        }
      }

      async function handleCopyChapter(chNum) {
        var ch = CHAPTERS.find(function (c) { return c.num === chNum; });
        if (!ch) return;
        try {
          var resp = await fetch(ch.href, { cache: "no-store" });
          if (!resp.ok) throw new Error("HTTP " + resp.status);
          var text = await resp.text();
          try {
            await navigator.clipboard.writeText(text);
            showToast("Copied " + ch.code + " (" + text.length.toLocaleString() + " chars) — paste into Google Sites!");
            return;
          } catch (_clipErr) {
            openCopyModal(
              ch,
              text,
              "Automatic clipboard access was blocked by the browser. Click Copy All Text below or press Ctrl+C."
            );
          }
        } catch (_fetchErr) {
          openCopyModal(
            ch,
            "",
            "Direct file fetch is blocked in offline file:// mode. Click Download HTML File below (or open " +
              ch.filename +
              "), then load it here or select-all & copy its contents into Google Sites."
          );
        }
      }

      unitPillsEl.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-unit]");
        if (!btn) return;
        activeUnit = btn.getAttribute("data-unit") || "all";
        renderUnitPills();
        renderGrid();
      });

      searchEl.addEventListener("input", function () {
        searchText = searchEl.value || "";
        renderGrid();
      });

      gridEl.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-copy-ch]");
        if (!btn) return;
        handleCopyChapter(Number(btn.getAttribute("data-copy-ch")));
      });

      modalCopyBtn.addEventListener("click", async function () {
        if (!modalTextEl.value) {
          showToast("Download or load the HTML file first.");
          return;
        }
        modalTextEl.focus();
        modalTextEl.select();
        try {
          await navigator.clipboard.writeText(modalTextEl.value);
          showToast("Copied embed HTML to clipboard!");
          return;
        } catch (_e) {}
        try {
          if (document.execCommand("copy")) {
            showToast("Copied embed HTML to clipboard!");
            return;
          }
        } catch (_e2) {}
        showToast("Press Ctrl+C to copy the selected text.");
      });

      modalFileInput.addEventListener("change", function () {
        var file = modalFileInput.files && modalFileInput.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
          modalTextEl.value = String(reader.result || "");
          modalTextEl.focus();
          modalTextEl.select();
          showToast("Loaded " + file.name + " — click Copy All Text.");
        };
        reader.readAsText(file);
        modalFileInput.value = "";
      });

      modalCloseBtn.addEventListener("click", function () {
        modalEl.classList.add("hidden");
      });
      modalEl.addEventListener("click", function (e) {
        if (e.target === modalEl) modalEl.classList.add("hidden");
      });

      renderUnitPills();
      renderGrid();
    })();
  </script>
</body>
</html>
"""

    rendered = (
        template.replace("__STATUS_BANNER__", status_banner)
        .replace("__ROWS_JSON__", rows_json)
        .replace("__UNITS_JSON__", units_json)
        .replace("__CHAR_LIMIT__", str(GOOGLE_SITES_CHAR_LIMIT))
    )
    if URL_RE.search(rendered):
        raise AssertionError("Google_Sites_Chromebook_Chapters.html unexpectedly contains http(s):// URL")
    return rendered


def build_all_google_sites_chapters(
    force: bool = False,
    chapters: Optional[Sequence[int]] = None,
    allow_over_limit: bool = False,
) -> Dict[str, Any]:
    """Build compact single-HTML Google Sites files for MRAC chapters + copy dashboard."""
    if chapters is not None:
        target_chapters = sorted({int(c) for c in chapters if 1 <= int(c) <= 52})
    else:
        target_chapters = list(range(1, 53))

    script_sha256 = _sha256_file(Path(__file__).resolve())

    existing_manifest: Dict[str, Any] = {}
    if EMBED_MANIFEST_PATH.is_file():
        try:
            loaded = json.loads(EMBED_MANIFEST_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing_manifest = loaded
        except (OSError, json.JSONDecodeError):
            existing_manifest = {}

    stored_script_ver = existing_manifest.get("script_version")
    stored_script_sha = existing_manifest.get("script_sha256")
    script_unchanged = (
        stored_script_ver == SCRIPT_VERSION and stored_script_sha == script_sha256
    )

    stored_chapters = existing_manifest.get("chapters")
    chapters_meta: Dict[str, Any] = (
        dict(stored_chapters) if isinstance(stored_chapters, dict) else {}
    )

    built_chapters: List[int] = []
    skipped_chapters: List[int] = []
    manifest_dirty = not EMBED_MANIFEST_PATH.is_file() or not script_unchanged

    for ch_num in target_chapters:
        src_path = CHAPTERS_SRC_DIR / f"ch{ch_num:02d}.html"
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing source chapter HTML: {src_path}")

        out_path = OUTPUT_DIR / f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html"
        key = str(ch_num)
        prev_entry = chapters_meta.get(key) if isinstance(chapters_meta.get(key), dict) else None

        src_stat = src_path.stat()
        src_sha256: Optional[str] = None

        can_skip = False
        if not force and script_unchanged and prev_entry is not None and out_path.is_file():
            if (
                prev_entry.get("src_size") == src_stat.st_size
                and abs(float(prev_entry.get("src_mtime", -1.0)) - src_stat.st_mtime) <= 0.01
                and out_path.stat().st_size > 0
            ):
                can_skip = True
            else:
                src_sha256 = _sha256_file(src_path)
                if prev_entry.get("src_sha256") == src_sha256 and out_path.stat().st_size > 0:
                    # Source mtime drifted without content change; refresh cached mtime once.
                    prev_entry["src_mtime"] = src_stat.st_mtime
                    prev_entry["src_size"] = src_stat.st_size
                    manifest_dirty = True
                    can_skip = True

        if can_skip:
            skipped_chapters.append(ch_num)
            continue

        src_bytes = src_path.read_bytes()
        if src_sha256 is None:
            src_sha256 = _sha256_bytes(src_bytes)
        src_text = src_bytes.decode("utf-8", errors="replace")

        compact_inner, gs_figs, raw_figs_map, data = _compact_chapter_html(src_text)
        gz_bytes = gzip.compress(compact_inner.encode("utf-8"), compresslevel=9)
        b85_payload, orig_len = encode_safe_base85(gz_bytes)

        ch_title = str(data.get("chapter_title") or f"Chapter {ch_num:02d}").strip()
        engine_id = str(data.get("engine_id") or "").strip()
        shell_title = f"Ch {ch_num:02d} — {ch_title} (Google Sites)"
        out_html = _render_bootstrap_shell(
            title=shell_title,
            b85_payload=b85_payload,
            orig_len=orig_len,
            gs_figs=gs_figs,
        )

        # If multi-figure chapters approach the 195k budget, adaptively switch figures to compact WebP.
        if gs_figs and raw_figs_map and len(out_html) >= 188_000:
            for fmt, dim, q in (("WEBP", 440, 50), ("WEBP", 380, 42), ("WEBP", 320, 36)):
                alt_figs = {
                    fk: _recompress_image_data_uri(raw_u, fmt=fmt, max_dim=dim, quality=q)
                    for fk, raw_u in raw_figs_map.items()
                }
                alt_html = _render_bootstrap_shell(
                    title=shell_title,
                    b85_payload=b85_payload,
                    orig_len=orig_len,
                    gs_figs=alt_figs,
                )
                if len(alt_html) < len(out_html):
                    gs_figs = alt_figs
                    out_html = alt_html
                if len(out_html) < 188_000:
                    break

        if URL_RE.search(out_html):
            raise AssertionError(
                f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html contains external http(s):// URL"
            )

        char_count = len(out_html)
        if char_count >= MAX_EMBED_CHARS and not allow_over_limit:
            raise AssertionError(
                f"Ch_{ch_num:02d}_Google_Sites_Chromebook.html is {char_count:,} chars "
                f"(>= {MAX_EMBED_CHARS:,} limit; run upstream rebuild or pass allow_over_limit=True)"
            )

        out_bytes = out_html.encode("utf-8")
        out_sha256 = _sha256_bytes(out_bytes)
        if not out_path.is_file() or _sha256_file(out_path) != out_sha256:
            _atomic_write_text(out_path, out_html)
            built_chapters.append(ch_num)
        else:
            skipped_chapters.append(ch_num)

        chapters_meta[key] = {
            "src_sha256": src_sha256,
            "src_mtime": src_stat.st_mtime,
            "src_size": src_stat.st_size,
            "out_sha256": out_sha256,
            "chars": char_count,
            "raw_bytes": len(src_bytes),
            "gz_bytes": orig_len,
            "fig_count": len(gs_figs),
            "title": ch_title,
            "engine_id": engine_id,
        }
        manifest_dirty = True

    manifest_written = False
    if manifest_dirty:
        ordered_chapters = {
            str(k): chapters_meta[str(k)]
            for k in sorted((int(c) for c in chapters_meta.keys()), key=int)
        }
        new_manifest = {
            "script_version": SCRIPT_VERSION,
            "script_sha256": script_sha256,
            "chapters": ordered_chapters,
        }
        _atomic_write_text(
            EMBED_MANIFEST_PATH,
            json.dumps(new_manifest, indent=2, ensure_ascii=False) + "\n",
        )
        manifest_written = True
        chapters_meta = ordered_chapters

    dashboard_written = False
    if built_chapters or manifest_written or force or not DASHBOARD_PATH.is_file():
        dash_html = _render_dashboard_html(chapters_meta)
        dash_sha = _sha256_bytes(dash_html.encode("utf-8"))
        if not DASHBOARD_PATH.is_file() or _sha256_file(DASHBOARD_PATH) != dash_sha:
            _atomic_write_text(DASHBOARD_PATH, dash_html)
            dashboard_written = True

    char_counts = [
        int(chapters_meta[str(ch)]["chars"])
        for ch in target_chapters
        if str(ch) in chapters_meta and isinstance(chapters_meta[str(ch)], dict)
    ]
    return {
        "built": built_chapters,
        "skipped": skipped_chapters,
        "manifest_written": manifest_written,
        "dashboard_written": dashboard_written,
        "changed_count": len(built_chapters)
        + (1 if manifest_written else 0)
        + (1 if dashboard_written else 0),
        "min_chars": min(char_counts) if char_counts else 0,
        "median_chars": int(statistics.median(char_counts)) if char_counts else 0,
        "max_chars": max(char_counts) if char_counts else 0,
        "chapters": {str(ch): chapters_meta.get(str(ch)) for ch in target_chapters},
    }


def _parse_chapters_arg(raw: Optional[str]) -> Optional[List[int]]:
    if not raw:
        return None
    cleaned = raw.strip().lower()
    if cleaned in ("all", "*"):
        return None
    result: List[int] = []
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
                    result.append(ch)
        else:
            ch = int(tok)
            if 1 <= ch <= 52:
                result.append(ch)
    return sorted(set(result))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build compact (<195KB) single-HTML Google Sites Chromebook chapters."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuilding target chapter files even if source SHA-256 matches.",
    )
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Comma/range list of chapter numbers (e.g. '1,11' or '1-5'). Defaults to all 1..52.",
    )
    parser.add_argument(
        "--allow-over-limit",
        action="store_true",
        help="Allow outputting chapters >= 195,000 chars (diagnostic mode before upstream rebuild).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_stdio()
    args = build_arg_parser().parse_args(list(argv) if argv is not None else None)
    selected = _parse_chapters_arg(args.chapters)
    res = build_all_google_sites_chapters(
        force=args.force,
        chapters=selected,
        allow_over_limit=args.allow_over_limit,
    )
    print(
        f"[OK] Google Sites Chromebook chapters: built={len(res['built'])}, "
        f"skipped={len(res['skipped'])}, dashboard_written={res['dashboard_written']}, "
        f"chars(min={res['min_chars']:,}, median={res['median_chars']:,}, max={res['max_chars']:,})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
