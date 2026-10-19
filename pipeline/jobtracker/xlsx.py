"""Minimal streaming .xlsx reader (first worksheet only), stdlib only.

Enough for the government registers used here; it does not evaluate
formulas or handle dates, which those files do not need.
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COL = re.compile(r"([A-Z]+)")


def _col_index(ref):
    letters = _COL.match(ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    out = []
    for _, el in ET.iterparse(z.open("xl/sharedStrings.xml")):
        if el.tag == _NS + "si":
            out.append("".join(t.text or "" for t in el.iter(_NS + "t")))
            el.clear()
    return out


def iter_rows(data):
    """Yield each row of the first sheet as a list of strings."""
    z = zipfile.ZipFile(io.BytesIO(data))
    strings = _shared_strings(z)
    sheets = sorted(
        (n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)),
        key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)),
    )
    if not sheets:
        return
    for _, el in ET.iterparse(z.open(sheets[0])):
        if el.tag != _NS + "row":
            continue
        row = []
        for c in el.iter(_NS + "c"):
            ref = c.get("r")
            idx = _col_index(ref) if ref else len(row)
            while len(row) < idx:
                row.append("")
            t = c.get("t")
            v = c.find(_NS + "v")
            if t == "s" and v is not None:
                row.append(strings[int(v.text)])
            elif t == "inlineStr":
                row.append("".join(x.text or "" for x in c.iter(_NS + "t")))
            else:
                row.append(v.text if v is not None and v.text is not None else "")
        el.clear()
        yield row
