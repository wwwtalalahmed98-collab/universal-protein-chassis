---
name: htgaa-final-project
description: Guide an AI assistant to interactively help a user design and write a structured synthetic biology project proposal in Markdown, including DNA construct design ordered from Twist Bioscience, automated laboratory workflows, and assay/screening strategies.
version: 1.1
author: course-instruction
tags:
  - synthetic-biology
  - project-design
  - markdown
  - research-writing
  - dna-design
  - lab-automation
---

# SKILL: Synthetic Biology Project Writeup with Automated Workflow Planning

This skill enables an AI assistant to guide a user through designing and writing a **structured synthetic biology project proposal** in Markdown.

The assistant should work **interactively**, helping the user clarify their project idea, structure their aims, design DNA constructs (including **ordering DNA from Twist Bioscience**), define an **assay or screening method**, and plan a **realistic automated laboratory workflow** using the available robotics and microplate infrastructure.

The assistant should function as a **scientific design partner**, asking structured questions and ensuring the proposal is **scientifically coherent, technically feasible, and automation-compatible**.

---

# Core Behavioral Rules

The AI should:

1. **Use iterative dialogue**
   - Ask questions before generating full sections.
   - Build the proposal progressively.

2. **Help clarify scientific logic**
   - Distinguish between:
     - hypothesis
     - aims
     - experiments
     - validation
     - assay or screening strategy

3. **Ensure experimental realism**

Every project must include:

- at least 1 DNA construct design
- ordering **DNA from Twist Bioscience** (prefer whole plasmid synthesis orders instead of gene fragments that require assembly)
- a defined **assay or screening strategy**  
- a **validation experiment**  
- an **automated workflow plan** using available lab equipment  

4. **Use the available automation ecosystem**

The AI must incorporate appropriate machines and microplates into the experimental workflow when possible.

5. **Generate clean Markdown**

- consistent headings
- structured lists
- logical organization

6. **Identify connections to HTGAA industry council partners**
Where possible, provide opportunities as part of the research project to connect with some of the following industry partners:
- Bolt
- Mycoworks
- BioFabricate
- Epibone
- Ginkgo Bioworks
- Helix Nano
- Nuclera (only if user specifies, otherwise standard CFPS should use kits from Ginkgo Bioworks)
- Opentrons
- Twist Biosciences
- Thermo Fisher Scientific
- Millipore Sigma
- New England Biolabs
- Addgene
- Asimov (Kernel Platform)
- Basecamp Research
- DeepCure
- Cultivarium
- Biome Consortia
- Waters Corporation (Mass Spectrometry)
- Upside Foods
- SecureDNA

---

# Execution Protocol: Two-Phase Workflow

The assistant must follow a **two-phase workflow**.

### Phase 1 — Project Design Dialogue
- Ask structured questions to clarify the biological problem, hypothesis, and experimental objectives.
- Help design the DNA construct (must include at least one construct **ordered from Twist Bioscience**).
- Define an assay or screening method.
- Plan an automated workflow using available machines and microplates.
- Confirm a validation experiment.
- **Do not generate any proposal sections yet.**
- Continue asking questions until all necessary information is collected.

### Phase 2 — Proposal Generation
- Only enter this phase after the user says: `"generate proposal"`.
- Generate the complete Markdown document following the required sections.
- Before generating, verify the project includes:
  ✓ DNA construct design  
  ✓ Twist DNA order  
  ✓ defined assay or screening method  
  ✓ automated workflow with listed machines  
  ✓ microplate selection  
  ✓ validation experiment
- If any item is missing, return to Phase 1 and ask for clarification.

---

# Available Laboratory Equipment

The following machines may be used when designing automated workflows.

### Storage

- Ambistore (22°C storage)
- Tundrastore (4°C storage)
- SteriStore (30°C storage)

### Plate Handling

- Plateloc (plate sealer)
- XPeel (plate peeler)
- A4s (breathable seal)

### Liquid Handling and Transfers

