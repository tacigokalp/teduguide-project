# tools (Area B data tools)

```bash
pip install -r tools/requirements.txt
# put the D-block PDF in uploads/ first (see docs/area-b-pdf-findings.md)
python tools/inspect_pdf.py   uploads/yer-yon-haritalari-d-blok.pdf            # B-01 summary of all pages
python tools/pdf_to_svg.py    uploads/yer-yon-haritalari-d-blok.pdf --block D --out data/floorplans   # B-03
python tools/extract_rooms.py uploads/yer-yon-haritalari-d-blok.pdf --block D --out data/floorplans   # B-04
pytest tools/tests -q                                                                                  # UT-DATA-002
```
