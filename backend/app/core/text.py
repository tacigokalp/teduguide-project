"""Text helpers shared by the whole backend.

fold_tr turns "Çapın", "CAPIN" and "capin" into the same string ("capin").
Data (at seed time) and user queries (at search time) must both go through
this one function, so that search just works.
"""

import re
import unicodedata

# Turkish letters that do not decompose with NFKD (ı) or that we want
# to flatten explicitly.
_MAP = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"})


def fold_tr(s: str) -> str:
    """Return a simple, comparable form of s.

    Lower case, no Turkish accents, punctuation turned into spaces,
    repeated spaces collapsed.

    >>> fold_tr("İBADETHANE")
    'ibadethane'
    """
    # Must happen BEFORE lower(): Python's "I".lower() gives "i" (wrong for
    # Turkish) and "İ".lower() gives "i" + a combining dot.
    s = s.replace("İ", "i").replace("I", "ı")
    s = s.lower().translate(_MAP)
    s = unicodedata.normalize("NFKD", s)  # split "é" into "e" + accent mark
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^\w\s]", " ", s)  # punctuation -> space
    return " ".join(s.split())
