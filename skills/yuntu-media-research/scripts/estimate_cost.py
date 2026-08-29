#!/usr/bin/env python3
"""Estimate RedFox request cost using documented tier classes."""

import argparse
import json
from pathlib import Path


BASE_PRICES = {"quality": 0.04, "realtime": 0.06}
TIERS = (
    (1000, 1.00),
    (5000, 0.90),
    (10000, 0.80),
    (20000, 0.70),
    (30000, 0.60),
    (None, 0.50),
)


def discount_for(cumulative_calls):
    for upper, discount in TIERS:
        if upper is None or cumulative_calls < upper:
            return discount
    return 0.50


def estimate_items(items, cumulative_calls=0):
    total = 0.0
    estimated_requests = 0
    unknown = []
    unknown_requests = 0
    lines = []
    current = int(cumulative_calls)
    for item in items:
        requests = int(item.get("requests", 0))
        price_class = item.get("price_class", "unknown")
        unit_price = item.get("unit_price")
        if unit_price is None:
            unit_price = BASE_PRICES.get(price_class)
        if requests < 0:
            raise ValueError("requests must be >= 0")
        if unit_price is None:
            unknown.append(item.get("operation", "unknown"))
            unknown_requests += requests
            lines.append({
                **item,
                "estimated_cost_cny": None,
                "public_price_range_cny": [round(requests * 0.02, 4), round(requests * 0.06, 4)],
                "reason": "unknown-current-endpoint-price",
            })
            current += requests
            continue
        line_cost = 0.0
        for _ in range(requests):
            line_cost += float(unit_price) * discount_for(current)
            current += 1
        estimated_requests += requests
        total += line_cost
        lines.append({**item, "estimated_cost_cny": round(line_cost, 4)})
    return {
        "starting_cumulative_calls": int(cumulative_calls),
        "ending_cumulative_calls": current,
        "priced_requests": estimated_requests,
        "estimated_cost_cny": round(total, 4),
        "estimated_total_range_cny": [round(total + unknown_requests * 0.02, 4), round(total + unknown_requests * 0.06, 4)],
        "unknown_price_operations": unknown,
        "items": lines,
        "price_basis": "Known classes use RedFox published quality/realtime tiers. Unknown classes use the public advertised 0.02-0.06 CNY range only as a planning range; endpoint docs and account bill remain authoritative.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, help="JSON file containing items[]")
    parser.add_argument("--cumulative-calls", type=int, default=0)
    parser.add_argument("--out")
    args = parser.parse_args()
    payload = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    result = estimate_items(payload.get("items", []), args.cumulative_calls)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
