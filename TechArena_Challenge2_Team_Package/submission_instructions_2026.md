TechArena 2026 - Challenge 2 Submission Instructions

> **Before you distribute this document, fill in / confirm the items marked
> `<<TODO: ...>>`** - these are event-logistics details (contacts, deadline,
> platform links) that aren't derivable from the codebase and were left as
> placeholders rather than guessed.

# 📋 Overview

Welcome to the second round of TechArena 2026! Challenge 2 asks you to build a
**battery State-of-Health (SOH) estimator for a real pack under real-world
operation**: given the operating data of a 4-cell LFP pack (current, cell
voltages, temperatures, BMS-style Ah counters) and a single beginning-of-life
capacity test, estimate the pack's SOH at every monthly checkup date - using
only the data recorded *before* that date.

As in Challenge 1, the submission is a **fixed framework with one file you fill
in**. You are not writing an entry point, a CLI, or an output writer - all of
that is provided and frozen so every team is scored through the exact same
harness. Your job is to implement two Python methods. Please read this document
fully before you start.

# 🎯 Submission Requirements

## Required Deliverables

Your submission is the **entire provided template folder** (without `data/`),
with these parts filled in / updated:

1. **Model implementation**: `my_model/model_template.py` - implement
   `fit()` and `estimate_soh()` (see below).
2. **Active-model switch**: `my_model/__init__.py` - flip the import to
   point at your model instead of the example.
3. **Dependencies**: `requirements.txt` - every package your model needs,
   pinned versions recommended.
4. **Documentation**: `README.md` - replace the provided one with a
   description of your approach: method, features derived from the operating
   data, any open datasets used (with citations and licenses), and what
   transferred to this task. Your report following the Student Report
   Template ships inside the zip as well (`REPORT.md` or `REPORT.pdf`).
5. **Final TechArena presentation**: `<TeamName>_Final_Presentation.pptx` -
   include a presentation summarizing your methods and key results from both
   Challenge 1 and Challenge 2. You may update this presentation with each
   Challenge 2 resubmission to reflect your latest methods and results. The
   presentation included in your final Challenge 2 submission zip before the
   submission deadline will be used as your final presentation for the
   TechArena final event.
6. Optionally, any additional files your model needs (helper modules,
   pre-trained weight files) - place them inside `my_model/`.

**Do not modify** `run_model.py`, anything under `framework/`, or
`validate_submission.py`. These implement the fixed evaluation interface and
are identical across all teams; the organizers run your submission through
their own untouched copies of these files regardless of what you submit, so
local edits to them have no effect on scoring and only risk breaking your own
local testing. Framework files are compared byte-wise against the original and
deviations are reported to the jury.

## The Two Functions You Implement

```python
class MyModel:
    def fit(self, dataset):
        # dataset.operation:           all released operating rows (10 s)
        # dataset.checkups_released:   the beginning-of-life checkup CK0
        # dataset.reference_discharge: the CK0 C/20 discharge curve
        # Learn whatever you need and store it on self.* - the framework
        # pickles your whole fitted object after this call.
        ...

    def estimate_soh(self, dataset, at_date):
        # dataset is CUT at at_date: only rows recorded before the checkup.
        # Return the pack SOH in percent of the NOMINAL capacity (102 Ah).
        ...
```

`fit()` is called once with the full released dataset. `estimate_soh()` is
called once per checkup date; the framework performs the causal cut, so you do
not need to (and cannot) filter by date yourself.

# 📁 Project Structure

Your submission zip must preserve this exact structure:

```
<TeamName>_Challenge2.zip
|
|-- run_model.py                DO NOT EDIT
|-- framework/                  DO NOT EDIT
|     __init__.py
|     data.py
|     io.py
|     persistence.py
|-- my_model/
|     __init__.py               flip the switch here
|     model_template.py         your model
|     model_example.py          the reference baseline (leave it in)
|     ...                       your helper files / pre-trained artefacts
|-- validate_submission.py      DO NOT EDIT
|-- sample_data/                leave it in (used by the validator)
|-- requirements.txt            your dependencies
|-- README.md                   your approach writeup
|-- REPORT.md / REPORT.pdf      your report (Student Report Template)
|-- <TeamName>_Final_Presentation.pptx
|                               final TechArena presentation (Challenge 1 + Challenge 2)
```

