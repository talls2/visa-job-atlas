"""Writes site/src/cv/family.ts from jobtracker/families.py so the web app
classifies CV titles exactly like the pipeline classifies postings.

Run from pipeline/: python gen_family_ts.py
"""

import json
from pathlib import Path

from jobtracker import families as F

OUT = Path(__file__).resolve().parents[1] / "site" / "src" / "cv" / "family.ts"


def main():
    names = {}
    for name in dir(F):
        obj = getattr(F, name)
        if name.isupper() and hasattr(obj, "pattern") and hasattr(obj, "search"):
            names[id(obj)] = name

    def ref(rx):
        return names[id(rx)] if rx is not None else "null"

    used = []
    for _, rx, veto in F._CREATIVE + F._ORDER:
        for r in (rx, veto):
            if r is not None and ref(r) not in used:
                used.append(ref(r))
    for extra in (F.NOT_CREATIVE, F.NON_TECH):
        if ref(extra) not in used:
            used.append(ref(extra))

    lines = [
        "// Job-family classification. GENERATED from pipeline/jobtracker/families.py",
        "// by pipeline/gen_family_ts.py; edit the Python file and regenerate.",
        'import type { Family } from "../types";',
        "",
        'const rx = (s: string) => new RegExp(s, "i");',
        "",
    ]
    for name in used:
        lines.append(f"const {name} = rx({json.dumps(getattr(F, name).pattern, ensure_ascii=False)});")
    lines.append("")

    def table(items):
        return "\n".join(f'  ["{fam}", {ref(rx)}, {ref(veto)}],' for fam, rx, veto in items)

    lines += [
        "const ORDER: [Family, RegExp, RegExp | null][] = [",
        table(F._ORDER),
        "];",
        "",
        "// Creative roles often sit in marketing teams (\"Video Editor, Marketing\"), so they",
        "// are matched first.",
        "const CREATIVE: [Family, RegExp, RegExp | null][] = [",
        table(F._CREATIVE),
        "];",
        "",
        "export function jobFamily(title: string): Family | null {",
        "  if (!title) return null;",
        "  if (!NOT_CREATIVE.test(title)) {",
        "    for (const [family, re, veto] of CREATIVE) {",
        "      if (re.test(title) && !(veto && veto.test(title))) return family;",
        "    }",
        "  }",
        "  if (NON_TECH.test(title)) return null;",
        "  for (const [family, re, veto] of ORDER) {",
        "    if (re.test(title) && !(veto && veto.test(title))) return family;",
        "  }",
        "  return null;",
        "}",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
