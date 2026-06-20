"""Trim recorded exchange fixtures to a few diverse rows (test tooling, T11/D4).

Offline, idempotent. The recorder (`agents/_dev/tools/exchange_fixtures`) captures full live
responses; tests only assert structure (`len>0`, `iloc[0]`, value filters), so keep a
handful of diverse rows per file and drop the rest (multi-MB -> ~40-50 kB per exchange).

    uv run python -m tests.utils.exchange_fixtures.trim --check
    uv run python -m tests.utils.exchange_fixtures.trim
"""

from __future__ import annotations

import argparse
import json
import os
import re

FIXTURES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "unit", "io", "exchange", "fixtures")
)

# Rows kept per diversity group, per file. Test assets are force-kept.
PER_GROUP = 2
_KEEP_ASSETS = ("SI", "AFLT", "SBER")


def _row_group(row: dict) -> str:
    """Diversity key: option call/put (+kind), else asset_type. Force-keep test assets."""
    code = str(row.get("asset_code") or row.get("secid") or "")
    if code in _KEEP_ASSETS and "option_type" not in row:
        return "KEEP"
    name = str(row.get("instrument_name") or row.get("secid") or "")
    kind = str(row.get("kind") or row.get("asset_type") or "")
    right = ""
    if name.endswith(("-C", "-P")):
        right = name[-1]
    elif str(row.get("option_type", "")) in ("call", "put", "c", "p"):
        right = str(row["option_type"])[0]
    return f"{kind}|{right}"


def _trim_list(rows: list) -> list:
    seen: dict[str, int] = {}
    out = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        g = _row_group(row)
        if g == "KEEP":
            out.append(row)
        elif seen.get(g, 0) < PER_GROUP:
            seen[g] = seen.get(g, 0) + 1
            out.append(row)
    return out


def _trim_body(body):
    """Trim Deribit ``{"result":[…]}``, a bare list, or MOEX optionboard
    ``{"call":[…],"put":[…]}``. Returns (trimmed, kept, total)."""
    if isinstance(body, dict) and isinstance(body.get("result"), list):
        total = len(body["result"])
        body["result"] = _trim_list(body["result"])
        return body, len(body["result"]), total
    if isinstance(body, list):
        trimmed = _trim_list(body)
        return trimmed, len(trimmed), len(body)
    if isinstance(body, dict) and body and all(isinstance(v, list) for v in body.values()):
        total = sum(len(v) for v in body.values())
        for key in body:
            body[key] = _trim_list(body[key])
        return body, sum(len(v) for v in body.values()), total
    return body, None, None


def trim_exchange(name: str, check: bool = False) -> None:
    out_dir = os.path.join(FIXTURES_ROOT, name)
    if not os.path.isdir(out_dir):
        print(f"[{name}] no fixtures dir, skip")
        return
    for fn in sorted(os.listdir(out_dir)):
        if not re.fullmatch(r"\d+\.json", fn):
            continue
        path = os.path.join(out_dir, fn)
        before = os.path.getsize(path)
        with open(path, encoding="utf-8") as f:
            body = json.load(f)
        trimmed, kept, total = _trim_body(body)
        if check:
            print(f"  {name}/{fn}: {before // 1024}KB, {total} rows -> would keep {kept}")
            continue
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=1, default=str)
        print(f"  {name}/{fn}: {before // 1024}KB->{os.path.getsize(path) // 1024}KB ({total} -> {kept} rows)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Trim recorded exchange fixtures.")
    parser.add_argument("--check", action="store_true", help="Report only, write nothing.")
    parser.add_argument("--only", choices=("deribit", "moex"))
    args = parser.parse_args(argv)
    for name in ("deribit", "moex") if not args.only else (args.only,):
        trim_exchange(name, args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
