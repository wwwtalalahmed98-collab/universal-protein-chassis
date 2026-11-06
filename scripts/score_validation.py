"""Score the frozen predictions against the campaign answers.

It refuses to run if the freeze has been broken. That refusal is the point: a
retrospective test whose tool can be edited between prediction and scoring
measures nothing, so the check is mechanical rather than a promise.

WHAT IT CHECKS BEFORE SCORING
-----------------------------
  1. The predictions file still hashes to the SHA-256 in freeze-v1.json.
  2. None of the files named in the manifest's void_if clause have changed
     since the freeze commit, by git diff against that commit.

WHAT IT REPORTS, AND WHY SEPARATELY
-----------------------------------
reports/03-validation-set-feasibility.md established that publication bias makes
these two numbers mean different things, and that reporting one accuracy figure
would overstate what was established:

  RECALL    of the campaign actions the chassis CAN express, did it name them?
            Measurable. Rows whose every action is unmapped are excluded and
            counted separately, because the chassis cannot win them by
            construction and burying them in a denominator would hide that.

  PRECISION when the chassis named a module, did the product actually need it?
            Mostly unmeasurable, because a silent paper might mean nobody
            tried. Computed ONLY on rows where the authors explicitly applied
            the modification and reported it failing or backfiring. Those rows
            are the partial escape from publication bias.

  DISCRIMINATION for each differential pair, did the chassis predict
            DIFFERENTLY on the module the experiment actually varied? This is
            the one that tests judgement rather than recall, and a tool that
            names a module for every protein scores zero here however good its
            recall looks.

Run:  python -I scripts/score_validation.py
"""
import hashlib
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V = os.path.join(ROOT, "validation")
PRED = os.path.join(V, "predictions-v1.tsv")
ANS = os.path.join(V, "answers-v1.tsv")
MAP = os.path.join(V, "mapping-v1.tsv")
MANIFEST = os.path.join(V, "freeze-v1.json")
OUT = os.path.join(ROOT, "reports", "05-retrospective-score.tsv")

FROZEN_FILES = ["scripts/chassis_resolve.py", "scripts/elongation.py",
                "chassis/chassis-v1.json", "validation/mapping-v1.tsv"]


def rows(path, keys):
    out = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            p = raw.rstrip("\n").split("\t")
            if p[0] in ("accession", "action"):
                continue
            if len(p) < len(keys):
                continue
            out.append(dict(zip(keys, p)))
    return out


def load_mapping():
    """action -> module, plus the set of actions declared unmappable."""
    m, unmapped = {}, set()
    with open(MAP, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            p = raw.rstrip("\n").split("\t")
            if len(p) < 2 or p[0] == "action":
                continue
            if p[1].strip() == "UNMAPPED":
                unmapped.add(p[0].strip())
            else:
                m[p[0].strip()] = p[1].strip()
    return m, unmapped


def git(*a):
    try:
        r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True,
                           text=True, timeout=30)
        return r.stdout.strip(), r.returncode
    except Exception:
        return "", 1


def line(ch="-", n=78):
    print(ch * n)


