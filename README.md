# Conflict-aware minimal regression

This repository contains exact finite request-suite selection, two separately implemented policy semantics, a certificate checker, complete written arguments, and reproducible owned validation. It is a research artifact for **Certifying Minimum Request Suites for Two Access-Control Policy Snapshots**. It is not a production policy engine or a native XACML importer.

## What is supported

For two snapshots whose inclusion-minimal nonempty mutation supports are disjoint within each snapshot, the minimum common suite has size `a+b−maximum_matching`. The producer extracts a covering suite and an equally sized packing of actual mutation supports. Error-free first-applicable policies and masked-laminar override policies with all local flips/deletions meet sufficient semantic conditions. Other finite instances use a complete, bounded recurrence certificate rather than an asserted heuristic optimum.

Written proofs also establish a sharp factor-two disjoint-packing gap for two first-applicable snapshots with public errors, three-snapshot NP-completeness even for disjoint error-free permit rules, and output-preserving DO/FA revisions whose local minimum grows from one to n (the retained all-permit PO contrast grows from zero to n). General proofs are mathematical text, not proof-assistant mechanizations.

An explicit `--fa-local` route now constructs the tight one-snapshot
first-applicable packing even when public errors make flip/delete supports
incomparable. It requires the complete local profile and refuses other scopes.
The default route and all historical campaign proof classes remain unchanged.
This is a theorem-to-production connection, not a new set-cover algorithm.

The retained campaign has **144 owned cases**: 120 generated and 24 fixtures. There are 111 packing and 33 recurrence certificates. All 144 passed the separately coded checker. Native full-XACML replay is outside the retained model because the artifact has no semantics-preserving importer. See `proofs/theorems.md`, the claim ledger, and `docs/limitations.md` for precise boundaries.

## Run from a clean extraction

Requirements: Python 3.10 or later with the standard library, on Linux with `resource` and `signal` support. No packages need downloading. There are no model calls, external solvers, native services, GPUs, network operations, or background workers. Commands are run from this directory.

```sh
python reproduce.py --output /tmp/conflict-regression-replay
```

The output path must not exist. The command regenerates all 144 exact input objects, executes the tiny oracles, error-boundary tests, input-contract regressions, generator-independent checks and request-order checks, then runs the campaign and stronger greedy challenge. It compares 296 deterministic JSON outputs and four CSV outputs with the retained evidence. An additional portable replay checks all 144 inputs using both optimization routes. It writes `reproduction.json`, per-child stdout/stderr logs, real exit codes and timings into the chosen output directory. It refuses to overwrite the reference evidence. Exit zero means those finite checks and comparisons succeeded.

One case can be optimized and independently checked without any campaign:

```sh
python src/optimize.py data/cases/fixture-017.json /tmp/conflict-suite.json
python src/checker.py data/cases/fixture-017.json /tmp/conflict-suite.json
```

The checker exits zero on acceptance and two on rejection. For an uncovered detectable mutation, its JSON output includes the first missed mutation in declared order, the least distinguishing request index, the concrete request, and the unequal reference/mutant observations. Empty supports are explicitly inventoried as equivalent on the finite domain, not silently counted as covered.

For the public-error single-snapshot route and its ordinary exact comparison:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B src/optimize.py data/cases/fixture-007.json fa-suite.json --fa-local
PYTHONDONTWRITEBYTECODE=1 python -B src/checker.py data/cases/fixture-007.json fa-suite.json
PYTHONDONTWRITEBYTECODE=1 python -B src/optimize.py data/cases/fixture-007.json ordinary-suite.json --force-dp
PYTHONDONTWRITEBYTECODE=1 python -B tests/test_fa_constructor.py -v
PYTHONDONTWRITEBYTECODE=1 python -B src/fa_comparison.py --cases data/cases --work fa-wire-work --out fa-cost-results
```

Choose fresh certificate paths and fresh disjoint cost directories. The same-
information ordinary exact baseline is the existing general recurrence, not an
external or independently implemented optimizer. Both obtain the full declared
table/inventory and the same joint quotient; the separately coded checker
recomputes all supports. The six constructor methods connect the existing
2,971-case theorem domain to the actual production entry, plus named scope,
quotient, witness and null controls. A portable 144-case default/forced replay
still reproduces historical structures, 111/33 proof classes and 32/25 greedy
excess counts. It does not claim Linux resource-guard execution.

`results/fa-local/` records five alternating paired repetitions on the two
eligible **unchanged** retained cases, fixtures 004 and 007. All twenty proof
checks pass; both routes have optimum one. Ordinary DAG states are 2/3, while
the constructor uses none. Timed phases include input reading, all producer
semantics/quotient/selection work, certificate file roundtrip, and independent
semantic/proof checking. Process startup/imports, experiment packaging and
native-policy execution are excluded. Observed tiny CPU samples are zero at
the timer's effective resolution; RSS is unmeasured. No speedup or deployment-
cost claim is drawn. `results/fa-local-checks/` preserves actual public command
logs, inputs, certificates, verdicts and source/environment bindings. Historical
measurements remain separate. See `docs/fa-local.md` for the proof connection,
cost scope and unresolved native-translation obligations.

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
python tests/test_input_contract.py
python -B tests/test_sparse_transpose.py -v
python tests/test_generator_independence.py --output /tmp/conflict-generator-checks.json
python tests/test_metamorphic.py --output /tmp/conflict-request-order.json
python tests/test_retained_replay.py --output /tmp/conflict-portable-replay
python src/generate.py /tmp/conflict-owned-inputs
python src/run_campaign.py --cases data/cases --output /tmp/conflict-campaign --start 0 --stop 144
python src/kernel_baseline.py --cases data/cases --output /tmp/conflict-kernel.json
```

