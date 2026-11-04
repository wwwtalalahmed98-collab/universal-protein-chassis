# The theory stack, version 1

**The instruction:** stop building a tool that matches rules, and ground it in
the physics and quantitative theory the field has actually established —
systems biology, genomics, proteomics, transcription, translation, circuit
engineering.

**This document says what those layers are, what each one would replace, and
which are reachable.** It is an architecture, not an implementation. One layer
has been implemented as a demonstration and it immediately corrected a
conclusion already in the project.

---

## What the tool is today, stated honestly

`chassis_resolve.py` is a **rule matcher**. It asks categorical questions — does
this protein have cysteines, does it have sequons — and returns categorical
answers. It contains **no rates, no energies, no concentrations, and no
dynamics.** Nothing in it could tell you how much protein you would get, or how
the cell would respond.

That is the gap. Every layer below replaces a categorical answer with a
quantitative one.

---

## Layer 1 — Sequence to rates: the biophysics of expression

### 1a. Transcription, as statistical mechanics

The level of transcription is computed as the **probability that RNA polymerase
occupies the promoter**, from binding energies and regulator copy numbers. This
is equilibrium statistical mechanics applied to a promoter.

> *"We review a class of models (**thermodynamic models**) which exploit
> **statistical mechanics** to compute the probability that RNA polymerase is at
> the appropriate promoter"* — Bintu et al., *Transcriptional Regulation by the
> Numbers*

**It works in yeast specifically**, which matters because the chassis is yeast:

> *"Thermodynamic models based only on the **equilibrium binding** of
> transcription factors to DNA and to each other **captured a large fraction of
> the variation**"* — synthetic promoter libraries in *S. cerevisiae*, *Nature* 2008

And binding energies can now be predicted from sequence:

> *"We use these models to predict the binding energies of transcription factor
> binding sites to **within 1 kBT** of their measured values"*

**Replaces:** capability A2, currently the boolean *"promoter works in host"*.
**Would give:** a transcription rate from a promoter sequence and a regulator
concentration.
**Parameters needed:** binding energies per TF-site pair, TF copy numbers.
Available for a modest set of yeast TFs; not for arbitrary ones.

### 1b. Translation initiation, as free energy

Initiation rate follows from the free-energy change of assembling the ribosome
on the message. In bacteria this is the RBS-calculator formalism. **In yeast the
equivalent is weaker** — Kozak context is understood qualitatively but there is
no yeast initiation model of the same standing.

**Replaces:** capability A3, currently boolean.
**Honest status:** this is a **real gap for a yeast chassis**, not a solved
layer to plug in.

### 1c. Translation elongation, as traffic

Ribosomes move along a message and can jam. The standard treatment is a
**TASEP** — a particle-flow model from statistical physics — with codon-specific
rates set by tRNA abundance.

**Replaces:** capability A1, currently *"codon usage compatible"*.
**Would give:** elongation rate, and warning of ribosome queueing on
rare-codon stretches.

---

## Layer 2 — Resource allocation and growth coupling

**This is the highest-value layer and it is the one already implemented.**

The cell has one ribosome pool shared by its own genes and ours. Expressing a
heterologous protein therefore does two things at once: it makes product, and it
slows the cell down. The growth laws make this quantitative.

> *"the proteome partitions into several **coarse-grained sectors**, with each
> sector's total mass abundance exhibiting **positive or negative linear
> relations with the growth rate**"* — Hui et al., *Mol Syst Biol* 2015

> *"A **mechanistic link** between cellular trade-offs, gene expression and
> growth"* — Weiße et al., *PNAS* 2015. The model that couples a synthetic
> construct to host physiology.

And parts characteristics feed straight in:

> *"**RBS and Promoter Strengths Determine** the Cell-Growth-Dependent Protein
> Mass Fractions and Their Optimal Synthesis Rates"* — *ACS Synth Biol* 2021

**Replaces:** `proteome_budget.py`, which treats the cell as a box of fixed
volume and asks only whether the modules fit.

### What it corrected, immediately

Implemented in `scripts/growth_coupling.py`. Growth falls roughly linearly with
heterologous mass fraction, reaching zero at the measured ceiling. Productivity
is the product of per-cell yield and cell accumulation, so it is maximised at
**half the ceiling**:

