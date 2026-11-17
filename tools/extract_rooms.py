"""B-04: Read the room list out of a wayfinding PDF automatically.

On every floor page:
  * the numbered circles on the plan are the room positions ("anchors"),
  * the legend says what each number is: "17  D232 Numaralı Sınıf | Class Number D232".
Pairing number -> legend row gives a correct room list with positions.

Writes data/floorplans/<block>/<level>.rooms.json:
  [{"n": "17", "code": "D232", "name_tr": "D232 Numaralı Sınıf", "name_en": "Class Number D232",
    "type": "classroom", "anchor": [x, y], "anchors": [[x, y], ...]}, ...]
Coordinates are PDF points relative to the cropped plan picture made by pdf_to_svg.py
(same numbers as the SVG viewBox; y grows down). If the crop file is missing, raw page
points are used. Metres come later (S-04 campus measurement).

A room can have several markers (the library on level 3 has "13" twice), so "anchors" is a list.

Usage:
    python tools/extract_rooms.py uploads/yer-yon-haritalari-d-blok.pdf --block D --out data/floorplans
Needs: pip install pymupdf
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tedu_pdf import HEADER_BOTTOM, MARKER_RE, QR_RIGHT_PT, layout, open_pdf

CODE_RE = re.compile(r"\b([A-Z]{1,2}\d{3})\b")

# keyword (folded, lower case) -> room type. First match wins, so specific words go first.
TYPE_RULES: list[tuple[str, str]] = [
    ("restroom", "wc"), ("tuvalet", "wc"), ("wc", "wc"),
    ("prayer", "prayer"), ("ibadethane", "prayer"), ("mescit", "prayer"),
    ("kitchenette", "kitchenette"), ("cay ocagi", "kitchenette"),
    ("electrical", "technical"), ("elektrik", "technical"), ("server", "technical"), ("sistem odasi", "technical"),
    ("infodesk", "info"), ("information", "info"), ("danisma", "info"),
    ("library", "library"), ("kutuphane", "library"),
    ("amphi", "amphitheatre"), ("amfi", "amphitheatre"),
    ("laborator", "lab"),
    ("atelier", "studio"), ("atolye", "studio"), ("studio", "studio"), ("studyo", "studio"),
    ("class", "classroom"), ("sinif", "classroom"), ("derslik", "classroom"),
    ("meeting", "meeting"), ("toplanti", "meeting"),
    ("workspace", "study"), ("calisma alani", "study"), ("study", "study"),
    ("storage", "storage"), ("depo", "storage"),
    ("reserve", "reserved"), ("rezerv", "reserved"),
    ("terrace", "terrace"), ("teras", "terrace"),
    ("cafe", "cafe"), ("kafe", "cafe"), ("kantin", "cafe"),
    ("dean", "office"), ("dekan", "office"), ("secretar", "office"), ("sekreter", "office"),
    ("office", "office"), ("ofis", "office"), ("chair", "office"), ("baskan", "office"),
]


def fold(s: str) -> str:
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return s.translate(str.maketrans("çğıöşü", "cgiosu"))


def room_type(name_tr: str, name_en: str) -> str:
    text = fold(f"{name_en} {name_tr}")
    for key, t in TYPE_RULES:
        if key in text:
            return t
    return "other"


def legend_rows(words: list[dict], legend_top: float) -> dict[str, dict]:
    """Return {number: {"name_tr", "name_en", "y"}} for every legend row."""
    legend = [w for w in words if w["top"] >= legend_top + 25]  # skip the "WAYFINDING LEGEND" heading
    # A row number is a marker-like word with name text just to its right.
    nums = [
        w for w in legend
        if MARKER_RE.match(w["text"])
        and any(abs(o["y"] - w["y"]) < 30 and 0 < o["x0"] - w["x1"] < 40 for o in legend)
    ]
    # Columns: the numbers sit in circles whose centres line up, so group by centre x
    # ("10" is wider than "9", so the left edges do not line up).
    cols: list[list[dict]] = []
    for n in sorted(nums, key=lambda n: n["x"]):
        if cols and n["x"] - cols[-1][0]["x"] < 60:
            cols[-1].append(n)
        else:
            cols.append([n])
    cols = [sorted(c, key=lambda n: n["y"]) for c in cols]
    col_starts = [min(n["x0"] for n in c) for c in cols]

    rows: dict[str, dict] = {}
    for ci, col in enumerate(cols):
        x_lo = max(n["x1"] for n in col)
        x_hi = col_starts[ci + 1] - 5 if ci + 1 < len(cols) else 10_000
        for ri, n in enumerate(col):
            y_lo = (col[ri - 1]["y"] + n["y"]) / 2 if ri > 0 else n["y"] - 30
            y_hi = (n["y"] + col[ri + 1]["y"]) / 2 if ri + 1 < len(col) else n["y"] + 30
            part = [w for w in legend if x_lo < w["x"] < x_hi and y_lo <= w["y"] < y_hi and w is not n]
            text = " ".join(w["text"] for w in reading_order(part))
            text = re.sub(r"\s+", " ", text).strip()
            if "|" in text:
                tr, en = (t.strip() for t in text.split("|", 1))
            else:
                tr, en = text, ""
            rows[n["text"]] = {"name_tr": tr, "name_en": en.replace("|", "").strip(), "y": n["y"]}
    return rows


def reading_order(words: list[dict], line_tol: float = 6.0) -> list[dict]:
    """Sort words line by line, then left to right. Words belong to the same line when their
    centres are within line_tol points. (The bold Turkish part sits ~1 pt higher than the
    English part of the same line, so plain rounding of y can split one line into two.)"""
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda w: w["y"]):
        if lines and w["y"] - lines[-1][0]["y"] <= line_tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [w for line in lines for w in sorted(line, key=lambda w: w["x0"])]


def circle_centres(page) -> list[tuple[float, float, float]]:
    """Centres (x, y, size) of the small round marker shapes drawn on the page."""
    out = []
    for d in page.get_drawings():
        r = d["rect"]
        if 12 <= r.width <= 40 and abs(r.width - r.height) < 2:
            out.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, r.width))
    return out


def marker_anchor(m: dict, circles: list[tuple[float, float, float]]) -> tuple[float, float]:
    """The centre of the circle around a marker number. Falls back to the text centre.
    Using the drawn circle makes the anchor independent of how a PDF library measures text."""
    best = None
    for cx, cy, size in circles:
        d = abs(cx - m["x"]) + abs(cy - m["y"])
        if d < size / 2 and (best is None or d < best[0]):
            best = (d, cx, cy)
    return (best[1], best[2]) if best else (m["x"], m["y"])


def plan_markers(words: list[dict], qr_top: float, legend_box_top: float) -> list[dict]:
    """Marker numbers on the plan. The plan can reach below the QR block on the right side,
    so we take everything above the legend frame except the QR caption area."""
    out = []
    for w in words:
        if not MARKER_RE.match(w["text"]):
            continue
        if not (HEADER_BOTTOM < w["top"] < legend_box_top):
            continue
        if w["top"] >= qr_top and w["x"] < QR_RIGHT_PT:  # inside the QR block
            continue
        out.append(w)
    return out


def extract_page(page, crop: tuple[float, float] | None, override: dict | None = None):
    """override: {"legendRowForMarker": {"24": "13", ...}, "verified": bool} for pages where the
    PDF's plan numbers and legend numbers do not match (see data/floorplans/<block>/overrides.json)."""
    lay = layout(page)
    remap = (override or {}).get("legendRowForMarker", {})
    markers = plan_markers(lay.words, lay.qr_top, lay.legend_box_top)
    legend = legend_rows(lay.words, lay.legend_top)
    ox, oy = crop if crop else (0.0, 0.0)
    circles = circle_centres(page)

    rooms: dict[str, dict] = {}
    for m in markers:
        n = m["text"]
        ax, ay = marker_anchor(m, circles)
        xy = [round(ax - ox, 2), round(ay - oy, 2)]
        if n in rooms:
            rooms[n]["anchors"].append(xy)
            continue
        legend_row = remap.get(n, n)
        row = legend.get(legend_row, {"name_tr": "", "name_en": ""})
        codes = CODE_RE.findall(f"{row['name_tr']} {row['name_en']}")
        rooms[n] = {
            "n": n,
            **({"legend_row": legend_row, "verified": bool(override.get("verified"))} if legend_row != n else {}),
            "code": codes[0] if codes else None,
            "name_tr": row["name_tr"],
            "name_en": row["name_en"],
            "type": room_type(row["name_tr"], row["name_en"]),
            "anchor": xy,
            "anchors": [xy],
        }

    def sort_key(n: str):
        return tuple(int(p) for p in n.split("."))

    report = {
        "title": lay.title,
        "level": lay.level,
        "markers": len(markers),
        "rooms": len(rooms),
        "legend_rows": len(legend),
        "missing_in_legend": sorted(set(rooms) - set(legend), key=sort_key),
        "missing_on_plan": sorted(set(legend) - set(rooms), key=sort_key),
        "multi_marker": sorted((n for n, r in rooms.items() if len(r["anchors"]) > 1), key=sort_key),
        "duplicate_codes": sorted({r["code"] for r in rooms.values() if r["code"]
                                   and sum(1 for o in rooms.values() if o["code"] == r["code"]) > 1}),
    }
    return [rooms[k] for k in sorted(rooms, key=sort_key)], report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--block", required=True)
    ap.add_argument("--out", default="data/floorplans")
    args = ap.parse_args()
    out_dir = Path(args.out) / args.block
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'lvl':>4} {'markers':>7} {'rooms':>5} {'legend':>6}  {'codes':>5}  check")
    all_ok = True
    ov_file = out_dir / "overrides.json"
    overrides = json.loads(ov_file.read_text(encoding="utf-8")) if ov_file.exists() else {}
    doc = open_pdf(args.pdf)
    for i, page in enumerate(doc):
        lay = layout(page)
        name = str(lay.level) if lay.level is not None else f"page{i}"
        meta_file = out_dir / f"{name}.meta.json"
        crop = None
        if meta_file.exists():
            c = json.loads(meta_file.read_text(encoding="utf-8"))["crop_pt"]
            crop = (c["x0"], c["y0"])
        override = overrides.get(str(lay.level))
        rooms, rep = extract_page(page, crop, override)
        if override:
            print(f"     (level {name}: using the marker->legend correction in overrides.json, "
                  f"verified={override.get('verified')})")
        (out_dir / f"{name}.rooms.json").write_text(json.dumps(rooms, indent=2, ensure_ascii=False), encoding="utf-8")
        problems = []
        if rep["missing_in_legend"]:
            problems.append(f"no legend row for {rep['missing_in_legend']}")
        if rep["missing_on_plan"]:
            problems.append(f"no marker for {rep['missing_on_plan']}")
        if rep["duplicate_codes"]:
            problems.append(f"same code twice {rep['duplicate_codes']}")
        all_ok &= not problems
        notes = problems + ([f"several markers: {rep['multi_marker']}"] if rep["multi_marker"] else [])
        n_codes = sum(1 for r in rooms if r["code"])
        print(f"{name:>4} {rep['markers']:>7} {rep['rooms']:>5} {rep['legend_rows']:>6}  {n_codes:>5}  "
              f"{'OK' if not problems else 'CHECK'} {'; '.join(notes)}")
    print("\nAll floors match." if all_ok else "\nSome floors need a look (see CHECK).")


if __name__ == "__main__":
    main()
