# GEMSDOE83 — Auditable fault-mapping research for the DOE GEMS Prize

> **Before every session or project change:** read this README, [`PROMPT.md`](PROMPT.md), and [`research/review.md`](research/review.md). They are the project starting point and evidence boundary. Do not treat a TIFF, stale page, owner mirror, projection, or leaderboard report as a validated submission.

## Current disposition: **NOT READY — DO NOT SUBMIT**

There is **no current eligible submission TIFF** in the published site. The old H83-B GeoTIFFs were moved out of `docs/` and quarantined. The old all-finite `-zeros.tif` passes an independent **format-only** audit against the locally restored owner-mirrored template; it is not scientifically validated, checked against the full registry, officially authenticated, or eligible for submission. Its NaN-outside twin fails the strict full-grid range audit. Neither file is offered for download.

No new experiment was run and no weekly slot was used. The current run card is [`docs/run-card.json`](docs/run-card.json). The landing page and executive summary both show the same blocked status and no file link. The status JSON is a static project snapshot, not a live leaderboard feed.

### Why a new TIFF is blocked

1. The prompt refers to a single assigned method paragraph, but that paragraph is absent from the supplied request and current project records. Selecting a lane ourselves would violate the parallel-run rule.
2. The canonical shared `evaluate_holdout.py`, `submission_writer.py`, cached feature stack, and full registry of comparison rasters are absent. Similar project-local utilities are not accepted substitutes and were not used as canonical tools.
3. The competition feature raster is not present. Three small owner-mirrored files were restored for audit; their hashes match a local manifest, but that does not establish organizer provenance. The official DrivenData data page and USGS/GDR sources were not fetched in this session.
4. Without the canonical tools, full feature data, and full registry rasters, no valid segment holdout, feature-only leakage canary, pre-placement surface duplicate check, final-dot duplicate check, or accepted automated submission validation can be completed.

These are blockers, not zeros. Missing holdout, confidence intervals, correlations, and overlaps stay `null`. The safe outcome is a negative/blocked run, not a synthetic or copied raster.

## Mission and standing prompt

Build an auditable research project for discovering **previously unmapped faults that may inform geothermal exploration**. Do not claim a fault-prediction raster has discovered a geothermal vent, reservoir, permeability, or resource. Keep scientific hypotheses separate from measurements and organizer scores.

The archived operating requirements—including lane restrictions, canonical-tool reuse, holdout/scoring protocol, duplicate thresholds, result labels, three review passes, submission format, and source limitations—are in [`PROMPT.md`](PROMPT.md). User-supplied submission names/scores are preserved once in [`registry/user_supplied_score_ledger.csv`](registry/user_supplied_score_ledger.csv).

## Why the user-reported GEMSDOE32 value 0.2778 may have performed well

`0.2778` is **USER-REPORTED, not ORGANIZER-CONFIRMED** in this project: there is no submission-page receipt linking the value to the submitted TIFF bytes. A pinned owner-repository snapshot names the same H33-2-B2 file, but its submission manifest says `UNSCORED` and its receipt field is null. A later organizer score is possible; it is not verified here.

The method in the preserved code is **catalogue-flank pruning**. H33-2-B2 starts from an owner-reported 0.2708 base claim (40,199 dots; USER-REPORTED, NOT ORGANIZER-CONFIRMED, with no receipt tied to the base artifact), removes the 2,545 dots within 2 pixels (200 m at 100 m/pixel) of the mapped-fault catalogue, and keeps 37,654. That is a 6.3% reduction in dot count. It is not, by itself, a new geological detector.

The owner code claims the organizer masks existing-fault pixels during scoring. Conditional on that rule, dots spent on masked catalogue pixels may add false-positive penalty without gaining credit there. Removing low-expected-credit dots while retaining coverage of hidden faults can therefore improve a precision-weighted objective. This makes **prediction-mass reallocation** a plausible explanation for why a moderate B=2 prune could have performed well. The masking/scoring premise is owner-code documentation, not freshly verified against the official problem/scorer in this session.

The pinned owner validation reports a custom LM-calibrated proxy change from 0.2630509876 to 0.2679205316 (difference +0.0048695440, four of four quadrants positive). That is **OWNER-REPORTED PROXY METRIC — NOT a `HOLDOUT-DTI` or score**: it is not the required canonical evaluator and lacks the accepted version/withheld-count/95% CI receipt. The owner’s 0.2746731598 live-anchor output is a **projection, not a score**. The owner manifest marks the named H33-2-B2 artifact unscored. See [`docs/research.html`](docs/research.html) and the pinned owner-source record [`evidence/upstream/GEMSDOE32_owner_evidence_receipt.json`](evidence/upstream/GEMSDOE32_owner_evidence_receipt.json).

A separate owner-local proxy value 0.4412792647 rounds to the user-supplied current public maximum of 0.4413. This is a numerical coincidence, not evidence that the proxy is the public score; the prompt also supplies a conflicting current maximum of 0.3195, and neither was fetched from the live official leaderboard. See [`docs/leaderboard.html`](docs/leaderboard.html) and [`registry/irregularities.json`](registry/irregularities.json).

