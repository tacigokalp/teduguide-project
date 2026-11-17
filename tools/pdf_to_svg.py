"""B-03: Turn each floor page of a wayfinding PDF into a clean floor-plan picture (PyMuPDF).

For every page it writes, in data/floorplans/<block>/:
    <level>.png          the plan only (no title, QR or legend), high resolution
    <level>.webp         the same picture, much smaller, for the web app
    <level>.svg          a tiny SVG that shows <level>.webp; its viewBox is in PDF points
    <level>.meta.json    where the crop came from (PDF points) and the pixel scale
    <level>.preview.png  a small preview to check by eye

Why PNG/WebP and not page.get_svg_image(): the walls in these PDFs are an embedded raster
image (about 6800 px wide), not vector lines. get_svg_image() would only wrap that same
picture (base64, several MB per floor), so we save the picture directly and keep a thin SVG
for anything that expects an .svg file. Leaflet can show either (ImageOverlay).

Usage:
    python tools/pdf_to_svg.py uploads/yer-yon-haritalari-d-blok.pdf --block D --out data/floorplans
Needs: pip install pymupdf pillow
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops, ImageDraw

from tedu_pdf import HEADER_BOTTOM, QR_RIGHT_PT, layout, open_pdf

SCALE = 4.0  # pixels per PDF point (= 288 dpi); the embedded plan images are ~4.1 px/pt
MARGIN_PT = 8.0  # empty border kept around the plan
SIDE_PT = 15.0  # ignore the outermost strip of the page (page edge artefacts)


def render(page: pymupdf.Page, clip: pymupdf.Rect, scale: float) -> Image.Image:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def blank_qr(img: Image.Image, origin_x: float, origin_y: float, qr_top: float, scale: float, bg) -> None:
    """Paint the QR block (bottom-left) with the background colour. The plan can reach lower
    than the QR block on the right-hand side, so we cannot simply cut everything below qr_top."""
    top = (qr_top - origin_y) * scale
    right = (QR_RIGHT_PT - origin_x) * scale
    if top < img.height and right > 0:
        ImageDraw.Draw(img).rectangle([0, max(0, top), right, img.height], fill=bg)


def find_plan_box(page: pymupdf.Page, y0: float, y1: float, qr_top: float) -> pymupdf.Rect:
    """Render the plan band at low resolution and return the bounding box of everything
    that is not background, in PDF points."""
    s = 1.0
    band = pymupdf.Rect(SIDE_PT, y0, page.rect.width - SIDE_PT, y1)
    img = render(page, band, s)
    bg = img.getpixel((2, 2))
    blank_qr(img, band.x0, band.y0, qr_top, s, bg)
    diff = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L")
    bbox = diff.point(lambda v: 255 if v > 18 else 0).getbbox()
    if not bbox:
        return band
    bx0, by0, bx1, by1 = bbox
    return pymupdf.Rect(
        max(0.0, band.x0 + bx0 / s - MARGIN_PT),
        max(0.0, band.y0 + by0 / s - MARGIN_PT),
        min(page.rect.width, band.x0 + bx1 / s + MARGIN_PT),
        min(y1, band.y0 + by1 / s + MARGIN_PT),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--block", required=True, help="building code, e.g. D")
    ap.add_argument("--out", default="data/floorplans")
    args = ap.parse_args()

    out_dir = Path(args.out) / args.block
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = open_pdf(args.pdf)

    print(f"{'page':<5}{'level':>6}  {'crop (pt)':<28}{'pixels':>13}  png/webp kB")
    for i, page in enumerate(doc):
        lay = layout(page)
        name = str(lay.level) if lay.level is not None else f"page{i}"
        clip = find_plan_box(page, HEADER_BOTTOM + 5, lay.legend_box_top - 3, lay.qr_top)
        img = render(page, clip, SCALE)
        blank_qr(img, clip.x0, clip.y0, lay.qr_top, SCALE, img.getpixel((img.width - 3, 3)))

        png = out_dir / f"{name}.png"
        webp = out_dir / f"{name}.webp"
        img.save(png, optimize=True)
        img.save(webp, quality=82, method=6)
        img.resize((img.width // 6, img.height // 6), Image.LANCZOS).save(out_dir / f"{name}.preview.png")

        w_pt, h_pt = clip.width, clip.height
        (out_dir / f"{name}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w_pt:.2f} {h_pt:.2f}" width="{w_pt:.0f}" height="{h_pt:.0f}">\n'
            f'  <title>{args.block} block, level {name}</title>\n'
            f'  <image href="{webp.name}" xlink:href="{webp.name}" x="0" y="0" '
            f'width="{w_pt:.2f}" height="{h_pt:.2f}" preserveAspectRatio="none"/>\n</svg>\n',
            encoding="utf-8",
        )
        meta = {
            "block": args.block,
            "level": lay.level,
            "title": lay.title,
            "source_pdf": Path(args.pdf).name,
            "page_index": i,
            "crop_pt": {"x0": round(clip.x0, 2), "y0": round(clip.y0, 2),
                        "x1": round(clip.x1, 2), "y1": round(clip.y1, 2)},
            "size_pt": [round(w_pt, 2), round(h_pt, 2)],
            "size_px": [img.width, img.height],
            "px_per_pt": SCALE,
            "note": "Plan coordinates = PDF points minus crop_pt.x0/y0, y down. "
                    "Metres come later from the campus measurement (S-04 / B4).",
        }
        (out_dir / f"{name}.meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{i:<5}{name:>6}  ({clip.x0:6.0f},{clip.y0:4.0f})-({clip.x1:5.0f},{clip.y1:4.0f})  "
              f"{img.width:>5}x{img.height:<5}  {png.stat().st_size // 1024}/{webp.stat().st_size // 1024}")


if __name__ == "__main__":
    main()
