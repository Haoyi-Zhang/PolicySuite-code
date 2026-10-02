# Final artifact-only audit

## Release result

**PASS for the retained finite internal-research scope.** The packet does not claim acceptance, independent review, native full-XACML replay, deployment evidence, or systematic novelty clearance.

## Bibliography and citation gate

- BibTeX entries: **61**; unique keys: **61**.
- Unique cited keys: **61**; total citation occurrences: **70**.
- Generated `main.bbl` items: **61**; compiled PDF contains reference **[61]**.
- Missing keys, uncited entries, duplicate keys, duplicate normalized titles, duplicate DOI values, unclassified keys, and invalid DOI strings: **0**.
- DOI-bearing records: **60**; sole no-DOI record: official OASIS XACML 3.0 standard.
- Hopcroft--Karp maximum matching appears once as `hopcroft1973`; Karp reducibility appears once as `karp1972`.
- Required metadata are present for all 61 records, with the formal standard checked under its standards-body fields.

The row-level evidence is `results/reference-audit.csv`; the machine gate is `results/reference-audit.json`; verification scope is documented in `docs/reference-verification.md` and `external_resources.csv`.

## Source, BBL, PDF, and layout synchronization

`main.pdf` was rebuilt after `main.tex`, `references.bib`, and `main.bbl`; all source/PDF timestamp checks pass. The main paper is exactly 12 letter-size double-column pages and the supplement is three pages. The LaTeX logs contain no undefined citation/reference and no overfull box. Fonts are embedded Type 1 with no Type 3. Rendering produced 12 main and three supplement pages at 200 dpi; page 12 contains references [14]--[61] without clipping or overlap.

## Scientific artifact replay

A fresh output directory was used. The reproduction command reports `accepted=true`, 144 campaign cases, 144 regenerated owned inputs, 4 proof inputs, 294 matching deterministic JSON outputs, and 4 matching CSV outputs, offline with one worker and the separately coded checker.

Focused checks pass:

- 3905 scalar policies and 1715 exact finite cases;
- 13107 structural evaluations and 2704 two-layer family pairs;
- 2971 public-error first-applicable cases and four exact sharp-gap constructions;
- 2800 generator-independent disjoint support families and 1200 unrestricted set families;
- 144/144 request/rule-order metamorphic cases, retaining 111 packing and 33 recurrence certificates.

The retained campaign has 4862 declared mutations, 3108 detectable and 1754 equivalent obligations. Full greedy exceeds the optimum in 32 cases and the post-protocol stronger challenge in 25; these are descriptive finite results, not population estimates.

## Scope and remaining external-use checks

The final empirical scope is deliberately the 144 owned finite cases. Native full-language import, external PDP replay, public deployment breadth, policy intent, and production safety are non-claims. The 61-source bibliography is a relevance-first identity and citation-context audit; unavailable full texts are not used to infer absent prior results, and the manuscript makes no first-in-literature claim.

First-party IEEE Computer Society guidance confirms the journal template requirement, the 12-formatted-page regular Transactions publication limit including references, a 100--200 word journal abstract, separate supplemental files, and TDSC's single-anonymous route. Human authors must recheck the actual submission portal and current journal-specific overrides at submission time.

## Clean-package verification

The machine-readable clean-extraction record is `results/clean-package-verification.json`. It is regenerated after final packaging and records ZIP integrity, single-root shape, replay/test results, reference gate, PDF page counts, and rebuilt-PDF text equality. Successful commands are finite evidence, not an independent blind review.
