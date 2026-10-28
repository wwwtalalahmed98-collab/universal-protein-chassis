# Can the retrospective validation set be built?

**The question, asked before committing to it:** the goal is now the virtual
chassis, falsified by running the tool blind against published yeast expression
campaigns. That test only works if papers actually state which modifications a
protein needed. **Do they?**

**Answer: yes for what was done, largely no for what was tried and failed. That
asymmetry decides what the test can measure.**

Sample: **40 abstracts** returned by two literature searches — one on secretion
and chaperone engineering in *S. cerevisiae*, one on glycoengineering in
*P. pastoris*. Not a random sample; keyword-selected and therefore biased toward
papers that report engineering. Scored by reading, not by script.

---

## What the abstracts contain

| | Roughly |
|---|---|
| Names a specific target protein | **almost all** |
| Names a specific modification — a gene, a signal peptide, a deletion | **almost all** |
| Gives a quantitative outcome in the abstract | **about 1 in 4** |
| Is a review rather than a primary result | 2 of 40 |

The modifications are named at exactly the resolution the chassis uses. Not
"improved folding" but the actual parts:

> *"the combination chaperones of **YDJ1p/PDI, YDJ1p/Sec63, and Kar2p/PDI**
> synergistically increase secretion levels **8.7, 7.6, and 6.5 times**"*

> *"overexpression of the ER chaperone, **protein disulphide isomerase**, further
> increased the secretion of **rTf approximately twelve-fold**"*

> *"Overexpression of the chaperone **BiP** or **protein disulfide isomerase
> (PDI)** increases secretion titers **2-8 fold** for **five scFvs**"*

Glycoengineering is documented at gene resolution too — `ALG3` deletion, `OCH1`
knockout, GnTI and GnTII, galactosyltransferase, sialylation — with outcomes
like *"more than 1 g/l of a functional monoclonal antibody… with uniform
N-linked glycans of the type Man5GlcNAc2"*.

**So (protein, modification) pairs are extractable at scale. Quantitative
outcomes often sit in the full text rather than the abstract, which raises the
cost per paper but does not block the test.**

---

## The find that matters more than the coverage

**The literature contains cases where the same modification helped one protein
and not another.** Those are not noise — they are the hardest possible test of
the tool, because they test *discrimination* rather than recall.

In a 40-abstract sample, at least four:

| Paper | The discrimination |
|---|---|
| *"Overexpression of binding protein and disruption of the PMR1 gene synergistically stimulate secretion of **bovine prochymosin but not plant thaumatin**"* | same two modifications, opposite outcomes |
| *"**Protein disulfide isomerase, but not binding protein**, overexpression enhances secretion of a **non-disulfide-bonded protein**"* | PDI helps a protein with no disulfides — which the obvious rule would not predict |
| *"**Contrasting** secretory processing of simultaneously expressed heterologous proteins"* — BPTI versus scFv D1.3 | same cell, same run, different fates |
| *"Structural Homology **Fails to Predict** Secretion Efficiency… **Divergent Responses of Architecturally Similar scFvs**"* | the project's existing counter-evidence |

**These are the test cases that would actually falsify the chassis.** A tool
that recommends PDI for everything scores well on a set of successes and fails
completely here. **The validation set should be built around these
deliberately**, not around the easy cases.

The second row is worth staring at. PDI improves secretion of a protein with
**no disulfide bonds**. The chassis currently fires its disulfide capability on
cysteine count — and `reports/02-feature-validation.md` already caught that rule
firing on seven proteins whose cysteines never pair. **The literature says the
relationship is not the one the tool assumes.**

---

## The limitation that shapes the whole test

**Papers report what worked. They rarely report what was tried and abandoned.**

That asymmetry is not a detail. It means:

- **Recall is measurable.** The tool says a protein needs humanised glycans; the
  paper says they humanised the glycans. That is a check.
- **Precision is mostly not measurable.** The tool says a protein needs a
  chaperone; the paper does not mention one. **We cannot tell whether that is a
  false positive or simply something the authors never tried.**

**So the retrospective test can show the tool misses things. It cannot cleanly
show the tool over-prescribes.** Any score reported from it must say which of
the two it is, or it will overstate what was established.

The differential cases above are the partial escape, because in those the
authors *did* test the alternative and report it failing.

---

## Verdict

**Build it, with the scope stated honestly.**

- **Feasible:** (protein, modification) extraction at scale, from abstracts.
- **More expensive:** quantitative outcomes, which usually need full text.
- **Most valuable:** the differential cases, which are rarer and must be hunted
  deliberately rather than collected by keyword.
- **Out of reach:** a clean false-positive rate, because of publication bias.

A first set of **30 to 50 proteins**, weighted toward differential cases, is
enough to find out whether the chassis discriminates or just pattern-matches.

---

## What is not done, and what could still go wrong

- **No validation set has been built.** This assessed feasibility only.
- **The sample is 40 abstracts and is not random.** Both searches used keywords
  that select for papers reporting engineering, so the coverage figures above
  are an **upper bound**, not an estimate of the literature as a whole.
- **Scoring was by reading, not by script**, so it is not reproducible in the
  way `scripts/validate_features.py` is.
- **No full texts were retrieved.** Whether outcomes are reliably extractable
  from full text is assumed, not checked.
- **Older papers dominate the secretion sample** — several are from the 1990s.
  Strains, vectors and measurement methods differ across three decades, and the
  set will need that recorded per entry.
- **The blind condition needs enforcing.** If the tool is adjusted after seeing
  the answers, the test is worthless. Predictions must be frozen and written
  down before the papers are read.
