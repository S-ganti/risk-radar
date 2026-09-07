#!/usr/bin/env python3
"""
Recover score history that the old 26-entry rolling cap discarded.

`pipeline.py` used to truncate data/history.json to the last 26 dates on every
run, so four weeks of real observations (17 Jul - 11 Aug 2026) fell out of the
live file even though the pipeline had run successfully every day. Every daily
commit still carries the file, so the full series is reconstructable as the
union of all committed snapshots.

Run once after raising the cap:  python scripts/backfill_history.py
Idempotent - re-running only ever adds dates it does not already have.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history.json")
REL = "data/history.json"


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args],
                          capture_output=True, text=True, check=True).stdout


def snapshots():
    """Every committed version of history.json, oldest commit first."""
    shas = git("log", "--format=%H", "--", REL).split()
    for sha in reversed(shas):
        try:
            yield sha, json.loads(git("show", f"{sha}:{REL}"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue


def main():
    merged = {}   # date -> {risk_id: score}
    seen_risks = set()

    for _sha, snap in snapshots():
        dates = snap.get("dates") or []
        scores = snap.get("scores") or {}
        for rid, vals in scores.items():
            seen_risks.add(rid)
            # scores arrays are positionally aligned with dates; a shorter
            # array means the risk was added later, so align from the right.
            offset = len(dates) - len(vals)
            for i, v in enumerate(vals):
                di = i + offset
                if 0 <= di < len(dates):
                    merged.setdefault(dates[di], {})[rid] = v

    try:
        with open(HIST, encoding="utf-8") as f:
            live = json.load(f)
        for rid, vals in (live.get("scores") or {}).items():
            seen_risks.add(rid)
            dates = live.get("dates") or []
            offset = len(dates) - len(vals)
            for i, v in enumerate(vals):
                di = i + offset
                if 0 <= di < len(dates):
                    merged.setdefault(dates[di], {})[rid] = v
    except FileNotFoundError:
        live = {"dates": [], "scores": {}}

    all_dates = sorted(merged)
    if not all_dates:
        print("No history found in git or on disk - nothing to backfill.", file=sys.stderr)
        return 1

    out = {"dates": all_dates, "scores": {}}
    gaps = 0
    for rid in sorted(seen_risks):
        series, last = [], None
        for d in all_dates:
            v = merged[d].get(rid)
            if v is None:              # risk not yet tracked on that date
                v = last
                gaps += 1
            if v is None:
                continue
            series.append(v)
            last = v
        # left-pad so the array stays positionally aligned with `dates`
        if len(series) < len(all_dates):
            series = [series[0]] * (len(all_dates) - len(series)) + series
        out["scores"][rid] = series

    before = len(live.get("dates") or [])
    with open(HIST, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)

    print(f"history.json: {before} -> {len(all_dates)} dates "
          f"({all_dates[0]} -> {all_dates[-1]}), {len(out['scores'])} risks"
          + (f", {gaps} carried-forward gaps" if gaps else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
