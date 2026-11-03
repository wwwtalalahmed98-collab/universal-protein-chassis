"""The parameter registry: no number enters a layer without a source.

WHY THIS EXISTS
---------------
protocol/theory-stack-v1.md reached a conclusion that this file acts on:

    "Parameters are the hard part, not the equations. The equations are
     published. Yeast-specific values for most of them are not assembled
     anywhere, and collecting them is the actual work."

and warned about the failure mode:

    "Done carelessly, a stack of models produces confident numbers with no
     more content than the rules they replaced - and that is worse than the
     rule matcher, because it looks authoritative."

A number typed into a script looks exactly like a number measured in a
laboratory. Once six layers of models are stacked, nobody can tell them apart
by reading the output. This module makes the difference machine-checkable:
every parameter lives in params/parameters-v1.json with its organism, its
source, and a provenance grade, and asking for an unregistered parameter is an
error rather than a silent success.

GRADES
------
    A   measured in S. cerevisiae, primary publication identified, uncertainty stated
    B   measured in S. cerevisiae or taken from a named database, source identified
    C   measured in another organism and transferred, or a published model
        constant whose applicability to yeast is unchecked
    D   no external source; chosen inside this project because the code needed
        something

Run:  python -I scripts/params.py --audit
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTRY = os.path.join(ROOT, "params", "parameters-v1.json")
TRNA_TSV = os.path.join(ROOT, "params", "trna-scerevisiae-gtrnadb-v1.tsv")

# GtRNAdb reports this total independently, in its own Overview box, separately
# from the per-anticodon tables the TSV was transcribed from. Using it as a
# checksum catches a dropped or mistyped row. It does not catch two errors that
# cancel out.
GTRNADB_TOTAL_SCERE3 = 275


def load():
    """The whole registry."""
    with open(REGISTRY, encoding="utf-8") as fh:
        return json.load(fh)


def _index(reg=None):
    reg = reg or load()
    return {p["id"]: p for p in reg["parameters"]}


def get(pid, reg=None):
    """A parameter's value. Unregistered parameters are an error, not a default.

    This is the whole point of the module. A layer that wants a number it has
    not registered cannot quietly proceed with a guess.
    """
    idx = _index(reg)
    if pid not in idx:
        raise KeyError(
            "Parameter %r is not in the registry.\n"
            "A layer may not use a number that has no recorded source.\n"
            "Add it to params/parameters-v1.json with its organism, source and\n"
            "grade, or do not use it." % pid)
    return idx[pid]["value"]


def meta(pid, reg=None):
    """A parameter's provenance record, for a layer that wants to report it."""
    idx = _index(reg)
    if pid not in idx:
        raise KeyError("Parameter %r is not in the registry." % pid)
    return idx[pid]


