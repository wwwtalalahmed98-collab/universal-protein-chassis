"""Resolve a target protein against the computational chassis.

Reads chassis/chassis-v1.json, computes what the target protein needs from its
sequence, and reports which chassis capabilities must be active, which are
native to the base organism and which require an engineered module.

This is modules 1 and 2 of protocol/tool-spec-v1.md. It needs no MATLAB and no
external model. It does NOT predict titre, yield or success - module 3 would do
that and is not implemented.

Sequence features marked HEURISTIC below are computed by simple rules, not by a
trained predictor, and are the weakest part of this script.

Run:  python -I scripts/chassis_resolve.py
      python -I scripts/chassis_resolve.py --seq MALWMRLL... --name "my protein"
      python -I scripts/chassis_resolve.py --fasta path/to/file.fasta
"""
import argparse
import json
import os
import re
import sys

# python -I drops the script's own directory from sys.path, so sibling modules
# (elongation, params) need it put back explicitly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHASSIS = os.path.join(HERE, "chassis", "chassis-v1.json")

# Kyte-Doolittle hydropathy, used for the two heuristic calls below.
KD = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
    "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
    "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}

AA = set(KD)


def mean_hydropathy(seq):
    vals = [KD[c] for c in seq if c in KD]
    return sum(vals) / len(vals) if vals else 0.0


def features(seq):
    """Derive the protein's requirements from its sequence."""
    seq = re.sub(r"[^A-Z]", "", seq.upper())
    unknown = sorted(set(seq) - AA)
    n = len(seq)

    # N-glycosylation sequon: N-X-S/T where X is not proline. Sequence-exact.
    sequons = [
        i + 1
        for i in range(n - 2)
        if seq[i] == "N" and seq[i + 1] != "P" and seq[i + 2] in "ST"
    ]

    cys = seq.count("C")

    # HEURISTIC: N-terminal signal peptide. Real answer needs SignalP.
    # Signal peptides carry a short hydrophobic h-region inside the first ~30
    # residues, so scan 9-residue windows and take the strongest rather than
    # averaging a fixed slice - averaging dilutes the h-region with the charged
    # n-region and the polar c-region around it.
    sig_h = max((mean_hydropathy(seq[i:i + 9]) for i in range(0, min(22, max(n - 9, 0)) + 1)),
                default=0.0)
    sig_like = n > 30 and sig_h > 1.6

    # HEURISTIC: internal transmembrane segments. Real answer needs DeepTMHMM.
    tm_windows = 0
    i = 25 if sig_like else 0
    while i <= n - 19:
        if mean_hydropathy(seq[i:i + 19]) > 1.6:
            tm_windows += 1
            i += 19
        else:
            i += 1

    return {
        "length_aa": n,
        "unknown_residues": unknown,
        "cysteine_count": cys,
        "cysteine_pairs": cys // 2,
        "n_glyc_sequons": len(sequons),
        "n_glyc_positions": sequons,
        "signal_peptide_predicted": sig_like,
        "tm_segments_predicted": tm_windows,
        "o_glyc_required": None,
        "other_ptm_required": None,
    }


def resolve(chassis, feat, product_class, secreted):
    """Decide which capabilities are active. Returns (active, inactive, unknowns)."""
    active, inactive, unknowns = [], [], []

    for cap in chassis["capabilities"]:
        cid, trig = cap["id"], cap.get("triggered_by")
        reason = None

        if cap.get("always_required"):
            reason = "required by every product"
        elif cid == "B2" and feat["cysteine_pairs"] >= 1:
            reason = f"{feat['cysteine_count']} cysteines, up to {feat['cysteine_pairs']} disulfide pairs"
        elif cid == "B3" and feat["n_glyc_sequons"] >= 1:
            reason = f"{feat['n_glyc_sequons']} N-X-S/T sequons at {feat['n_glyc_positions'][:6]}"
        elif cid == "B4" and feat["n_glyc_sequons"] >= 1 and product_class == "therapeutic":
            reason = "glycosylated therapeutic: yeast high-mannose glycans are immunogenic"
        elif cid == "A4" and feat["length_aa"] > 1000:
            reason = f"{feat['length_aa']} residues exceeds the routine range"
        elif cid == "E3" and secreted:
            reason = "product is to be secreted"
        elif cid == "D5":
            reason = None  # decided after B4, below
        elif cid in ("B5", "B6"):
            unknowns.append((cid, cap["name"], "needs annotation this script cannot compute from sequence"))
            continue

        if reason:
            active.append((cid, cap, reason))
        else:
            inactive.append((cid, cap))

    # D5 couples to B4: only needed if humanised glycans are on.
    if any(c[0] == "B4" for c in active):
        d5 = next(c for c in chassis["capabilities"] if c["id"] == "D5")
        active.append(("D5", d5, "feeds the humanised glycan pathway (MOD-glycan)"))
        inactive = [x for x in inactive if x[0] != "D5"]

    return active, inactive, unknowns


