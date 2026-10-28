# Defining the goal

**The question:** three candidate goals have been named.

1. **The tool outputs a specification a human wet lab reproduces.**
2. **The tool drives a robot or autonomous lab**, which executes its designs.
3. **The tool itself is the goal** — a virtual universal chassis.

**They are not three alternatives. They are a ladder, and you cannot build the
upper rungs without the lower one.** Goals 1 and 2 are *applications* of goal 3.
Neither can exist until the virtual chassis exists, because the specification a
lab or a robot receives is the thing the virtual chassis emits.

**So the real question is not which to pick. It is which one you are
accountable for.**

---

## What makes a goal effective

A goal is worth setting only if it meets four conditions:

1. **Falsifiable.** You can tell whether you failed. A goal you cannot fail is
   not a goal, it is a mood.
2. **Achievable with resources you control.** A goal that depends on a facility
   you do not have is a wish about someone else's behaviour.
3. **Valuable if achieved**, and valuable to someone other than you.
4. **Bounded.** You can say roughly when it is done.

---

## The three, scored

| | **1. Human lab** | **2. Autonomous lab** | **3. Virtual chassis** |
|---|---|---|---|
| What you hand over | a build specification | an executable protocol | a validated model |
| Success means | a strain is built and works | the design-test loop converges | predictions match published results |
| **Who decides if you succeeded** | a lab you do not have | a robot you do not have | **you, against the literature** |
| Time until you know | years | years | **months** |
| Cost to find out | a laboratory | cloud-lab fees | **nothing** |
| Falsifiable by you alone | **no** | **no** | **yes** |
| Principal threat | the lookalike-divergence result | funding and access | drifting into the unfalsifiable |

### Goal 1 is the one the evidence most threatens

`scope-proteins-v1.md` records the strongest counter-evidence this project has
found:

> *"**Structural Homology Fails to Predict Secretion Efficiency** in Pichia
> pastoris: **Divergent Responses of Architecturally Similar scFvs** to
> Multi-Parametric Genetic Engineering"*

Two proteins that look alike behaved differently under identical engineering.
**A single specification handed once to a human lab is exactly the form that
result argues against.** Goal 1 is the weakest of the three on the project's own
evidence, not the strongest.

### Goal 2 is the answer to that counter-evidence

An autonomous loop does not claim to get it right first time. It measures,
corrects and tries again — which is precisely what the Pichia result says is
necessary. **Goal 2 is scientifically the most defensible of the three.**

It is also the one you have least ability to reach alone: it needs a robotic
facility, an account, and money.

### Goal 3 is the only one you can finish

You control every input. The model is yours, the literature is public, the
solver is free, and the validation set already exists in published papers.

**And it has precedent.** Yeast8 and Yeast9 are models of yeast, cited
thousands of times, and nobody considers them incomplete because no one built a
yeast from them. `pcSecYeast` is a model, and it is the paper, and it is the
contribution. A model *is* a legitimate scientific object.

---

## The recommendation

**Goal 3 is the project. Goal 2 is a design constraint. Goal 1 is the eventual
validation.**

Concretely:

- **Build the virtual universal chassis**, and be accountable for it. This is
  what you are claiming to have made.
- **Make every output machine-executable from the start.** Structured,
  unambiguous, parameterised — a protocol an autonomous lab *could* run. This
  costs very little now and is expensive to retrofit later. It keeps goal 2
  reachable without requiring a robot today.
- **Treat a human lab build as validation**, not as a dependency. If someone
  builds it, that is a test of the model, not the completion of the project.

**The thing you hand over is the chassis. What anyone does with it is their
step, not yours.**

---

## The real danger, and the guard against it

**Goal 3 can quietly become unfalsifiable.** A model of an organism nobody
builds can be made more elegant indefinitely without ever being shown wrong.
That failure is comfortable and it is fatal — it produces a beautiful document
that no one can argue with because it predicts nothing checkable.

**The guard is to make the virtual chassis predict things that have already been
measured.**

This is available now and needs no laboratory:

> **The retrospective test.** There are hundreds of published cases where a
> protein was expressed in yeast and the paper states what engineering was
> required to make it work — which signal peptide, which chaperone
> overexpression, whether glycans were humanised, what the titre was. Run the
> tool against those proteins **without seeing the answers**, and measure
> agreement.

That turns goal 3 into a falsifiable claim with a number attached:

> *Given a protein sequence alone, the chassis predicts the host modifications
> that published campaigns actually found necessary, in N of M cases.*

**If that number is poor, the project is wrong and you will know within months.**
That is what an effective goal looks like.

It is also the obvious extension of what already exists:
`reports/02-feature-validation.md` validated the tool's **perception** against
UniProt and scored 16 of 16 inside its domain. **This would validate its
judgement**, which is the half that remains completely untested.

---

## What each goal would additionally require

| Goal | Still needed |
|---|---|
| 3. Virtual chassis | the retrospective validation set; module costs from pcSecYeast; the theory layers |
| 2. Autonomous lab | a structured protocol output format; a cloud-lab account; funding |
| 1. Human lab | a collaborating laboratory; consumables; months of someone's time |

**Only the first row is made of things within reach.**

---

## What is not decided here

- **This is a recommendation, not a decision.** The project owner chooses.
- **No validation set has been built.** The retrospective test is proposed and
  does not exist. Whether enough papers report their engineering in usable
  detail is **an assumption, not a verified fact** — it could turn out that most
  papers report the final strain without reporting what failed first.
- **No protocol output format has been designed**, so the goal-2 design
  constraint is currently a statement of intent and nothing more.
- **The ladder argument assumes goals 1 and 2 genuinely depend on goal 3.** A
  different project could attack goal 2 directly with a crude tool and let the
  loop do the work. That is a real alternative and it is not the one recommended
  here.
