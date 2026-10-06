"""Generator-independent finite checks for the set-family core.

This harness bypasses policy parsing and the owned case generator.  It compares
(1) the two-layer matching formula with exhaustive hitting-set optimization on
random disjoint support layers, and (2) two exact algorithms on unrestricted
finite set families.  These checks are finite evidence, not a general proof.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import time
from pathlib import Path

SEED = 20260929
DIRECT_CASES = 2800
GENERAL_CASES = 1200


def hits_all(chosen: set[int], supports: list[set[int]]) -> bool:
    return all(chosen & support for support in supports)


def exhaustive(universe: list[int], supports: list[set[int]]) -> int:
    for size in range(len(universe) + 1):
        for choice in itertools.combinations(universe, size):
            if hits_all(set(choice), supports):
                return size
    raise AssertionError("finite nonempty supports must be hittable")


def mask_dp(universe: list[int], supports: list[set[int]]) -> int:
    full = (1 << len(supports)) - 1
    cover = []
    for request in universe:
        mask = 0
        for index, support in enumerate(supports):
            if request in support:
                mask |= 1 << index
        cover.append(mask)
    reachable = {0}
    for request_mask in cover:
        reachable |= {mask | request_mask for mask in tuple(reachable)}
    # Use a second, independent cardinality DP rather than the subset loop above.
    infinity = len(universe) + 1
    values = [infinity] * (full + 1)
    values[0] = 0
    for request_mask in cover:
        old = values[:]
        for mask, value in enumerate(old):
            if value < infinity:
                merged = mask | request_mask
                values[merged] = min(values[merged], value + 1)
    if full not in reachable or values[full] == infinity:
        raise AssertionError("finite nonempty supports must be hittable")
    return values[full]


def maximum_matching(left_count: int, right_count: int, edges: set[tuple[int, int]]) -> int:
    adjacency = [[] for _ in range(left_count)]
    for left, right in sorted(edges):
        adjacency[left].append(right)
    owner: dict[int, int] = {}

    def augment(left: int, seen: set[int]) -> bool:
        for right in adjacency[left]:
            if right in seen:
                continue
            seen.add(right)
            if right not in owner or augment(owner[right], seen):
                owner[right] = left
                return True
        return False

    for left in range(left_count):
        augment(left, set())
    return len(owner)


def direct_instance(rng: random.Random) -> tuple[list[int], list[set[int]], list[set[int]], set[tuple[int, int]]]:
    left_count = rng.randint(1, 5)
    right_count = rng.randint(1, 5)
    density = rng.choice((0.15, 0.30, 0.50, 0.75))
    edges = {
        (left, right)
        for left in range(left_count)
        for right in range(right_count)
        if rng.random() < density
    }
    left = [set() for _ in range(left_count)]
    right = [set() for _ in range(right_count)]
    request = 0
    # One request per overlap edge makes the cross-layer incidence exact.
    for l_index, r_index in sorted(edges):
        left[l_index].add(request)
        right[r_index].add(request)
        request += 1
    # Isolated blocks receive private requests; optional private requests vary size.
    for support in left + right:
        if not support or rng.random() < 0.30:
            support.add(request)
            request += 1
    universe = list(range(request))
    return universe, left, right, edges


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='optional destination outside retained reference results')
    args = parser.parse_args()
    started = time.process_time()
    rng = random.Random(SEED)
    direct_passed = 0
    for _ in range(DIRECT_CASES):
        universe, left, right, edges = direct_instance(rng)
        matching = maximum_matching(len(left), len(right), edges)
        predicted = len(left) + len(right) - matching
        observed = exhaustive(universe, left + right)
        assert observed == predicted, (observed, predicted, left, right, edges)
        direct_passed += 1

    general_passed = 0
    for _ in range(GENERAL_CASES):
        universe = list(range(rng.randint(1, 9)))
        support_count = rng.randint(1, min(9, 2 ** len(universe) - 1))
        supports = []
        for _support in range(support_count):
            support = {request for request in universe if rng.random() < 0.38}
            if not support:
                support = {rng.choice(universe)}
            supports.append(support)
        assert exhaustive(universe, supports) == mask_dp(universe, supports)
        general_passed += 1

    result = {
        "status": "PASS",
        "seed": SEED,
        "direct_disjoint_support_families": direct_passed,
        "unrestricted_finite_set_families": general_passed,
        "cpu_seconds": time.process_time() - started,
        "scope": "finite generator-independent validation; not a machine-checked general proof",
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
