# Where the data comes from, version 1

**The instruction:** build this *"backed by every principle that is required —
mathematics, physics, systems biology, genomic data, proteomic data,
transcriptional data, translational data, genetic circuits engineering
principles, and other synthetic biology relevant databases"*.

[`layer-architecture-v1.md`](layer-architecture-v1.md) says a layer is
established only when **every parameter has a source**. This document is the
other half: **where those sources are**, by data type.

---

## Read this column first

| | Meaning |
|---|---|
| **BOUND** | This project has actually retrieved data from it, and that data is in the repository. |
| **NAMED** | Identified as the right source and **not yet accessed**. Its contents, coverage, format and licence are assumed, not verified. |

**Three sources are bound. Everything else on this page is NAMED.** A long list
of databases is not evidence of depth, and this document should not be read as
if it were. It is a work plan with the done part marked.

---

## 1. Genomic — the host's own sequence and gene complement

| Source | Supplies | Feeds layer | Status |
|---|---|---|---|
| **GtRNAdb** (sacCer3) | tRNA gene copy numbers per anticodon, 275 genes | **1c elongation** | **BOUND** → [`params/trna-scerevisiae-gtrnadb-v1.tsv`](../params/trna-scerevisiae-gtrnadb-v1.tsv) |
| SGD (*Saccharomyces* Genome Database) | ORF coordinates, gene names, systematic IDs, essentiality | 3, 4 | NAMED |
| Codon usage tables for *S. cerevisiae* | Observed codon frequencies genome-wide | 1c, as an independent check on the tRNA-derived weights | NAMED |

**Why the tRNA table mattered more than its size suggests.** It is 61 rows. It
converted capability A1 from *"codon usage compatible: native, confidence high"*
into a computed number per protein, and it produced the one result in this
project that fell out of the data rather than being put in: the arginine codon
ordering.

---

## 2. Proteomic — how much of each protein a cell actually holds

| Source | Supplies | Feeds layer | Status |
|---|---|---|---|
| **UniProt** | Curated sequence features: signal peptides, disulfide bonds, glycosylation sites, transmembrane regions | **validation of the resolver** | **BOUND** → 24 records in [`data/uniprot/`](../data/uniprot) |
| PaxDb | Absolute protein abundance, cross-organism | 2 growth coupling, 5 secretory costs | NAMED |
| ProteomeXchange / PRIDE | Raw and processed proteomics underlying abundance estimates | 2, 5 | NAMED |
| AlphaFold DB | Predicted structures, for folding-difficulty features the sequence alone cannot give | B-series capabilities | NAMED |

**What the bound one bought.** UniProt is the reason
[`reports/02-feature-validation.md`](../reports/02-feature-validation.md) exists:
N-glycosylation sequons recovered 43 of 45 annotated sites (96% recall), and the
disulfide rule was caught firing on 7 proteins whose cysteines never pair. **The
only defects this project has found in its own tool were found with this
database.**

**The gap it leaves.** Abundance is what layers 2 and 5 need, and UniProt does
not carry it. Proteome sector fractions for yeast are not assembled anywhere in
this project, which is why
[`scripts/growth_coupling.py`](../scripts/growth_coupling.py) runs on a single
ceiling value rather than on measured sectors.

---

## 3. Transcriptional — promoters, regulators, binding energies

| Source | Supplies | Feeds layer | Status |
|---|---|---|---|
| JASPAR | Transcription-factor binding motifs as position weight matrices, including yeast | **1a transcription thermodynamics** | NAMED |
| YEASTRACT | Documented regulator–target associations in *S. cerevisiae* | 1a, 3 | NAMED |
| GEO / ArrayExpress | Expression data under defined conditions | 1a, 6 noise | NAMED |

**The honest problem with layer 1a.** Thermodynamic promoter models need
**binding free energies**, in kBT or kcal/mol. A position weight matrix is a
frequency model, not an energy, and converting one to the other is itself an
assumption with a literature. `theory-stack-v1.md` cites that energies are now
predictable *"to within 1 kBT"* — but that is a capability in the literature,
**not a table this project can download**. Layer 1a is further away than the
database list makes it look.

---

## 4. Translational — initiation and elongation

