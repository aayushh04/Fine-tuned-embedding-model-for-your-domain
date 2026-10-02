"""Structure-aware chunking: split markdown into blocks, then pack blocks into chunks.

A block is a paragraph, a heading, or a whole fenced code block, so chunks never cut a
sentence or a code example in half unless the block itself is longer than a chunk.
Each chunk is prefixed with a breadcrumb ("FastAPI > Request Body > Declare it ...")
so it stays understandable on its own, both to the embedder and to the question writer.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Callable

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
BREADCRUMB_RESERVE = 48  # tokens kept free in each chunk for the breadcrumb line (p99 length)

CountFn = Callable[[str], int]


@dataclass
class Block:
    text: str
    kind: str                 # "heading" | "text" | "code"
    level: int = 0            # heading level (1-6) for headings
    path: tuple[str, ...] = ()  # heading path this block lives under
    n_tokens: int = 0


def parse_blocks(md: str, default_title: str) -> list[Block]:
    """Split markdown into heading / paragraph / code blocks, tracking the heading path."""
    blocks: list[Block] = []
    path: list[tuple[int, str]] = [(1, default_title)]  # replaced if the doc has an H1
    buf: list[str] = []
    fence: str | None = None

    def current_path() -> tuple[str, ...]:
        return tuple(t for _, t in path)

    def flush(kind: str = "text") -> None:
        if buf and "".join(buf).strip():
            blocks.append(Block("\n".join(buf).strip("\n"), kind, path=current_path()))
        buf.clear()

    for line in md.split("\n"):
        if fence is not None:
            buf.append(line)
            if line.strip() == fence:
                fence = None
                flush("code")
            continue
        m = FENCE_OPEN.match(line)
        if m:
            flush()
            fence = m.group(1)
            buf.append(line)
            continue
        h = HEADING.match(line)
        if h:
            flush()
            level, title = len(h.group(1)), h.group(2).strip()
            path = [(l, t) for l, t in path if l < level] + [(level, title)]
            blocks.append(Block(f"{h.group(1)} {title}", "heading", level, current_path()))
            continue
        if not line.strip():
            flush()
        else:
            buf.append(line)
    flush("code" if fence is not None else "text")
    return blocks


# Successively finer split points for over-long text: lines, then sentences, then words.
SPLIT_LEVELS = (r"[^\n]*\n?", r"[^.!?\n]*[.!?]+\s*|[^.!?\n]+\s*", r"\S+\s*")


def _pack(text: str, budget: int, count: CountFn, levels: tuple[str, ...] = SPLIT_LEVELS) -> list[str]:
    """Cut text into pieces of at most `budget` tokens at the coarsest possible boundary."""
    if count(text) <= budget or not levels:
        return [text]
    pieces, cur = [], ""
    for unit in (u for u in re.findall(levels[0], text) if u):
        if count(unit) > budget:
            if cur.strip():
                pieces.append(cur)
            cur = ""
            pieces.extend(_pack(unit, budget, count, levels[1:]))
            continue
        if cur and count(cur + unit) > budget:
            pieces.append(cur)
            cur = ""
        cur += unit
    if cur.strip():
        pieces.append(cur)
    return [p.strip("\n") for p in pieces if p.strip()]


def _split_long(block: Block, budget: int, count: CountFn) -> list[Block]:
    """Split a block into pieces that fit the budget; code pieces are re-fenced."""
    if block.kind == "code":
        lines = block.text.split("\n")
        open_line = lines[0]
        has_close = len(lines) > 1 and FENCE_OPEN.match(lines[-1]) is not None
        close_line = lines[-1] if has_close else open_line.strip()[:3]
        inner = "\n".join(lines[1:-1] if has_close else lines[1:])
        overhead = count(f"{open_line}\n\n{close_line}")
        pieces = [f"{open_line}\n{p}\n{close_line}" for p in _pack(inner, budget - overhead, count)]
    else:
        pieces = _pack(block.text, budget, count)
    return [Block(p, block.kind, block.level, block.path, count(p)) for p in pieces]


def chunk_blocks(
    blocks: list[Block],
    count: CountFn,
    chunk_size: int,
    overlap: int,
    min_tokens: int,
) -> list[tuple[tuple[str, ...], str]]:
    """Greedily pack blocks into chunks. Returns (section_path, body) pairs.

    - A new H1/H2 section starts a new chunk (if the current one is big enough), so
      chunks rarely mix unrelated topics.
    - When a chunk overflows, up to `overlap` tokens of trailing blocks are repeated at
      the start of the next one (light overlap), and dangling headings move forward.
    - A too-small final chunk is merged into the previous one, or dropped.
    """
    budget = chunk_size - BREADCRUMB_RESERVE
    for b in blocks:
        b.n_tokens = count(b.text)

    chunks: list[tuple[tuple[str, ...], list[Block]]] = []
    cur: list[Block] = []

    def size(bs: list[Block]) -> int:
        return sum(b.n_tokens for b in bs)

    def emit(bs: list[Block]) -> None:
        content = [b for b in bs if b.kind != "heading"]
        if content:
            chunks.append((content[0].path, list(bs)))

    for block in blocks:
        if block.kind == "heading" and block.level <= 2 and size(cur) >= min_tokens:
            emit(cur)
            cur = []
        queue = deque([block] if block.n_tokens <= budget else _split_long(block, budget, count))
        while queue:
            piece = queue.popleft()
            room = budget - size(cur)
            if cur and piece.n_tokens > room and size(cur) < min_tokens \
                    and room >= min_tokens and piece.kind != "heading":
                # a small chunk (e.g. "Here are the types you can use:") would be orphaned;
                # take the head of the next block into it instead
                parts = _split_long(piece, room, count)
                if len(parts) > 1 and parts[0].n_tokens <= room:
                    cur.append(parts[0])
                    queue.extendleft(reversed(parts[1:]))
                    continue
            if cur and piece.n_tokens > room:
                # headings at the end of a full chunk belong to the next chunk
                tail = []
                while cur and cur[-1].kind == "heading":
                    tail.insert(0, cur.pop())
                emit(cur)
                carry: list[Block] = []
                for b in reversed(cur):
                    if b.kind == "heading" or size(carry) + b.n_tokens > overlap:
                        break
                    carry.insert(0, b)
                cur = carry + tail
                if size(cur) + piece.n_tokens > budget:
                    cur = tail
            cur.append(piece)

    if cur:
        if size(cur) < min_tokens and chunks and size(chunks[-1][1]) + size(cur) <= budget:
            chunks[-1][1].extend(cur)
        elif size(cur) >= min_tokens:
            emit(cur)

    out = []
    for path, bs in chunks:
        # the breadcrumb already names the section, so drop a heading that opens the chunk
        while bs and bs[0].kind == "heading":
            bs = bs[1:]
        out.append((path, "\n\n".join(b.text for b in bs)))
    return out


def make_chunk_text(label: str, path: tuple[str, ...], body: str) -> str:
    return f"{' > '.join((label,) + path)}\n\n{body}"
