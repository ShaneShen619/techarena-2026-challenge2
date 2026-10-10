# TechArena 2026 - Challenge 2: Team Submission Template

 You implement your model in `my_model/` - everything
else is provided and stays untouched.

```
team_submission_template/
|
|-- my_model/                <<< YOUR CODE LIVES HERE
|     model_template.py        the skeleton you fill in (fit + estimate_soh)
|     model_example.py         a complete working reference baseline
|     __init__.py              ONE line selects which of the two runs
|
|-- framework/               DO NOT EDIT (data loading, output, saving)
|-- run_model.py             DO NOT EDIT - fixed evaluation interface
|-- validate_submission.py   run this before every submission
|-- data/                    the released dataset (see data/DATA_DESCRIPTION.md)
|-- sample_data/             tiny synthetic dataset for the dry run
|-- requirements.txt         add your dependencies here
|-- README.md                replace with a description of your approach
|-- REPORT.md / REPORT.pdf   your Challenge 2 technical report
|-- <TeamName>_Final_Presentation.pptx
|                            final TechArena presentation (Challenge 1 + Challenge 2)
|-- submission_instructions_2026.md   read this first
```

## Run model - 4 input arguments

```
python run_model.py --model train --input data --output-dir out
python run_model.py --model test  --input data --state-dir out --output-dir out --eval-point all
```

`train` fits your model on the released dataset and pickles it into `--output-dir`.
`test` estimates the pack SOH at every checkup date listed in
`data/checkups/evaluation_points.csv` (or at a single one, e.g. `--eval-point CK3`).
For each date the framework hands your model only the data recorded before it - the
same causal cut the organizers use for scoring. Output: `output.csv` with
`checkup, date, SOH_est` - SOH in percent of the nominal capacity 102 Ah (CK0 = 98.44 %).

## Before you submit

```
python validate_submission.py
```
It runs the full train/test dry run on `sample_data/`, checks the output schema and
writes `validation_report.txt`. Run it inside a fresh virtual environment created from
your `requirements.txt` - that is exactly what the evaluation does.

Before packaging, include your `<TeamName>_Final_Presentation.pptx`, summarizing your
methods and key results from both Challenge 1 and Challenge 2. The presentation may be
updated with each Challenge 2 resubmission; the version included in the final Challenge 2
submission zip before the deadline will be used for the TechArena final event. It is not
part of the Challenge 2 submission score or leaderboard evaluation.

Then zip the folder (without `data/`) as `<TeamName>_Challenge2.zip` - see
`submission_instructions_2026.md`.
