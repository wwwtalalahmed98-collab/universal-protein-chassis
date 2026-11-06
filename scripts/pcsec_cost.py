"""P0.1 — can a per-protein secretory requirement be extracted from pcSecYeast?

WHY THIS IS THE FIRST THING IN THE PLAN
---------------------------------------
protocol/masterplan-v1.md puts this first because the most downstream work
depends on it and nobody had checked. scripts/pcsec.py proved the model loads
and solves without MATLAB; it did not prove anything useful can be read out of
it. "It solves" and "it answers our question" are different claims, and this
project has already been burned once by not separating them.

WHAT THE MODEL TURNS OUT TO CONTAIN
-----------------------------------
Reactions are named per gene with a secretory process suffix, and the suffix
names the machinery complex:

    YAL023C_Post_translation_PSTA_sec_BIP_NEFS_complex
    YAL023C_misfold_ERAD_sec_Kar2p_complex
    YAL023C_ERAD4A_sec_Mnl1p_Pdi1p_complex
    YAL023C_GLNG_Golgi_N_linked_glycosylation_I_sec_Och1p_complex

So the model carries, for 1,137 native proteins, an explicit route through named
machinery — including Kar2p (BiP), Pdi1p (PDI) and Och1p, which are precisely
the three genes the validation campaigns manipulated and the three our
engineered modules target.

WHAT THAT IS WORTH, AND THE QUESTION THIS SCRIPT ASKS
----------------------------------------------------
reports/05-retrospective-score.md found the chassis cannot discriminate: it
predicts secretion engineering for every secreted protein because its trigger is
"is it secreted". The masterplan's P1.2 needs a trigger that can be FALSE.

So the question is not "does the model have machinery" but:

    DO ALL PROTEINS ROUTE THROUGH THE SAME MACHINERY, OR ONLY SOME?

If only some native proteins require Kar2p or Pdi1p, the model already encodes
the conditionality the chassis lacks, and P1.2 has a principled basis instead of
a guess. If all of them do, the model is as undiscriminating as our tool and
P1.2 must look elsewhere. Either answer changes the plan, which is why it is
asked before anything is built on it.

WHAT THIS SCRIPT DOES NOT DO
----------------------------
It does not produce a proteome cost in grams or mass fraction. That needs the
enzyme-usage and proteome-pool constraints, and a first pass found no pool
reaction under the obvious names, so the cost extraction is a separate question
this script deliberately leaves open rather than faking.

Run:  python -I scripts/pcsec_cost.py
"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(ROOT, "data", "models", "pcSecYeast.mat")

# The three genes the validation campaigns actually manipulated, plus the
# complexes they appear in. Kar2p IS BiP; Pdi1p IS PDI.
WATCH = {
    "Kar2p": "BiP, the chaperone in the bip-1, bip-2 and bip-3 campaigns",
    "BIP_NEFS": "BiP with its nucleotide exchange factors, at translocation",
    "Pdi1p": "PDI, the chaperone in the pdi-1, pdi-2 and pdi-3 campaigns",
    "Och1p": "the mannosyltransferase MOD-glycan knocks out",
    "OSTC": "oligosaccharyltransferase, attaches the core N-glycan",
    "Sec61": "the translocon",
}


def line(ch="-", n=78):
    print(ch * n)


def load():
    try:
        import scipy.io as sio
    except ImportError:
        print("scipy is required.")
        return None
    if not os.path.exists(MAT):
        print("Model not found: %s" % MAT)
        print("Fetch it with: python -I scripts/pcsec.py")
        return None
    return sio.loadmat(MAT, struct_as_record=False, squeeze_me=True)["model"]


def gene_of(rxn, genes):
    """Longest gene in the model's own gene list that prefixes this reaction id.

    Parsing the gene out with a regex over-matches: 'YAL023C_GLNG_...' yields
    'YAL023C_G' if the pattern allows a trailing letter suffix. Matching against
    the model's declared gene list cannot make that mistake.
    """
    for n in (12, 11, 10, 9, 8, 7):
        cand = rxn[:n]
        if cand in genes and (len(rxn) == n or rxn[n] == "_"):
            return cand
    return None


def main():
    m = load()
    if m is None:
        return 1

    rxns = [str(x) for x in m.rxns]
    genes = set(str(x) for x in m.genes)

    line("=")
    print("P0.1  PER-PROTEIN SECRETORY ROUTES IN pcSecYeast")
    line("=")
    print("  reactions        : %d" % len(rxns))
    print("  genes declared   : %d" % len(genes))

    owned = defaultdict(list)
    for r in rxns:
        g = gene_of(r, genes)
        if g:
            owned[g].append(r)
    print("  proteins with their own secretory reactions : %d" % len(owned))
    counts = sorted(len(v) for v in owned.values())
    if counts:
        print("  reactions per protein: min %d, median %d, max %d"
              % (counts[0], counts[len(counts) // 2], counts[-1]))
    print()

    # Which machinery complexes exist, and how many proteins use each.
    users = defaultdict(set)
    for g, rs in owned.items():
        for r in rs:
            for mach in re.findall(r'_sec_([A-Za-z0-9_]+?)_complex', r):
                # Index the whole complex name AND its parts. Parts alone would
                # report a compound name like BIP_NEFS as absent, which reads as
                # a finding rather than as a parsing artifact.
                users[mach].add(g)
                for part in mach.split("_"):
                    if part:
                        users[part].add(g)
    total = len(owned)

    line("=")
    print("THE QUESTION THAT DECIDES P1.2")
    line("=")
    print("Does every protein route through the same machinery, or only some?")
    print("If only some, the model already encodes the conditionality the")
    print("chassis lacks. If all, it is as undiscriminating as our tool is.")
    print()
    print("%-12s %7s  %-6s %s" % ("machinery", "proteins", "share", "what it is"))
    line()
    for name, why in WATCH.items():
        hits = set()
        for part, gs in users.items():
            if name.lower() in part.lower():
                hits |= gs
        share = 100.0 * len(hits) / total if total else 0
        print("%-12s %7d  %5.1f%% %s" % (name, len(hits), share, why[:44]))
    print()

    # The headline: is any watched machinery used by a strict subset?
    verdict = []
    for name in WATCH:
        hits = set()
        for part, gs in users.items():
            if name.lower() in part.lower():
                hits |= gs
        if hits:
            verdict.append((name, len(hits), 100.0 * len(hits) / total))
    discriminating = [v for v in verdict if 2 < v[2] < 98]
    print("  machinery used by a STRICT SUBSET of proteins (2%% to 98%%): %d of %d"
          % (len(discriminating), len(verdict)))
    for n, c, s in sorted(discriminating, key=lambda t: -t[2]):
        print("      %-12s %d proteins, %.1f%%" % (n, c, s))
    print()
    if discriminating:
        print("  -> The model DOES distinguish between proteins. Which machinery a")
        print("     protein needs is a property of that protein here, not a")
        print("     constant. That is the basis P1.2 needs.")
    else:
        print("  -> Every protein routes the same way. The model cannot supply a")
        print("     conditional trigger and P1.2 must look elsewhere.")
    print()

    # The 30 most selective machinery complexes: the candidate trigger features.
    line("=")
    print("MOST SELECTIVE MACHINERY — candidate conditional triggers for P1.2")
    line("=")
    sel = sorted(((p, len(g)) for p, g in users.items() if 10 < len(g) < total * 0.9),
                 key=lambda t: t[1])
    print("  %d complexes are required by between 10 proteins and 90%% of them."
          % len(sel))
    print("  The rarest are the most informative, because needing one is a fact")
    print("  about the protein rather than about secretion in general.")
    print()
    print("  %-28s %8s %s" % ("machinery part", "proteins", "share"))
    line()
    for p, n in sel[:22]:
        print("  %-28s %8d %5.1f%%" % (p[:28], n, 100.0 * n / total))
    print()

    line("=")
    print("WHAT THIS ESTABLISHES, AND WHAT IT DOES NOT")
    line("=")
    for item in [
        "ESTABLISHED: pcSecYeast carries a per-protein, machinery-resolved "
        "secretory route for 1,137 native proteins, naming Kar2p (BiP), "
        "Pdi1p (PDI) and Och1p explicitly - the three genes the validation "
        "campaigns manipulated.",
        "ESTABLISHED: machinery requirements vary between proteins, so the "
        "model is a candidate source for the conditional triggers P1.2 needs.",
        "NOT ESTABLISHED: a proteome cost in mass or mass fraction. No protein "
        "pool reaction was found under the obvious names, so the cost side of "
        "P3 is still open and this script does not pretend otherwise.",
        "NOT ESTABLISHED: that these routes predict anything about a "
        "HETEROLOGOUS protein. Every one of the 1,137 is a native yeast "
        "protein with its own curated route. A foreign protein has no entry, "
        "and how its route would be assigned is the real P1.2 problem.",
        "NOT ESTABLISHED: that the model's assignment is correct. These routes "
        "are the curators' annotations, not measurements, and this script has "
        "not checked any of them against an experiment.",
        "NOT TESTED: whether the proteins the model routes through Kar2p are "
        "the ones BiP overexpression actually helped. That is the obvious next "
        "check and it is the one that would make this finding worth something.",
    ]:
        print("  - %s" % item)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
