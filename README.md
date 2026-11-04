# UCP-1 — a computational universal protein chassis

**A machine-readable definition of a yeast chassis for producing any protein,
plus the code to query it.** Give it a protein sequence; it reports which
production capabilities that protein needs, which the host already has, and
which must be engineered in.

**Nothing here has been built in a laboratory.** The chassis is a design being
simulated. Every engineered part is a proposal carrying published precedent, not
a validated construct.

**Interactive simulation:** `sim/chassis-sim.html` — pick a protein and watch the
chassis configure itself.

---

## What runs today

```bash
# Resolve a protein against the chassis
python -I scripts/chassis_resolve.py
python -I scripts/chassis_resolve.py --fasta targets.fasta --class therapeutic

# Reproduce the scope filter: 37 capabilities down to the 22 proteins need
python -I scripts/protein_scope.py

# Reproduce the proteome budget arithmetic
python -I scripts/proteome_budget.py

# Provenance audit: every number the tool uses, graded by where it came from
python -I scripts/params.py --audit

# Theory-stack layer 1c: codon adaptiveness from the yeast tRNA gene pool
python -I scripts/elongation.py

# Validate that layer against published ribosome profiling
python -I scripts/validate_elongation.py
```

No dependencies beyond the Python standard library.

### Worked examples

| Target | Capabilities active | Native to yeast | Need engineering |
|---|---:|---:|---:|
| Human preproinsulin | 16 of 22 | 14 | **2** |
| Human erythropoietin | 19 of 22 | 15 | **4** |

Erythropoietin carries three N-glycosylation sequons, so it pulls in the
humanised-glycan module and the sugar-nucleotide module that feeds it. Insulin
has none, so it does not. The chassis configures differently per protein, which
is the behaviour the whole design rests on.

---

## What this is not

- **It does not predict titre, yield, or whether expression will succeed.** The
  step that would needs a proteome-constrained metabolic model, which runs in
  MATLAB and is not wired in.
- **No engineered module has a measured proteome cost**, so the 40% budget
  constraint is recorded but cannot be checked against a resolved configuration.
- **Signal-peptide and transmembrane calls are hydropathy heuristics**, labelled
  as such in every run. Real answers need SignalP and DeepTMHMM.
- **There is no validation against measured expression outcomes.** Two proteins
  chosen by the author is not a test set.

A published result reports that architecturally similar antibody fragments
behave differently under identical engineering, so sequence alone has a ceiling
that no larger model removes.

---

## Layout

| Path | What is in it |
|---|---|
| `chassis/chassis-v1.json` | **The chassis object.** 22 capabilities, 5 engineered modules, 4 global constraints, provenance, and its own statement of what it cannot do |
| `scripts/chassis_resolve.py` | Resolves a protein sequence against the chassis |
| `params/parameters-v1.json` | **The parameter registry.** Every number the tool uses, with its organism, source and provenance grade A-D |
| `scripts/params.py` | Registry loader. Refuses to return an unregistered parameter; `--audit` grades the lot |
| `scripts/elongation.py` | Theory-stack layer 1c: codon adaptiveness from tRNA gene copy numbers |
| `scripts/validate_elongation.py` | Tests that layer against measured yeast ribosome profiling |
| `sim/chassis-sim.html` | Interactive simulation, same logic in JavaScript |
| `protocol/` | The reasoning, one document per question, each ending in what it does not know |
| `docs/PROJECT-STORY.md` | Durable record: every checkpoint, decision, and reversal, newest first |
| `reports/` | Findings from investigations that were closed out |

### The protocol documents, in the order they were written

1. `capability-set-v1.md` — 37 capabilities a universal chassis would need
2. `conflict-map-v1.md` — which of them cannot coexist, and why
3. `proteome-budget-v1.md` — whether one cell can carry them all
4. `regulatory-capacity-v1.md` — whether enough independent switches exist
5. `candidate-assessment-v1.md` — which real organism comes closest
6. `scope-proteins-v1.md` — narrowing to proteins, and what that cost
7. `tool-spec-v1.md` — the six modules, and which are blocked
8. `computational-chassis-v1.md` — the chassis as a queryable object

Each document states its own limits. `scope-proteins-v1.md` records that
narrowing to proteins **weakened** two of the four architectural requirements
derived earlier; the earlier documents were left unrevised as the record of how
the reasoning actually went.

---

## External models, referenced but not run

- [pcSecYeast](https://github.com/SysBioChalmers/pcSecYeast) — proteome-constrained
  genome-scale secretory model of *S. cerevisiae*. GPL-3.0. Last updated
  2021-07-20. **MATLAB.** Ships `Protein_Information.xlsx`, the Protein Specific
  Information Matrix, which is the feature schema this project needed.
- [pcSecYeastSpecies](https://github.com/LiLabTsinghua/pcSecYeastSpecies) —
  extends it to *K. phaffii* and *K. marxianus* with humanised glycosylation
  modules. Updated December 2025. **MATLAB.**

Neither has been downloaded or run. Everything stated about them comes from
their README files and papers. **MATLAB access is the open blocker** on the
simulation module.

---

## License

MIT — see [LICENSE](LICENSE). The two external models this project references
are licensed separately and are not redistributed here; pcSecYeast is GPL-3.0,
so copying its code into this repository would change what this repository can
be licensed under.

---

## How this project is written up

Every claim carries the quote behind it. Every document ends with a section
saying what is not done and not verified. Where a later finding undercut an
earlier conclusion, both are kept and the reversal is recorded — see
`docs/PROJECT-STORY.md`.