| Source | Supplies | Feeds layer | Status |
|---|---|---|---|
| **GtRNAdb** | tRNA gene complement | **1c, implemented** | **BOUND** |
| Ribosome profiling datasets (Ribo-seq) | Ribosome density per codon — the direct measurement of where elongation is slow | 1c, validation | NAMED |
| MODOMICS-type tRNA modification data | Wobble-position modifications, which the single wobble penalty currently summarises | 1c refinement | NAMED |

**This is the layer where the next real gain sits.** The elongation model
currently predicts which codons are poorly served *from gene copy number*.
Ribosome profiling measures where ribosomes actually slow down. **Comparing the
two is a Gate 4 validation this project could run without a laboratory**, and it
would test the layer against an external measurement rather than against known
codon-usage tables.

**And the gap that is not a data problem.** Layer 1b, translation initiation in
yeast, has **no model of standing to parameterise**. The bacterial RBS
calculator has no yeast equivalent. No database fixes that.

---

## 5. Metabolic and secretory — the machinery costs

| Source | Supplies | Feeds layer | Status |
|---|---|---|---|
| **pcSecYeastSpecies** | Proteome-constrained secretory model: 25,776 metabolites × 37,688 reactions, incl. 805 glycosylation and 63 disulfide reactions | **4, 5** | **BOUND** → [`data/models/pcSecYeast.mat`](../data/models) |
| Yeast8 / Yeast9 | Consensus genome-scale metabolic model of *S. cerevisiae* | 4 | NAMED |
| BRENDA / SABIO-RK | Enzyme turnover numbers and Michaelis constants | 4, 5 | NAMED |
| BioNumbers | Curated biological quantities with their primary citations | **all layers — this is the obvious fix for the missing-citation problem** | NAMED |

**Bound but not yet used for its purpose.** The model loads and solves in 6
seconds via scipy's HiGHS, confirmed in
[`scripts/pcsec.py`](../scripts/pcsec.py). **No module cost has been extracted
from it.** All five engineered modules in `chassis-v1.json` still carry
`cost_status: "not measured"`, which is the single largest hole in the chassis
object. The data is on the disk; the extraction is not written.

---

## 6. Genetic circuits — parts, and why this one is different

| Source | Supplies | Status |
|---|---|---|
| iGEM Registry / Addgene | Physical parts and their documentation | NAMED |
| SynBioHub | Parts and designs in SBOL, machine-readable | NAMED |
| Published yeast promoter and terminator libraries | Characterised expression strengths in this host | NAMED |

**This is not a parameter-lookup problem and it should not be listed as if it
were.** A part's measured strength is **conditional on everything else in the
cell** — the load it places on shared machinery, what else competes for that
machinery, and the host's growth rate. That is exactly what theory-stack layer 3
(resource competition) exists to model.

So the circuits requirement decomposes into two different things:

- **Part inventories** — the databases above. Retrievable.
- **Context-dependence** — retroactivity, load, and competition for shared
  resources. **No database supplies this.** It is a model, and it is layer 3,
  and layer 3 is not started.

**There is no yeast parts database that reports performance as a function of
cellular context.** Treating a parts list as if it were characterised physics is
one of the specific ways this project could become superficial while appearing
data-rich.

---

## What this document establishes, and what it does not

**Established:**

- Every layer now has a named route to its parameters, by data type.
- Three sources are bound and in the repository, and each one has already
  changed a conclusion: GtRNAdb produced the elongation layer, UniProt found two
  defects in the resolver, pcSecYeastSpecies killed the MATLAB blocker.

**Not established, stated plainly:**

- **Everything marked NAMED has not been accessed.** Coverage, format, units and
  licence are assumed. Some will not contain what this document expects.
- **No licences have been checked** except pcSecYeastSpecies (MIT). Before any
  derived data enters this repository, its terms have to be read.
- **Naming a database is not having the data.** This page lists roughly twenty
  sources and the project holds data from three. The ratio is the honest
  summary.
- **Two needs have no database at all:** yeast translation-initiation models
  (layer 1b) and context-dependent circuit performance (layer 3). Those are
  modelling gaps that no amount of data retrieval closes.
- **The missing-citation problem is not fixed here.** Four load-bearing constants
  still have a recorded quote and no identified paper. BioNumbers is named above
  as the likely fix and has not been tried.
