# How a theory layer becomes real, version 1

**The instruction:** *"we don't build this superficially we build this
authentically backed by every principle that is required not only based on
sequence"*.

`theory-stack-v1.md` answered *which* layers. It did not answer *how a layer
stops being a document and starts being a layer*. Without that, the stack grows
by writing more prose, and the project's own warning comes true:

> *"Done carelessly, a stack of models produces confident numbers with no more
> content than the rules they replaced — and that is worse than the rule
> matcher, because it looks authoritative."*

**This document is the gate. A layer counts as established when it passes five
checks, and not before.**

---

## Why gates rather than more equations

The equations are not the scarce thing. Thermodynamic promoter models, growth
laws, TASEP, flux balance analysis — all published, all available to copy. The
scarce things are the **numbers that go into them** and the **honesty about what
comes out**.

So the architecture is not a list of models. It is a discipline applied to each
model.

---

## The five gates

### Gate 1 — Equation: the form is published, cited, and not ours

The mathematical form must come from the literature with a citation, not be
assembled here because it seemed reasonable. **If this project invents the
functional form, the layer is a guess with decoration.**

*Why it matters:* a plausible equation is the easiest thing in the world to
write and the hardest thing to disprove.

### Gate 2 — Parameter: every constant is registered with its provenance

Every number lives in [`params/parameters-v1.json`](../params/parameters-v1.json)
with the organism it was measured in, its source, and a provenance grade:

| Grade | Meaning |
|---|---|
| **A** | Measured in *S. cerevisiae*, primary publication identified, uncertainty stated |
| **B** | Measured in *S. cerevisiae* or from a named database, source identified, no uncertainty available |
| **C** | Measured in another organism and transferred, or a published model constant whose applicability to yeast is unchecked |
| **D** | No external source — chosen inside this project because the code needed something |

[`scripts/params.py`](../scripts/params.py) enforces it: asking for an
unregistered parameter raises an error instead of returning a default. **A layer
cannot quietly proceed on a number nobody can check.**

**The rule that has teeth:** a grade-D parameter must not appear in anything the
tool presents as a prediction. It may appear in a heuristic, labelled as one.

### Gate 3 — Unit: the output has a unit, or refuses to be converted

A layer must say what its output *is*. If it is dimensionless, it must say so
and **decline to be turned into a physical quantity** without a registered
scaling constant.

*This gate has already stopped something.*
[`scripts/elongation.py`](../scripts/elongation.py) computes relative
adaptiveness, which is dimensionless. Converting it to codons per second needs a
scaling constant this project does not have, so the module **does not print a
rate at all**. Printing one would have looked more like physics and contained
less.

### Gate 4 — Validation: it reproduces something it was not tuned to reproduce

The layer must recover a known result from inputs that did not include that
result. This is the difference between a model and a curve fit.

*Worked example:* the elongation layer was given tRNA gene copy numbers and
wobble penalties, **and no codon usage data whatsoever**. It ranks arginine
codons `AGA > CGT > AGG > CGC > CGG > CGA`, with CGA effectively unreadable.
Yeast codon-usage tables independently report AGA as the dominant arginine codon
and CGA as the rarest. **The ordering fell out of the tRNA genes.**

That establishes the layer is wired up correctly. **It does not establish that
the layer predicts yield**, and the module says so in its own output.

### Gate 5 — Boundary: the limits are printed where a user will see them

Every layer ends with what it cannot do, in its own output, not in a separate
document. The pattern already used in `chassis-v1.json`
(`what_this_object_cannot_do`) and in every script's closing block.

*Why in the output:* limitations in a design document get read once. Limitations
printed beside the number get read every time the number is used.

---

## How layers compose, and the rule for uncertainty

`theory-stack-v1.md` flagged the real danger of stacking:

> *"Errors compound across layers. A transcription rate feeding a translation
> model feeding a growth model multiplies its uncertainty at each step. Nothing
> in the plan above tracks that yet, and it must."*

**The rule, and it is deliberately crude: a composed output carries the lowest
grade of any input it depended on.**

