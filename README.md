# GEMSDOE83 — auditable fault-discovery research

## Submission status: **NOT READY — DO NOT SUBMIT**

This audit run generated no TIFF and used no weekly submission slot. A concurrent session
added synthetic TIFFs to main during review; they are preserved outside the website in
`research/quarantine/concurrent-session/` and are **not approved for submission**.
This is an honest negative/preflight deliverable, not a successful training run.
[Executive summary](docs/executive-summary.html) · [Research review](research/review.md) ·
[Run card](docs/run-card.json) · [Website](https://buffedlizard55-lab.github.io/GEMSDOE83/)

Read this README and [the operating brief](research/operating-brief.md) at the start of every session.
The supplied prompt is summarized there, not archived verbatim. Outstanding prompt requirements,
including the full verbatim archive, are explicitly tracked in the review.

## Starting condition and result

The initial commit contained **only this README**. There was no model, data, cache, template,
registry, evaluator, writer, or previous-session next-step log. Consequently, the statement in
the supplied prompt that only data placement remained was not true of this checkout.
Three small hash-pinned mirrored rasters were recovered into ignored `data/` and inspected.
The feature stack was located in an upstream mirror manifest but not downloaded.
Mirrored data consistency is not organizer authentication.

**Critical unresolved inputs:** the single assigned lane (no method paragraph was supplied),
the canonical shared template with `evaluate_holdout.py` and `submission_writer.py`,
the current registry of competing surfaces and dots, an authenticated submission template,
and the incumbent result on the exact same required holdout instrument.
We do not build a private replacement evaluator/writer or perturb a previous submission.

## Operating requirements from the user prompt

> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS
> SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.

That goal is **not yet fulfilled**. A missing artifact must never be presented as safe.
The required pipeline is: assigned lane → cached features → individual-feature leakage canaries
→ buffered whole-segment hide-and-recover → pooled distance-tolerant Tversky evaluation
→ registry checks on surface → placement → registry checks on dots → strict format validator
→ separate selector. Feature AUC above 0.90 is a leakage alarm; surface rank correlation above
0.90 or dot overlap above 70% within 3 pixels is a duplicate stop. Limit experiments to three
or two hours, whichever comes first. No weekly slot is authorized by this project run.
Every measured score must be labeled HOLDOUT-DTI with evaluator version, withheld positives,
and 95% CI, or ORGANIZER-CONFIRMED with an actual submission-page receipt. User-reported
numbers and calibrated projections cannot be relabeled to meet that rule.

## Reproduce the implemented audit

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_audit_data.py # gh CLI; small hash-pinned mirrors only
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_site.py
# Format-only audit of an independently generated candidate, once available:
.venv/bin/python scripts/validate_artifact.py candidate.tif data/sample_submission.tif --output evidence/candidate-format.json
```

The format audit rejects NaN, infinity, negative values, values above one, masked missing
predictions inside the footprint, multiple bands, empty footprint, or mismatched CRS/shape/transform.
It checks raw values even outside the footprint so nodata cannot conceal a range error.
It **does not clip or silently repair** and **never grants submission readiness**.
The upstream shared writer/evaluator must still be supplied and reused.
Tests create synthetic rasters in temporary directories only; these are never submissions.

## Core values and next session

**Maximize P(Win):** reject unvalidated leaderboard extrapolations; prioritize independent evidence
and budget-matched controls. **Own the Outcome:** automate checks, keep failures visible,
and do not substitute a copied TIFF for scientific work.

Next: resolve lane/template/registry first; restore pinned features using upstream restoration tools;
verify band provenance; implement only the assigned mechanism in the shared template; run canaries
and the required holdout; compare with the incumbent using paired segment/block bootstrap;
perform both uniqueness checks; write and validate a genuinely new TIFF; publish its exact hash,
unique name and short note. Only a separate selector can spend a weekly slot.

CI runs tests and website consistency checks. The repository already has legacy GitHub Pages
configured for the root of `main` (verified via GitHub API). The root landing page routes to
`docs/index.html`. Updating Pages settings was denied by integration permissions; the existing
legacy configuration is retained. Deployment success must be verified separately.
No automatically refreshed leaderboard feed or organizer submission integration is implemented.