def a1_block(seq, chassis):
    """Capability A1, computed rather than asserted.

    A1 used to print as "native, confidence high" on the strength of a note
    saying yeast codon tables are well characterised. That is a statement
    about the literature, not about the protein on the bench. The elongation
    layer turns it into numbers for this sequence.

    Degrades to a one-line notice if the layer is unavailable, because the
    rest of the resolver does not depend on it.
    """
    a1 = next((c for c in chassis["capabilities"] if c["id"] == "A1"), None)
    ql = (a1 or {}).get("quantitative_layer")
    print("\nA1  CODON ADAPTIVENESS, COMPUTED FOR THIS SEQUENCE")
    print("-" * 72)
    if not ql:
        print("  chassis object carries no quantitative layer for A1")
        return
    try:
        import elongation
    except Exception as exc:
        print(f"  layer unavailable ({exc.__class__.__name__}); A1 falls back to")
        print(f"  the categorical judgement: {a1['status']}, {a1['confidence']}")
        return

    w, _ = elongation.relative_adaptiveness()
    rng = elongation.protein_range(seq, w)
    if not rng:
        print("  no scorable residues in this sequence")
        return

    groups = elongation.by_amino_acid(w)
    print(f"  best reachable by codon choice : {rng['best']:.3f}")
    print(f"  worst reachable                : {rng['worst']:.3f}")
    print(f"  design headroom                : {rng['best'] / rng['worst']:.2f}x")
    print(f"  residues scored                : {rng['n_scored']} "
          f"(methionine excluded by the method)")

    counts = {}
    for aa in seq.upper():
        if aa in groups and aa != "M":
            counts[aa] = counts.get(aa, 0) + 1
    worst = sorted(counts, key=lambda a: groups[a][0][1])[:3]
    if worst:
        print("  worst-served residues present  : " + ", ".join(
            f"{a} x{counts[a]} (best w {groups[a][0][1]:.3f})" for a in worst))

    ev = ql["external_validation"]["per_codon_decoding_speed"]
    print(f"  layer validation               : rho {ev['spearman_rho']:+.3f} "
          f"vs measured decoding speed, n={ev['n_codons']} codons")
    print(f"  grade of anything built on it  : {ql['lowest_parameter_grade']}"
          f"  (lowest input parameter)")
    print("  NO RATE IS GIVEN. The layer's predicted spread between best and")
    print("  worst codon is ~27,000x; the measured spread is 2.7x. Ordering is")
    print("  usable, magnitude is not.")


