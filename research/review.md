# Repository, evidence, and implementation review — 2026-10-21

This is the current review for the active GEMSDOE83 worktree. Read this with [`README.md`](../README.md) and [`PROMPT.md`](../PROMPT.md) before further changes. It supersedes older review notes that described different branches, readiness states, or candidate hypotheses.

## Current disposition

**Negative / blocked; NOT READY — DO NOT SUBMIT.** No assigned method paragraph was identifiable in the supplied prompt. The canonical cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, and full comparison registry are absent. The old H83-B TIFFs and local pipeline scripts are quarantined outside the published `docs/` tree. No experiment, new candidate raster, holdout, slot selection, competition submission, or organizer-confirmed score was produced in this revision.

## Repository and protocol review

- Checked the local package, scripts, evidence, site, GitHub Pages/CI workflows, registry, and source tree. The Python modules under `src/gems83/` are historical/local utilities; they are not the named shared evaluator or writer.
- Exact-name GitHub API/code searches in the owner organization did not find the required shared files; the sibling checkout also lacked the canonical cache/tools. Do not replace them with a private fork.
- The current Pages workflow uploads the reviewed `docs/` directory. The landing page, executive summary, static status feed, and run card are fail-closed and expose no TIFF/ZIP. Historical artifacts remain under `research/quarantine/` outside the Pages tree. The legacy feed helper was made static-only so it neither probes external sources nor publishes a second leaderboard feed.
- Three small owner-mirrored audit rasters were restored locally. The sample-grid mirror is 3,730 × 3,292, float32, EPSG:32611; its SHA-256 is `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc`. The feature stack is absent, and mirror hashes establish consistency with owner files—not organizer provenance.
- The owner sample has 5,167,373 finite cells, while legacy `grid.py` claims a 5,165,852-cell feature footprint from a missing receipt (1,521-cell difference). The mirror manifest also reports 60,988 template ones on mirrored fault labels. Official package semantics were not checked; this is logged as `IR-83-GRID-01` and blocks template validation.
- The full canonical registry rasters are absent. Previous H83-B evidence checked a small subset and used a different binary-correlation method; it does not satisfy the requested rank-correlation and final-dot overlap gates.

## H32-A prior-art correction and new candidate register

The initial cross-physics phase-displacement idea was withdrawn after code review. Local H32-A already uses gravity/magnetic cross-strike odd/even profile asymmetry and down-dip back-projection, with surface corroboration. Calling a phase-offset variant novel would be misleading.

The revised four-candidate list is in [`docs/hypotheses.html`](../docs/hypotheses.html) and [`docs/research/h83-hypotheses.md`](../docs/research/h83-hypotheses.md). Candidate 1 is cross-frequency wavelet phase coupling, but its relation to the supplied xscale/worm-persistence and other scale/orientation methods is an unresolved duplication risk. The saddle/topology idea overlaps basement-step and tip families; InSAR overlaps broad geodetic-strain work; radiometric alteration has obvious prior art. A focal-mechanism candidate was removed because H33-E already proposes raw seismicity with nodal-plane strikes. The ranking describes qualitative potential and cost only; it is not a score forecast, and no idea is authorized because the lane is unassigned. Exact layer names and indices are provisional until checked against the missing canonical metadata.

## Why the user-reported 0.2778 may have performed well

The user-supplied `0.2778` for GEMSDOE32 H33-2-B2 is **USER-REPORTED, not ORGANIZER-CONFIRMED**. At pinned upstream owner-repository commit `f62038b54dcb7767d4d997f80b033cdc3d42bef9`, the matching manifest names the GeoTIFF and SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, but says `UNSCORED` and has `receipt: null`. A later organizer score is possible; there is no receipt tying it to these bytes in the material reviewed.

The owner’s H33-2-B2 method starts with an owner-reported 0.2708 base claim containing 40,199 dots (USER-REPORTED, NOT ORGANIZER-CONFIRMED; no receipt ties that base value to its bytes), deletes the 2,545 dots within 2 pixels/200 m of the mapped catalogue, and leaves 37,654. The owner’s custom LM-calibrated proxy changes from 0.2630509876 to 0.2679205316 (difference +0.0048695440, positive in all four quadrants). This is **OWNER-REPORTED PROXY METRIC — NOT a `HOLDOUT-DTI` and not a score** under this project’s protocol. The owner live-anchor output 0.2746731598 is a **projection, not a score**.

Conditional mechanism: if the organizer scoring mask excludes existing-fault pixels as the owner code claims, predictions spent on the masked catalogue may add false-positive penalty without earning credit there. A moderate catalogue-flank prune could then improve precision-weighted credit by removing low-expected-value prediction mass while retaining unseen-fault coverage. That is a plausible metric mechanism, not proof of causality, new geology, or the 0.2778 attribution; the official scorer was not fetched.

