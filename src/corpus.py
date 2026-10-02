"""Download pinned documentation releases and turn their markdown into clean text.

Docs are read straight out of the GitHub release zip (no extraction), so the raw
corpus is a single cached file per source.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Optional

import requests


@dataclass
class RawDoc:
    doc_id: str      # "<source>/<path without .md>", e.g. "fastapi/tutorial/body"
    source: str
    path: str        # path relative to the source's docs_dir
    text: str        # cleaned markdown


# ---------------------------------------------------------------- download

def download_source(source: dict, raw_dir: Path) -> Path:
    """Download the source's release zip once and return its local path."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / f"{source['name']}-{source['ref']}.zip"
    if not zip_path.exists():
        url = f"https://codeload.github.com/{source['repo']}/zip/refs/tags/{source['ref']}"
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        zip_path.write_bytes(resp.content)
    return zip_path


def iter_docs(source: dict, zip_path: Path, missing_includes: Optional[list] = None) -> Iterator[RawDoc]:
    """Yield cleaned markdown docs from the zip, in sorted (deterministic) order.

    Include paths that cannot be resolved are appended to `missing_includes`, so the
    caller can fail loudly instead of silently losing code examples.
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        top = next(iter(names)).split("/")[0]  # GitHub zips have one top-level dir
        docs_prefix = f"{top}/{source['docs_dir'].strip('/')}/"
        include_base = f"{top}/{source.get('include_base', source['docs_dir']).strip('/')}"

        def read_text(zip_name: str) -> Optional[str]:
            if zip_name not in names:
                return None
            return zf.read(zip_name).decode("utf-8", errors="replace")

        def read_include(path: str) -> Optional[str]:
            resolved = posixpath.normpath(posixpath.join(include_base, path))
            text = read_text(resolved)
            if text is None and missing_includes is not None:
                missing_includes.append(resolved)
            return text

        for name in sorted(names):
            if not name.startswith(docs_prefix) or not name.endswith(".md"):
                continue
            rel = name[len(docs_prefix):]
            if any(fnmatch.fnmatch(rel, pat) for pat in source.get("exclude", [])):
                continue
            text = clean_markdown(read_text(name) or "", read_include)
            yield RawDoc(
                doc_id=f"{source['name']}/{rel[:-3]}",
                source=source["name"],
                path=rel,
                text=text,
            )


# ---------------------------------------------------------------- cleaning

INCLUDE_STAR = re.compile(r"^\{\*\s+(\S+).*\*\}\s*$")        # FastAPI: {* ../../docs_src/x.py hl[3] *}
INCLUDE_BANG = re.compile(r"^\{!>?\s*(\S+?)\s*!\}\s*$")      # FastAPI: {!> ../../docs_src/x.py!}
FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+#.-]*).*$")
# mkdocs-material admonitions / content tabs; "===(?=\s)" so "=====" heading underlines don't match
INDENTED_BLOCK = re.compile(r'^( *)(!!!|\?\?\?\+?|===(?=\s))\s*(\S+)')
LANG_BY_EXT = {".py": "python", ".js": "javascript", ".ts": "typescript", ".json": "json",
               ".toml": "toml", ".sh": "bash", ".html": "html", ".txt": ""}


def clean_markdown(text: str, read_include: Callable[[str], Optional[str]]) -> str:
    """Strip doc-site syntax so the text reads like plain markdown a user would see."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)   # front matter
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)          # HTML comments
    lines = text.split("\n")
    lines = _process_indented_blocks(lines)
    lines = _keep_first_tab(lines)
    lines = _expand_includes(lines, read_include)
    lines = _clean_inline(lines)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _take_indented(lines: list[str], i: int, indent: str) -> tuple[list[str], int]:
    """Collect the body indented 4 spaces past `indent`, starting at lines[i].

    Returns the body re-indented to `indent` (so blocks nested in list items stay in the
    list) and the index of the first line after the body.
    """
    inner = indent + "    "
    body = []
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith(inner)):
        body.append(indent + lines[i][len(inner):] if lines[i].strip() else "")
        i += 1
    return body, i


def _process_indented_blocks(lines: list[str]) -> list[str]:
    """Handle mkdocs-material `!!! note`, `??? api` and `=== "tab"` blocks (Pydantic docs).

    Admonitions are unwrapped, API-reference callouts dropped, and in a group of
    content tabs only the first tab is kept (the others repeat it for other Python versions).
    """
    out: list[str] = []
    i, prev_was_tab = 0, False
    while i < len(lines):
        m = INDENTED_BLOCK.match(lines[i])
        if not m:
            if lines[i].strip():
                prev_was_tab = False
            out.append(lines[i])
            i += 1
            continue
        indent, marker, kind = m.groups()
        body, i = _take_indented(lines, i + 1, indent)
        body = _process_indented_blocks(body)
        if marker == "===":
            if not prev_was_tab:
                out.extend(body)
            prev_was_tab = True
        elif kind != "api":
            out.extend(body)
            prev_was_tab = False
    return out


def _keep_first_tab(lines: list[str]) -> list[str]:
    """FastAPI `//// tab | Python 3.10+` ... `////` groups: keep the first tab only.

    Also drops FastAPI admonition fences (`/// tip`, `///`) while keeping their content.
    """
    out: list[str] = []
    i, prev_was_tab = 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith("//// tab"):
            i += 1
            body = []
            while i < len(lines) and lines[i].strip() != "////":
                body.append(lines[i])
                i += 1
            i += 1  # skip closing ////
            if not prev_was_tab:
                out.extend(body)
            prev_was_tab = True
            continue
        if line.strip():
            prev_was_tab = False
        if re.match(r"^///(?!/)", line):
            i += 1
            continue
        out.append(line)
        i += 1
    return [l for l in out if not re.match(r"^///(?!/)", l)]


def _expand_includes(lines: list[str], read_include: Callable[[str], Optional[str]]) -> list[str]:
    """Inline code that FastAPI pulls in from docs_src/ so chunks contain the real examples."""
    out: list[str] = []
    for line in lines:
        star, bang = INCLUDE_STAR.match(line.strip()), INCLUDE_BANG.match(line.strip())
        if not (star or bang):
            out.append(line)
            continue
        path = (star or bang).group(1)
        code = read_include(path)
        if code is None:
            continue
        code = code.rstrip("\n")
        if star:  # {* *} renders its own code block; {! !} is already inside a fence
            lang = LANG_BY_EXT.get(posixpath.splitext(path)[1], "")
            out.extend([f"```{lang}", code, "```"])
        else:
            out.append(code)
    return out


def _clean_inline(lines: list[str]) -> list[str]:
    """Clean links/HTML/attributes outside code fences; normalise fence info strings."""
    out: list[str] = []
    fence: Optional[str] = None
    fence_lang = ""
    for line in lines:
        m = FENCE_OPEN.match(line)
        if fence is None and m:
            indent, fence, fence_lang = m.groups()
            fence_lang = fence_lang.lower()
            out.append(f"{indent}{fence}{fence_lang}")
            continue
        if fence is not None:
            if line.strip() == fence:
                fence = None
            elif fence_lang == "console":  # terminal output is colourised with <span> tags
                line = re.sub(r"</?span[^>]*>", "", line)
            out.append(line)
            continue
        if line.startswith("::: "):        # mkdocstrings API directive
            continue
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)             # images
        line = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", line)         # [text][autoref]
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)          # [text](url)
        line = re.sub(r"<[^>\n]+>", "", line)                          # HTML tags
        line = re.sub(r"\{\s*[:.#][^}]*\}", "", line)                  # attr lists { .annotate }
        out.append(line.rstrip())
    return out
