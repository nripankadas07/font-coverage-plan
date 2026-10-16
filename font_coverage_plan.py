"""Inspect SFNT cmap coverage and build a deterministic greedy font fallback plan."""
from __future__ import annotations

import argparse
import bisect
import json
import struct
import sys
import unicodedata
from collections import Counter
from pathlib import Path

MAX_FONT = 32 * 1024 * 1024
PREFERENCE = ((3, 10), (0, 6), (0, 4), (3, 1), (0, 3), (0, 2), (0, 1), (0, 0))


def u16(data, offset):
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("truncated 16-bit font field")
    return struct.unpack_from(">H", data, offset)[0]


def u32(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("truncated 32-bit font field")
    return struct.unpack_from(">I", data, offset)[0]


def cmap(data: bytes):
    if len(data) > MAX_FONT or len(data) < 12 or data[:4] not in (b"\0\1\0\0", b"OTTO"):
        raise ValueError("expected bounded standalone TrueType/OpenType SFNT, not WOFF/TTC")
    count = u16(data, 4)
    if not 1 <= count <= 256 or 12 + count * 16 > len(data):
        raise ValueError("invalid SFNT directory")
    tables = {}
    for i in range(count):
        pos = 12 + 16 * i
        tag = data[pos:pos + 4]
        start, size = u32(data, pos + 8), u32(data, pos + 12)
        if tag in tables or start < 12 + count * 16 or start + size > len(data):
            raise ValueError("duplicate, overlapping-directory or truncated table")
        tables[tag] = data[start:start + size]
    if b"cmap" not in tables or b"maxp" not in tables:
        raise ValueError("cmap and maxp tables are required")
    glyphs = u16(tables[b"maxp"], 4)
    if not glyphs:
        raise ValueError("maxp declares no glyphs")
    raw = tables[b"cmap"]
    if u16(raw, 0) or not 1 <= u16(raw, 2) <= 64 or 4 + u16(raw, 2) * 8 > len(raw):
        raise ValueError("invalid cmap encoding directory")
    records = {}
    for i in range(u16(raw, 2)):
        pos = 4 + 8 * i
        pair = u16(raw, pos), u16(raw, pos + 2)
        offset = u32(raw, pos + 4)
        if pair in records or offset < 4 + u16(raw, 2) * 8 or offset + 2 > len(raw):
            raise ValueError("duplicate cmap encoding or invalid offset")
        records[pair] = offset
    chosen = next((p for p in PREFERENCE if p in records), None)
    if chosen is None:
        raise ValueError("no supported Unicode encoding record")
    start = records[chosen]
    fmt = u16(raw, start)
    if fmt not in (4, 12):
        raise ValueError("preferred Unicode cmap format is unsupported: " + str(fmt))
    length = u16(raw, start + 2) if fmt == 4 else u32(raw, start + 4)
    if length < (16 if fmt == 12 else 24) or start + length > len(raw):
        raise ValueError("invalid cmap subtable length")
    sub = raw[start:start + length]
    ranges = []
    if fmt == 12:
        if u16(sub, 2) or u32(sub, 12) > 100000 or 16 + 12 * u32(sub, 12) != length:
            raise ValueError("invalid format12 group directory")
        previous = -1
        for i in range(u32(sub, 12)):
            pos = 16 + 12 * i
            first, last, gid = u32(sub, pos), u32(sub, pos + 4), u32(sub, pos + 8)
            if first <= previous or last < first or last > 0x10FFFF or gid + last - first >= glyphs:
                raise ValueError("invalid/overlapping format12 group or out-of-range glyph")
            ranges.append((first, last, gid))
            previous = last
        ends = [r[1] for r in ranges]

        def lookup(cp):
            i = bisect.bisect_left(ends, cp)
            if i == len(ranges) or cp < ranges[i][0]:
                return 0
            return ranges[i][2] + cp - ranges[i][0]
    else:
        twice = u16(sub, 6)
        n = twice // 2
        if twice % 2 or not 1 <= n <= 8192 or 16 + n * 8 > length or u16(sub, 14 + 2 * n):
            raise ValueError("invalid format4 segment directory")
        previous = -1
        for i in range(n):
            last = u16(sub, 14 + 2 * i)
            first = u16(sub, 16 + 2 * n + 2 * i)
            delta = u16(sub, 16 + 4 * n + 2 * i)
            range_pos = 16 + 6 * n + 2 * i
            ro = u16(sub, range_pos)
            if first > last or first <= previous or ro % 2:
                raise ValueError("invalid/overlapping format4 segment")
            if ro and (range_pos + ro < 16 + 8 * n or range_pos + ro + 2 * (last - first) + 2 > length):
                raise ValueError("format4 glyph-array offset outside subtable")
            ranges.append((first, last, delta, range_pos, ro))
            previous = last
        if ranges[-1][:2] != (0xFFFF, 0xFFFF):
            raise ValueError("format4 needs its final sentinel segment")
        ends = [r[1] for r in ranges]

        def lookup(cp):
            if cp > 0xFFFF:
                return 0
            i = bisect.bisect_left(ends, cp)
            if i == len(ranges) or cp < ranges[i][0]:
                return 0
            first, _, delta, pos, ro = ranges[i]
            if not ro:
                return (cp + delta) % 65536
            gid = u16(sub, pos + ro + 2 * (cp - first))
            return (gid + delta) % 65536 if gid else 0

    def checked(cp):
        gid = lookup(cp)
        if gid >= glyphs:
            raise ValueError("queried glyph index exceeds maxp.numGlyphs")
        return gid

    return checked, {"platform": chosen[0], "encoding": chosen[1], "format": fmt, "declared_glyphs": glyphs}


def analyze(text, fonts):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 2 * 1024 * 1024 or not 1 <= len(fonts) <= 16:
        raise ValueError("corpus <=2 MiB and 1..16 fonts required")
    counts = Counter(ord(c) for c in text if unicodedata.category(c) not in ("Cc", "Cf", "Zl", "Zp"))
    if not counts or len(counts) > 4096:
        raise ValueError("corpus needs 1..4096 non-control unique code points")
    if len({name for name, _ in fonts}) != len(fonts):
        raise ValueError("font labels must be distinct")
    coverage, reports = [], []
    for name, data in fonts:
        lookup, selected = cmap(data)
        covered = {cp for cp in counts if lookup(cp) != 0}
        coverage.append(covered)
        reports.append({"font": name, "selected_cmap": selected, "covered_unique": len(covered),
                        "missing": [f"U+{cp:04X}" for cp in sorted(set(counts) - covered)]})
    remaining = set(counts)
    plan = []
    available = list(range(len(fonts)))
    while available:
        best = max(available, key=lambda i: (len(coverage[i] & remaining), -i))
        added = coverage[best] & remaining
        if not added:
            break
        plan.append({"font": fonts[best][0], "new_codepoints": [f"U+{c:04X}" for c in sorted(added)],
                     "new_occurrences": sum(counts[c] for c in added)})
        remaining -= added
        available.remove(best)
    return {"unique_codepoints": len(counts), "occurrences": sum(counts.values()), "fonts": reports,
            "greedy_plan": plan, "uncovered": [f"U+{cp:04X}" for cp in sorted(remaining)],
            "scope": "Nominal cmap mapping only, not shaping, font validity, glyph quality or minimum-cardinality cover."}


def fixture(mapping):
    """Original structural cmap/maxp fixture; it has no outlines and is not a renderable font."""
    groups = b"".join(struct.pack(">III", cp, cp, gid) for cp, gid in sorted(mapping.items()))
    sub = struct.pack(">HHIII", 12, 0, 16 + len(groups), 0, len(mapping)) + groups
    table = struct.pack(">HHHHI", 0, 1, 3, 10, 12) + sub
    maxp = struct.pack(">IH", 0x00005000, max(mapping.values(), default=0) + 1)
    offset = 44
    return (struct.pack(">IHHHH", 0x00010000, 2, 0, 0, 0) +
            struct.pack(">4sIII", b"cmap", 0, offset, len(table)) +
            struct.pack(">4sIII", b"maxp", 0, offset + len(table), len(maxp)) + table + maxp)


def make_example(path):
    p = Path(path)
    p.mkdir()
    (p / "latin.ttf").write_bytes(fixture({ord("A"): 1, ord("B"): 2}))
    (p / "accent.ttf").write_bytes(fixture({ord("é"): 1, 0x1F642: 2}))
    (p / "corpus.txt").write_text("ABé🙂\n", encoding="utf-8")


def bounded(path, limit):
    with Path(path).open("rb") as f:
        data = f.read(limit + 1)
    if len(data) > limit:
        raise ValueError("file exceeds byte limit")
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fonts", nargs="*")
    p.add_argument("--corpus")
    p.add_argument("--make-example", metavar="NEW_DIRECTORY")
    a = p.parse_args()
    try:
        if a.make_example:
            if a.fonts or a.corpus:
                raise ValueError("example generation cannot be combined with inputs")
            make_example(a.make_example)
            print(json.dumps({"example_directory": a.make_example, "renderable_fonts": False}))
            return 0
        if not a.corpus or not 1 <= len(a.fonts) <= 16:
            raise ValueError("--corpus and 1..16 SFNT files required")
        report = analyze(bounded(a.corpus, 2 * 1024 * 1024).decode("utf-8"),
                         [(str(Path(f)), bounded(f, MAX_FONT)) for f in a.fonts])
        print(json.dumps(report, sort_keys=True, indent=2))
        return 1 if report["uncovered"] else 0
    except (ValueError, OSError, UnicodeError, struct.error) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