| | Measured ceiling | **Actual optimum** |
|---|---:|---:|
| *E. coli* | 33% | **16.5%** |
| *S. cerevisiae* | 40% | **20%** |

**The existing budget model and the published simulator both treat 40% as a
budget you may spend up to. Under the growth laws, 40% is the point of zero
yield.** A design sitting at the ceiling produces nothing, because nothing is
growing.

This is a conclusion in the project that the theory layer overturned on contact.

---

## Layer 3 — Resource competition inside the circuit

Parts are not independent. They compete for shared machinery, so adding a
component changes the behaviour of components already there.

> *"The **transcription factor titration effect** dictates level of gene
> expression"* — *Cell* 2014

> *"despite highly specific sgRNA-promoter binding, multiple sgRNAs still
> **interfere with one another by competing for dCas9**"*

**Replaces:** the ~12-switch ceiling in `regulatory-capacity-v1.md`, which this
project currently carries as **a number borrowed from an *E. coli* experiment**.
A competition model would *derive* that ceiling, and derive it for yeast rather
than importing it.

**This matters more than it looks.** Two independent lines of reasoning in this
project both landed on about twelve, and we recorded that we could not tell
whether it was a shared cause or a coincidence. **A resource-competition model
is exactly the thing that would settle it.**

---

## Layer 4 — Metabolism, under enzyme and thermodynamic constraints

Flux balance analysis constrained by enzyme abundance and by the free energy of
each reaction. This is the family `pcSecYeast` belongs to, and the 2026 work
coupling it to machine learning:

> *"a hybrid machine learning and **enzyme-constrained metabolic model** for ab
> initio prediction of **proteome reallocation**… doubled the predictive accuracy
> of protein abundances (Pearson r = 0.501)"*

Note that number honestly: **r = 0.501 is the state of the art, and it is not
close to precise.**

**Replaces:** capabilities D4 and D5, precursor and sugar-nucleotide supply,
currently booleans.
**No longer blocked.** See the correction at the end of this document.

---

## Layer 5 — The secretory pathway, with costs

`pcSecYeast` models translocation, folding, glycosylation and trafficking as
enzymatic steps with turnover numbers and proteome costs.

**Replaces:** the single worst gap in `chassis-v1.json` — every engineered module
carries `cost_status: not measured`, which is why the budget constraint cannot
be checked against a real configuration. **This layer is where those costs come
from.**
**No longer blocked.** See the correction at the end of this document.

---

## Layer 6 — Noise

Expression is stochastic. A design that works on the population average can fail
in most individual cells. Transcriptional bursting, intrinsic versus extrinsic
noise, and fluctuation-dissipation relations for biochemical networks are the
standard apparatus.

**Replaces:** nothing currently in the tool, because the tool has no concept of
variation at all.
**Would add:** the fraction of the population that actually performs.

---

## Tractability, ranked honestly

| Layer | Value | Blocked by | Reachable now |
|---|---|---|---|
| **2. Growth coupling** | **Highest — corrects a live error** | Nothing | **Done, first pass** |
| 3. Resource competition | High — derives the twelve | Yeast parameters | Partly |
| 1a. Transcription thermodynamics | High | TF binding energies | Partly, for known TFs |
| 1c. Elongation / TASEP | Medium | tRNA abundances for yeast | Yes |
| 4. Enzyme-constrained metabolism | High | ~~MATLAB~~ nothing | **Yes** |
| 5. Secretory costs | **Highest for the chassis** | ~~MATLAB~~ nothing | **Yes** |
| 1b. Yeast translation initiation | Medium | **No model of standing exists** | No |
| 6. Noise | Lower for a first design | Parameters | Yes, structurally |

**This was wrong when first written.** It said two of the three highest-value
layers were behind MATLAB and called that the central obstacle. The correction
below replaced that conclusion within the same day.

---

## What this is not

**This is not a weekend of work.** Each layer is a model with parameters,
assumptions and a validity range. Done carelessly, a stack of models produces
confident numbers with no more content than the rules they replaced — and that
is worse than the rule matcher, because it looks authoritative.

**Specific risks:**

- **Parameters are the hard part, not the equations.** The equations are
  published. Yeast-specific values for most of them are not assembled anywhere,
  and collecting them is the actual work.
