# The chassis's judgement, scored

**The claim under test**, from
[`protocol/goal-definition-v1.md`](../protocol/goal-definition-v1.md):

> *Given a protein sequence alone, the chassis predicts the host modifications
> that published campaigns actually found necessary, in N of M cases.*

**N of M is now known.** 18 protein-paper rows, 14 papers, predictions frozen
and hashed before any answer was read.

Run: `python -I scripts/score_validation.py`

---

## The three numbers

| | | |
|---|---:|---|
| **Recall** | **8 of 8 = 100%** | of campaign actions the chassis can express, it named every one |
| **Precision** | **8 of 14 = 57%** | on rows where authors tested a modification and reported it failing |
| **Discrimination** | **0 of 2** | differential pairs where it called the two halves differently |

**Read in that order they look like a pass, a wobble, and a footnote. The right
order is the reverse.**

---

## Discrimination: 0 of 2, and the recall number is why

`MOD-secretion` was predicted for **18 of 18 targets**. Under the frozen
mapping, every chaperone campaign in the literature maps to it. So:

**100% recall is not an achievement. It is what always saying yes looks like.**

The two differential pairs are the whole point of the set, because in each one
the authors applied the same modification to two proteins and it worked for one:

| pair | protein | outcome | chassis predicted |
|---|---|---|---|
| **bip-1** | Bovine prochymosin | **helped** | MOD-secretion |
| | Thaumatin I | **not helped** | MOD-secretion |
| **pdi-2** | Human serum albumin | **helped** | MOD-secretion |
| | Human interleukin-1β | **not helped** | MOD-secretion |

**Identical call for both halves of both pairs.** The chassis does not get these
wrong so much as fail to have an opinion. It has no mechanism that could produce
a different answer for the two members of a pair, because the trigger is
"is this protein secreted", and both are.

---

## Precision: 57%, and these six are real false positives

Normally precision is unmeasurable here — a paper silent about chaperones might
mean nobody tried. **These six rows escape that**, because the authors applied
the modification and reported it not working:

| protein | outcome | what the chassis said |
|---|---|---|
| Human interleukin-1β | not helped | MOD-secretion |
| Thaumatin I | not helped | MOD-secretion |
| Human G-CSF | not helped | MOD-secretion |
| Bovine pancreatic trypsin inhibitor | not helped | MOD-secretion |
| *S. pombe* acid phosphatase | not helped | MOD-secretion |
| *A. niger* glucose oxidase | **actively hurt** | MOD-secretion |

The last one matters most. BiP overexpression **made glucose oxidase secretion
worse** — the protein accumulated in the ER. **The chassis recommended the
module that would have caused the damage.**

And note *S. pombe* acid phosphatase appears twice in this set, in two papers:
**PDI helped it 4-fold, BiP did nothing for it.** Both map to `MOD-secretion`.
The chassis gives one answer where the literature gives two, and cannot
represent the difference between PDI and BiP at all.

---

## The pre-registration held

[`validation/protocol-v1.md`](../validation/protocol-v1.md), committed with the
frozen predictions and **before any answer was extracted**, said:

> *"Expect high recall and near-zero discrimination. The chassis will name the
> right module most of the time because it names that module every time."*

> *"If that is what the scoring shows, the right conclusion is not that the
> chassis passed. It is that `MOD-secretion` as currently defined is not a
> prediction."*

**Recall 100%, discrimination 0 of 2.** The prediction was exact.

That matters for a reason beyond being right: it means the discipline worked.
The finding could not be dressed up afterwards, because the expectation and the
scoring rule were both in git before the answers existed.

### The freeze was checked, not assumed

`score_validation.py` refuses to run unless the predictions still hash to
`a50fe5c8ebf3679ae…` and none of `chassis_resolve.py`, `elongation.py`,
`chassis-v1.json` or `mapping-v1.tsv` has changed since freeze commit `7c1029c`.
It verified all five and then scored.