def report(name, seq, product_class, secreted, chassis):
    feat = features(seq)
    active, inactive, unknowns = resolve(chassis, feat, product_class, secreted)

    bar = "=" * 72
    print(bar)
    print(f"TARGET: {name}")
    print(f"chassis: {chassis['chassis_id']} on {chassis['base_organism']['species']}")
    print(bar)

    print("\nSEQUENCE FEATURES")
    print("-" * 72)
    print(f"  length                      : {feat['length_aa']} aa")
    print(f"  cysteines                   : {feat['cysteine_count']} "
          f"(up to {feat['cysteine_pairs']} disulfide pairs)")
    print(f"  N-glycosylation sequons     : {feat['n_glyc_sequons']} "
          f"{feat['n_glyc_positions'][:8] if feat['n_glyc_positions'] else ''}")
    print(f"  signal peptide              : {feat['signal_peptide_predicted']}   [HEURISTIC]")
    print(f"  transmembrane segments      : {feat['tm_segments_predicted']}   [HEURISTIC]")
    print(f"  O-glycosylation             : unknown, not computable here")
    print(f"  other PTMs                  : unknown, not computable here")
    if feat["unknown_residues"]:
        print(f"  !! non-standard residues    : {feat['unknown_residues']}")

    a1_block(seq, chassis)

    eng = [(cid, c, r) for cid, c, r in active if c["status"] == "engineered"]
    nat = [(cid, c, r) for cid, c, r in active if c["status"] != "engineered"]

    print(f"\nCAPABILITIES ACTIVE: {len(active)} of "
          f"{chassis['scope']['capabilities_required_for_proteins']} in the protein set")
    print("-" * 72)
    print(f"  native to {chassis['base_organism']['species']} ({len(nat)}):")
    for cid, c, r in sorted(nat):
        print(f"    {cid:<3} {c['name'][:40]:<42} {r}")
    print(f"\n  REQUIRE AN ENGINEERED MODULE ({len(eng)}):")
    if not eng:
        print("    none - the base organism covers this product as it stands")
    for cid, c, r in sorted(eng):
        print(f"    {cid:<3} {c['name'][:40]:<42} {r}")
        print(f"        module: {c['module']}   confidence: {c['confidence']}")

    mods = sorted({c["module"] for _, c, _ in eng})
    if mods:
        print(f"\nMODULES TO BUILD: {len(mods)}")
        print("-" * 72)
        bymod = {m["id"]: m for m in chassis["engineered_modules"]}
        for mid in mods:
            m = bymod[mid]
            print(f"  {mid}  ({m['confidence']} confidence)")
            print(f"    goal  : {m['goal']}")
            print(f"    parts : {', '.join(m['parts_required'])}")
            print(f"    cost  : {m['cost_status']}")
            if m.get("unverified"):
                print(f"    !!    : {m['unverified']}")

    print("\nCANNOT BE CONCLUDED FROM THIS RUN")
    print("-" * 72)
    for cid, nm, why in unknowns:
        print(f"  {cid} {nm}: {why}")
    print("  No titre, yield or success probability. Module 3 is not implemented.")
    con = chassis["global_constraints"][0]
    print("  No proteome cost check: no engineered module has a measured cost,")
    print(f"  so the {con['value']:.0%} operating point cannot be tested against this")
    print(f"  configuration. {con['measured_ceiling_fraction']:.0%} is the measured ceiling and "
          "the point of zero yield,")
    print("  not a budget; the useful target is half of it.")
    print("  Signal peptide and transmembrane calls are heuristics, not predictors.")
    print()


EXAMPLES = [
    ("Human preproinsulin", "therapeutic", True,
     "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"),
    ("Human erythropoietin, mature chain", "therapeutic", True,
     "APPRLICDSRVLERYLLEAKEAENITTGCAEHCSLNENITVPDTKVNFYAWKRMEVGQQAVEVWQGLALLSEAVLRGQALLVNSSQPWEPLQLHVDKAVSGLRSLTTLLRALGAQKEAISPPDAASAAPLRTITADTFRKLFRVYSNFLRGKLKLYTGEACRTGDR"),
]


def main():
    p = argparse.ArgumentParser(description="Resolve a protein against the computational chassis.")
    p.add_argument("--seq", help="amino acid sequence")
    p.add_argument("--name", default="unnamed target")
    p.add_argument("--fasta", help="FASTA file with one or more sequences")
    p.add_argument("--class", dest="pclass", default="therapeutic",
                   choices=["therapeutic", "enzyme", "antigen", "other"])
    p.add_argument("--intracellular", action="store_true", help="product is not secreted")
    args = p.parse_args()

    with open(CHASSIS, encoding="utf-8") as fh:
        chassis = json.load(fh)

    if args.fasta:
        name, buf = None, []
        for line in open(args.fasta, encoding="utf-8"):
            if line.startswith(">"):
                if name:
                    report(name, "".join(buf), args.pclass, not args.intracellular, chassis)
                name, buf = line[1:].strip(), []
            else:
                buf.append(line.strip())
        if name:
            report(name, "".join(buf), args.pclass, not args.intracellular, chassis)
    elif args.seq:
        report(args.name, args.seq, args.pclass, not args.intracellular, chassis)
    else:
        print("No --seq or --fasta given. Running the two built-in examples.\n")
        for nm, cls, sec, sq in EXAMPLES:
            report(nm, sq, cls, sec, chassis)


if __name__ == "__main__":
    main()
