# Research and repository review — 2026-10-21

## What was actually verified

| Finding | Evidence | Confidence / limitation |
|---|---|---|
| Starting checkout contained README only | initial tree at commit `805ee1cc0225d3447dcf10f5adf2c39f0f792a81` | local fact; no previous pipeline existed here |
| Official reference uses U-Net with Monte Carlo patch splits and Tversky loss | [organizer reference notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb) | source read through GitHub API; training loss is not the required DTI evaluator |
| CPU training is supported | [official README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) | contradicts prompt's claim that GPU is required; GPU accelerates training |
| Mirrors exist for features, faults, template | [upstream manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/f62038b54dcb7767d4d997f80b033cdc3d42bef9/registry/data_manifest.json), local data receipt | small rasters restored and hashes verified; features located, not downloaded |
| Mirrored labels and existing faults are byte-identical | `evidence/data_receipt.json` | not independent hidden truth; holdout cannot validate against a second target inferred from these filenames |
| Mirrored template contains NaN outside its valid mask | `evidence/grid_audit.json` | template values are not predictions; copying it is unacceptable |
| H33-B2 is a catalogue-flank pruning family | [upstream implementation](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/f62038b54dcb7767d4d997f80b033cdc3d42bef9/src/gems32/hypotheses33.py#L304) and `evidence/upstream/evidence__h33_validation.json` | upstream source/evidence, not independently rerun |
| The required shared tools are absent | repository tree | similar upstream tools are not proof of protocol compliance; no private replacement created |

## Why might H33-B2 have helped?

The user reports H33-B2 at **0.2778 (USER-REPORTED; not ORGANIZER-CONFIRMED)**.
The upstream H33 validation record describes pruning a prior dot field near mapped faults.
A plausible mechanism is removing redundant predictions that use prediction mass without
recovering hidden faults. DTI rewards distance-tolerant coverage, not visual line density.
For the usual Tversky expression T/(T + aF + bN), removing false-positive mass while holding
true-positive credit and false-negative mass fixed strictly improves the ratio. That is a
conditional mathematical explanation, **not a causal attribution of the organizer result**.
Sparsity can also reduce recoverable credit; more pruning is not automatically better.

The upstream validation includes live-anchor inversions, SGMC truth and prevalence-calibrated
surrogates. These are not the user's stipulated pure hide-and-recover experiment. They are
not accepted as this run's HOLDOUT-DTI, and their projections are not reproduced as scores.
The supplied competing leaderboard maxima disagree. No current maximum is confirmed here.
There is no defensible numerical prediction that this checkout can beat the user-reported
result. It is scientifically possible, but untested. Winning needs better evidence and
placement, not a copied file with a different filename or random jitter.

## Candidate hypotheses — preregistration ideas, NOT assigned lanes

Ranking is qualitative expert judgment, not a score forecast. All differ from this initial
empty checkout; novelty across every sibling site has **not** been established. Prior work
already includes drainage alignment, oriented multiphysics consensus, radiometric fusion,
Radon structure and basement steps; these are not claimed as new here. No experiments are run
until the lane is resolved. Cached band availability/semantics must be verified in the shared
feature receipt before implementation. No proposal below depends on a new external source.

| Rank | Candidate and specific cached layers | Physical signature and off-catalogue rationale (hypothesis) | Non-fault mimic | Difference and expected benefit / cost |
|---|---|---|---|---|
| First | Cross-contact magnetic phase displacement; RTP/TMI, isostatic gravity | Detect lateral displacement of a continuous magnetic contact across a separate gravity edge using opposite-side phase correlation, not just co-located edge strength. A buried displacement may lack a visible scarp and be missing from a mapped catalogue. | Intrusive contact geometry or survey stitching | New candidate object is a displaced matched contact pair; not H33's local orientation vote. Highest expected benefit among these ideas, uncertain; medium-high CPU/implementation cost. |
| Second | Along-strike alternating flexure; detrended elevation and basement-depth surface | Localize repeated signed curvature reversals along an inferred boundary, testing whether surface flexure and basement flexure are phase-consistent. Could identify distributed buried deformation outside a mapped trace. | Differential compaction in sedimentary basins | Signed cross-field phase, not a basement gradient maximum or simple step. Moderate expected benefit, high cost; interpolated basement resolution may make it non-identifiable. |
| Third | Cross-strike radiometric asymmetry residual; K/Th/U with detrended elevation | Compare paired flanks of magnetic contacts after relief-matched background subtraction; test asymmetric multi-element alteration rather than raw anomaly brightness. A concealed fluid barrier might alter one flank without a scarp. | Lithologic contact or weathering gradient | Paired-flank residual hypothesis, not pixel fusion. Moderate-low expected benefit, medium cost; requires cached radiometric product and provenance confirmation. |
| Fourth | Scale-dependent termination scattering; RTP/TMI and gravity | Find magnetic ridge terminations that face coherent longer-wavelength gravity continuity, using graph endpoint pairing and scale-specific discordance. Could expose fault-truncated units under cover. | Finite lava flows or intrusive bodies | Graph truncation/continuity discordance, not generic line persistence or catalogue tip continuation. Low/uncertain expected benefit, high cost. |

These are testable hypotheses, not verified geological claims. Without feature canaries,
segment holdout, registry checks and budget-matched controls, none is viable for promotion.
No third-party data acquisition is proposed as necessary. The USGS and GDR links in the
brief are discovery entry points only, not independently fetched scientific evidence here.
The sandbox allows only GitHub and package-registry hosts; DrivenData, USGS, GDR, Dropbox
and PDF-host live access is unavailable. Official reference code was accessible on GitHub.
We did not turn mirror provenance into a claim of official-file authenticity.

## Three passes and remaining work

**Pass one:** inspected checkout; read upstream source and official reference notebook; recovered
and hash-checked the three small mirrored files; added format audit, tests, status site and CI.
No geological experiment was started; lane assignment is absent.

**Pass two:** tested NaN/infinity, hidden nodata sentinels, masked missing values, wrong grid,
wrong band count/shape and empty footprint. Rejected silent clipping. Replaced nonstandard
JSON NaN metadata with a string. Ensured format validity never grants submission readiness.

**Pass three:** checked source classes and all local website links; verified no TIFF is advertised
and run card stays negative; ran CI-equivalent tests. Documented that the full user prompt
is not archived verbatim, only the operating requirements. This is a remaining request, not
something claimed completed. Requirements for a unique TIFF, full shared-registry audit,
three-to-five verified-novel hypotheses, holdout superiority and live feed remain unmet.

### Ordered continuation

1. Supply/discover the session's assigned method paragraph and canonical template/registry;
   this is required context, not a request for manual raster inspection or passwords.
2. Reuse upstream restore tooling after verifying canonical paths; restore features and verify
   official data provenance. Do not train on the template's values.
3. Audit the shared evaluator for fold-local catalogue feature rebuilding, segment/buffer hiding,
   exact visible-pixel masks and pooled triangular-kernel sufficient statistics. Fix only upstream.
4. Run each feature alone on the held-out segments with a prespecified negative sampling domain;
   investigate every leakage alarm. Paired block/segment bootstrap for confidence intervals.
5. Run at most the allowed experiments within the assigned lane; beat the same-instrument
   incumbent; compare surface and dots with the complete registry. Undefined rank correlations
   or missing registry entries must block, not pass.
6. Write via shared writer, re-open and format-audit, publish unique filename/hash and note,
   download button and automated eligibility result. Selector handles weekly quota separately.

No human intervention is proposed as a substitute for missing automated validation.
No claim of line-by-line verification of inaccessible official pages is made.

### Source irregularity requiring care

The upstream H33-2 docstring describes a catalogue “masked halo.” Pixel-exact visible-fault
masking does not imply an entire buffer is unscored or that every nearby dot earns no credit:
a nearby hidden segment could still receive distance credit. We do **not** adopt that docstring
as an official metric fact. This is why the conditional false-positive pruning explanation above
is weaker than a claim of a proven mechanism. Verify the official scorer before transferring
its optimization assumptions.