- **Errors compound across layers.** A transcription rate feeding a translation
  model feeding a growth model multiplies its uncertainty at each step. Nothing
  in the plan above tracks that yet, and it must.
- **Most of this theory was built on *E. coli*.** The growth laws, the
  thermodynamic promoter models and the competition results are overwhelmingly
  bacterial. **The chassis is yeast.** Every transfer is an assumption.
- **The linear growth reduction used in Layer 2 is first-order.** It is well
  supported in bacteria and much less tested in yeast.
- **No layer removes the ceiling** reported in `scope-proteins-v1.md`: two
  architecturally similar antibody fragments behaved differently under identical
  engineering. More physics does not fix a problem that is not a physics problem.

---

## What is done and what is not

---

## Correction: MATLAB was never the obstacle

**Written hours after the above, and it overturns the document's own
conclusion.**

Both pcSecYeast repositories state they require MATLAB, the COBRA Toolbox, the
RAVEN Toolbox and the SoPlex solver. This document took that at face value and
concluded MATLAB access was the central obstacle to the project.

**MATLAB is required to BUILD those models. It is not required to USE them.**

The `pcSecYeastSpecies` repository commits the **built models** as `.mat` files
under an **MIT licence**: `pcSecYeast.mat`, `pcSecPichia.mat`, `pcSecKmarx.mat`.
A `.mat` file is a container, not a MATLAB program. `scipy.io` reads it, and the
linear program inside is solved by **HiGHS, which ships with scipy**.

Verified, in `scripts/pcsec.py`:

| | |
|---|---|
| Model size | **25,776 metabolites x 37,688 reactions**, 1,156 genes |
| Loaded with | `scipy.io.loadmat` — standard COBRA fields all present |
| Solved with | **HiGHS, bundled with scipy. No MATLAB, no SoPlex** |
| Result | Optimal in **6 seconds**, biomass reaction `r_2111` at 0.1418 |
| File size | **1.6 MB** |

And the machinery the chassis modules need costs for is all in it:

| Probe | Reactions |
|---|---:|
| folding | **6,646** |
| degradation | 3,460 |
| protein | 1,295 |
| Golgi | 908 |
| **glycosylation** | **805** |
| translocation | 361 |
| mannosylation | 133 |
| **disulfide** | **63** |
| dolichol | 15 |

**Layers 4 and 5 are unblocked.** The thing this project called its central
obstacle was an assumption nobody had tested, taken from a README.

**What this does not establish:** it solves the model *as shipped*. The authors'
published results set media, heterologous protein and enzyme constraints through
their own MATLAB scripts, and **that logic has not been reimplemented**. No
module cost has been extracted yet. The objective value above has not been
checked against any published number, so it is a solve, not a validation.

---

## What is done and what is not

**Done:** Layer 2, first pass, in `scripts/growth_coupling.py`. It runs, and it
corrected the budget conclusion. And `scripts/pcsec.py`, which loads and solves
the secretory model without MATLAB.

**Not done:** every other layer. No parameters have been collected for any of
them. The chassis object still carries no measured module cost. The simulator
still displays the uncorrected 40% ceiling.

---

## Addition 2026-11-03: the layers now have a method, and 1c is implemented

The document above says *which* layers. It did not say how a layer stops being
prose and becomes a layer. Two documents and a registry now answer that.

**[`layer-architecture-v1.md`](layer-architecture-v1.md)** — the five gates a
layer must pass: published equation, every parameter registered with its
provenance, a declared unit (or a refusal to be converted), a validation against
something it was not tuned to reproduce, and limits printed in its own output.
Plus the composition rule: **a composed prediction carries the lowest grade of
any input it used.**

**[`data-sources-v1.md`](data-sources-v1.md)** — where the parameters live, by
data type: genomic, proteomic, transcriptional, translational, metabolic,
circuits. **Three sources are bound and in the repository. Roughly seventeen are
named and have not been accessed.** That ratio is the honest state of the
project's data depth.

**[`../params/parameters-v1.json`](../params/parameters-v1.json)** — every number
the tool uses, with organism, source and grade.
[`../scripts/params.py`](../scripts/params.py) refuses to return an unregistered
parameter.

### What applying the gates to existing code revealed

