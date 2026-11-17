"""UT-DATA-002: extract_rooms on the D-block PDF.

Expected (Backlog B-04): floor 2 gives 24 rooms, D232 has the right name,
and markers match legend rows on every floor.

Run from the repo root:  pytest tools/tests -q
The PDF path can be changed with TEDU_D_PDF=/path/to/yer-yon-haritalari-d-blok.pdf
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tools/

from extract_rooms import extract_page, room_type  # noqa: E402
from tedu_pdf import layout, open_pdf, parse_level  # noqa: E402

PDF = Path(os.environ.get("TEDU_D_PDF", "uploads/yer-yon-haritalari-d-blok.pdf"))
pytestmark = pytest.mark.skipif(not PDF.exists(), reason=f"{PDF} not found")


_OV = Path(__file__).resolve().parents[2] / "data" / "floorplans" / "D" / "overrides.json"
OVERRIDES = json.loads(_OV.read_text(encoding="utf-8")) if _OV.exists() else {}


@pytest.fixture(scope="module")
def pages():
    doc = open_pdf(str(PDF))
    yield [(layout(p), *extract_page(p, None, OVERRIDES.get(str(layout(p).level)))) for p in doc]
    doc.close()


def test_levels_in_page_order(pages):
    assert [lay.level for lay, _, _ in pages] == [-2, -1, 0, 1, 2, 3, 4]


def test_floor2_has_24_rooms(pages):
    _, rooms, _ = pages[4]
    assert len(rooms) == 24


def test_d232_named_correctly(pages):
    _, rooms, _ = pages[4]
    d232 = [r for r in rooms if r["code"] == "D232"]
    assert len(d232) == 1
    r = d232[0]
    assert r["n"] == "17"
    assert r["name_tr"] == "D232 Numaralı Sınıf"
    assert r["name_en"] == "Class Number D232"
    assert r["type"] == "classroom"


def test_markers_match_legend_on_every_floor(pages):
    for lay, rooms, rep in pages:
        assert rep["missing_in_legend"] == [], lay.title
        assert rep["missing_on_plan"] == [], lay.title
        assert rep["duplicate_codes"] == [], lay.title
        assert all(r["name_en"] or r["name_tr"] for r in rooms), lay.title


def test_room_with_two_markers_keeps_both(pages):
    _, rooms, _ = pages[5]  # level 3: the library has two "13" markers
    lib = next(r for r in rooms if r["n"] == "13")
    assert lib["type"] == "library"
    assert len(lib["anchors"]) == 2


def test_advisor_office_d207_is_marker_21(pages):
    _, rooms, _ = pages[4]
    assert next(r for r in rooms if r["code"] == "D207")["n"] == "21"


@pytest.mark.parametrize(
    "tr,en,expected",
    [
        ("Erkek Tuvaleti", "Man Restroom", "wc"),
        ("Kadın İbadethane", "Woman Prayer Room", "prayer"),
        ("Çay Ocağı", "Kitchenette", "kitchenette"),
        ("D128 Numaralı Stüdyo", "Studio Number D128", "studio"),
        ("DB014 Numaralı Amfi", "Amphi Number DB014", "amphitheatre"),
        ("Eğitim Fakültesi Dekanlığı", "Faculty of Education Dean's Office", "office"),
    ],
)
def test_room_type(tr, en, expected):
    assert room_type(tr, en) == expected


def test_parse_level():
    assert parse_level("D BLOK ZEMİN KAT D BLOCK GROUND FLOOR") == 0
    assert parse_level("D BLOK -2.KAT D BLOCK -2nd FLOOR") == -2
    assert parse_level("D BLOK 4. KAT D BLOCK 4th FLOOR") == 4


def test_ground_floor_names_not_mixed(pages):
    # The bold Turkish part sits ~1 pt higher than the English part; both must still split on "|".
    # (Markers 24 and 18 hold legend rows 13 and 19 after the ground-floor correction.)
    _, rooms, _ = pages[2]
    for code, n in [("D002", "1"), ("D001", "24"), ("D013", "18")]:
        r = next(r for r in rooms if r["n"] == n)
        assert (r["code"], r["name_tr"], r["name_en"]) == (code, f"{code} Numaralı Ofis", f"Office Number {code}")


def test_every_room_has_both_languages(pages):
    for lay, rooms, _ in pages:
        for r in rooms:
            assert r["name_tr"] and r["name_en"], (lay.level, r["n"])


def test_ground_floor_correction(pages):
    """The official ground-floor PDF numbers the plan and the legend differently (overrides.json).
    After the correction the amphis are the four big rooms on the east side, west to east."""
    _, rooms, _ = pages[2]
    amphis = sorted((r for r in rooms if r["type"] == "amphitheatre"), key=lambda r: r["anchor"][0])
    assert [r["code"] for r in amphis] == ["D026", "D028", "D030", "D032"]
    assert [r["n"] for r in amphis] == ["14", "15", "16", "17"]
    offices = sorted((r for r in rooms if r["code"] and r["code"][1:].isdigit() and int(r["code"][1:]) % 2 == 1),
                     key=lambda r: r["anchor"][0])
    assert [r["code"] for r in offices] == ["D001", "D003", "D005", "D007", "D009", "D011", "D013"]
    assert all(r.get("verified") is False for r in amphis)
