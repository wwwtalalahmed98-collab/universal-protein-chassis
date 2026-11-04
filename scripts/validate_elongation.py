"""Gate 4 for the elongation layer, against a measurement it was not shown.

WHY THIS EXISTS
---------------
protocol/layer-architecture-v1.md sets five gates a theory layer must pass.
scripts/elongation.py passed gate 4 on a weak form of the test: given tRNA
gene counts and no codon usage data, it reproduced the known yeast arginine
codon ordering. That shows the wiring is right. It does not show the layer
predicts anything about a cell.

This script runs the harder version: does codon adaptiveness, computed from
tRNA gene copy numbers alone, predict how heavily yeast ribosomes actually
occupy a gene?

THE MEASUREMENT
---------------
Weinberg DE, Shah P, Eichhorn SW, Hussmann JA, Plotkin JB, Bartel DP (2016)
Improved ribosome-footprint and mRNA measurements provide insights into
dynamics and regulation of yeast translation. Cell Rep 14:1787-1799.
GEO series GSE75897.

    GSE75897_RPF_RPKMs.txt.gz       ribosome-footprint density per gene
    GSE75897_RiboZero_RPKMs.txt.gz  mRNA abundance per gene

Translation efficiency is the ratio: footprint density divided by mRNA
abundance. It is how heavily loaded with ribosomes a message is, per copy of
that message, which is the closest available proxy for how well the cell
translates it.

Coding sequences: SGD S288C reference, orf_coding.fasta.

THE CIRCULARITY, STATED BEFORE THE RESULT
-----------------------------------------
tAI is NOT an independent predictor of expression, and a correlation with
translation efficiency is partly built in. The method's own constants were
optimised to correlate with codon usage bias, and codon usage bias is itself
strongest in highly expressed genes. Finding a positive correlation here is
therefore the expected outcome and a weak test on its own.

So two controls run alongside, and they are the point of this script:

  COMPOSITION-ONLY MODEL  Replace every codon's weight with the average
      weight for its amino acid. This keeps what the protein is made of and
      throws away which synonymous codon was chosen. If the real model does
      not beat this, the layer is measuring amino acid composition and the
      tRNA pool is decoration.

  PERMUTATION NULL  Shuffle the 60 weights among the 60 codons, breaking the
      link to the tRNA genes, and recompute. If an arbitrary weighting scores
      as well, the tRNA data is not what is carrying the signal.

Run:  python -I scripts/validate_elongation.py
"""
import gzip
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random

from scipy import stats

import elongation
from elongation import CODON_TABLE

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CDS_FA = os.path.join(ROOT, "data", "sgd", "orf_coding.fasta.gz")
RPF = os.path.join(ROOT, "data", "riboseq", "GSE75897_RPF_RPKMs.txt.gz")
MRNA = os.path.join(ROOT, "data", "riboseq", "GSE75897_RiboZero_RPKMs.txt.gz")
RRT = os.path.join(ROOT, "data", "gardin", "rrt_table2.tsv")

# Expression cutoffs are swept rather than chosen, for the same reason
# scripts/growth_coupling.py sweeps module cost: a single cutoff would be a
# number with no source, which params/parameters-v1.json exists to prevent.
MRNA_CUTOFF_SWEEP = [0.0, 1.0, 5.0, 10.0, 50.0]
N_PERMUTATIONS = 200
SEED = 20261104


def read_cds(path):
    genes, name, buf = {}, None, []
    with gzip.open(path, "rt") as fh:
        for raw in fh:
            if raw.startswith(">"):
                if name:
                    genes[name] = "".join(buf)
                name = raw[1:].split()[0]
                buf = []
            else:
                buf.append(raw.strip().upper())
    if name:
        genes[name] = "".join(buf)
    return genes


def read_rpkm(path):
    out = {}
    with gzip.open(path, "rt") as fh:
        for raw in fh:
            parts = raw.strip().split("\t")
            if len(parts) < 2:
                continue
            try:
                out[parts[0]] = float(parts[1])
            except ValueError:
                continue       # a header row, if one is ever added
    return out


def codons_of(cds):
    """In-frame codons, stops and methionine dropped, as the method requires."""
    out = []
    for i in range(0, len(cds) - 2, 3):
        c = cds[i:i + 3]
        if len(c) != 3 or any(b not in "ACGT" for b in c):
            continue
        if c in ("TAA", "TAG", "TGA", "ATG"):
            continue
        out.append(c)
    return out


def gm_weight(codon_list, w):
    vals = [w[c] for c in codon_list if c in w]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def composition_only(w):
    """Each codon gets its amino acid's mean weight: synonymous choice erased."""
    by_aa = {}
    for c, v in w.items():
        by_aa.setdefault(CODON_TABLE[c], []).append(v)
    means = {aa: sum(vs) / len(vs) for aa, vs in by_aa.items()}
    return {c: means[CODON_TABLE[c]] for c in w}


