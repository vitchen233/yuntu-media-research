#!/usr/bin/env python3
"""Rank evidence-backed topic cards with a transparent fixed formula."""

import argparse
import csv
import json
from pathlib import Path

FIELDS = {"demand": 0.25, "momentum": 0.20, "differentiation": 0.15, "evidence": 0.20, "shootability": 0.10, "asset_value": 0.10}


def score(card):
    total = 0
    for field, weight in FIELDS.items():
        value = float(card.get(field, 0))
        if not 0 <= value <= 5:
            raise ValueError(f"{field} must be between 0 and 5")
        total += value * weight
    return round(total - (0 if card.get("source_ids") else 2), 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    cards = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    ranked = sorted(((score(card), card) for card in cards), key=lambda item: (-item[0], item[1].get("topic_id", "")))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "topic_id", "score", "title", "readiness", "source_count"])
        for index, (value, card) in enumerate(ranked, 1):
            writer.writerow([index, card.get("topic_id"), value, card.get("title"), card.get("readiness"), len(card.get("source_ids", []))])
    print(f"ranked {len(cards)} topics -> {out}")


if __name__ == "__main__":
    main()
