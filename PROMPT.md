# GEMSDOE83 standing prompt — read every session

This file preserves the complete set of unique operating requirements in the user’s project prompt. The extensive repeated prompt text and the per-site score names/values are represented once; the scores themselves are transcribed in [`registry/user_supplied_score_ledger.csv`](registry/user_supplied_score_ledger.csv). Read this file, the top-level [`README.md`](README.md), and [`research/review.md`](research/review.md) before changing the project.

## Mission

Build an auditable, useful project to improve discovery of previously unmapped faults in the DOE GEMS Prize area and support geothermal exploration. The goal is a competitive result, but scientific integrity is mandatory: do not assert geothermal-vent discovery from a fault map, do not fabricate scores or geology, and do not claim that an idea beats a baseline until the required holdout has run.

## Highest-priority deliverable

Produce a unique single-band GeoTIFF for the competition, without copying an earlier submission. The project—not a human inspector—must automatically validate it. The website must make it obvious at first visit whether the file is OK to download and submit. If any scientific, uniqueness, provenance, or format gate is unavailable or fails, show **NOT READY — DO NOT SUBMIT**, do not link a stale TIFF, and report a negative result rather than fabricate a deliverable.

## Parallel-run protocol

1. **Lane:** Work only in the one assigned method paragraph. The current supplied request does not identify that paragraph, so no lane is assumed. Before placing dots, compare the candidate surface against every registry raster. After placement, compare the final dots. If rank correlation is greater than 0.90, or more than 70% of dots lie within 3 pixels of one registry raster’s dots, record a duplicate and stop.
2. **Reuse, do not rebuild:** Use the template’s cached feature stack, shared `evaluate_holdout.py`, and shared `submission_writer.py`. Do not keep a private fork. Correct a shared defect only in the canonical template, then report it. The named shared assets are absent from this checkout; do not substitute local historical utilities.
3. **Holdout:** Hide whole fault segments with a buffer; derive every catalogue-based feature only from visible faults; mask visible-fault pixels pixel-exactly; score pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel. A result is `HOLDOUT-DTI` only when the evaluator version, withheld-positive count, and 95% confidence interval are supplied.
4. **Leakage canary:** Test each feature alone on holdout. AUC above 0.90 is leakage until proven otherwise.
5. **Score provenance:** `ORGANIZER-CONFIRMED` requires a value copied from an organizer submission-page receipt. A public leaderboard snapshot, user report, local projection, or mirror is not such a receipt. Label every reported score accordingly; never write a projection as a score.
6. **Run card:** End each session with one JSON card containing hypothesis; mechanism; a named non-fault mimic; holdout DTI + CI; surface and final-dot correlation/overlap against the registry; raster SHA-256; validator output (no NaN inside footprint, values [0,1], CRS/shape/transform match); submission name and note (≤140 characters); and verdict `promote` or `negative`. Missing measurements are null, not zero.
7. **Budget:** Stop after at most 3 experiments or 2 hours. Do not choose a real submission slot. Promotion to a weekly slot belongs to a separate selector operating within the competition’s current weekly cap.

## Research process

Before implementation, create 3–5 candidate geological hypotheses not already implemented in this repository. For each, name exact layer(s), physical signature/transform, why the signal could indicate an unmapped fault rather than an already catalogued one, how the method differs from repository prior art, a named non-fault mimic, expected DTI direction (qualitative unless actually measured), implementation cost, and required data. If external data is needed, identify the exact free official source and verify that it is obtainable before calling the idea viable. If the sandbox cannot reach that source, mark the idea blocked, not viable.

Validate the top eligible idea on the spatially blocked holdout before any slot is touched. It must beat the current same-instrument holdout best, survive the feature-only leakage canary, and pass both duplicate screens. The competition’s private score may differ; holdout improvement is not a guarantee of an organizer result.

## Submission format and user experience

The output must match the official template’s single-band GeoTIFF CRS, shape, and geotransform. Values must be in [0,1] and finite inside the scoring footprint; a zeros-outside variant is the safest range audit unless the official format requires another encoding. Re-open the written bytes and validate automatically. Supply a unique name and a short comment no longer than 140 characters. Create an executive-summary subpage with exact portal steps. Make the download button appear only after the full run card says submission-ready.

## Sources and project quality

Use official, free public sources when possible; provide source URLs for manual review; store provenance, hashes, evidence class, and irregularities in auditable tables. Do not claim a source is freshly verified unless it was fetched and checked in this session. The competition data page may require login; do not bypass it or request/store credentials in chat. Identify what could not be fetched, what data/tools are missing, and what remains to be done. Build a clean, simple GitHub Pages site and a useful status feed, but do not automatically scrape or misrepresent a dynamic competition leaderboard.

## Required values and review passes

- **Maximize P(Win):** weigh evidence, uncertainty, and submission-slot cost; say no to weak candidates.
- **Own the Outcome:** take responsibility for the final result, disclose failures, and improve the system.
- Complete three passes before reporting: (1) implement what is supported and verify; (2) review for bugs, assumptions and edge cases and fix; (3) re-check the whole result against this brief and improve anything still wrong.
- Open a pull request from the active Arena branch. Merge it only after checks pass. Never switch or rename the session branch.

## Official/manual-review source entry points supplied by the user

- DOE GEMS Prize: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Problem description, metric, submission requirements: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About/resources: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Competition data: https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Public leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Official reference code: https://github.com/drivendataorg/gems-prize-reference-solution
- NLR rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- USGS GeoDAWN data: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- GBCGE INGENIOUS: https://gbcge.org/current-projects/ingenious/
- GDR submission 1391: https://gdr.openei.org/submissions/1391
- USGS ComCat FDSN service: https://earthquake.usgs.gov/fdsnws/event/1/
- EPSG:32611: https://epsg.io/32611
- Tversky index background: https://en.wikipedia.org/wiki/Tversky_index (secondary source, not an official competition source)
- User-reported GEMSDOE32 H33-2-B2 page: https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

The user-supplied site scores and conflicting leaderboard statements are retained only as `USER_REPORTED_UNVERIFIED` context in the score ledger. They are not organizer receipts and are not accepted as scores for a run card.
