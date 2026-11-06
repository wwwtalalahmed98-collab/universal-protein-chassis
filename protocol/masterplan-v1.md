# UCP-1 master plan, version 1

**Approved 2026-11-06.** This is the reference document for the project's
sequencing. Phases are revised as they complete; revisions are recorded here and
in `docs/PROJECT-STORY.md` rather than by overwriting.

**Owner decisions behind it:** open-ended horizon, no deadline. All four
definitions of done in scope — a proven discriminating tool, a preprint, a
wet-lab-buildable spec, and machine-executable output — which forces the
ordering below, because three of the four depend on the first.

---

# UCP-1 master plan: from here to a chassis that discriminates

## Context

**Why this plan exists now.** On 2026-11-06 the chassis's judgement was scored
against 14 published yeast expression campaigns, with predictions frozen and
hashed before any answer was read. The result:

| | | |
|---|---:|---|
| Recall | 8 of 8 = 100% | of campaign actions the tool can express |
| Precision | 8 of 14 = 57% | on rows where authors tested a fix and it failed |
| **Discrimination** | **0 of 2** | **differential pairs called differently** |

`MOD-secretion` was predicted for **18 of 18** targets. Every chaperone campaign
in the literature maps to it. **The tool says the same thing about every
secreted protein, so it cannot be wrong and cannot be useful.** 100% recall is
what always-saying-yes looks like.

That is the single fact this plan is organised around. Work so far has been
opportunistic — real, mostly honest, and not aimed. Nineteen checkpoints
produced one of eight theory layers validated on external evidence, a published
3D simulation, a parameter registry that found six unsourced thresholds, and a
pre-registered test. **What it has not produced is a tool that says something
different about two different proteins.**

**Goal, as the owner states it:** a universal protein chassis able to produce
**different types of protein**, carrying every required capability at the
genomic, metabolomic and cellular level, such that *"this chassis will produce
your desired protein"* is defensible.

**All four definitions of done are in scope** — a proven discriminating tool, a
preprint, a wet-lab-buildable spec, and machine-executable output. They are not
parallel. Three of the four depend on the first, which forces the ordering
below.

---

## The forced ordering

```
P0  verify the plan's own inputs exist
         |
P1  make the tool capable of discriminating   <-- blocks everything
         |
P2  build the evidence that says WHAT discriminates
         |
    +----+----+--------------------+
    |         |                    |
P3 parameterise   P4 build the      P5 propagate
   existing          missing           uncertainty
   layers            layers            honestly
    +----+----+--------------------+
         |
P6  emit a spec, in a machine-executable format
         |
P7  write it up
```

**Nothing in P3–P7 is worth doing before P1 and P2.** A tool with six more
physics layers that still says "needs secretion engineering" about every protein
is a worse tool, not a better one — it would look authoritative and discriminate
exactly as badly.

---

## Governing discipline, already in place

These are not new. They exist, they work, and every phase below is subject to
them. The plan's job is to apply them, not to invent more.

| Mechanism | Where | What it enforces |
|---|---|---|
| **Five gates** | `protocol/layer-architecture-v1.md` | published equation, registered parameters, declared unit, untuned validation, printed limits |
| **Parameter registry** | `params/parameters-v1.json`, `scripts/params.py` | raises on an unregistered number; grades A–D |
| **Grade inheritance** | layer-architecture | a composed prediction carries its weakest input's grade |
| **Pre-registered freeze** | `scripts/freeze_predictions.py`, `validation/freeze-v1.json` | predictions hashed and bound to a commit; scoring refuses if the code changed |
| **Frozen scoring map** | `validation/mapping-v1.tsv` | near-misses cannot be argued into hits |
| **Corrections stay visible** | `docs/PROJECT-STORY.md`, superseded scripts kept | the project's four reversals are all still readable |

