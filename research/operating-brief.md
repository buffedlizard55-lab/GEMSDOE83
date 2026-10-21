# Operating brief — 2026-10-21

This is a condensed index, not a verbatim prompt. The complete standing requirements are in [`PROMPT.md`](../PROMPT.md); the current evidence/repository review is [`review.md`](review.md); the project guide is [`README.md`](../README.md). User-supplied submission names and score transcriptions are in [`registry/user_supplied_score_ledger.csv`](../registry/user_supplied_score_ledger.csv).

## Current decision

**NOT READY — DO NOT SUBMIT.** The assigned lane is not identifiable. The canonical feature stack, `evaluate_holdout.py`, `submission_writer.py`, and complete registry rasters are absent. The owner-mirrored sample/feature footprint counts differ by 1,521 cells and the official template semantics are unresolved. No experiment, candidate TIFF, holdout, slot selection, or submission was made. The negative run card is [`docs/run-card.json`](../docs/run-card.json).

## Requirements at a glance

- Stay within the assigned single-method lane; do not guess it.
- Reuse the canonical cached feature stack, evaluator, and writer; do not substitute local historical code.
- Hide whole fault segments with a buffer; derive catalogue features from visible faults only; mask visible faults pixel-exactly; evaluate pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel.
- Test each feature alone; AUC >0.90 is a leakage alarm until resolved.
- Compare the candidate surface against every registry raster and final dots within 3 pixels. Rank correlation >0.90 or overlap >70% is a duplicate stop.
- Label accepted results only as `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` from a submission-page receipt. User reports, owner proxy metrics, and projections are separate evidence classes.
- Stop at 3 experiments or 2 hours. Do not select a weekly slot; an independent selector owns that decision.
- Create a unique, automatically validated GeoTIFF only if scientific, uniqueness, provenance, and exact-grid format checks pass. Otherwise keep the landing page negative and fail closed.
- Preserve sources, hashes, limitations, irregularities, and three implementation/review passes. Keep **Maximize P(Win)** and **Own the Outcome** central.

Official/manual-review URLs, including the proposed Copernicus source, and their fetch statuses are in [`registry/sources.json`](../registry/sources.json). Current external source availability was not verified except GitHub owner sources; the live official leaderboard was not fetched. Conflicting user-supplied current maximum claims remain unverified.
