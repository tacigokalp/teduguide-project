import pytest

from app.core.text import fold_tr


# UT-TXT-001: the three examples from the Test Plan
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Çapın", "capin"),
        ("İBADETHANE", "ibadethane"),
        ("Kütüphane", "kutuphane"),
    ],
)
def test_fold_tr_examples(raw, expected):
    assert fold_tr(raw) == expected


def test_same_word_typed_three_ways_is_equal():
    assert fold_tr("Çapın") == fold_tr("CAPIN") == fold_tr("capin")


def test_dotless_capital_i():
    # In Turkish, capital I becomes dotless ı, which we then flatten to i.
    assert fold_tr("IŞIK") == "isik"


def test_punctuation_and_spaces_are_collapsed():
    assert fold_tr("  D-232.  Ofis ") == "d 232 ofis"


def test_empty_string():
    assert fold_tr("") == ""
