# The retrospective test: protocol, and what the freeze already showed

**The claim being tested**, from
[`protocol/goal-definition-v1.md`](../protocol/goal-definition-v1.md):

> *Given a protein sequence alone, the chassis predicts the host modifications
> that published campaigns actually found necessary, in N of M cases.*

[`reports/02-feature-validation.md`](../reports/02-feature-validation.md)
validated the tool's **perception** — can it read a protein — at 16 of 16 inside
its domain. **This tests its judgement**, which is the half that has never been
checked.

---

## The headline, and it needed no answers at all

**The chassis predicts `MOD-secretion` for 18 of 18 targets, and `MOD-burden`
for 18 of 18.**

| Module | Targets it was predicted for |
|---|---|
| **MOD-secretion** | **18 of 18** |
| **MOD-burden** | **18 of 18** |
| MOD-glycan | 4 of 18 |
| MOD-sugarnt | 4 of 18 |

`MOD-secretion` is what every chaperone campaign maps to — PDI, BiP/Kar2, Ssa1,
Ydj1, Sec63, HAC1, signal-peptide choice, gene dosage. All of it, under
[`mapping-v1.tsv`](mapping-v1.tsv), lands on one module that the chassis names
for **every secreted protein without exception.**

**So the chassis will score near-perfect recall on the chaperone literature and
exactly zero discrimination.** That is not a prediction about the papers. It is
arithmetic about the tool, readable off the frozen predictions, with no outcome
consulted.

`reports/03-validation-set-feasibility.md` called this shot:

> *"A tool that recommends PDI for everything scores well on a set of successes
> and fails completely here."*

**It recommends PDI for everything.**

### Why it happens

Two triggers fire unconditionally.

- **E3, secretion capacity** fires on `secreted == True` and nothing else. The
  chassis has no way to say *this protein will secrete adequately unaided*.
- **G2, burden control** carries `always_required: true`, so it is in every
  answer by construction.

The only discriminating signal in the whole set is the glycan pair, which fires
on sequons plus therapeutic class — 4 of 18.

### The pair that points the wrong way

The `bip-1` pair is the cleanest test in the set: BiP overexpression plus PMR1
disruption **stimulated bovine prochymosin and not plant thaumatin**.

| | cysteine pairs | sequons | signal peptide | modules predicted |
|---|---:|---:|---|---|
| Prochymosin — **helped** | 3 | 2 | yes | burden, glycan, secretion, sugarnt |
| Thaumatin I — **not helped** | **8** | 0 | yes | burden, secretion |

**Thaumatin has nearly three times the disulfide load of the protein the
chaperones rescued.** The tool's one quantitative handle on folding difficulty
points at the wrong member of the pair. It does not use that handle to decide
anything, which is why it does not get the pair wrong so much as fail to have
an opinion.

And `PMR1 disruption`, half of what the campaign actually did, is declared
**UNMAPPED** — no capability in the chassis can express it.

### The hit that proves nothing

*P. furiosus* β-glucosidase CelB (`Q51723`) has **zero cysteines**, and PDI
overexpression improved its secretion anyway — the result that contradicts the
obvious rule. The chassis predicts `MOD-secretion` for it and will be scored a
**hit**.

**It is a hit for the wrong reason.** The tool did not reason about PDI acting
as a general chaperone. It said secretion engineering because the protein is
secreted, as it does for everything. A scoring table that counts this as a
success is measuring nothing.

---

## The freeze, and why it is auditable rather than trust-based

The condition from the feasibility report:

> *"The blind condition needs enforcing. If the tool is adjusted after seeing
> the answers, the test is worthless."*

"Don't look" cannot be audited. What can:

1. **[`predictions-v1.tsv`](predictions-v1.tsv)** is produced by
   [`scripts/freeze_predictions.py`](../scripts/freeze_predictions.py), which
   **imports the real resolver** rather than reimplementing it.
2. The predictions file carries a **SHA-256**, recorded in
   [`freeze-v1.json`](freeze-v1.json).
3. The manifest records the **git commit** the predictions were produced at, and
   whether the tree was clean.
