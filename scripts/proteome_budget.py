"""Proteome budget arithmetic for the universal chassis question.

SUPERSEDED. KEPT AS A RECORD OF A WRONG ANSWER.
-----------------------------------------------
This script treats the measured ceiling as a budget: it asks whether the sum
of module costs fits under 40% of cell protein, and calls anything below that
line acceptable.

Under the growth laws that is wrong in a consequential way. Growth rate falls
roughly linearly with heterologous mass fraction and reaches ZERO at the
ceiling. Harvested product is per-cell yield times cell accumulation, so
productivity is maximised at HALF the ceiling and is zero AT the ceiling.

    this script says    anything under 40% fits
    the physics says    40% yields nothing; aim for 20%

Use scripts/growth_coupling.py instead. chassis/chassis-v1.json was corrected
in schema 1.1 and sim/chassis-sim.html now shows the growth curve rather than
a pass/fail line.

This file is not deleted because the project keeps its corrections visible,
and because the question it asks - can one cell carry all 37 capabilities -
was answered correctly here even though the threshold was read wrongly.

Asks: can one cell carry all 37 capabilities at once?

All input numbers are measured values from the literature, cited in
protocol/proteome-budget-v1.md. Nothing here is fitted or assumed except
the per-capability cost, which is swept across a plausible range because
nobody has measured it.

Run:  python -I scripts/proteome_budget.py
"""

# ---- measured inputs -------------------------------------------------------

# "we estimated the maximum capacities of the cell for heterologous expression
#  to be 46% of the total RNA and the 33% of the total protein"  (E. coli)
BUDGET_ECOLI = 0.33

# "These proteins can be expressed at levels exceeding 40% of total protein
#  while maintaining yeast growth"
BUDGET_YEAST = 0.40

# "The limits of some glycolytic proteins were up to 15% of the total cellular
#  protein"  - single-protein burden ceiling in yeast
SINGLE_PROTEIN_CEILING = 0.15

N_CAPABILITIES = 37

# How many capabilities does ONE product actually need at the same time?
# Not measured. Range reasoned from the capability set: every product needs the
# expression and process categories, plus a product-specific handful.
NEEDED_PER_PRODUCT = (5, 12)

# Plausible proteome cost of one capability, swept. A capability may be a single
# enzyme (cheap) or a multi-enzyme pathway plus cofactor supply (expensive).
COST_SWEEP = [0.005, 0.01, 0.02, 0.03, 0.05, 0.10]


def line(c=" ", n=66):
    print(c * n)


def capacity(budget, cost):
    return int(budget // cost)


print("PROTEOME BUDGET: can one cell carry 37 capabilities at once?")
line("=")
print(f"  heterologous ceiling, E. coli : {BUDGET_ECOLI:.0%} of total protein")
print(f"  heterologous ceiling, yeast   : {BUDGET_YEAST:.0%} of total protein")
print(f"  single-protein ceiling        : {SINGLE_PROTEIN_CEILING:.0%}")
print(f"  capabilities to cover         : {N_CAPABILITIES}")
print()

# ---- scenario 1: everything switched on at once ----------------------------

print("SCENARIO 1 - all capabilities expressed constitutively")
line("-")
print(f"{'cost each':>10}{'E. coli fits':>14}{'yeast fits':>12}{'need 37?':>12}")
line("-")
feasible_constitutive = []
for cost in COST_SWEEP:
    e, y = capacity(BUDGET_ECOLI, cost), capacity(BUDGET_YEAST, cost)
    ok = "YES" if y >= N_CAPABILITIES else "no"
    if y >= N_CAPABILITIES:
        feasible_constitutive.append(cost)
    print(f"{cost:>9.1%}{e:>14}{y:>12}{ok:>12}")
line("-")
break_even = BUDGET_YEAST / N_CAPABILITIES
print(f"  break-even cost per capability: {break_even:.2%} of proteome")
print(f"  i.e. every one of the 37 would have to cost under {break_even:.2%}")
print()

# ---- scenario 2: capabilities carried but switched on per product ----------

print("SCENARIO 2 - genes carried silent, only what the product needs is on")
line("-")
lo, hi = NEEDED_PER_PRODUCT
print(f"{'cost each':>10}{'needs ' + str(lo):>12}{'needs ' + str(hi):>12}{'fits 33%?':>12}")
line("-")
for cost in COST_SWEEP:
    use_lo, use_hi = lo * cost, hi * cost
    ok = "YES" if use_hi <= BUDGET_ECOLI else ("partly" if use_lo <= BUDGET_ECOLI else "no")
    print(f"{cost:>9.1%}{use_lo:>12.1%}{use_hi:>12.1%}{ok:>12}")
line("-")
print()

# ---- verdict ---------------------------------------------------------------

print("VERDICT")
line("=")
print("  Constitutive universality: arithmetically possible ONLY if every one")
print(f"  of the 37 costs under {break_even:.2%} of proteome. That is plausible for a")
print("  single-enzyme capability and not plausible for the expensive ones -")
print("  human-like glycosylation is a whole pathway plus sugar-nucleotide")
print("  supply, and compartmentalisation means building organelles. One or")
print("  two expensive capabilities exhaust the budget alone.")
print("  => Constitutive universality fails on the expensive capabilities,")
print("     not on the average one.")
print()
max_cost_switchable = BUDGET_ECOLI / hi
print(f"  Switchable universality: feasible while a capability costs under")
print(f"  {max_cost_switchable:.1%} of proteome (at {hi} capabilities per product).")
print("  That is a demanding but not absurd target.")
print()
print("  => The proteome budget does not kill the idea.")
print("     It forces one architecture: capabilities must be SWITCHABLE,")
print("     not constitutive. The chassis carries everything and expresses")
print("     only what the current product needs.")
