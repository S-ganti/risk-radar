#!/usr/bin/env python3
"""Deterministic publication gate for Risk Radar data, registries, and public copy."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_datetime(value: str | None):
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class Gate:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, check_id: str, status: str, detail: str):
        self.checks.append({"id": check_id, "status": status, "detail": detail})

    def ok(self, check_id: str, detail: str):
        self.add(check_id, "pass", detail)

    def warn(self, check_id: str, detail: str):
        self.add(check_id, "warning", detail)

    def error(self, check_id: str, detail: str):
        self.add(check_id, "error", detail)

    @property
    def errors(self):
        return [check for check in self.checks if check["status"] == "error"]

    @property
    def warnings(self):
        return [check for check in self.checks if check["status"] == "warning"]


def validate_latest(gate: Gate, now: datetime, latest: dict | None = None):
    latest = latest if latest is not None else read_json(DATA / "latest.json")
    generated = parse_datetime(latest.get("generated"))
    if not generated:
        gate.error("latest.generated", "generated must be an ISO-8601 timestamp")
    else:
        age_hours = (now - generated.astimezone(timezone.utc)).total_seconds() / 3600
        if age_hours < -1:
            gate.error("latest.generated", "generated is in the future")
        elif age_hours > 72:
            gate.warn("latest.freshness", f"latest.json is {age_hours:.1f} hours old")
        else:
            gate.ok("latest.freshness", f"latest.json is {age_hours:.1f} hours old")

    spot = latest.get("spot") or {}
    required_spot = ("usdinr", "gold", "brent")
    missing = [key for key in required_spot if not isinstance(spot.get(key), dict)]
    if missing:
        gate.error("spot.required", f"missing required spot records: {', '.join(missing)}")
    else:
        gate.ok("spot.required", "USD/INR, gold and Brent records are present")

    vols = latest.get("vols") or {}
    if len(vols) < 5:
        gate.error("volatility.coverage", f"only {len(vols)} volatility series")
    else:
        gate.ok("volatility.coverage", f"{len(vols)} volatility series")
    for factor, record in vols.items():
        if not isinstance(record, dict):
            gate.error(f"volatility.{factor}", "record must be an object")
            continue
        monthly = record.get("monthly")
        observations = record.get("n")
        if not isinstance(monthly, (int, float)) or not math.isfinite(monthly) or not 0 <= monthly <= 1:
            gate.error(f"volatility.{factor}.monthly", f"invalid monthly volatility: {monthly}")
        if not isinstance(observations, int) or observations < 24:
            gate.error(f"volatility.{factor}.observations", f"requires at least 24 observations, got {observations}")

    correlations = latest.get("corr") or {}
    if len(correlations) < 10:
        gate.error("correlation.coverage", f"only {len(correlations)} correlation pairs")
    else:
        gate.ok("correlation.coverage", f"{len(correlations)} correlation pairs")
    for pair, value in correlations.items():
        if "|" not in pair or not isinstance(value, (int, float)) or not math.isfinite(value) or not -1 <= value <= 1:
            gate.error(f"correlation.{pair}", f"invalid correlation: {value}")

    return latest


def validate_history(gate: Gate, history: dict | None = None):
    history = history if history is not None else read_json(DATA / "history.json")
    dates = history.get("dates") or []
    if not dates:
        gate.error("history.dates", "history has no dates")
        return history
    parsed = [parse_datetime(value) for value in dates]
    if any(value is None for value in parsed):
        gate.error("history.dates", "history includes an invalid date")
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        gate.error("history.order", "history dates must be sorted and unique")
    else:
        gate.ok("history.order", f"{len(dates)} sorted, unique dates")
    if len(dates) > 730:
        gate.error("history.retention", f"history exceeds the documented 730-day cap: {len(dates)}")
    elif len(dates) < 84:
        gate.warn("history.validation-window", f"{len(dates)} score snapshots; outcome labels and a longer evaluation window are still required")
    else:
        gate.ok("history.validation-window", f"{len(dates)} score snapshots retained; outcome labels are still required for validation")
    scores = history.get("scores") or {}
    for risk_id, values in scores.items():
        if len(values) != len(dates):
            gate.error(f"history.{risk_id}.length", f"{len(values)} scores for {len(dates)} dates")
        if any(not isinstance(value, (int, float)) or not 0 <= value <= 100 for value in values):
            gate.error(f"history.{risk_id}.bounds", "scores must be numeric and between 0 and 100")
    return history


def validate_registries(gate: Gate):
    model_registry = read_json(DATA / "model-registry.json")
    models = model_registry.get("models") or []
    model_ids = [model.get("id") for model in models]
    if not models or None in model_ids or len(model_ids) != len(set(model_ids)):
        gate.error("model-registry.ids", "model IDs must be present and unique")
    else:
        gate.ok("model-registry.ids", f"{len(models)} unique model records")
    for model in models:
        for field in ("version", "status", "decision_ready", "outputs", "metrics_required", "limitations"):
            if field not in model:
                gate.error(f"model-registry.{model.get('id')}.{field}", "required field is missing")

    evidence_registry = read_json(DATA / "evidence-registry.json")
    evidence = evidence_registry.get("evidence") or []
    evidence_ids = [item.get("id") for item in evidence]
    if not evidence or None in evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
        gate.error("evidence-registry.ids", "evidence IDs must be present and unique")
    else:
        gate.ok("evidence-registry.ids", f"{len(evidence)} unique evidence records")
    for item in evidence:
        for field in ("claim_id", "source_url", "publisher", "source_type", "accessed_at", "verification_status", "confidence"):
            if not item.get(field):
                gate.error(f"evidence-registry.{item.get('id')}.{field}", "required field is missing")
        url = urlparse(item.get("source_url") or "")
        if url.scheme != "https" or not url.netloc:
            gate.error(f"evidence-registry.{item.get('id')}.url", "source URL must be an absolute HTTPS URL")

    benchmarks = read_json(DATA / "benchmarks.json")
    for index, benchmark in enumerate(benchmarks.get("benchmarks") or []):
        sources = benchmark.get("official_sources") or []
        if not sources:
            gate.error(f"benchmarks.{index}.sources", "at least one official source is required")
        for source in sources:
            url = urlparse(source)
            if url.scheme != "https" or not url.netloc:
                gate.error(f"benchmarks.{index}.url", f"invalid official source: {source}")


def validate_public_copy(gate: Gate):
    public_files = [ROOT / "index.html", ROOT / "README.md"]
    forbidden = {
        "80–125%": "legacy Ind AS 39 bright-line wording",
        "80-125%": "legacy Ind AS 39 bright-line wording",
        "breachProb30d": "uncalibrated index aliased as a probability",
        "Six independent model families": "false independence claim",
        "official sources only": "false source-quality claim",
        "GPD fit diagnostics": "non-existent EVT diagnostic claim",
        "1.3 (calibrated)": "false calibration claim",
        "adv:{buyer:": "public business-development targeting data",
        "tab-pipeline": "public pursuit pipeline",
        "First talking point": "public sales talking point"
    }
    hits = []
    for path in public_files:
        text = path.read_text(encoding="utf-8")
        for token, reason in forbidden.items():
            if token.lower() in text.lower():
                hits.append(f"{path.name}: {reason} ({token})")
    if hits:
        for index, hit in enumerate(hits):
            gate.error(f"public-copy.{index + 1}", hit)
    else:
        gate.ok("public-copy", "no blocked trust or confidentiality phrases found")


def source_health(latest: dict, now: datetime):
    sources = []
    for key, record in (latest.get("spot") or {}).items():
        if not isinstance(record, dict) or "asof" not in record:
            continue
        as_of = parse_datetime(str(record.get("asof")))
        age_days = None if as_of is None else (now - as_of).total_seconds() / 86400
        source = str(record.get("src") or "unknown")
        is_manual = "manual" in source.lower()
        if age_days is None:
            state = "unavailable"
        elif is_manual and age_days > 14:
            state = "stale"
        elif age_days > 7:
            state = "delayed"
        else:
            state = "manual" if is_manual else "live"
        sources.append({"id": key, "state": state, "as_of": record.get("asof"), "age_days": None if age_days is None else round(age_days, 1), "source": source})
    return sources


def validate_all(now: datetime | None = None, latest_override: dict | None = None, history_override: dict | None = None):
    now = now or datetime.now(timezone.utc)
    gate = Gate()
    latest = validate_latest(gate, now, latest_override)
    validate_history(gate, history_override)
    validate_registries(gate)
    validate_public_copy(gate)
    health = {
        "generated": now.isoformat(timespec="seconds"),
        "overall": "blocked" if gate.errors else "degraded" if gate.warnings else "healthy",
        "error_count": len(gate.errors),
        "warning_count": len(gate.warnings),
        "checks": gate.checks,
        "sources": source_health(latest, now)
    }
    return gate, health


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-health", action="store_true", help="write data/health.json")
    args = parser.parse_args()
    gate, health = validate_all()
    if args.write_health:
        with (DATA / "health.json").open("w", encoding="utf-8") as handle:
            json.dump(health, handle, indent=2)
            handle.write("\n")
    for check in gate.checks:
        print(f"{check['status'].upper():7} {check['id']}: {check['detail']}")
    print(f"\nPublication gate: {health['overall']} — {len(gate.errors)} error(s), {len(gate.warnings)} warning(s)")
    return 1 if gate.errors else 0


if __name__ == "__main__":
    sys.exit(main())
