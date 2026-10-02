# Reference verification and source/PDF synchronization

The final manuscript contains **61 unique bibliography records** and cites all 61 keys in claim-specific related-work or attribution sentences. The generated `main.bbl` contains 61 items. `artifact/results/reference-audit.json` is the executable release gate; `reference-audit.csv` records title, authors, year, venue, DOI or official URL, citation count, section, and surrounding citation context for every record.

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

Sixty records carry unique DOI identifiers; the remaining item is the official OASIS XACML 3.0 standard. The release gate checks required metadata, DOI syntax, key/title/DOI uniqueness, citation use, BBL emission, the presence of reference [61] in the compiled PDF, 12-page length, and source-to-PDF modification order. Metadata and claim fit were reviewed against DOI, publisher, institutional, or standards-body records. This is a bibliographic audit, not independent peer review and not a redistribution of copyrighted full texts.
