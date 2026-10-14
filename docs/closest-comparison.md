# Closest objective and semantic boundary checks

The [author-hosted coverage-selection paper](https://www.mouelhi.com/uploads/1/8/2/6/1826097/sectest14-coverage-selection-ac.pdf)
was read in complete extracted text, with its result figure inspected. Its
Sections III/IV distinguish target/condition coverage selection from a
mutation-informed greedy comparator at the coverage suite's fixed budget.
That comparator has the mutation information; it is not an exact minimum
full-detectable-coverage solver. This supports an objective distinction, not
a claim that prior work lacked mutation information or that PolicySuite is a
native reproduction of their six policies.

The [four-page policy-evolution postprint](https://orbilu.uni.lu/bitstream/10993/16020/1/test_selection_ase2012-short.pdf)
was likewise read in complete extracted text, with method figures and cost
tables inspected. Sections 3.1--3.3 separate mutation-based rule/test correlation,
coverage correlation, and recorded-request decision changes. Table 2 separates
correlation/recording from later selection cost. PolicySuite's support tabulation
is therefore included in the paired workflow costs, not treated as free input
when discussing the finite method's cost. No upstream system or native source
is executed or incorporated.

The supplied ordinary exact comparator is the existing generic recurrence on
identical tables, complete inventory, supports and joint quotient. It shares
producer code and is not an independent external solver; the separate checker
recomputes semantics for both proof forms. The optimum equality on the two
eligible retained fixtures is preserved, as are default historical greedy/null
results. These checks calibrate this bounded implementation, not all related
work or a systematic novelty search.

[XACML 3.0 plus Errata 01](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-en.html)
Sections 7.11--7.14 and Appendix C.8 were checked for rule/policy target gates,
typed errors, root error collapse and first-applicable stopping behavior. A
native translator must preserve each declared mutant as well as its reference.
For example, an enclosing policy target that does not match still gates the
policy after a rule-target edit; replacing a flattened joint table by constant
true need not preserve that gate. This is an unresolved translation obligation,
not a claimed experiment with a native PDP. No importer or such PDP is supplied.

Only these specific sources and passages were freshly checked. Inherited
metadata/context records for the other bibliography items are not converted
into full-text certification or independent novelty clearance.