The main runner supports `--start`, `--stop`, and `--resume` for bounded chunks. Use a fresh output directory for a clean reproduction. `--resume` deliberately trusts existing output files and is not a substitute for the clean command. The reproduction driver runs one child at a time and imposes a 45-second subprocess deadline; the campaign also has a 60-second whole-case guard, a 2.75 GiB address-space limit, and a 100,000-state exact-fallback cap. A failure is recorded, never converted into an optimality claim. The portable replay does not exercise Linux resource guards and does not replace the guarded campaign. The generator-independent and request-order tests print their results by default and only write to an explicitly supplied output path.

`.github/workflows/scientific-checks.yml` runs the complete offline reproduction sequentially on Linux for pushes to `main` and manual dispatch. It uses a 720-second outer bound, fails on any scientific failure, and uploads the actual raw output directory even when a check fails. The workflow itself does not imply that a hosted run has occurred.

## Evidence layout

The recurrence producer initializes request rows once, then transposes only the
set request bits of each support into the original mutation-position columns.
Request order, first duplicate-row representatives, pivots, children, suite ties,
complete states and refusal guards are retained. No runtime improvement is
measured. Five additional self-contained regression methods compare actual
production routines with subset-enumerated optima and a complete-child closure,
exercise fixed-clock budget boundaries, and check real finite policy supports
with the unchanged independent checker. The reproduction driver/CI runs this
module explicitly; it adds a raw stage log, not a replacement for archived counts
or any additional equality exclusion. Historical 2,800/1,200 generator checks
remain the independent algorithms originally reported, not retroactively
claimed production-core executions.

`src/` contains the producer, independent checker, deterministic generator, baselines, runner, and table derivation. `tests/` contains exact subset oracles and constructive boundary checks. `data/cases/` is the fixed 144-case owned corpus; `data/proof-cases/` contains four additional theorem constructions, not public benchmark cases. `results/campaign/` contains all original case records and certificates, including failed-suite witnesses; `results/derived/` contains numeric tables and plot data. `results/kernel-greedy.json` is the separately labeled post-protocol stronger baseline. `proofs/theorems.md` is standalone and does not require the paper directory. Source-attribution and claim-evidence CSVs are at this repository root.

## Reproducibility contract

Case inputs and deterministic results must agree exactly as JSON objects. CPU time, wall time, peak RSS, and measured certificate byte length containing a timing field are excluded from equality comparisons; the exact excluded keys are emitted by the reproduction driver. No timing figure is represented as repeatable bit-for-bit. Certificates are compared structurally after excluding their timing field, and newly generated certificates are already checked against the complete fresh inputs. The artifact does not need a checksum or toolchain fingerprint to run.

The original campaign records 5,522,547 conservative checking steps and 3.347 summed process CPU seconds. Workloads actually use at most 32 requests, 21 rules per snapshot, and 84 declared mutations; supported input caps are not measured scale. The one-worker finite run is not a production performance study. The retained clean-extraction result is `results/reproduction.json`; per-run resource observations are in `results/resource-accounting.json`. Original measurements and fresh measurements are separate records.

## License

Original repository materials use the accompanying MIT license. No third-party solver, Balana code, native policy corpus, or external research PDF is redistributed here. The companion paper package's unmodified IEEE template assets retain their own notices.

## Local paper-reference checks

The complete project packet includes a paper-side release checker:

```sh
python -B ../paper/audit_references.py --paper-dir ../paper --output-dir paper-audit-new
```

Run that optional command from this artifact directory only when the sibling
`../paper/` directory from the complete project packet is present.
It checks 61 scholarly references, TeX citation use, DOI/title/key uniqueness,
the canonical Hopcroft and Karp identifiers, the emitted bibliography, the
supplied 12-page budget, and source-to-PDF modification order. IEEE style-control
entries are counted separately. PDF tool output is decoded explicitly as UTF-8.
The manuscript has 12 pages and its supplement has three. Generate a matching
BBL before running the command and choose a fresh output path. Results are
labeled `local_structure_only`: publisher identity and cited-sentence support
require separate source reading. Retained audit records remain historical
observations. This optional check belongs to the complete project packet;
standalone scientific reproduction is independent of the paper directory.