4. **[`mapping-v1.tsv`](mapping-v1.tsv) is frozen in the same commit.** Without
   that, every near-miss could be argued into a hit after the fact.
5. The manifest declares the test **void** if `chassis_resolve.py`,
   `elongation.py`, `chassis-v1.json` or the mapping changes between freeze and
   scoring. The remedy is to re-freeze, not to proceed.

### What is blind and what is not

**Blind:** the predictions. Sequence in, through frozen code, no outcome read.

**Not blind:** the choice of proteins. Assembling a set of campaigns means
reading which campaigns exist, so titles and abstracts were read. That is
unavoidable and pretending otherwise would be the dishonest move.

**So the guard is not ignorance.** It is that the predictions are fixed and
hashed, the mapping is fixed beside them, and the unmapped categories are
declared misses in advance.

### Seven ways to lose, declared up front

[`mapping-v1.tsv`](mapping-v1.tsv) lists seven categories of campaign action the
chassis **cannot express at all**: PMR1 disruption, other protease deletions,
temperature and cultivation conditions, vesicle trafficking, mutating the
product itself, promoter choice, and changing host species.

Each will score as a **miss by construction**. Declaring them now, before the
answers, is the difference between a test and a sales pitch — and it will make
the recall number worse than it would otherwise look.

---

## The set

18 protein-paper rows from **14 papers**, resolved against PubMed and UniProt.
**11 of the 18 rows belong to a differential or negative result**, which is the
weighting the feasibility report asked for: successes test recall, only
differentials test discrimination.

| Case type | Rows |
|---|---:|
| differential_helped | 4 |
| differential_not_helped | 2 |
| negative | 4 |
| success | 8 |

Full list with accessions, hosts, PMIDs and DOIs:
[`targets-v1.tsv`](targets-v1.tsv).

---

## What happens next, and what would count as failure

**Next:** extract, per row, what the campaign actually did, into
`answers-v1.tsv`. Score only through the frozen mapping. Report recall and
precision separately, because publication bias makes precision mostly
uninterpretable.

**The outcome that already looks likely**, stated before scoring so it cannot be
claimed as a prediction afterwards: **high recall, near-zero discrimination.**
The chassis will name the right module most of the time because it names that
module every time.

**If that is what the scoring shows, the right conclusion is not that the
chassis passed.** It is that `MOD-secretion` as currently defined is not a
prediction, and the chassis needs a way to decide *which* proteins need
secretion help rather than asserting that all of them do. That is a design
change, and this test will have earned it.

---

## What is not done

- **No answer has been read or scored.** This commit contains predictions only.
- **18 rows, not the 30 to 50** the feasibility report called for. The set
  should grow, and growing it will not change the 18-of-18 problem above.
- **Three campaigns were excluded** for lack of a usable sequence: the
  hydrophobic cutinase mutant CY028, which would have been the sharpest test of
  our hydropathy heuristics; the bivalent anti-CD3 immunotoxin; and the scFv
  divergence pair this project already treats as its strongest
  counter-evidence. All three are recorded in `targets-v1.tsv`.
- **Every target is treated as secreted**, because every campaign measured
  secretion. **Product class is assigned from the protein's origin** — human or
  mammalian hormone counts as therapeutic — which is a judgement made in the
  freeze script, not something read off the sequence. It changes whether
  `MOD-glycan` fires, so it is a real assumption and not a detail.
- **Hosts differ across the set**: *S. cerevisiae*, *P. pastoris*,
  *K. lactis*, *H. polymorpha*. The chassis is defined on *S. cerevisiae* only.
  Every non-cerevisiae row is a transfer assumption, and there are five of them.
- **Three decades separate the oldest and newest paper.** Strains, vectors,
  promoters and assays are not comparable across that span, and nothing in the
  set records those differences yet.
- **Precision will remain mostly unmeasurable.** A paper silent on chaperones
  may mean the chassis over-prescribed, or may mean nobody tried. The
  differential rows are the partial escape, because there the authors did test
  the alternative and reported it failing.
