# Reference verification and source/PDF synchronization

The manuscript contains **61 unique bibliography records** and cites all 61 keys in related-work or attribution sentences. The generated `main.bbl` contains 61 items. `artifact/results/reference-audit.json` and `reference-audit.csv` are retained outputs of an earlier local check, with title, authors, year, venue, DOI or official URL, citation count, section, and surrounding citation context for every record.

## Duplicate resolution

- `hopcroft1973` is the sole record for Hopcroft and Karp, *An n^(5/2) Algorithm for Maximum Matchings in Bipartite Graphs*, DOI `10.1137/0202019`.
- `karp1972` is the sole record for Karp, *Reducibility among Combinatorial Problems*, DOI `10.1007/978-1-4684-2001-2_9`.
- The audit rejects duplicate keys, normalized titles, or DOI values.

These are different works and remain separately cited for different purposes: maximum bipartite matching versus NP-completeness reductions.

## Added claim-specific sources

Six records were added only where the manuscript makes a corresponding comparison: XACML fault localization (`xu2016localization`), NGAC mutation analysis (`chen2021ngac`), the ABAC model overview (`hu2015abac`), extended ABAC evaluation under missing information (`morisset2019`), the policy-language survey (`han2012`), and quantitative policy permissiveness (`eiers2022`). Their DOI, title, author, venue, year, and page/article metadata are recorded in `references.bib`, `external_resources.csv`, and the row-level audit. None is used as evidence for this project's measured results.

## Metadata correction retained

The page range for Martin and Xie's *Automated Test Generation for Access Control Policies via Change-Impact Analysis* is pp. 5--12, rather than the earlier erroneous single-page value.

## Verification boundary

Sixty records carry unique DOI identifiers; the remaining item is the official OASIS XACML 3.0 standard. The local command checks required metadata, DOI syntax, key/title/DOI uniqueness, citation use, BBL emission, the presence of reference [61] in the compiled PDF, 12-page length, and source-to-PDF modification order. It does not retrieve external sources or read their results. New rows therefore use `local_structure_only` and do not assign a source-verification date. Historical source-review assertions in retained outputs are distinct from what this executable can establish. Publisher identity and whether a citation supports a sentence require separate primary-source reading.
