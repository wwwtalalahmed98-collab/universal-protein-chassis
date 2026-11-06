"""Freeze the chassis's predictions before any answer is read.

WHY THIS EXISTS
---------------
reports/03-validation-set-feasibility.md ended with the condition that makes or
breaks the whole retrospective test:

    "The blind condition needs enforcing. If the tool is adjusted after seeing
     the answers, the test is worthless. Predictions must be frozen and written
     down before the papers are read."

"Don't look" is not enforceable and not auditable. What is auditable is binding
the predictions to the exact code that produced them:

  1. This script runs the REAL resolver, imported from scripts/chassis_resolve.py.
     It does not reimplement anything.
  2. It records the git commit of the working tree, and whether the tree was
     dirty at the time.
  3. It records a SHA-256 of the predictions file itself.
  4. Predictions and the frozen action-to-module mapping are committed together,
     in a commit that contains no answers.

Afterwards, anyone can check whether the code changed between prediction and
scoring. If it did, the test is void and must be rerun from a fresh freeze.
That is a stronger guarantee than anybody's good intentions, including mine.

WHAT IS AND IS NOT BLIND
------------------------
Honest about this, because overclaiming here would defeat the point.

  BLIND:     the predictions. They come from sequence alone, through frozen
             code, and no outcome was read into them.
  NOT BLIND: the choice of proteins. Building the set meant reading paper
             titles and abstracts, which state outcomes. That is unavoidable:
             you cannot assemble a set of campaigns without knowing which
             campaigns exist.

So the guard is not ignorance. The guard is that the predictions are fixed and
hashed, the mapping from campaign actions to chassis modules is fixed in the
same commit, and the unmapped categories are declared as misses in advance.

Run:  python -I scripts/freeze_predictions.py
      python -I scripts/freeze_predictions.py --offline   (cached sequences only)
"""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chassis_resolve import features, resolve, CHASSIS  # the real resolver
import elongation

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGETS = os.path.join(ROOT, "validation", "targets-v1.tsv")
OUT = os.path.join(ROOT, "validation", "predictions-v1.tsv")
MANIFEST = os.path.join(ROOT, "validation", "freeze-v1.json")
CACHE = os.path.join(ROOT, "data", "uniprot")

UA = "UCP-1-chassis-validation/1.0 (https://github.com/wwwtalalahmed98-collab/universal-protein-chassis)"


