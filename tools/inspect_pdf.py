"""B-01: Inspect a TEDU wayfinding PDF with PyMuPDF.

Prints every piece of text with its (x, y) position and labels it as
HEADER, PLAN, QR or LEGEND, then checks that the room markers on the plan
match the numbered rows in the legend.

Usage:
    python tools/inspect_pdf.py uploads/yer-yon-haritalari-d-blok.pdf            # summary of every page
    python tools/inspect_pdf.py uploads/yer-yon-haritalari-d-blok.pdf --page 4   # all text of one page

Needs: pip install pymupdf
Coordinates are PDF points (1/72 inch), origin top-left, y grows downward.
"""
import argparse

from tedu_pdf import HEADER_BOTTOM, MARKER_RE, QR_RIGHT_PT, layout, open_pdf


def region(w, lay) -> str:
    if w["top"] < HEADER_BOTTOM:
        return "HEADER"
    if w["top"] >= lay.legend_box_top:
        return "LEGEND"
    if w["top"] >= lay.qr_top and w["x"] < QR_RIGHT_PT:
        return "QR"
    return "PLAN"


def legend_numbers(words, lay) -> set[str]:
    legend = [w for w in words if w["top"] >= lay.legend_top + 25]
    return {
        w["text"] for w in legend
        if MARKER_RE.match(w["text"])
        and any(abs(o["y"] - w["y"]) < 30 and 0 < o["x0"] - w["x1"] < 40 for o in legend)
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, help="print every word of this page (0-based)")
    args = ap.parse_args()

    doc = open_pdf(args.pdf)
    if args.page is not None:
        page = doc[args.page]
        lay = layout(page)
        imgs = [i["bbox"] for i in page.get_image_info() if i["bbox"][3] - i["bbox"][1] < 800]
        print(f"Page {args.page}: {lay.title}")
        print(f"size {page.rect.width:.0f} x {page.rect.height:.0f} pt | level {lay.level} | "
              f"vector drawings {len(page.get_drawings())} | plan image(s) {[tuple(round(v) for v in b) for b in imgs]}")
        print(f"QR from y={lay.qr_top:.0f} (x < {QR_RIGHT_PT:.0f}) | legend frame from y={lay.legend_box_top:.0f}\n")
        print(f"{'region':<7} {'x':>7} {'y':>7}  text")
        for w in lay.words:
            print(f"{region(w, lay):<7} {w['x']:7.1f} {w['y']:7.1f}  {w['text']}")
        return

    print(f"{'pg':<3} {'level':>5}  {'markers':>7} {'legend':>6}  check")
    for i, page in enumerate(doc):
        lay = layout(page)
        nums = sorted(w["text"] for w in lay.words if region(w, lay) == "PLAN" and MARKER_RE.match(w["text"]))
        leg = legend_numbers(lay.words, lay)
        dupes = sorted({n for n in nums if nums.count(n) > 1})
        problems = []
        if set(nums) - leg:
            problems.append(f"not in legend {sorted(set(nums) - leg)}")
        if leg - set(nums):
            problems.append(f"not on plan {sorted(leg - set(nums))}")
        note = "; ".join(problems) or "OK"
        if dupes:
            note += f" (several markers: {dupes})"
        print(f"{i:<3} {str(lay.level):>5}  {len(nums):>7} {len(leg):>6}  {note}")


if __name__ == "__main__":
    main()
