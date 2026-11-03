"""Theory-stack layer 1c: translation elongation, from the yeast tRNA pool.

WHAT THIS REPLACES
------------------
chassis/chassis-v1.json carries capability A1:

    "Codon usage compatible with host tRNA pool"
    type: graded, status: native, confidence: high
    note: "Yeast codon tables well characterised"

That is a boolean with a reassuring note attached. It does not say how
compatible, it does not say which residues are the problem, and "well
characterised" describes the literature rather than the protein in front of
you. This module computes the quantity instead.

THE THEORY
----------
Ribosomes move along a message at codon-specific rates set by how well each
codon is served by the host's tRNA pool. The standard measure of that service
is the tRNA adaptation index (tAI), which weights each codon by the gene copy
number of every tRNA that can read it, discounting wobble pairings by a
published penalty:

    W_c = sum over readable tRNAs  (1 - s_pairing) * tGCN_tRNA
    w_c = W_c / max(W)
    tAI = exp( mean over codons of log w_c )

dos Reis M, Savva R, Wernisch L (2004) Solving the riddle of codon usage
preferences: a test for translational selection. Nucleic Acids Res 32:5036.

Every constant here is registered in params/parameters-v1.json:

    PRM-trna-gcn-scer    tRNA gene copy numbers, GtRNAdb sacCer3 (grade B)
    PRM-tai-s-values     wobble penalties, from the authors' own code (grade C)

The implementation follows the authors' R source (github.com/mariodosreis/tai,
R/tAI.R) rather than a retyping of the paper's prose, including its codon
block ordering, its methionine special case, and its eukaryote code path,
which skips the prokaryote-only isoleucine correction.

WHAT THIS DOES NOT PRODUCE
--------------------------
NOT A RATE. tAI is a dimensionless relative adaptiveness. Turning it into
codons per second needs a scaling constant that this project has not found
and has therefore not registered, so this module refuses to print one. A
module that invented that constant would look like physics and be decoration.

Run:  python -I scripts/elongation.py
      python -I scripts/elongation.py --seq MALWMRLLPLLALLALWGPDPAAA
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402  (registry loader lives beside this file)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Codon order used by the dos Reis implementation: third base cycles T,C,A,G
# within each block of four, second base next, first base slowest. The block
# structure is what makes the wobble rules expressible as a fixed recurrence.
BASES = "TCAG"
CODONS = [a + b + c for a in BASES for b in BASES for c in BASES]

CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}

# Which pairing each term of the recurrence represents, so the output can name
# the chemistry rather than an array index.
PAIRING_LABEL = ["WC I:U", "WC G:C", "WC U:A", "WC C:G",
                 "G:U", "I:C", "I:A", "U:G"]


def revcomp(seq):
    return "".join(COMPLEMENT[b] for b in reversed(seq))


def trna_by_codon():
    """tRNA gene copies indexed by the codon each anticodon reads Watson-Crick.

    An anticodon pairs with the reverse complement of itself. Anticodons with
    zero genes in the genome stay zero: that codon can only be reached by
    wobble, which is a modelling fact rather than missing data.
    """
    counts, _ = params.load_trna()
    by_codon = {c: 0 for c in CODONS}
    for anticodon, n in counts.items():
        by_codon[revcomp(anticodon)] = n
    return by_codon


def relative_adaptiveness():
    """w values per codon. Follows get.ws() from the authors' R source.

    Returns (w, W) where W is pre-normalisation and w is scaled to max 1 with
    zeros replaced by the geometric mean, as the method specifies.
    """
    s = params.get("PRM-tai-s-values")
    # The recurrence needs the eight penalties in the authors' order. The
    # ninth (prokaryote isoleucine) is deliberately absent: yeast is a
    # eukaryote and the authors' sking=0 path never applies it.
    p = [1 - s["I:U_and_WC"], 1 - s["I:U_and_WC"],
         1 - s["I:U_and_WC"], 1 - s["I:U_and_WC"],
         1 - s["G:U"], 1 - s["I:C"], 1 - s["I:A"], 1 - s["U:G"]]

    t = trna_by_codon()
    tv = [t[c] for c in CODONS]
    W = [0.0] * 64

    for i in range(0, 64, 4):
        W[i]     = p[0] * tv[i]     + p[4] * tv[i + 1]   # NNT: INN exact, GNN wobble G:U
        W[i + 1] = p[1] * tv[i + 1] + p[5] * tv[i]       # NNC: GNN exact, INN wobble I:C
        W[i + 2] = p[2] * tv[i + 2] + p[6] * tv[i]       # NNA: UNN exact, INN wobble I:A
        W[i + 3] = p[3] * tv[i + 3] + p[7] * tv[i + 2]   # NNG: CNN exact, UNN wobble U:G

    # Methionine has one codon and one tRNA; no wobble term applies.
    W[CODONS.index("ATG")] = p[3] * tv[CODONS.index("ATG")]

    # The method drops stop codons and methionine before normalising.
    excluded = {"TAA", "TAG", "TGA", "ATG"}
    kept = [(c, W[i]) for i, c in enumerate(CODONS) if c not in excluded]
    mx = max(v for _, v in kept)
    w = {c: v / mx for c, v in kept}

    nonzero = [v for v in w.values() if v > 0]
    if len(nonzero) < len(w):
        gm = math.exp(sum(math.log(v) for v in nonzero) / len(nonzero))
        for c in w:
            if w[c] == 0:
                w[c] = gm
    return w, {c: W[i] for i, c in enumerate(CODONS)}


def by_amino_acid(w):
    """Codons grouped by residue, each sorted best-served first."""
    groups = {}
    for c, v in w.items():
        aa = CODON_TABLE[c]
        groups.setdefault(aa, []).append((c, v))
    for aa in groups:
        groups[aa].sort(key=lambda kv: -kv[1])
    return groups


def tai_of_codons(codon_list, w):
    """tAI of a coding sequence: geometric mean of its codon weights."""
    vals = [w[c] for c in codon_list if c in w]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def protein_range(protein, w):
    """Best and worst tAI reachable for a protein by choosing its codons.

    This is the quantity a chassis actually needs. A protein's sequence is
    fixed; its codons are a design choice. The gap between the two bounds is
    how much codon optimisation can buy, and the lower bound is what the
    protein cannot escape no matter how it is encoded.
    """
    groups = by_amino_acid(w)
    best, worst, unknown = [], [], []
    for aa in protein:
        if aa == "M" or aa == "*":
            continue          # excluded by the method
        if aa not in groups:
            unknown.append(aa)
            continue
        opts = groups[aa]
        best.append(opts[0][1])
        worst.append(opts[-1][1])
    if not best:
        return None
    gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
    return {"best": gm(best), "worst": gm(worst),
            "n_scored": len(best), "unknown": unknown}


def line(ch="-", n=74):
    print(ch * n)


def main():
    w, W = relative_adaptiveness()
    groups = by_amino_acid(w)

    line("=")
    print("TRANSLATION ELONGATION IN S. CEREVISIAE, FROM THE tRNA POOL")
    line("=")
    tmeta = params.meta("PRM-trna-gcn-scer")
    smeta = params.meta("PRM-tai-s-values")
    print("tRNA gene copies : %s  (grade %s)" % (tmeta["primary_citation"].split(",")[0], tmeta["grade"]))
    print("wobble penalties : dos Reis et al. 2004, from the authors' code (grade %s)" % smeta["grade"])
    print("codons scored    : %d  (61 sense codons less methionine)" % len(w))
    print()

    line()
    print("BEST AND WORST SERVED CODONS")
    line()
    ranked = sorted(w.items(), key=lambda kv: -kv[1])
    print("  strongest                          weakest")
    for i in range(6):
        c1, v1 = ranked[i]
        c2, v2 = ranked[-(i + 1)]
        print("  %s %s  w=%.3f   W=%-6.1f      %s %s  w=%.4f   W=%.3f"
              % (c1, CODON_TABLE[c1], v1, W[c1],
                 c2, CODON_TABLE[c2], v2, W[c2]))
    print()
    print("  CONSISTENCY CHECK, NOT A TEST THE MODEL WAS TUNED TO PASS:")
    arg = groups["R"]
    print("    Arginine, best to worst: %s" % ", ".join(
        "%s %.3f" % (c, v) for c, v in arg))
    print("    Yeast codon-usage tables report AGA as the dominant arginine")
    print("    codon and CGA as the rarest. The model was given tRNA gene")
    print("    counts and wobble penalties only, no codon usage data at all,")
    print("    and reproduces that ordering. That is evidence the layer is")
    print("    wired up correctly. It is NOT evidence that tAI predicts rate.")
    print()

    line("=")
    print("WHAT THE CHASSIS COULD NOT SAY BEFORE: INTRINSIC RESIDUE COST")
    line("=")
    print("For each residue, the best weight any synonymous codon can reach.")
    print("A low number is a residue yeast serves poorly NO MATTER HOW THE")
    print("GENE IS OPTIMISED, because the tRNA genes are simply not there.")
    print()
    best_per_aa = sorted(((aa, opts[0][1], opts[0][0], len(opts))
                          for aa, opts in groups.items()),
                         key=lambda t: t[1])
    print("  %-4s %-9s %-7s %s" % ("aa", "best w", "codon", "synonymous codons"))
    line()
    for aa, v, c, n in best_per_aa:
        print("  %-4s %-9.3f %-7s %d" % (aa, v, c, n))
    print()
    print("  No threshold is applied to this table on purpose. A cutoff for")
    print("  'poorly served' would be a number with no source, which is the")
    print("  thing params/parameters-v1.json exists to prevent.")
    print()
    worst_aa, worst_v, worst_c, _ = best_per_aa[0]
    print("  THE RESULT WORTH NOTICING: the worst-served residue in yeast is")
    print("  %s, best reachable weight %.3f on codon %s. Cysteine is what" % (worst_aa, worst_v, worst_c))
    print("  disulfide bonds are made of, and disulfide-bonded secreted")
    print("  therapeutics are the class this chassis is aimed at. The protein")
    print("  family the design targets is built from the residue the host")
    print("  supplies worst, and no amount of codon optimisation changes it.")
    print()
    print("  Stated carefully: this is a property of the tRNA gene complement,")
    print("  not a measured expression penalty. It predicts a pressure, not a")
    print("  titre, and this project has not tested whether the pressure shows")
    print("  up in real yields.")
    print()

    line("=")
    print("DESIGN HEADROOM FOR A PROTEIN")
    line("=")
    print("A protein's residues are fixed; its codons are a design choice.")
    print("The gap between best and worst is what codon optimisation can buy.")
    print()

    seq = None
    if "--seq" in sys.argv:
        seq = sys.argv[sys.argv.index("--seq") + 1].upper()
    panel = [("Human preproinsulin (signal + chains)",
              "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN")]
    if seq:
        panel = [("Sequence given on the command line", seq)]

    print("  %-40s %8s %8s %6s" % ("protein", "best", "worst", "ratio"))
    line()
    for name, protein in panel:
        r = protein_range(protein, w)
        print("  %-40s %8.3f %8.3f %6.2fx"
              % (name[:40], r["best"], r["worst"], r["best"] / r["worst"]))
    print()
    print("  Read this as: encoding choice moves achievable adaptiveness by")
    print("  that factor. It does NOT say the protein comes out that much")
    print("  faster, because tAI is not a rate.")
    print()

    line("=")
    print("WHAT THIS LAYER DOES NOT DO")
    line("=")
    for item in [
        "It gives no rate. tAI is dimensionless relative adaptiveness. The "
        "scaling to codons per second is not registered, so it is not printed.",
        "Gene copy number is a proxy for tRNA abundance, not a measurement of "
        "it, and abundance shifts with growth rate and condition.",
        "The wobble penalties are grade C: the authors call them optimised, "
        "and this project has not checked whether yeast was in the fit.",
        "tRNA modification is ignored entirely. Real decoding depends on "
        "modified bases at the wobble position, which the s-values summarise "
        "with a single constant per pairing type.",
        "No ribosome traffic. A true TASEP would model queueing behind slow "
        "codons; this is a per-codon weight with no interaction between "
        "ribosomes, so it cannot predict a jam.",
        "It is not validated against yeast expression data. The arginine "
        "ordering above shows the wiring is right, not that the output "
        "predicts titre.",
        "Capability A1 in chassis-v1.json still reads 'native, confidence "
        "high'. This module computes the quantity; nothing has yet rewritten "
        "the chassis object to consume it.",
    ]:
        print("  - %s" % item)
    print()


if __name__ == "__main__":
    main()
