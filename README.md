# Conflict-aware minimal regression

This repository contains exact finite request-suite selection, two separately implemented policy semantics, a certificate checker, complete written arguments, and reproducible owned validation. It is a research artifact for **Certifying Minimum Request Suites for Two Access-Control Policy Snapshots**. It is not a production policy engine or a native XACML importer.

## What is supported

For two snapshots whose inclusion-minimal nonempty mutation supports are disjoint within each snapshot, the minimum common suite has size `a+b−maximum_matching`. The producer extracts a covering suite and an equally sized packing of actual mutation supports. Error-free first-applicable policies and masked-laminar override policies with all local flips/deletions meet sufficient semantic conditions. Other finite instances use a complete, bounded recurrence certificate rather than an asserted heuristic optimum.

Written proofs also establish a sharp factor-two disjoint-packing gap for two first-applicable snapshots with public errors, three-snapshot NP-completeness even for disjoint error-free permit rules, and output-preserving DO/FA revisions whose local minimum grows from one to n (the retained all-permit PO contrast grows from zero to n). General proofs are mathematical text, not proof-assistant mechanizations.

The retained campaign has **144 owned cases**: 120 generated and 24 fixtures. There are 111 packing and 33 recurrence certificates. All 144 passed the separately coded checker. It is not the proposed 164-case public-and-generated campaign: native full-XACML replay is deliberately outside the retained model because the artifact has no semantics-preserving importer. The paper treats this as an external-validity limitation rather than relabeling public examples as compatible inputs. See `proofs/theorems.md`, the claim ledger, and `docs/limitations.md` for precise boundaries.

## Run from a clean extraction

Requirements: Python 3.10 or later with the standard library, on Linux with `resource` and `signal` support. No packages need downloading. There are no model calls, external solvers, native services, GPUs, network operations, or background workers. Commands are run from this directory.

```sh
python reproduce.py --output /tmp/conflict-regression-replay
```

The output path must not exist. The command regenerates all 144 exact input objects, executes the tiny oracles and error-boundary tests, runs the campaign and stronger greedy challenge, and compares every deterministic campaign result/certificate with the retained evidence. It writes `reproduction.json` into the chosen output directory. It refuses to overwrite the reference evidence. Exit zero means those finite checks and comparisons succeeded; it does not establish external or human review.

One case can be optimized and independently checked without any campaign:

```sh
python src/optimize.py data/cases/fixture-017.json /tmp/conflict-suite.json
python src/checker.py data/cases/fixture-017.json /tmp/conflict-suite.json
```

The checker exits zero on acceptance and two on rejection. For an uncovered detectable mutation, its JSON output includes the first missed mutation in declared order, the least distinguishing request index, the concrete request, and the unequal reference/mutant observations. Empty supports are explicitly inventoried as equivalent on the finite domain, not silently counted as covered.

The retained refinement interpretation has a separate read-only reconciliation command:

```sh
python src/audit_refinement.py
```

It verifies that the 20 unchanged refinement records comprise 13 DO/FA cases with old minimum one and seven all-permit PO cases with old minimum zero, while all common minima equal the block count and all public output deltas are empty. This is a record audit, not a new benchmark run.

## Focused commands

```sh
python tests/test_core.py
python tests/test_structure.py
python tests/test_error_boundary.py
python tests/test_generator_independence.py
python tests/test_metamorphic.py
python src/generate.py /tmp/conflict-owned-inputs
python src/run_campaign.py --cases data/cases --output /tmp/conflict-campaign --start 0 --stop 144
python src/kernel_baseline.py --cases data/cases --output /tmp/conflict-kernel.json
```

The main runner supports `--start`, `--stop`, and `--resume` for bounded chunks. Use a fresh output directory for a clean reproduction. `--resume` deliberately trusts existing output files and is not a substitute for the clean command. The reproduction driver runs one child at a time and imposes a 45-second subprocess deadline; the campaign also has a 60-second whole-case guard, a 2.75 GiB address-space limit, and a 100,000-state exact-fallback cap. A failure is recorded, never converted into an optimality claim.

## Evidence layout

`src/` contains the producer, independent checker, deterministic generator, baselines, runner, and table derivation. `tests/` contains exact subset oracles and constructive boundary checks. `data/cases/` is the fixed 144-case owned corpus; `data/proof-cases/` contains four additional theorem constructions, not public benchmark cases. `results/campaign/` contains all original case records and certificates, including failed-suite witnesses; `results/derived/` contains numeric tables and plot data. `results/kernel-greedy.json` is the separately labeled post-protocol stronger baseline. `proofs/theorems.md` is standalone and does not require the paper directory. Source-attribution and claim-evidence CSVs are at this repository root.

## Reproducibility contract

Case inputs and deterministic results must agree exactly as JSON objects. CPU time, wall time, peak RSS, and measured certificate byte length containing a timing field are excluded from equality comparisons; the exact excluded keys are emitted by the reproduction driver. No timing figure is represented as repeatable bit-for-bit. Certificates are compared structurally after excluding their timing field, and newly generated certificates are already checked against the complete fresh inputs. The artifact does not need a checksum or toolchain fingerprint to run.

The original campaign records 5,522,547 conservative checking steps and 3.347 summed process CPU seconds. Workloads actually use at most 32 requests, 21 rules per snapshot, and 84 declared mutations; supported input caps are not measured scale. The one-worker finite run is not a production performance study. The retained clean-extraction result is `results/reproduction.json`; the observed CPU boundary and separate run counts are in `results/resource-accounting.json`. Aggregate exploratory logical-step accounting is not fully certified; retained-run and clean-replay counts are reported separately rather than presented as an exact record of every development attempt.

## License and assistance

Original repository materials use the accompanying MIT license. No third-party solver, Balana code, native policy corpus, or external research PDF is redistributed here. The companion paper package's unmodified IEEE template assets retain their own notices. ChatGPT was used substantively in formulation, proof drafting, code, finite execution, and documentation; this is not a claim of human-only authorship or independent validation. External use requires human assessment of rights, authorship, scientific responsibility, and the relevant disclosure rules.

## Paper-reference release audit

The complete project packet includes a paper-side release checker:

```sh
python paper/audit_references.py --paper-dir paper --output-dir artifact/results
```

It verifies the 61-entry bibliography, TeX citation use, DOI/title/key uniqueness, the canonical Hopcroft and Karp records, the 61-item BBL, the 12-page PDF, and source-to-PDF modification order. Its retained output is `results/reference-audit.json`; the row-level citation-context ledger is `results/reference-audit.csv`. This optional release check belongs to the complete project package; the standalone scientific reproduction above remains independent of `paper/`.