Do **not** include the `data/` folder - the organizers use their own copy.

# 🚨 Critical Requirements

- **Flip the switch.** `my_model/__init__.py` ships pointing at the example
  model so the template runs out-of-the-box; forgetting to flip this switch
  means the organizers score the reference model and your score is exactly
  1.0.
- **Declare every dependency.** The evaluation installs your
  `requirements.txt` into a fresh virtual environment and nothing else. A
  missing declaration was the most frequent failure in Challenge 1.
- **Only CK0 is a target.** The beginning-of-life capacity (100.41 Ah =
  98.44 % SOH of the nominal 102 Ah) is the only capacity value you receive. Checkups CK1 to CK7 are
  hidden and scored; their dates are known (`evaluation_points.csv`), their
  values are not. Do not attempt to reconstruct them from external sources.
- **One zip, correctly named**: `<TeamName>_Challenge2.zip`. Nothing is
  uploaded alongside it. The final TechArena presentation must be included
  inside this zip.

# 💻 Technical Specifications

## Python Requirements

- **Python version**: 3.11 or 3.12. Pin only what you need; very old pins
  may have no wheels on the evaluation machine.
- Provided framework dependencies: `numpy>=1.24`, `pandas>=2.0`.

## Data You're Given

See `data/DATA_DESCRIPTION.md` for the column reference. In short:

- `data/operation/segment_NN_TTdegC.csv.gz` - 13 operating segments
  (Jan-Sep 2025, 10-s sampling; segment 3 is not provided): timestamp, elapsed time, current, BMS-style
  cumulative charge/discharge Ah counters, the four cell voltages, pack voltage
  and cell temperature statistics.
- `data/checkups/checkup_capacities_released.csv` - CK0 only.
- `data/checkups/evaluation_points.csv` - all checkup dates: CK0 2025-01-14 (released),
  CK1 2025-02-08, CK2 2025-03-11, CK3 2025-04-14, CK4 2025-05-16, CK5 2025-06-16,
  CK6 2025-07-25, CK7 2025-08-28 (hidden, scored).
- `data/checkups/CK0_reference_discharge.csv.gz` - the beginning-of-life
  C/20 discharge curve.

Real lab data means real imperfections: segment 3 (19 Feb - 11 Mar) is not
provided, there are recording gaps inside segments (the Ah counters stay
correct across both), duplicate timestamps mark step transitions, and the profile is a simulated application profile,
not a laboratory cycling protocol.

## Hardware & Runtime Limits

The evaluation enforces wall-clock limits per submission: **up to 2 hours**
for `--model train` and **up to 30 minutes per evaluation point** for
`--model test`. Those limits are measured on the organizers' evaluation
machine (`<<TODO: confirm hardware>>`). Pre-training on open data is not
re-run at evaluation - ship its artefacts inside `my_model/`.

# 🔧 Implementation Guidelines

## Where to Start

1. Run the template as-is (`python run_model.py --model train ...`, then
   `--model test ... --eval-point all`) to see the reference baseline work.
2. Read `my_model/model_example.py` - it is a complete, minimal estimator:
   partial-charge coulomb counting on the periodic full charges, anchored at
   CK0. Understand why it is optimistic on LFP.
3. Implement `MyModel` in `my_model/model_template.py`, flip the switch,
   rerun.

## Best Practices

- Validate causally: hold out later months and estimate them from earlier
  data only - `run_model.py --model test --eval-point all` does exactly this.
- Exploit what a BMS actually has: the cell voltages under a *repeating*
  load, their spread, the temperature difference between the 25 and 45 degC
  segments, and the Ah counters. Imbalance grows over the campaign.
- Keep it robust across both temperatures and across the whole campaign -
  the hidden checkups span all of it.
- All datasets used or provided in Challenge 1 may be used again; further open-source
  datasets are welcome (see the challenge description). Document every dataset with
  citation and license in your README and report.

## Sample `requirements.txt`

```
numpy>=1.24
pandas>=2.0
# add anything else your model needs, e.g.:
# scikit-learn>=1.3
# torch>=2.1
```