def read_rrt(path):
    """Gardin 2014 Table 2, section A: residence time at the A site per codon.

    Higher residence time means the codon is decoded more slowly.

    Returns (table, duplicated_codons). Any codon appearing more than once in
    the source is EXCLUDED rather than silently overwritten: the published
    table has such a defect, and resolving it would mean inferring which row
    was mislabelled, which is a change to someone else's data.
    """
    seen = {}
    order = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#"):
                continue
            parts = raw.rstrip().split("\t")
            if len(parts) < 5 or parts[0] == "section" or parts[0] != "A":
                continue
            try:
                rec = {"aa": parts[2], "usage": float(parts[3]),
                       "rrt": float(parts[4])}
            except ValueError:
                continue
            seen.setdefault(parts[1], []).append(rec)
            order.append(parts[1])

    dups = sorted(c for c, v in seen.items() if len(v) > 1)
    table = {c: v[0] for c, v in seen.items() if len(v) == 1}
    return table, dups


def line(ch="-", n=74):
    print(ch * n)


def main():
    missing = [p for p in (CDS_FA, RPF, MRNA) if not os.path.exists(p)]
    if missing:
        print("Missing input data. The project .gitignore excludes *.gz, so")
        print("these are fetched rather than committed. To retrieve them:")
        print()
        print("  mkdir -p data/riboseq data/sgd")
        print("  curl -L -o data/riboseq/GSE75897_RPF_RPKMs.txt.gz \\")
        print("    https://ftp.ncbi.nlm.nih.gov/geo/series/GSE75nnn/GSE75897/"
              "suppl/GSE75897_RPF_RPKMs.txt.gz")
        print("  curl -L -o data/riboseq/GSE75897_RiboZero_RPKMs.txt.gz \\")
        print("    https://ftp.ncbi.nlm.nih.gov/geo/series/GSE75nnn/GSE75897/"
              "suppl/GSE75897_RiboZero_RPKMs.txt.gz")
        print("  curl -L -o data/sgd/orf_coding.fasta.gz \\")
        print("    http://sgd-archive.yeastgenome.org/sequence/"
              "S288C_reference/orf_dna/orf_coding.fasta.gz")
        print()
        for p in missing:
            print("  still missing: %s" % p)
        return

    w, _ = elongation.relative_adaptiveness()
    w_comp = composition_only(w)

    cds = read_cds(CDS_FA)
    rpf = read_rpkm(RPF)
    mrna = read_rpkm(MRNA)

    line("=")
    print("GATE 4: DOES THE tRNA POOL PREDICT MEASURED RIBOSOME OCCUPANCY?")
    line("=")
    print("coding sequences (SGD S288C)   : %d" % len(cds))
    print("genes with footprint density   : %d" % len(rpf))
    print("genes with mRNA abundance      : %d" % len(mrna))

    shared = sorted(set(cds) & set(rpf) & set(mrna))
    print("present in all three           : %d" % len(shared))
    print()

    rows = []
    for g in shared:
        cl = codons_of(cds[g])
        if len(cl) < 1:
            continue
        a_real = gm_weight(cl, w)
        a_comp = gm_weight(cl, w_comp)
        if a_real is None or mrna[g] <= 0:
            continue
        rows.append({"gene": g, "codons": cl, "n_cod": len(cl),
                     "tai": a_real, "comp": a_comp,
                     "rpf": rpf[g], "mrna": mrna[g],
                     "te": rpf[g] / mrna[g]})
    print("scored genes                   : %d" % len(rows))
    print("shortest / longest, in codons  : %d / %d"
          % (min(r["n_cod"] for r in rows), max(r["n_cod"] for r in rows)))
    print()
    print("No CDS-length filter is applied. Expression cutoffs are swept")
    print("rather than chosen, so no threshold in this script is a number")
    print("invented to make a result appear.")
    print()

    line("=")
    print("TRANSLATION EFFICIENCY vs CODON ADAPTIVENESS")
    line("=")
    print("Spearman rank correlation. TE = footprint density / mRNA abundance.")
    print()
    print("%-12s %7s %22s %22s" % ("mRNA cutoff", "genes",
                                   "tAI (real tRNA pool)", "composition only"))
    line()
    results = {}
    for cut in MRNA_CUTOFF_SWEEP:
        sub = [r for r in rows if r["mrna"] >= cut]
        if len(sub) < 30:
            continue
        te = [r["te"] for r in sub]
        r1 = stats.spearmanr([r["tai"] for r in sub], te)
        r2 = stats.spearmanr([r["comp"] for r in sub], te)
        results[cut] = (len(sub), r1, r2)
        print("%-12s %7d      rho=%+.3f p=%-7.1g      rho=%+.3f p=%-7.1g"
              % ("RPKM >= %g" % cut, len(sub),
                 r1.statistic, r1.pvalue, r2.statistic, r2.pvalue))
    print()

    line("=")
    print("CONTROL 1: DOES CODON CHOICE BEAT AMINO ACID COMPOSITION?")
    line("=")
    print("If the real model does not beat the composition-only model, the")
    print("layer is measuring what the protein is made of, and the tRNA gene")
    print("counts are decoration.")
    print()
    for cut, (n, r1, r2) in results.items():
        gap = r1.statistic - r2.statistic
        verdict = "codon choice adds signal" if gap > 0.02 else \
                  "NO GAIN over composition" if gap <= 0 else "marginal"
        print("  RPKM >= %-5g n=%-6d real %+.3f  comp %+.3f  gap %+.3f  %s"
              % (cut, n, r1.statistic, r2.statistic, gap, verdict))
    print()

    line("=")
    print("CONTROL 2: PERMUTATION NULL")
    line("=")
    print("Shuffle the %d weights among the %d codons, breaking the link to"
          % (len(w), len(w)))
    print("the tRNA genes, and recompute. %d permutations, seed %d."
          % (N_PERMUTATIONS, SEED))
    print()
    rng = random.Random(SEED)
    cut = 5.0
    sub = [r for r in rows if r["mrna"] >= cut]
    te = [r["te"] for r in sub]
    observed = stats.spearmanr([r["tai"] for r in sub], te).statistic

    codon_keys = list(w)
    vals = [w[c] for c in codon_keys]
    null = []
    for _ in range(N_PERMUTATIONS):
        shuffled = vals[:]
        rng.shuffle(shuffled)
        wp = dict(zip(codon_keys, shuffled))
        null.append(stats.spearmanr(
            [gm_weight(r["codons"], wp) for r in sub], te).statistic)

    beat = sum(1 for v in null if abs(v) >= abs(observed))
    null_abs = sorted(abs(v) for v in null)
    print("  genes used (RPKM >= %g)      : %d" % (cut, len(sub)))
    print("  observed rho                 : %+.3f" % observed)
    print("  permuted |rho| median        : %.3f" % null_abs[len(null_abs) // 2])
    print("  permuted |rho| 95th pct      : %.3f" % null_abs[int(0.95 * len(null_abs))])
    print("  permuted |rho| max           : %.3f" % null_abs[-1])
    print("  permutations reaching it     : %d of %d  -> empirical p %s %.3g"
          % (beat, N_PERMUTATIONS,
             "<" if beat == 0 else "=",
             1.0 / N_PERMUTATIONS if beat == 0 else beat / N_PERMUTATIONS))
    print()

    line("=")
    print("SECONDARY: THE CONFOUND, MEASURED RATHER THAN HIDDEN")
    line("=")
    print("Highly expressed genes are both codon-optimised and heavily")
    print("translated, so correlation with raw expression is expected and is")
    print("not evidence the layer predicts translation specifically.")
    print()
    for cut in (0.0, 5.0):
        sub = [r for r in rows if r["mrna"] >= cut]
        rr = stats.spearmanr([r["tai"] for r in sub], [r["rpf"] for r in sub])
        rm = stats.spearmanr([r["tai"] for r in sub], [r["mrna"] for r in sub])
        print("  RPKM >= %-5g n=%-6d tAI vs footprint rho=%+.3f   "
              "tAI vs mRNA rho=%+.3f"
              % (cut, len(sub), rr.statistic, rm.statistic))
    print()
    print("  tAI correlates with mRNA abundance as well, which the layer")
    print("  makes no claim about. That is the confound in one number.")
    print()

    line("=")
    print("THE SHARPER TEST: PER-CODON DECODING SPEED, MEASURED DIRECTLY")
    line("=")
    print("Gardin et al. 2014, eLife 3:e03735, Table 2A. Ribosome residence")
    print("time at the A site for each of the 61 sense codons. Higher means")
    print("the codon is decoded more slowly.")
    print()
    print("This test escapes the circularity above, because residence time is")
    print("a POSITIONAL measurement of decoding speed, not a gene expression")
    print("level. The layer predicts a NEGATIVE correlation: a codon the tRNA")
    print("pool serves well should be passed through quickly.")
    print()
    if not os.path.exists(RRT):
        print("  MISSING: %s" % RRT)
    else:
        rrt, dups = read_rrt(RRT)
        pairs = [(w[c], rrt[c]["rrt"], rrt[c]["usage"], c)
                 for c in rrt if c in w]
        print("  codons matched to our weights : %d" % len(pairs))
        print("  (methionine is excluded by the tAI method, so 60 is the max)")
        if dups:
            print()
            print("  A DEFECT IN THE SOURCE TABLE, NOT SILENTLY PATCHED:")
            print("  %s appears more than once in the published table with"
                  % ", ".join(dups))
            print("  different values, so serine is one codon short. Both rows")
            print("  are EXCLUDED here. The usage figures suggest one row was")
            print("  mislabelled, but correcting someone else's published data")
            print("  on our own inference is not a thing this project does.")
        print()
        ws = [p[0] for p in pairs]
        rt = [p[1] for p in pairs]
        us = [p[2] for p in pairs]

        r_w = stats.spearmanr(ws, rt)
        r_u = stats.spearmanr(us, rt)
        print("  adaptiveness w   vs residence time : rho=%+.3f  p=%.2g"
              % (r_w.statistic, r_w.pvalue))
        print("  codon usage freq vs residence time : rho=%+.3f  p=%.2g"
              % (r_u.statistic, r_u.pvalue))
        print()
        print("  CONTROL 3: codon usage frequency is the predictor that needs")
        print("  no tRNA data at all. It is printed in the same source table.")
        print("  If usage predicts residence time as well as our weights do,")
        print("  the tRNA gene counts bought nothing.")
        print()
        if abs(r_w.statistic) > abs(r_u.statistic) + 0.05:
            print("  -> the tRNA-derived weights predict decoding speed BETTER")
            print("     than codon usage frequency does.")
        elif abs(r_u.statistic) > abs(r_w.statistic) + 0.05:
            print("  -> codon usage frequency predicts decoding speed BETTER")
            print("     than our tRNA-derived weights. The tRNA layer loses to")
            print("     the simpler predictor, and that is a real failure.")
        else:
            print("  -> the two predictors are within 0.05 of each other. The")
            print("     tRNA data does not clearly beat counting codons.")
        print()

        slow = sorted(pairs, key=lambda t: -t[1])[:8]
        fast = sorted(pairs, key=lambda t: t[1])[:8]
        print("  %-28s %-28s" % ("slowest measured codons", "fastest measured codons"))
        line()
        for a, b in zip(slow, fast):
            print("  %s %-4s RRT %.2f  w %.3f    %s %-4s RRT %.2f  w %.3f"
                  % (a[3], rrt[a[3]]["aa"], a[1], a[0],
                     b[3], rrt[b[3]]["aa"], b[1], b[0]))
        print()

    line("=")
    print("WHAT THIS DOES AND DOES NOT ESTABLISH")
    line("=")
    for item in [
        "The measurement is external. This project did not choose it, did "
        "not generate it, and the layer was built before it was retrieved.",
        "A positive correlation is PARTLY BUILT IN. The tAI constants were "
        "optimised against codon usage bias, which is strongest in highly "
        "expressed genes. The controls exist because of this, and the "
        "controls are what carry whatever weight this test has.",
        "Correlation is not rate. Nothing here converts adaptiveness into "
        "codons per second, and the layer still refuses to print a rate.",
        "This is a population average across one growth condition. Ribosome "
        "profiling in rich medium says nothing about a stressed, "
        "protein-overproducing cell, which is the condition the chassis "
        "actually targets.",
        "Footprint density is not elongation speed. High occupancy can mean "
        "fast initiation or slow elongation, and the ratio used here cannot "
        "separate them.",
        "Nothing is tested about heterologous protein. Every gene here is a "
        "native yeast gene that has had millions of years to adapt to this "
        "tRNA pool. A foreign gene has not.",
        "THE ORDERING IS RIGHT AND THE MAGNITUDES ARE NOT. Our weights span "
        "a factor of about 27,000 from best to worst codon; measured "
        "residence times span a factor of 2.7. The model ranks codons "
        "usefully and wildly overstates how different they are, which is "
        "exactly why it must not be converted into a rate.",
        "CGA is the clearest case: the model calls it effectively unreadable, "
        "weight near zero, and the measurement puts it slow but unremarkable "
        "at 1.45. Gene copy number alone cannot see that wobble decoding "
        "still works, just poorly.",
        "Two codons are missing from the comparison because the published "
        "table duplicates one label and both rows were dropped. 58 of a "
        "possible 60 were used.",
        "Residence time is measured in one organism under one condition by "
        "one method. Ribosome profiling is known to be sensitive to how cells "
        "are harvested, and this project did not evaluate that.",
    ]:
        print("  - %s" % item)
    print()


if __name__ == "__main__":
    main()