---

## The three rows the chassis could not win, declared in advance

| protein | what the campaign actually did |
|---|---|
| Measles hemagglutinin | heat shock at 37 °C at high cell density |
| Human GRP78/BiP | same temperature shift |
| Human IGF-1 | **mutated the product itself**, Lys27→Glu27 |

All three were declared **UNMAPPED** in the mapping file before scoring, and
they are excluded from recall rather than buried in its denominator.

**The IGF-1 row is the interesting one.** The fix was to change the protein, not
the host. The chassis takes the sequence as fixed input, so an entire class of
real solution — redesign the product — is outside what it can propose. That is
a scope limit worth knowing, and it did not surface until a real campaign was
scored against it.

---

## What this diagnoses, precisely

**The defect is not that the chassis is wrong. It is that two of its five
modules are not predictions.**

- **E3 / `MOD-secretion`** fires on `secreted == True` and nothing else.
- **G2 / `MOD-burden`** carries `always_required: true`.

Both appear in every answer by construction. A field that is always the same
value carries no information, and three quarters of what this tool says about a
secreted protein is one of those two.

**`MOD-glycan` and `MOD-sugarnt` are different** — 4 of 18, fired by sequons
plus product class. They are doing real work, and nothing in this set tested
them, because no glycoengineering campaign made it into the 14 papers. **That is
a gap in the set, not a credit to the chassis.**

---

## What the chassis would need to pass this

Stated as the test's output, since this is what the test was for:

1. **`MOD-secretion` has to become conditional.** It needs a reason to fire for
   one secreted protein and not another. The literature in this very set says
   what the axis is: PDI helped a protein with **no disulfide bonds**
   (β-glucosidase) and did not help a disulfide-rich one (thaumatin, 8 pairs).
   **Disulfide count is not that axis** — this set shows it pointing the wrong
   way.
2. **`MOD-secretion` has to split.** PDI, BiP, signal peptide and gene dosage
   are different interventions with different and sometimes opposite effects on
   the same protein. One module cannot represent "PDI yes, BiP no", which is
   the actual result for both β-glucosidase and acid phosphatase.
3. **`MOD-burden` has to stop being always-required**, or be dropped from the
   per-protein answer and stated once as a property of the chassis.
4. **Something has to represent "this protein needs nothing."** There is no such
   output today, and for the wild-type cutinase — secreted at 25 mg/g with no
   reported modification — that was the correct answer.

**None of these are implemented. This report is the evidence that they are
needed, not a plan that they exist.**

---

## What is not established

- **Answers come from abstracts only.** No full text was retrieved. A
  modification reported only in a paper's body is missing, which can only make
  recall look better than it is.
- **The denominators are small.** Recall rests on 8 rows, precision on 14,
  discrimination on 2 pairs. One reclassified row moves recall by 12 points.
- **Two differential pairs is thin.** The feasibility report asked for a set
  built around them; 2 pairs is the honest count of what 14 papers yielded, and
  the number should be several times that.
- **Precision is not the chassis's false-positive rate.** It is the rate on
  rows where someone published a failure. For most proteins nobody did.
- **Five of 18 rows are not *S. cerevisiae*.** The chassis is defined on
  *S. cerevisiae*; those rows carry a host-transfer assumption.
- **Three decades separate oldest and newest paper**, across strains, vectors,
  promoters and assays that are not comparable, and the set does not record
  those differences.
- **Product class was assigned by me, not computed.** Human or mammalian
  hormone counted as therapeutic, which is what decides whether `MOD-glycan`
  fires. Four rows depend on that call.
- **No glycoengineering campaign is in the set**, so the two modules that do
  discriminate were never tested.
- **Nothing here tests titre.** The chassis says which modules a product needs,
  never how much product you get.
- **The project's strongest counter-evidence is still not in the set** — the
  architecturally similar scFv pair that diverged under identical engineering.
  No PubMed record for it was resolved in this pass.