# 📝 Submission Process

## Step 1: Implement

Fill in `my_model/model_template.py` and flip the switch in
`my_model/__init__.py`:

```python
# from .model_example import ExampleModel as ActiveModel   # reference baseline
from .model_template import MyModel as ActiveModel          # your model
```

## Step 2: Validate Locally

Create a fresh virtual environment from your `requirements.txt` and run the
validator inside it:

```
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python validate_submission.py
```

`validate_submission.py` performs the full train/test dry run on
`sample_data/` and checks the output schema. It writes
`validation_report.txt` with the full detail.

## Step 3: Package

1. Zip the entire submission folder (without `data/`).
2. Name it: `<TeamName>_Challenge2.zip`.
3. Extract the zip somewhere clean and re-run `validate_submission.py`
   from the extracted copy.

## Step 4: Submit

`<<TODO: submission platform / upload link>>`. There is no limit on how
many times you may resubmit before the deadline
(`<<TODO: deadline date/time and timezone>>`); the last submission counts.

The final TechArena presentation may also be updated with each resubmission.
The version of `<TeamName>_Final_Presentation.pptx` included in your last
Challenge 2 submission before the deadline will be used as the final version
for the TechArena final event. No separate presentation upload is required.

Submissions are evaluated every two weeks and the public leaderboard is
updated accordingly.

# ⚡ Automated Validation & Scoring

## Local Validation (`validate_submission.py`)

Runs your model exactly the way the organizers do, on the tiny synthetic
`sample_data/`, and checks: training completes, one SOH estimate per
evaluation point, values in percent, framework files present.

## Official Scoring

Model performance is scored on the hidden checkups CK1..CK7 only, as error
metrics of your SOH estimates (including the worst-case error), each
normalised by the reference baseline - **baseline = 1.0, lower is better**.
The exact metric set is not published. Model performance counts 70 % of the
final score; Technical Innovation (data efficiency, transferability, use of
open data), Interpretability & Explainability, and Code Quality &
Reproducibility (PEP 8, documentation) count 10 % each and are assessed from
your submission and report.

The final TechArena presentation is **not part of the Challenge 2 submission
score or leaderboard evaluation**. It will be evaluated separately during
the TechArena final event.

# 🚨 Common Issues and Solutions

**"no operation files under `<path>/operation`"**
`--input` must point at the folder that contains `operation/` and
`checkups/` (the `data/` folder of the template).

**"output must contain one row per evaluation point"**
`estimate_soh()` raised or returned nothing for a checkup - it must return a
number for every date, even when little data is available before it.

**"SOH_est must be in percent (50..110)"**
Return percent of the nominal capacity (102 Ah), not a fraction; CK0 reads 98.44 %.

**"ActiveModel still points at the EXAMPLE model"**
Flip the switch in `my_model/__init__.py`.

**"It passed on my machine but failed during scoring" / `ModuleNotFoundError`**
`validate_submission.py` runs your model with whatever Python environment
you launch it from. If that environment has packages your
`requirements.txt` does not declare, the fresh evaluation environment will
not have them. Always validate from a fresh virtual environment.

**Dry run in `validate_submission.py` times out**
The local sanity limits inside the validator are not the competition limits -
they exist so a hanging script does not block you locally.

# 📋 Submission Checklist

- [ ] `my_model/model_template.py` implements `fit()` and `estimate_soh()`
- [ ] `my_model/__init__.py` points `ActiveModel` at `MyModel`
- [ ] `requirements.txt` lists every dependency; validated from a fresh venv
- [ ] `README.md` describes your approach, datasets used (with licenses), and
      what transferred
- [ ] `REPORT.md` / `REPORT.pdf` follows the Student Report Template
- [ ] `<TeamName>_Final_Presentation.pptx` is included and summarizes the
      methods and key results from both Challenge 1 and Challenge 2
- [ ] `run_model.py`, `framework/`, `validate_submission.py` are unmodified
- [ ] `validate_submission.py` passes and `validation_report.txt` is clean
- [ ] Zip is named `<TeamName>_Challenge2.zip`, contains no `data/` folder, and
      was tested from a clean extraction
