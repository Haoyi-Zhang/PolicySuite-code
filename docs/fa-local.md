# Constructive one-snapshot FA route

`src/optimize.py --fa-local` implements the public-error lemma in
`proofs/theorems.md` section 5. It accepts exactly one first-applicable snapshot
with the complete local flip/delete profile; errors are allowed. The ordinary
default matching/recurrence route remains unchanged. This explicit mode does
not apply the one-layer conclusion to two snapshots, to overrides or to a
declared/extended subset.

After complete finite semantic evaluation and the unchanged joint-signature
quotient, each rule supplies its flip and deletion support. Their union belongs
to that rule's first-nonfalse visibility region. The constructor chooses the
least shared request when the two supports intersect, otherwise the least
request in each nonempty support. It names one actual support for each chosen
request. Different visibility regions are disjoint, so the resulting adequate
suite and equally sized packing certify the minimum using the unchanged checker.
The constructor never runs the general recurrence or assumes that the two
supports themselves form a disjoint minimal layer.

This closes a theorem-to-production gap, not a new hitting-set or matching
algorithm. On retained fixture 007, the ordinary recurrence and the constructor
both select request 1 and certify minimum one. The ordinary proof has three DAG
states; the constructor supplies one packing support. Default historical output
is still the recurrence. Joint quotient lifting, finite equivalents, complete
profile admission and canonical missed-mutation witnesses are unchanged.

## Same-information ordinary exact comparison and costs

Run `src/fa_comparison.py` with fresh disjoint `--work` and `--out` directories.
It inventories all 144 retained inputs without replacing them. Only fixtures
004 and 007 satisfy the constructor's explicit scope. For each, five alternating
paired repetitions use the same input, complete mutation inventory, semantic
matrix and joint quotient. The ordinary exact baseline is the existing generic
recurrence selected by `--force-dp`, not a new or independently implemented
external optimizer. The checker is separately coded and reconstructs all
original-domain supports before accepting either proof.

The actual twenty runs all check successfully and have the same optimum (one).
Ordinary recurrence states are 2/3 for fixtures 004/007; the constructor uses
zero recurrence states. This is a proof-construction difference, not a
cardinality improvement. `results/fa-local/` contains the exact inputs,
supports, every certificate/verdict, raw per-phase costs, the complete 144-input
scope with hashes, and source/environment bindings.

Timed phases include input file reading/parsing, production optimization
(including semantic tabulation and quotienting), certificate encoding/file
roundtrip, and independent semantic/proof checking. Imports, process startup,
benchmark result packaging and native-policy execution are excluded explicitly.
These are warm in-process Windows measurements; RSS is unmeasured. The CPU
clock's sub-resolution samples are recorded as observed zeros, not interpreted
as zero work. No speedup, scaling or deployment-cost claim is drawn.

The constructive phase scans at most two supports per rule and sorts selected
indices. Its bitset-operation cost is distinct from constructing those supports:
the current producer and checker still evaluate complete finite reference and
mutant rule lists, so the one-snapshot local profile has an `O(N R^2)` rule-visit
upper bound before proof checking. Bitset arithmetic, serialization and I/O
are additional costs; neither the scan nor the supported input ceilings certify
end-to-end scalability.

## Native-language translation remains unresolved

Inputs remain finite activation tables; no XACML importer or external PDP is
added. Reading combining passages is not native conformance. A future importer
must preserve not just reference outputs but every declared mutant's outputs.
In particular, policy-level targets cannot be silently conjoined into mutable
rule-activation tables: replacing a rule's table by constant true could then
remove an enclosing applicability gate. Request attributes, datatype/bag and
missing-attribute errors, policy targets, combining identifiers and the precise
source-level mutation must all be accounted for before claiming transfer.
No unowned policy or target is exercised here.