def load_trna():
    """tRNA gene copy numbers per anticodon, with the GtRNAdb checksum enforced.

    Returns (counts, n_initiator_met). Raises if the transcribed table does not
    reconcile with the total GtRNAdb reports separately.
    """
    counts = {}
    with open(TRNA_TSV, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if parts[0] == "anticodon":
                continue
            counts[parts[0]] = int(parts[2])

    n_init = get("PRM-trna-met-initiator-count")
    total = sum(counts.values()) + n_init
    if total != GTRNADB_TOTAL_SCERE3:
        raise ValueError(
            "tRNA table does not reconcile with GtRNAdb.\n"
            "  transcribed elongator genes : %d\n"
            "  initiator methionine genes  : %d\n"
            "  total                       : %d\n"
            "  GtRNAdb Overview reports    : %d\n"
            "The transcription is wrong somewhere. Do not use this table."
            % (sum(counts.values()), n_init, total, GTRNADB_TOTAL_SCERE3))
    return counts, n_init


def grade_counts(reg=None):
    reg = reg or load()
    out = {"A": 0, "B": 0, "C": 0, "D": 0}
    for p in reg["parameters"]:
        out[p["grade"]] = out.get(p["grade"], 0) + 1
    return out


def line(ch="-", n=74):
    print(ch * n)


def audit():
    reg = load()
    params = reg["parameters"]
    n = len(params)

    line("=")
    print("PARAMETER PROVENANCE AUDIT  -  %s" % reg["registry_id"])
    line("=")
    print("Registered parameters: %d" % n)
    print()

    for key in ("A", "B", "C", "D"):
        print("  %s  %s" % (key, reg["how_to_read_a_grade"][key]))
    print()

    counts = grade_counts(reg)
    line()
    print("GRADE DISTRIBUTION")
    line()
    for key in ("A", "B", "C", "D"):
        c = counts[key]
        bar = "#" * c
        print("  %s  %2d of %2d  %s" % (key, c, n, bar))
    print()

    line()
    print("EVERY PARAMETER, BY GRADE")
    line()
    print("%-5s %-30s %-11s %s" % ("grade", "id", "organism", "source"))
    line()
    for p in sorted(params, key=lambda q: (q["grade"], q["id"])):
        org = p["organism_measured_in"]
        if len(org) > 11:
            org = org[:10] + "."
        src = p["source_type"]
        if p.get("transfer_assumption"):
            src = "TRANSFERRED: " + src
        print("%-5s %-30s %-11s %s" % (p["grade"], p["id"], org, src[:30]))
    print()

    # The finding that matters: which numbers decide what gets built?
    line("=")
    print("THE NUMBERS THAT DECIDE WHAT THE CHASSIS BUILDS")
    line("=")
    print("A parameter is decision-making if it sits in a threshold that")
    print("switches a capability on or off, because that is what adds an")
    print("engineered module to the design.")
    print()
    deciders = [p for p in params
                if "scripts/chassis_resolve.py" in p.get("used_by", [])]
    d_bad = [p for p in deciders if p["grade"] == "D"]
    for p in sorted(deciders, key=lambda q: q["grade"]):
        mark = "  <-- no source" if p["grade"] == "D" else ""
        val = p["value"]
        if isinstance(val, dict):
            val = "(table of %d)" % len(val)
        print("  %s  %-30s %-12s%s" % (p["grade"], p["id"], val, mark))
    print()
    print("  %d of %d parameters inside the resolver are grade D." % (len(d_bad), len(deciders)))
    print()
    print("  This is the audit's real output. The resolver's conclusions are")
    print("  reported in the same voice whether they rest on a published")
    print("  measurement or on a round number, and until now nothing in the")
    print("  project distinguished them.")
    print()

    line("=")
    print("TRANSFER ASSUMPTIONS")
    line("=")
    trans = [p for p in params if p.get("transfer_assumption")]
    if not trans:
        print("  none")
    for p in trans:
        print("  %-30s %s -> %s" % (p["id"], p["organism_measured_in"],
                                    p["organism_used_for"]))
    print()
    print("  theory-stack-v1.md: \"Most of this theory was built on E. coli.")
    print("  The chassis is yeast. Every transfer is an assumption.\"")
    print()

    line("=")
    print("MISSING CITATIONS")
    line("=")
    nocite = [p for p in params if p.get("primary_citation") is None
              and p["grade"] in ("A", "B", "C")]
    for p in nocite:
        print("  %-30s %s" % (p["id"], p.get("citation_status", "")[:40]))
    print()
    print("  %d of %d sourced parameters have a quote but no identified paper." % (len(nocite), n))
    print("  A reader cannot verify these without the publication.")
    print()

    line("=")
    print("TRNA TABLE CHECKSUM")
    line("=")
    try:
        counts, n_init = load_trna()
        print("  anticodons listed          : %d" % len(counts))
        print("  elongator tRNA genes       : %d" % sum(counts.values()))
        print("  initiator methionine genes : %d (excluded from elongation)" % n_init)
        print("  total                      : %d" % (sum(counts.values()) + n_init))
        print("  GtRNAdb reports            : %d  -> reconciles" % GTRNADB_TOTAL_SCERE3)
    except ValueError as exc:
        print("  FAILED: %s" % exc)
    print()

    line("=")
    print("WHAT THIS REGISTRY DOES NOT CONTAIN")
    line("=")
    for item in reg["what_this_registry_does_not_contain"]:
        print("  - %s" % item)
    print()


if __name__ == "__main__":
    if "--audit" in sys.argv:
        audit()
    else:
        print(__doc__)
        print("Registered parameters: %d" % len(load()["parameters"]))
        print("Grades: %s" % grade_counts())
        print()
        print("Run with --audit for the full provenance report.")