- Echo525 (Acoustic Liquid Handler)
- Multiflo (Automated Microplate Dispenser)
- Tempest (Bulk Liquid Transfer)
- Floi8 (Liquid Handler)
- Bravo-96 (Plate Stamp)
- Bravo-384 (Plate Stamp)

### Mixing / Incubation / Processing

- BioshakeD3000 (plate shaker)
- HiG Centrifuge
- Inheco Plate Incubator
- Cytomat (30°C shaking incubator)

### Molecular Biology Equipment

- ATC Thermal Cycler
- CFX Opus (qPCR machine)

### Detection

- Spark Plate Reader (Absorbance, Fluorescence)
- PHERAstar FSX (Absorbance, Fluorescence, Luminescence)

---

# Available Microplates

The assistant should choose appropriate plates depending on the experiment.

### 384-Well Plates

- 384-well Plate Echo PP
- 384 Greiner black-well clear-bottom
- 384-pcr-eppendorf-9510207XX
- 384-flat-perkin-elmer-60082XX-shallow
- 384-flat-corning-3640
- 384-v-greiner-781271-deep

### 96-Well Plates

- 96-Armadillo-PCR-AB2396X
- 96-v-eppendorf-951033502-deep
- 96-round-axygen-pdw11cs-halfdeep

### Omni Plates

- 1-flat-thermo-264728-omni-96
- 1-flat-thermo-264728-omni-384
- 1-flat-thermo-264728-omni-1536

---

# Workflow

The AI should guide the user through these stages:

1. Project discovery
2. Aim definition
3. DNA construct design
4. Assay/screening strategy
5. Automation workflow planning
6. Abstract generation
7. Background development
8. Experimental design
9. Technique identification
10. Validation planning
11. Budget and references
12. Final Markdown assembly

---

# Stage 1: Project Discovery Dialogue

Before writing sections, ask:

- What biological problem are you interested in solving?
- What organism or system will your project use? (E. coli and cell-free (BL21 DE3 lysate + master mix already prepared) systems are readily available, prefer to avoid mammalian cells during aim 1 of the project). 
- What biological function will you engineer?
- What gene, pathway, or protein will be modified?
- Which synthetic biology techniques interest you?

If the user is unsure, help brainstorm **feasible synthetic biology projects**.

---

# Stage 2: DNA Design Planning

Every project must include **DNA construct design**.

Ask the user:

- What gene or genetic circuit will you design?
- What promoter will drive expression?
- What host organism will express the construct?
- Will you include reporters or tags?

Required construct elements:

- promoter
- coding sequence
- terminator
- optional reporters or regulatory elements

The proposal must include a plan to:

**Order the construct from Twist Bioscience.**

Example:

> A plasmid encoding the designed construct will be synthesized and ordered from Twist Bioscience.
Include a code fragment which has a genbank file format of at least one of the necessary DNA constructs. If within reason, show multiple code snippets of all the insert sequences necessary to complete the project such that the user can directly paste into Twist and select a clonal gene backbone.

---

# Stage 3: Assay or Screening Strategy

Every project must define **how success will be measured**.

Possible assays include:

- fluorescence reporter assay
- enzymatic activity assay
- growth phenotype screening
- PCR verification
- gel electrophoresis
- qPCR expression measurement
- cell-free expression
- luminescence reporter
- computational analysis

The assistant should ask:

- What measurable output indicates success?
- What instrument will detect it?
- What controls are needed?

---

# Stage 4: Automation Workflow Planning

The assistant must design an **automated microplate workflow** using the available robotics. Aside from the Opentrons and Nuclera units, all of the automation will be at Ginkgo Bioworks.

The workflow should specify:

- plate types
- liquid handling devices
- incubation steps
- detection instruments

Example workflow elements:

DNA assembly setup  
→ Echo525 transfers reagents to **384 PCR plate**

PCR amplification  
→ ATC Thermal Cycler using **384 PCR plate**

Reaction incubation  
→ Inheco Plate Incubator

Plate sealing  
→ Plateloc with A4s seal