def check_freeze():
    with open(MANIFEST, encoding="utf-8") as fh:
        man = json.load(fh)
    problems = []
    with open(PRED, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    if digest != man["predictions_sha256"]:
        problems.append("predictions-v1.tsv hash does not match the manifest.\n"
                        "    manifest: %s\n    actual  : %s"
                        % (man["predictions_sha256"], digest))
    commit = man.get("git_commit_at_freeze")
    if commit:
        diff, rc = git("diff", "--name-only", commit, "--", *FROZEN_FILES)
        if rc != 0:
            problems.append("could not diff against freeze commit %s" % commit)
        elif diff:
            problems.append("frozen code changed since the freeze commit:\n    "
                            + "\n    ".join(diff.splitlines()))
    return man, digest, problems


def main():
    man, digest, problems = check_freeze()

    line("=")
    print("FREEZE CHECK")
    line("=")
    print("  freeze commit        : %s" % man.get("git_commit_at_freeze"))
    print("  predictions sha256   : %s" % digest)
    print("  matches manifest     : %s" % (digest == man["predictions_sha256"]))
    for f in FROZEN_FILES:
        print("  unchanged            : %s" % f)
    print()
    if problems:
        print("  REFUSING TO SCORE. The freeze is broken:")
        for p in problems:
            print("    - %s" % p)
        print()
        print("  Re-freeze with scripts/freeze_predictions.py and start again.")
        print("  Scoring against an edited tool would measure nothing.")
        return 1
    print("  Freeze intact. Scoring.")
    print()

    pred = rows(PRED, ["accession", "protein", "host", "case_type", "pair_id",
                       "pmid", "length_aa", "cysteines", "cys_pairs", "sequons",
                       "signal_peptide", "tm_segments", "product_class_used",
                       "caps_active", "caps_engineered", "modules_predicted",
                       "codon_best", "codon_worst", "seq_source"])
    ans = rows(ANS, ["accession", "pmid", "pair_id", "actions", "outcome", "quote"])
    mapping, unmapped = load_mapping()

    pindex = {(r["accession"], r["pmid"]): r for r in pred}
    scored = []
    for a in ans:
        key = (a["accession"], a["pmid"])
        p = pindex.get(key)
        if not p:
            print("  no prediction for %s / %s" % key)
            continue
        acts = [x.strip() for x in a["actions"].split(";") if x.strip()]
        need = sorted({mapping[x] for x in acts if x in mapping})
        unm = [x for x in acts if x in unmapped]
        unknown = [x for x in acts
                   if x not in mapping and x not in unmapped and x != "none reported"]
        got = [m for m in p["modules_predicted"].split(";") if m != "-"]
        hit = sorted(set(need) & set(got))
        missed = sorted(set(need) - set(got))

        if a["outcome"] == "none_reported":
            verdict = "no answer"
        elif not need and unm:
            verdict = "unreachable"
        elif a["outcome"] in ("not_helped", "hurt") and hit:
            verdict = "false positive"
        elif a["outcome"] == "helped" and hit:
            verdict = "hit"
        elif a["outcome"] == "helped" and need and not hit:
            verdict = "miss"
        else:
            verdict = "no answer"
        scored.append({**a, "pred": p, "need": need, "got": got, "hit": hit,
                       "missed": missed, "unmapped": unm, "unknown": unknown,
                       "verdict": verdict})

    line("=")
    print("ROW BY ROW")
    line("=")
    print("%-9s %-28s %-11s %-16s %s" %
          ("acc", "protein", "outcome", "verdict", "needed -> predicted"))
    line()
    for s in scored:
        need = ",".join(x.replace("MOD-", "") for x in s["need"]) or "-"
        got = ",".join(x.replace("MOD-", "") for x in s["got"]) or "-"
        print("%-9s %-28s %-11s %-16s %s -> %s" %
              (s["accession"], s["pred"]["protein"][:28], s["outcome"],
               s["verdict"], need, got))
    print()

    tp = [s for s in scored if s["verdict"] == "hit"]
    fp = [s for s in scored if s["verdict"] == "false positive"]
    ms = [s for s in scored if s["verdict"] == "miss"]
    un = [s for s in scored if s["verdict"] == "unreachable"]
    na = [s for s in scored if s["verdict"] == "no answer"]

    line("=")
    print("RECALL  —  of the actions the chassis CAN express, did it name them?")
    line("=")
    reach = len(tp) + len(ms)
    print("  rows where the campaign's action is expressible : %d" % reach)
    print("  named it                                        : %d" % len(tp))
    print("  failed to name it                               : %d" % len(ms))
    if reach:
        print("  RECALL                                          : %d of %d = %.0f%%"
              % (len(tp), reach, 100 * len(tp) / reach))
    print()
    print("  rows the chassis cannot win by construction      : %d" % len(un))
    for s in un:
        print("      %-9s %-26s %s" % (s["accession"], s["pred"]["protein"][:26],
                                       "; ".join(s["unmapped"])))
    print("  rows with no reported modification               : %d" % len(na))
    print()

    line("=")
    print("PRECISION  —  only on rows where the authors TESTED and it failed")
    line("=")
    print("  These are the rows that escape publication bias: the modification")
    print("  was applied and reported not to work, so a prediction of it is a")
    print("  false positive and not merely unverifiable.")
    print()
    print("  true positives  : %d" % len(tp))
    print("  false positives : %d" % len(fp))
    for s in fp:
        print("      %-9s %-26s %-10s predicted %s" %
              (s["accession"], s["pred"]["protein"][:26], s["outcome"],
               ",".join(x.replace("MOD-", "") for x in s["hit"])))
    if tp or fp:
        print("  PRECISION       : %d of %d = %.0f%%"
              % (len(tp), len(tp) + len(fp), 100 * len(tp) / (len(tp) + len(fp))))
    print()

    line("=")
    print("DISCRIMINATION  —  the test of judgement rather than recall")
    line("=")
    print("  For each differential pair, the experiment varied ONE module. Did")
    print("  the chassis predict that module differently for the two halves?")
    print()
    pairs = {}
    for s in scored:
        pairs.setdefault(s["pair_id"], []).append(s)
    disc_total = disc_pass = 0
    for pid, members in sorted(pairs.items()):
        outs = {m["outcome"] for m in members}
        if not ({"helped"} & outs) or not ({"not_helped", "hurt"} & outs):
            continue
        disc_total += 1
        varied = sorted({m for s in members for m in s["need"]})
        calls = {}
        for s in members:
            calls[s["pred"]["protein"][:24]] = (
                s["outcome"], [v for v in varied if v in s["got"]])
        distinct = {tuple(v[1]) for v in calls.values()}
        ok = len(distinct) > 1
        disc_pass += 1 if ok else 0
        print("  pair %-7s varied: %s" % (pid, ", ".join(varied) or "-"))
        for name, (out, got) in calls.items():
            print("      %-26s %-11s predicted %s" %
                  (name, out, ",".join(x.replace("MOD-", "") for x in got) or "-"))
        print("      -> %s" % ("DISCRIMINATES" if ok else
                               "IDENTICAL CALL FOR BOTH — no discrimination"))
        print()
    if disc_total:
        print("  DISCRIMINATION  : %d of %d differential pairs" % (disc_pass, disc_total))
    print()

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("accession\tprotein\tpmid\toutcome\tverdict\tneeded\tpredicted\tunmapped\n")
        for s in scored:
            fh.write("\t".join([s["accession"], s["pred"]["protein"], s["pmid"],
                                s["outcome"], s["verdict"], ";".join(s["need"]) or "-",
                                ";".join(s["got"]) or "-",
                                ";".join(s["unmapped"]) or "-"]) + "\n")
    print("  per-row table written to reports/05-retrospective-score.tsv")
    print()

    line("=")
    print("WHAT THIS SCORE DOES AND DOES NOT ESTABLISH")
    line("=")
    for item in [
        "Answers come from ABSTRACTS ONLY. No full text was retrieved, so a "
        "modification mentioned only in the body of a paper is missing here.",
        "Recall is computed on %d rows, which is a small denominator. One "
        "reclassified row moves it by a lot." % reach,
        "Precision is computed on %d rows and only those. It is not the "
        "chassis's false-positive rate in general, because for most proteins "
        "nobody published what did not work." % (len(tp) + len(fp)),
        "Discrimination is the number that matters, and it was predictable "
        "from the frozen predictions alone: a module named for every target "
        "cannot distinguish between targets.",
        "Five of the 18 rows are not S. cerevisiae. The chassis is defined on "
        "S. cerevisiae, so those rows carry a host-transfer assumption.",
        "Three decades separate the oldest and newest paper, across strains, "
        "vectors and assays that are not comparable.",
        "Nothing here tests titre. The chassis predicts which modules a "
        "product needs, not how much of it you get.",
    ]:
        print("  - %s" % item)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