**One addition.** Adopt a MEMOTE-style self-test for the chassis object itself.
MEMOTE (Lieven et al. 2020, *Nat Biotechnol*,
[10.1038/s41587-020-0446-y](https://doi.org/10.1038/s41587-020-0446-y)) is the
community standard for testing genome-scale metabolic models — structural
checks, annotation coverage, consistency, scored and reported. We are building a
model of an organism and have no equivalent. New file
`scripts/chassis_memote.py`: every capability has evidence, every number is
registered, every module has a cost status, no capability is `always_required`
without justification, every claim resolves to a provenance pointer. Runs in CI.

---

## P0 — Verify the plan's own inputs (do not skip)

**Why first.** This project has already burned weeks on an input nobody checked:
MATLAB was recorded across three documents as the central obstacle, and was
never required. The cheapest possible insurance is to download every dataset
this plan depends on **before** planning around it.

| Input | Needed for | Check |
|---|---|---|
| `pcSecYeast.mat` per-protein secretory cost | P3, module costs | already on disk and solves; confirm a per-protein cost can actually be extracted, not just a biomass flux |
| Yeast absolute proteome (molecules/cell) | P3, growth-law sectors | download; confirm coverage and units |
| `kcat` coverage for yeast (BRENDA / SABIO-RK / ecYeast) | P3, layer 4 | measure what fraction of yeast enzymes have a value |
| GECKO / ecYeast toolchain | P3 | confirm it runs without MATLAB, as pcSecYeast did |
| Ribo-seq codon dwell times | layer 1c refinement | already bound (`data/gardin/`) |
| TF binding energies for yeast | P4, layer 1a | **expected to fail.** PWMs are frequency models, not energies |
| tRNA modification data | layer 1c, the CGA failure | find out whether a usable table exists |

**Deliverable:** `protocol/data-inventory-v1.md` — one row per input, each marked
**BOUND** (in the repo) or **ABSENT**, with the actual coverage number. Extends
the BOUND/NAMED convention already in `protocol/data-sources-v1.md`, where the
count today is 6 bound against ~17 named.

**Expected outcome, stated now:** two or three planned inputs will turn out not
to exist in usable form. That is the point of doing this first.

---

## P1 — Make the tool capable of discriminating

**The blocking phase.** Four defects, all diagnosed in
`reports/05-retrospective-score.md`.

### P1.1 Split `MOD-secretion`

One module cannot represent the literature. For *S. pombe* acid phosphatase,
**PDI helped 4-fold and BiP did nothing** — two papers, same protein, opposite
results. For *P. furiosus* β-glucosidase, **PDI helped and BiP actively hurt**.

Split into distinct, separately-triggered modules in `chassis/chassis-v1.json`:
`MOD-pdi`, `MOD-bip`, `MOD-leader`, `MOD-dosage`, `MOD-upr`. Update
`validation/mapping-v1.tsv` to map each campaign action to exactly one.

### P1.2 Make each conditional

Every new module needs a trigger that can be false for a secreted protein. **The
score already rules out the obvious candidate:** thaumatin has 8 disulfide pairs
and was *not* helped; prochymosin has 3 and *was*. **Disulfide count is not the
axis.** What the axis is comes from P2 — so P1.2 ships the *mechanism* for
conditional triggers and a deliberately weak first rule, and P2 supplies the
rule worth having.

### P1.3 Stop `MOD-burden` appearing in every answer

`G2` carries `always_required: true`. Move it out of the per-protein answer and
state it once as a property of the chassis. A field that never varies is not a
prediction.

### P1.4 Add a "needs nothing" output

There is no such output today. For wild-type cutinase — secreted at 25 mg/g with
no reported modification — **that was the correct answer and the tool could not
give it.** `scripts/chassis_resolve.py` must be able to return an empty
engineered-module set and say so.

### P1.5 Expand the validation set, then re-freeze and re-score

Current set: 18 rows, **2 differential pairs**. Target: **40–60 rows, 8–12
differential pairs**, which is the honest version of the 30–50 that
`reports/03-validation-set-feasibility.md` asked for. Add glycoengineering
campaigns — the set has none, so `MOD-glycan` and `MOD-sugarnt`, the only two
modules that currently discriminate at all, were **never tested**.

Then: freeze, score, and compare against the recorded baseline.

**Acceptance for P1:** discrimination **above 0**, measured the same way, on a
larger set, with the mapping frozen before scoring. Precision must not fall.

**Files:** `chassis/chassis-v1.json` (schema 1.2), `scripts/chassis_resolve.py`,
`validation/mapping-v2.tsv`, `validation/targets-v2.tsv`, re-run
`scripts/freeze_predictions.py` and `scripts/score_validation.py`.

---

## P2 — Build the evidence for what actually discriminates

**The scientific core, and the hardest part.** P1 gives the tool the ability to
say different things; P2 establishes *when* it should.

**The honest starting position:** a literature search for secretability
predictors in yeast returned essentially nothing applicable — cancer secretomes,
*Candida* virulence, algal enzymes. **There may be no off-the-shelf predictor to
adopt.** If so, the dataset has to be built.

### P2.1 The intervention-outcome dataset

Extend the validation set into a systematic resource: `(protein, host,
intervention, outcome, magnitude, assay)`. Target **200+ rows** across the yeast
heterologous-expression literature. This is a months-scale literature-mining
task and it is the asset the project does not have.

**Critical discipline:** this dataset is for *learning* the rule. The frozen
validation set must stay **disjoint** from it, or the test becomes training.
Separate directories, separate freeze, explicit non-overlap check in code.

### P2.2 Find the axis

Candidate features, all computable from sequence or structure today:
disulfide count **and pattern** (not just count — thaumatin's 8 are a tight
knottin-like core, albumin's 17 are modular), hydrophobic patch area,
predicted disorder, aggregation propensity, isoelectric point, AlphaFold pLDDT
as a proxy for foldability, length, glycan occupancy.

Fit the simplest model that beats the baseline — and the baseline is
**"recommend the intervention for everything"**, which is exactly what the tool
does now. If nothing beats it, that is a publishable negative and a reason to
redesign, not a reason to pick a model anyway.

### P2.3 Guard against the obvious failure

A fitted rule is a grade-D parameter under our own registry unless its training
data, performance and validity range are registered. It must pass **Gate 4**:
recover something it was not shown. Held-out differential pairs are the test.

**Acceptance for P2:** a registered, conditional trigger rule that beats
always-on, on held-out differential pairs.

---

## P3 — Parameterise the layers that already exist

Only now does depth pay. Three layers have models and no numbers.

| Layer | Work | Closes |
|---|---|---|
| **5. Secretory costs** | extract per-protein proteome cost from `pcSecYeast.mat` | every module's `cost_status: "not measured"` — the largest hole in the chassis object |
| **4. Enzyme-constrained metabolism** | apply the GECKO/ecYeast approach; register `kcat` coverage honestly | capabilities D4, D5 as numbers rather than booleans |
| **2. Growth coupling** | replace the single 40% ceiling with measured proteome sectors; **pass Gate 4**, which it currently fails | the only built layer with no external validation |

**This is where the metabolomic depth the owner asked for actually lands.** It
also finally makes the proteome constraint testable against a real
configuration, which no run of the tool has ever been able to do.

---

## P4 — Build the missing layers, and be honest about one that cannot be built

| Layer | Status | Plan |
|---|---|---|
| 1c elongation | **done, externally validated** (ρ = −0.62 vs measured decoding speed) | refine with tRNA modification data if P0 finds a table |
| 3 resource competition | specified, no parameters | build; **derives** the ~12-switch ceiling for yeast instead of importing it from an *E. coli* CRISPRi experiment |
| 1a transcription thermodynamics | specified | build only if P0 finds binding **energies**. PWMs are not energies |
| 6 noise | not started | build last; adds the fraction of the population that actually performs |
| **1b translation initiation** | **no model of standing exists in the field** | **cannot be built by effort.** Record as a permanent known gap until the field produces one |

**That last row is the plan's one irreducible hole.** No amount of rigour closes
it. Saying so now is better than discovering it in month eight.

---

## P5 — Uncertainty, and what to do when things break

The owner asked specifically about troubleshooting. This is that phase, and it
is a phase rather than a habit because it needs code.

**Today:** grade inheritance — a composed prediction carries its weakest input's
grade. Crude, and labelled crude in `layer-architecture-v1.md`.

**Target, in order:**

1. **Attach real uncertainties** to registered parameters. Most sources give one
   number; where that is all there is, say so rather than invent a spread.
2. **Propagate** by Monte Carlo over registered ranges. Outputs become intervals.
3. **Sensitivity analysis** — which parameter actually moves the answer. This is
   the single most useful troubleshooting tool, because it tells you where to
   spend effort.
4. **Identifiability check** — when two parameters trade off and cannot be
   separated by available data, the model is over-specified and must be
   simplified, not fitted harder.

**Standing error protocol** (`protocol/troubleshooting-v1.md`), generalised from
what has actually worked four times here:

| Symptom | First move | Precedent |
|---|---|---|
| A number looks authoritative | find its registry grade | six grade-D thresholds found in the resolver |
| A conclusion blocks the project | check the primary source yourself | MATLAB was never required |
| A model agrees with expectation | find what it was *not* shown | arginine ordering fell out of tRNA counts |
| A model's ordering is right | check its **magnitudes** | predicted spread 27,000× vs measured 2.7× |
| A score looks good | check whether a constant predictor would score the same | 100% recall, 0 discrimination |

**That bottom row is the lesson of the whole project so far and it belongs in a
file, not in my memory of this conversation.**

---

## P6 — Emit a buildable, machine-executable spec

`protocol/goal-definition-v1.md` already decided this: make the output
machine-executable **from the start**, because it is cheap now and expensive to
retrofit. It is currently "a statement of intent and nothing more."

- **Design the output schema early** (during P1), even while the content is
  thin: structured, versioned, every claim carrying its provenance and grade.
- **Fill it as layers land.** Parts, sequences, assembly strategy, integration
  loci, predicted costs, and the explicit uncertainty on each.
- **Two renderings, one source:** a human spec a wet lab can read, and a
  structured protocol an autonomous lab could consume. Both from the same
  object, so they cannot diverge.

**Hard rule:** the spec must carry its own grades and intervals. A buildable
spec that hides its uncertainty is the most dangerous artifact this project
could produce, because someone would spend real money on it.

---

## P7 — Write it up

Two publishable objects, and the order matters:

1. **The method and the negative result.** A pre-registered retrospective
   validation of a chassis design tool — frozen predictions, frozen scoring
   mapping, hash-bound, with a result that says the tool did not discriminate.
   **That is a real contribution and most of it already exists in the repo.**
   It is honest, unusual, and publishable even if P2 fails.
2. **The chassis as a citable object**, the way pcSecYeast and Yeast9 are — the
   model, its validation, its limits. **Only after P1 and P2 succeed**, because
   without discrimination there is no result to report.

---

## Effort, honestly

Open-ended, no deadline, so these are sized in **weeks of focused work**, not
dates. They are estimates and should be revised as phases complete.

| Phase | Estimate | Confidence |
|---|---|---|
| P0 verify inputs | 1–2 | high — mostly downloading and counting |
| P1 discrimination mechanism | 3–5 | medium — code is easy, the validation set expansion is the cost |
| **P2 the discriminating evidence** | **8–16** | **low. This is the research risk of the whole project** |
| P3 parameterise existing layers | 6–10 | medium — toolchains exist, coverage is unknown until P0 |
| P4 remaining layers | 8–14 | low-medium — one layer is unbuildable |
| P5 uncertainty + troubleshooting | 3–5 | high — standard methods |
| P6 spec + executable format | 3–4 | high if P1–P3 land |
| P7 write-up | 4–6 | high |

**P2 dominates the risk.** Everything else is engineering against known methods.
P2 is an open scientific question — what makes one protein secretable and
another not — and the literature search suggests nobody has answered it for
yeast.

---

## Kill and pivot criteria, agreed in advance

Written now so they cannot be rationalised later.

| If | Then |
|---|---|
| P2 finds **no feature that beats always-on** on held-out differential pairs | Publish that as a negative result. Pivot the tool from *predicting* interventions to *ranking* them with explicit uncertainty — an honest triage tool, not an oracle |
| Module costs **cannot be extracted** from pcSecYeast | The proteome constraint stays untestable. Say so in the chassis object and drop the budget claim rather than keep a decorative one |
| `kcat` coverage for yeast is **below ~50%** | Layer 4 cannot carry weight. Keep it qualitative and say so |
| The expanded validation set **still yields fewer than 6 differential pairs** | The retrospective test cannot settle discrimination. Add a second evidence route — prospective predictions, registered before new papers appear |
| Discrimination improves **only on the data the rule was fitted to** | The rule is overfitted. Revert it and record the attempt |

---

## Cross-cutting, every phase

- **Checkpoint** per `explain` skill: short version in chat, full entry in
  `docs/PROJECT-STORY.md`, always with a rendered diagram.
- **Decisions recorded** — what was chosen, what was rejected, why.
- **Corrections stay visible.** Four reversals are on the record; that count
  should keep rising, because a project that stops finding its own errors has
  stopped looking.
- **`scripts/chassis_memote.py` in CI** from P1 onward, so the object cannot
  silently regress.

---

## Verification

Each phase has a mechanical check, not a judgement.

| Phase | How we know it worked |
|---|---|
| P0 | `protocol/data-inventory-v1.md` exists; every row BOUND or ABSENT with a coverage number; `python -I scripts/params.py --audit` shows new registered parameters |
| P1 | `python -I scripts/score_validation.py` on the re-frozen v2 set reports **discrimination > 0** with precision not lower; freeze check passes; `chassis_memote.py` green |
| P2 | held-out differential pairs beat the always-on baseline; the rule is registered with its training data and performance; training and test sets provably disjoint |
| P3 | no module in `chassis-v1.json` carries `cost_status: "not measured"`; `growth_coupling.py` passes Gate 4 against an external measurement |
| P4 | each new layer passes all five gates; layer 1b recorded as a permanent gap |
| P5 | the tool emits intervals, not point values; sensitivity report names the top three parameters |
| P6 | a spec validates against its schema and round-trips; both renderings come from one source |
| P7 | preprint submitted |

**The one number that matters.** Today: recall 100%, precision 57%,
**discrimination 0 of 2**. P1 and P2 exist to move the third number, and no
amount of work in P3–P7 substitutes for it.

---

## First concrete action on approval

P0.1 — attempt to extract a per-protein secretory cost from
`data/models/pcSecYeast.mat`. It is the input the most downstream work depends
on, it is already on disk, and we have never confirmed it can actually be done.
If it cannot, the plan changes shape immediately and better now than in month
three.
