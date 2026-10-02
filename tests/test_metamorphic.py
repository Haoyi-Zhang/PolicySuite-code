"""Request-order metamorphic test over all retained campaign cases."""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARTIFACT / "src"))
import checker
from optimize import optimize


def reverse_requests(case: dict) -> dict:
    transformed = copy.deepcopy(case)
    transformed["id"] = case["id"] + "-request-reversed"
    transformed["requests"] = list(reversed(case["requests"]))
    for policy in transformed["policies"]:
        for rule in policy["rules"]:
            rule["match"] = rule["match"][::-1]
    return transformed


def main() -> None:
    started = time.process_time()
    cases = sorted((ARTIFACT / "data" / "cases").glob("*.json"))
    certificate_dir = ARTIFACT / "results" / "campaign" / "certificates"
    passed = 0
    packing = 0
    recurrence = 0
    for case_path in cases:
        case = json.loads(case_path.read_text(encoding="utf-8"))
        original = json.loads((certificate_dir / case_path.name).read_text(encoding="utf-8"))
        transformed = reverse_requests(case)
        certificate = optimize(transformed)
        result = checker.check(transformed, certificate)
        assert result["accepted"]
        assert len(certificate["suite"]) == len(original["suite"])
        passed += 1
        packing += certificate["kind"] == "packing"
        recurrence += certificate["kind"] == "recurrence"
    output = {
        "status": "PASS",
        "transformation": "reverse the request order and every rule's activation table",
        "cases": passed,
        "packing_certificates": packing,
        "recurrence_certificates": recurrence,
        "minimum_sizes_preserved": passed,
        "cpu_seconds": time.process_time() - started,
        "scope": "metamorphic request-order invariance on the retained finite campaign",
    }
    path = ARTIFACT / "results" / "metamorphic-request-order.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