The separate owner-local proxy value 0.4412792647 for `R2-safe-zeroTPp` rounds to the user-supplied current maximum 0.4413. This is a numerical coincidence/provenance warning, not evidence that the custom proxy is a public leaderboard score. The user also supplied a conflicting 0.3195 current maximum; the live official leaderboard was not fetched. These results and labels are recorded in the [research review](../docs/research.html), [score page](../docs/leaderboard.html), run card, and [`evidence/upstream/GEMSDOE32_owner_evidence_receipt.json`](../evidence/upstream/GEMSDOE32_owner_evidence_receipt.json).

## Evidence and result labels

- This run’s `HOLDOUT-DTI`: **not run**. Evaluator version, withheld-positive count, score, and CI are null. The required feature-only leakage canaries are not run.
- This run’s duplicate checks: **not run**. Surface rank-correlation and final-dot 3-pixel overlap fields are null; uniqueness is false/unverified.
- This run’s output validator: **not run; no candidate**. No current raster SHA, submission name, or note exists.
- `ORGANIZER-CONFIRMED`: **none**. No submission-page receipt was supplied or retrieved.
- The archived H83-B zeros TIFF passes only an independent format audit against an owner-mirrored template; its NaN-outside twin fails strict full-grid finite/range checks. The hashes in both receipts were cross-checked against the actual quarantined bytes. Format validity is not readiness.
- `docs/data/status.json` is a static project snapshot, not a live leaderboard feed.
- Official/USGS/GDR/NLR/PDF/Copernicus/EPSG/GitHub Pages source URLs are preserved for manual review. They were not fetched from this sandbox. GitHub owner-source evidence was fetched through the allowed GitHub API and remains explicitly non-organizer evidence.

## Three review passes completed for this revision

1. **Implement supported work:** reconciled public site and README to a blocked state; quarantined old TIFFs and local pipeline scripts; added a ranked, conditional hypothesis record; preserved owner evidence and source hashes; published score, source, status, and irregularity registers; kept the required negative JSON card.
2. **Review bugs and assumptions:** corrected the overlapping H32-A phase-displacement idea; removed focal mechanisms from the candidate list after finding H33-E prior art; audited H33-2-B2 against the pinned owner code, proxy, manifest, and receipt field; labelled all owner proxy/projection/user-reported values; hash-checked archived TIFF receipts; disabled legacy external feed probes; fixed the ignore rule that hid published static data; repaired stale test paths and local links.
3. **Recheck the full requirements:** confirmed the lane is still unassigned; no canonical tools/data/full registry exist; logged the unresolved grid-mask mismatch; fixed the root-data ignore so the static status/source/score feeds are tracked; no experiment, holdout, TIFF, slot, or submission was invented; nulls remain null; published site contains no TIFF/ZIP and says NOT READY. Ran Python compilation, 22 tests, the site checker (83 local links), JSON/CSV and Markdown-link checks, `git diff --check`, and a no-network-probe check successfully. Pytest reported 25 Rasterio `PendingDeprecationWarning`s; no test failures.

## Remaining work, in order

1. Supply/locate the assigned method paragraph and canonical shared template, feature cache, holdout evaluator, writer, and full registry. These are blocking inputs; do not infer the lane or substitute local tools.
2. Verify official data/provenance and exact feature metadata. Do not bypass the data login gate or claim owner mirrors are organizer files.
3. Inspect the canonical evaluator for whole-segment buffered hide/recover, fold-local catalogue features, exact visible-fault masking, pooled DTI α=0.2/β=0.8/300 m triangular kernel, and its CI method. Test each feature alone; resolve any AUC >0.90 alarm.
4. Only if the assigned lane authorizes a candidate, run the spatially blocked holdout and compare to a same-instrument incumbent. Then perform both surface and final-dot full-registry duplicate checks. Stop at 3 experiments or 2 hours; do not select a weekly slot.
5. Generate with the shared writer only after scientific/uniqueness gates pass; reopen and validate final bytes against the official template. Enable one download only when the full run card is submission-ready, and record the organizer receipt before labelling any score ORGANIZER-CONFIRMED.
6. Open a PR from the fixed Arena branch only after local verification; merge only after required checks pass. No PR/merge is claimed by this review unless an explicit PR number and merge result are recorded.

**No human visual inspection substitutes for automated validation.** A mapped-fault holdout, even when valid, remains a screening proxy for hidden organizer faults, not proof of a geothermal discovery or a private leaderboard gain.