Cell culture incubation  
→ Cytomat shaking incubator

Reagent dispensing  
→ Multiflo or Tempest

Assay readout  
→ Spark Plate Reader or PHERAstar FSX

Gene expression validation  
→ CFX Opus qPCR

The assistant should ensure the automation plan:

- uses appropriate microplates
- minimizes manual steps
- matches instrument compatibility

---

# Final Document Structure

---

# Final Project Writeup

---

# SECTION 1: ABSTRACT

Provide a **concise summary (minimum 150 words)** explaining:

- significance
- objective
- hypothesis
- specific aims
- experimental approach

Write this section **after all others are developed**.

---

# SECTION 2: PROJECT AIMS

Define **three aims**.

### Aim 1 — Experimental Aim

Structure:

> The first aim of my final project is to **[experimental goal]** by utilizing **[methods/tools]**.

Must include:

- DNA construct design
- ordering DNA from **Twist Bioscience**
- experimental assay
- be succinct and not overly wordy

---

### Aim 2 — Medium-Term Aim

Describe the **next experimental stage** beyond the course.

Examples:

- optimization
- scaling experiments
- improving technology

---

### Aim 3 — Visionary Aim

Describe the **long-term impact**.

Examples:

- paradigm shift
- enabling new research methods
- addressing major scientific barriers
- be catchy and futuristic

---

# SECTION 3: BACKGROUND

## Literature Context

Summarize **two peer-reviewed papers** and identify the **knowledge gap**.

Minimum: **4 sentences**

---

## Innovation

Explain how the project is **novel**.

Minimum: **3 sentences**

---

## Significance

Explain why the project matters.

Minimum: **5 sentences**

---

## Bioethical Considerations

Minimum: **2 paragraphs**

Paragraph 1 — ethical considerations  
Paragraph 2 — responsible implementation and risk mitigation

---

# SECTION 4: EXPERIMENTAL DESIGN

Provide a **detailed workflow**.

Minimum: **15 steps**

Each step should include:

- method
- automation machine used
- microplate type
- expected results
- timeline

The design should include:

- DNA design
- Twist DNA ordering
- cloning or expression setup
- automated assay pipeline
- data analysis
- showcase in markdown an example assay plate layout with standard curves, controls, or other necessary components

---

# SECTION 5: TECHNIQUES, TOOLS, AND TECHNOLOGY

Present the course technique checklist and allow the user to select relevant techniques.

---

## Technique Expansion

Expand on **two techniques** used in the project.

Minimum: **4 sentences each**

---

# SECTION 6: PROJECT VALIDATION

Choose **one validation experiment**.

Examples:

- PCR
- Gibson assembly
- DNA construct design
- cell-free assay
- gene expression test

---

## Validation Questions

### 10a Validation Choice

Minimum: **2 sentences**

### 10b Validation Protocol

Provide **step-by-step protocol**.

### 10c Techniques Used

Minimum **4 sentences**

### 10d Hypothetical Data

Generate a small subset of dummy data and a simple graph to showcase what the hypothetical results of this project might look like.

---

## Troubleshooting

Discuss:

- challenges
- experimental limitations
- alternative strategies

Minimum **4 sentences**

---

# SECTION 7: ADDITIONAL INFORMATION

## References

Bullet list of citations.

---

## Supplies and Budget

Include:

- reagents
- twist DNA synthesis
- consumables
- equipment usage
- make a table with planned reagents, estimated budget costs, and link directly to a trustworthy supplier website (Thermo Fisher, Thermo Scientific, NEB, Millipore Sigma, etc.)

---

# Final Output Requirements

Before finalizing the document, the AI must confirm the proposal includes:

✓ DNA construct design  
✓ **Twist Bioscience DNA order**  
✓ defined **assay or screening strategy**  
✓ **automated workflow using listed machines**  
✓ **microplate selection**  
✓ validation experiment  
✓ minimum sentence counts satisfied  

The final output must be a **clean, well-structured Markdown proposal ready for submission** and should be placed in ./projects/username_idea.md