def read_targets(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            p = raw.rstrip("\n").split("\t")
            if len(p) < 8 or p[0] == "accession":
                continue
            rows.append(dict(zip(
                ["accession", "protein", "origin", "host", "case_type",
                 "pair_id", "pmid", "doi"], p)))
    return rows


def fetch_sequence(acc, offline=False):
    """Sequence for an accession, cached on disk. Returns (seq, source)."""
    path = os.path.join(CACHE, acc + ".fasta")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        seq = "".join(l.strip() for l in body.splitlines() if not l.startswith(">"))
        if seq:
            return seq, "cache"
    if offline:
        return None, "missing"
    url = "https://rest.uniprot.org/uniprotkb/%s.fasta" % acc
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        return None, "fetch failed: %s" % exc
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    seq = "".join(l.strip() for l in body.splitlines() if not l.startswith(">"))
    return (seq or None), "uniprot"


def git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                              text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def predict(row, seq, chassis, w):
    """The prediction. Sequence in, chassis modules out. No outcome consulted."""
    f = features(seq)
    # Every target in this set is a secreted product: each campaign measured
    # secretion into the medium. Product class comes from what the protein is.
    secreted = True
    therapeutic = row["origin"] == "Homo sapiens" or row["protein"].startswith(
        ("Bovine prochymosin", "Bovine follitropin"))
    pclass = "therapeutic" if therapeutic else "enzyme"
    active, inactive, unknowns = resolve(chassis, f, pclass, secreted)
    mods = sorted({c["module"] for _, c, _ in active
                   if c["status"] == "engineered" and c.get("module")})
    caps_eng = sorted(cid for cid, c, _ in active if c["status"] == "engineered")
    cr = elongation.protein_range(seq, w)
    return {
        "length_aa": f["length_aa"],
        "cysteines": f["cysteine_count"],
        "cys_pairs": f["cysteine_pairs"],
        "sequons": f["n_glyc_sequons"],
        "signal_peptide": f["signal_peptide_predicted"],
        "tm_segments": f["tm_segments_predicted"],
        "product_class_used": pclass,
        "caps_active": len(active),
        "caps_engineered": ";".join(caps_eng) or "-",
        "modules_predicted": ";".join(mods) or "-",
        "codon_best": round(cr["best"], 4) if cr else "",
        "codon_worst": round(cr["worst"], 4) if cr else "",
    }


FIELDS = ["accession", "protein", "host", "case_type", "pair_id", "pmid",
          "length_aa", "cysteines", "cys_pairs", "sequons", "signal_peptide",
          "tm_segments", "product_class_used", "caps_active", "caps_engineered",
          "modules_predicted", "codon_best", "codon_worst", "seq_source"]


def line(ch="-", n=76):
    print(ch * n)


def main():
    offline = "--offline" in sys.argv
    with open(CHASSIS, encoding="utf-8") as fh:
        chassis = json.load(fh)
    w, _ = elongation.relative_adaptiveness()
    rows = read_targets(TARGETS)

    line("=")
    print("FREEZING PREDICTIONS  —  no answer has been read")
    line("=")
    print("targets          : %d rows" % len(rows))
    print("chassis          : %s schema %s" % (chassis["chassis_id"],
                                               chassis["schema_version"]))
    print("resolver         : scripts/chassis_resolve.py, imported not copied")
    print()

    out, failed = [], []
    for row in rows:
        seq, src = fetch_sequence(row["accession"], offline)
        if not seq:
            failed.append((row["accession"], src))
            continue
        p = predict(row, seq, chassis, w)
        rec = dict(row)
        rec.update(p)
        rec["seq_source"] = src
        out.append(rec)
        if src == "uniprot":
            time.sleep(0.34)          # be polite to the API

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Retrospective validation set, version 1 — FROZEN PREDICTIONS\n")
        fh.write("# Produced by scripts/freeze_predictions.py from sequence alone.\n")
        fh.write("# NO CAMPAIGN OUTCOME WAS CONSULTED. See validation/protocol-v1.md.\n")
        fh.write("# Scored only through validation/mapping-v1.tsv, frozen in the same commit.\n")
        fh.write("\t".join(FIELDS) + "\n")
        for r in out:
            fh.write("\t".join(str(r.get(k, "")) for k in FIELDS) + "\n")

    with open(OUT, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()

    # Dirtiness must exclude the two files this script just wrote, or the flag
    # reports its own output and tells you nothing about the code that ran.
    OWN = {"validation/predictions-v1.tsv", "validation/freeze-v1.json"}
    dirty_paths = sorted(
        p for p in (l[3:].strip() for l in git("status", "--porcelain").splitlines() if l)
        if p and p not in OWN)
    manifest = {
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predictions_file": "validation/predictions-v1.tsv",
        "predictions_sha256": digest,
        "targets_file": "validation/targets-v1.tsv",
        "mapping_file": "validation/mapping-v1.tsv",
        "git_commit_at_freeze": git("rev-parse", "HEAD"),
        "git_tree_dirty_at_freeze": bool(dirty_paths),
        "git_dirty_paths_at_freeze": dirty_paths,
        "chassis_id": chassis["chassis_id"],
        "chassis_schema_version": chassis["schema_version"],
        "rows_predicted": len(out),
        "rows_failed": failed,
        "answers_read": False,
        "void_if": ("scripts/chassis_resolve.py, scripts/elongation.py, "
                    "chassis/chassis-v1.json or validation/mapping-v1.tsv "
                    "changes between this freeze and scoring. Re-freeze instead."),
    }
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")

    print("WHAT THE CHASSIS PREDICTED")
    line()
    print("%-9s %-34s %-7s %-5s %-4s %s" %
          ("acc", "protein", "cysP", "seq", "sig", "modules predicted"))
    line()
    for r in out:
        print("%-9s %-34s %-7s %-5s %-4s %s" %
              (r["accession"], r["protein"][:34], r["cys_pairs"], r["sequons"],
               "Y" if r["signal_peptide"] else "n", r["modules_predicted"]))
    print()

    counts = {}
    for r in out:
        for m in r["modules_predicted"].split(";"):
            counts[m] = counts.get(m, 0) + 1
    print("MODULE CALL FREQUENCY")
    line()
    for m, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("  %-16s %2d of %d targets" % (m, n, len(out)))
    print()
    print("  A module the chassis names for almost every target cannot")
    print("  discriminate, whatever the papers say. That is visible here,")
    print("  before any answer is read.")
    print()

    line("=")
    print("FREEZE MANIFEST")
    line("=")
    print("  rows predicted      : %d of %d" % (len(out), len(rows)))
    if failed:
        for acc, why in failed:
            print("  FAILED              : %s (%s)" % (acc, why))
    print("  predictions sha256  : %s" % digest)
    print("  git commit          : %s" % (manifest["git_commit_at_freeze"] or "unknown"))
    print("  tree dirty          : %s%s" % (manifest["git_tree_dirty_at_freeze"],
        ("  -> " + ", ".join(dirty_paths[:4])) if dirty_paths else ""))
    if dirty_paths:
        print("  NOT A CLEAN FREEZE. Commit the tree and re-run, or the git")
        print("  commit recorded above does not describe the code that ran.")
    print("  answers read        : NO")
    print()
    print("  Commit validation/predictions-v1.tsv, validation/freeze-v1.json,")
    print("  validation/targets-v1.tsv and validation/mapping-v1.tsv together,")
    print("  with no answers in the same commit. Scoring comes after.")
    print()

    line("=")
    print("WHAT THIS DOES NOT ESTABLISH")
    line("=")
    for item in [
        "No answer has been scored. This run produces predictions only.",
        "The set is 18 protein-paper rows from 14 papers, short of the 30 to 50 "
        "that reports/03-validation-set-feasibility.md called for.",
        "Choosing the proteins was not blind. Assembling a set of campaigns "
        "requires reading which campaigns exist, so abstracts were read. The "
        "guard is the frozen code and the frozen mapping, not ignorance.",
        "Seven categories of campaign action are declared UNMAPPED in "
        "validation/mapping-v1.tsv and will score as misses by construction. "
        "That is deliberate and it will make the recall number worse.",
        "Precision is still mostly unmeasurable. A paper that does not mention "
        "a chaperone may mean the chassis over-prescribed, or may mean nobody "
        "tried one. Publication bias does not go away because the test is blind.",
        "Every target is treated as secreted, because every campaign measured "
        "secretion. Product class is assigned from the protein's origin, which "
        "is a judgement made here and not read off the sequence.",
    ]:
        print("  - %s" % item)
    print()


if __name__ == "__main__":
    main()