**Of the 8 registered parameters inside `chassis_resolve.py` — the code that
decides which engineered modules a protein needs — 6 have no source at all.**
Among them the threshold that triggers `MOD-largecds`, an engineered module
someone would build in a laboratory, fired by a protein being longer than a
round 1000 residues.

**And 0 of 15 registered parameters are grade A.** No number in this project is
a yeast measurement with an identified paper and a stated uncertainty.

### Layer 1c is now implemented and passes all five gates

[`../scripts/elongation.py`](../scripts/elongation.py) computes relative codon
adaptiveness for *S. cerevisiae* from tRNA gene copy numbers (GtRNAdb sacCer3,
275 genes, reconciled by checksum) and the published wobble penalties, following
the method authors' own implementation rather than a retyping of their paper.

**Gate 4 is satisfied by a result the model was not shown.** Given tRNA gene
counts and wobble penalties and **no codon usage data whatsoever**, it ranks
arginine codons `AGA > CGT > AGG > CGC > CGG > CGA`, with CGA effectively
unreadable — which is what yeast codon-usage tables independently report.

**Gate 3 stopped something.** The output is dimensionless. Converting it to
codons per second needs a scaling constant this project does not have, so the
module prints no rate. A rate would have looked more like physics and contained
less.

**The finding that connects two layers:** the worst-served residue in yeast is
**cysteine** (best reachable weight 0.246 across its 2 codons, only 4 tRNA genes
in the genome). Cysteine is what disulfide bonds are made of, and
disulfide-bonded secreted therapeutics are the class this chassis targets. **The
protein family the design aims at is built from the residue the host supplies
worst, and codon optimisation cannot change it.** Stated carefully: that is a
property of the tRNA gene complement, a predicted pressure and not a measured
penalty, and it has not been tested against real yields.

### Still not done

- **Nothing consumes the new layer.** Capability A1 in `chassis-v1.json` still
  reads *"native, confidence high"* with the note *"yeast codon tables well
  characterised"*.
- **Layer 2 fails Gate 4.** Growth coupling corrected an error inside this
  project, which is not the same as recovering an external measured result.
- **Six of eight layers have no parameters at all**, so they cannot be scored.
- **No module cost extracted from pcSecYeast**, though the model is on disk and
  solves.
- The grades are judgements, and grade inheritance tracks the weakest link
  rather than compounding uncertainty properly.

---

## Addition 2026-11-04: layer 1c passes gate 4 against external measurement

The entry above recorded layer 1c passing gate 4 on the weak form of the test —
reproducing the known arginine codon ordering. **The strong form has now been
run against two published datasets, and it passes.** Full account in
[`../reports/04-elongation-validation.md`](../reports/04-elongation-validation.md).

**Per-codon decoding speed**, Gardin et al. 2014 eLife, ribosome residence time
at the A site: **rho = −0.62, p = 2e-07 across 58 codons**, in the predicted
direction. The two slowest codons measured in the cell, CTC and CCC, are two the
model marks nearly unserved. **And it beats codon usage frequency, −0.62 against
−0.54** — so the tRNA gene data earns its place over a predictor that needs no
tRNA data at all.

**Per-gene translation efficiency**, Weinberg et al. 2016 GEO GSE75897:
**rho = +0.44 across 4,820 genes**, stable across swept expression cutoffs,
beating a composition-only control (+0.26) and all 200 runs of a
shuffled-weight null.

### The result that constrains every later layer

**Predicted spread between best and worst codon: about 27,000×. Measured spread:
2.7×.**

The model ranks codons usefully and overstates their differences by four orders
of magnitude. CGA is the clearest case: no tRNA reads it Watson-Crick, so the
model calls it unreadable, and the measurement finds it merely slow. **Wobble
decoding works, just poorly, and gene copy number cannot see that.**

This is the quantitative justification for Gate 3. Had the layer been allowed to
emit codons per second, it would have produced confident numbers that were wrong
by a factor of thousands. **Every layer added from here should be assumed to
have the same disease until measured: ordering trustworthy, magnitude not.**

### Gate scorecard, updated

| Layer | Gates passed |
|---|---|
| **1c. Elongation** | **5 of 5, on external measurement** |
| 2. Growth coupling | 4 of 5 — still no external validation |
| all six others | not started, or no parameters |

**One layer of eight is established. That is the honest count.**
