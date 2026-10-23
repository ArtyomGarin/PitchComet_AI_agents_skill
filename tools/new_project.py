#!/usr/bin/env python3
"""new_project.py — scaffold a new project folder from templates/ (copy of the working example).

CLI: python new_project.py --dir my_product [--name "My product"] [--locale ru|en|zh|vi|id|ms]
Creates project.json, market_input.json, finance_input.json, scoring_input.json, deck_spec.json,
report_spec.json. Templates come from templates/<locale>/ (currency, labels, sample text in that language).
Then edit the inputs and run:  python run_pipeline.py --project my_product/project.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "templates")
FILES = ["project", "market_input", "finance_input", "scoring_input", "deck_spec", "report_spec"]


def scaffold(target: str, name: str | None = None, locale: str | None = None) -> dict:
    sys.path.insert(0, HERE)
    from locales import norm_locale
    locale = norm_locale(locale or "en")
    os.makedirs(target, exist_ok=True)
    written = []
    for f in FILES:
        with open(os.path.join(TPL, locale, f"{f}.template.json"), encoding="utf8") as fh:
            d = json.load(fh)
        if f == "project":
            d["out_dir"] = "output"
            d.pop("_EXAMPLE_DATA", None)
            if name:
                d["name"] = name
            d["locale"] = locale
            d.pop("language", None)
        out = os.path.join(target, f"{f}.json")
        if os.path.exists(out):
            continue  # never overwrite user work
        with open(out, "w", encoding="utf8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
        written.append(out)
    return {"dir": target, "locale": locale, "written": [os.path.basename(w) for w in written],
            "next": f"python tools/run_pipeline.py --project {os.path.join(target, 'project.json')}"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--name")
    ap.add_argument("--locale", "-l", "--language", dest="locale", choices=["ru", "en", "zh", "vi", "id", "ms"], default="en")
    a = ap.parse_args(argv)
    print(json.dumps(scaffold(a.dir, a.name, a.locale), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