No claim that GEMSDOE83 can exceed 0.2778 is supported: this run has no eligible candidate, accepted holdout, current baseline, complete registry comparison, or organizer score.

## Candidate hypotheses — proposal only, not the assigned lane

Four candidates are ranked in [`docs/hypotheses.html`](docs/hypotheses.html) and documented in [`docs/research/h83-hypotheses.md`](docs/research/h83-hypotheses.md). The ranking is qualitative expert judgment about possible improvement/cost, not an expected numerical score. The top conditional proposal is **cross-frequency wavelet phase coupling** between magnetic and gravity bands. Its band names/indices are provisional and must be checked against the canonical stack; the supplied xscale-persistence method and other prior art create a duplication risk. It has not been implemented, screened for leakage, or validated. **No candidate is authorized while the lane is unassigned.**

The holdout status and acceptance protocol are recorded in [`docs/research/holdout-validation.md`](docs/research/holdout-validation.md). No holdout, leakage canary, unique raster, or score is claimed for the current run.

## Data, sources, and limitations

- [`registry/user_supplied_score_ledger.csv`](registry/user_supplied_score_ledger.csv) contains the submitted site names and values, each labelled `USER_REPORTED_UNVERIFIED`, `USER_REPORTED_CONFLICT`, or `NO_SCORE_SUPPLIED`; none is an organizer receipt.
- [`registry/sources.json`](registry/sources.json) and the rendered [`sources page`](docs/sources.html) distinguish official manual-review links, GitHub owner-source evidence, source fetch status, and provenance class.
- [`registry/irregularities.json`](registry/irregularities.json) records missing lane/tools/data/registry, score conflicts, owner-proxy confusion risk, prior-art overlap, the unresolved grid-mask mismatch, and mitigations for the stale site/feed and ignored static data.
- This session could fetch GitHub/API sources but not DrivenData, USGS, GDR, NLR-PDF, Copernicus Data Space, EPSG, Wikipedia, or GitHub Pages hosts. Official competition data was not acquired. The official data page may be login-gated according to prior project notes; do not bypass it or request credentials in chat.
- Owner mirrors and owner-authored evidence can support reproducibility and historical analysis, but do not prove organizer provenance or scores. The official reference repository is a source of code, not a substitute for the requested shared holdout evaluator.
- **Grid irregularity:** the owner-mirrored sample template has 5,167,373 finite cells, while historical local code cites a 5,165,852-cell feature footprint from a missing receipt (1,521-cell difference). Its manifest also reports 60,988 template ones coincident with mirrored fault labels. Official template semantics were not checked; do not use this mirror to certify final output.
- The current leaderboard is **unknown here**. A saved 2026-10-04 public-page snapshot is historical context, not a current result or submission-page receipt. The legacy feed helper reads only the checked-in static status and does not probe sources or publish a second leaderboard feed.

## Submission instructions

Start at [`docs/index.html`](docs/index.html), then review [`docs/executive-summary.html`](docs/executive-summary.html). The site deliberately shows **NOT READY — DO NOT SUBMIT** and no download link. A future candidate can be shown only after it passes the assigned-lane, shared holdout/leakage, complete-registry uniqueness, and automated final-byte format/provenance gates. The executive summary documents the portal steps; this repository does not choose a weekly slot or submit automatically.

## Three review passes for this revision

1. **Implement what evidence supports:** quarantined stale submission binaries/scripts; rebuilt the readiness, research, score, source, and irregularity pages; recorded owner evidence classes and candidate blockers; preserved an explicit negative run card.
2. **Review bugs, assumptions, and edge cases:** corrected the initial phase-displacement hypothesis after finding H32-A’s cross-strike parity/down-dip method; excluded focal mechanisms after finding H33-E’s raw-catalogue/nodal-plane prior art; checked TIFF hashes against receipts; audited the H33-2-B2 owner manifest and distinguished its proxy/projection from scores; disabled legacy external feed probes; replaced stale tests and checked all local site links.
3. **Recheck the full prompt and improve:** confirmed assigned lane remains unresolved; canonical tools, official feature stack, and full registry remain missing; verified no TIFF/ZIP is linked or published, all score classes are explicit, nulls remain null, and no holdout/slot/organizer result is claimed. Regression tests and final repository checks are recorded with this revision.

## Core Values

**Maximize P(Win).** Weigh evidence, uncertainty, prior art, and slot cost; do not spend a submission slot on a weak or unverified candidate.

**Own the Outcome.** Own the work end to end, disclose failures and irregularities, repair stale readiness claims, and treat a negative result as actionable evidence rather than hiding it.

## Full consolidated standing prompt archive

This is the full consolidated operating prompt, duplicated from [`PROMPT.md`](PROMPT.md) so the repository guide remains self-contained. Keep both copies synchronized; the per-site score rows are linked in the CSV ledger above.

<details>
<summary>Expand the full standing prompt</summary>

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

</details>