So a prediction that uses the growth law (grade B) and the regulator ceiling
(grade C) is a **grade C prediction**, and is reported as one. A prediction that
touches any grade-D threshold is a **grade D prediction**, which under Gate 2 is
not a prediction at all — it is a heuristic, and must be labelled.

This is not error propagation in the statistical sense. **It is weaker than
that and it is honest about being weaker:** most registered parameters have no
uncertainty attached, because most sources state a single number, and this
project will not invent a spread to make the arithmetic prettier. Grade
inheritance is what can be done with what exists. Real propagation needs
uncertainties, and that is a later gate, not a solved one.

---

## The six layers, scored against the gates

| Layer | 1 Equation | 2 Parameter | 3 Unit | 4 Validation | 5 Boundary | Status |
|---|---|---|---|---|---|---|
| **1c. Elongation / tRNA pool** | yes | yes (B, C) | yes | **yes — arginine ordering** | yes | **passes 5 of 5** |
| **2. Growth coupling** | yes | yes (B) | yes | **no** | yes | 4 of 5 |
| 1a. Transcription thermodynamics | yes | no | — | no | — | not started |
| 1b. Yeast translation initiation | **no model of standing exists** | — | — | — | — | blocked |
| 3. Resource competition | yes | no | — | no | — | not started |
| 4. Enzyme-constrained metabolism | yes | no | — | no | — | model loads, unconstrained |
| 5. Secretory costs | yes | no | — | no | — | model loads, no cost extracted |
| 6. Noise | yes | no | — | no | — | not started |

**Two layers of eight exist. One passes every gate.** Layer 2 fails Gate 4: it
corrected an error *inside this project*, which is useful but is not the same as
recovering an external measured result it was not shown.

---

## What this architecture changed on the day it was written

Applying Gate 2 to code that already existed produced the finding the project
most needed and least wanted:

**Of the 8 registered parameters inside `scripts/chassis_resolve.py` — the part
of the tool that decides which engineered modules a protein requires — 6 are
grade D.** No source. Chosen because the code needed a number.

| Parameter | Value | Grade |
|---|---|---|
| Kyte-Doolittle hydropathy scale | 20 values | B |
| N-glycosylation sequon motif | N-X-S/T, X≠P | B |
| Signal-peptide hydropathy threshold | 1.6 | **D** |
| Signal-peptide window | 9 residues | **D** |
| Transmembrane window | 19 residues | **D** |
| Transmembrane hydropathy threshold | 1.6 | **D** |
| N-terminal scan limit | 22 residues | **D** |
| **Large-CDS module threshold** | **1000 residues** | **D** |

**And 0 of 15 registered parameters are grade A.** Not one number in this
project is a yeast measurement with an identified paper *and* a stated
uncertainty.

The last row of the table is the clearest case. A protein longer than 1000
residues triggers `MOD-largecds`, an engineered module someone would have to
build in a laboratory. **The number that triggers it is a round number with
nothing behind it.** It is reported in exactly the same voice as the sequon
scan, which was measured at 96% recall against UniProt.

That is what "superficial" looks like in practice, and it was invisible until
the parameters were forced into one place.

---

## What this does not fix

- **The grades are judgements, not measurements.** Someone else might grade
  `PRM-single-protein-ceiling` a C rather than a B, since it was measured on
  native glycolytic enzymes and is applied to heterologous protein.
- **Grade inheritance is not error propagation.** It tracks the weakest link,
  not the compounding.
- **Four load-bearing constants have a recorded quote and no identified
  paper** — the yeast and *E. coli* proteome ceilings, the single-protein
  ceiling, and the regulator count. A reader cannot verify them. They are
  graded B and C on the strength of a quotation, which is generous.
- **Passing the gates does not make a layer right.** The elongation layer passes
  all five and is still a per-codon weight with no ribosome traffic, no tRNA
  modification, and no connection to measured titre.
- **Nothing consumes the new layer yet.** `chassis-v1.json` capability A1 still
  reads *"native, confidence high"*. The quantity is computed; the chassis has
  not been rewired to use it.
- **The gates are retrospective here.** They were written after the code, and
  applied to it. The honest test is whether the next layer is built to pass them
  from the start.
