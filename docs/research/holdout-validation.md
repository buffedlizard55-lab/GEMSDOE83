# Holdout-validation status

**Disposition: NOT RUN.** No current candidate has an accepted `HOLDOUT-DTI` result.

The protocol requires the canonical shared evaluator, cached feature stack, and authorized input rasters. This checkout has none of the named shared assets. The local `src/gems83/holdout.py` and related scripts are historical project-local code; they are not accepted as substitutes. Their old receipts have been moved to [`research/quarantine/prior-h83b/`](../../research/quarantine/prior-h83b/), outside the published site.

The owner-mirrored sample grid has 5,167,373 finite cells; legacy local code claims a 5,165,852-cell feature footprint from a missing receipt, and the manifest notes 60,988 template ones coincident with mirrored fault labels. This 1,521-cell discrepancy and value-semantics conflict remain unresolved because the official template/package was not accessed. See [`IR-83-GRID-01`](../irregularities.html#ir-83-grid-01).

| Required evidence | Status | Why |
|---|---|---|
| Assigned method lane | **BLOCKED** | The single method paragraph is absent from the supplied prompt/context. |
| Whole-segment buffered hide-and-recover | **NOT RUN** | Canonical evaluator and feature stack are missing. |
| Fold-local catalogue-derived features and exact visible-pixel mask | **NOT VERIFIED** | No canonical evaluator available for inspection/run. |
| Pooled α=0.2, β=0.8, 300 m triangular-kernel DTI | **NOT RUN** | No accepted evaluator execution. |
| Feature-only leakage canary | **NOT RUN** | No feature stack or holdout evaluator. |
| 95% CI and withheld-positive count | **NULL / NOT MEASURED** | No accepted experiment. |
| Same-instrument incumbent comparison | **NOT AVAILABLE** | No accepted current baseline on this evaluator. |
| Surface rank-correlation vs full registry | **NOT RUN** | Registry rasters are missing. |
| Final-dot 3-pixel overlap vs full registry | **NOT RUN** | Registry rasters are missing and no candidate is authorized. |
| New candidate TIFF | **NOT GENERATED** | Generating one without the required lane/evidence would violate the protocol. |
| Weekly submission slots | **0 used** | No submission was made or selected. |

A previous H83-B local run card reported multiple model/proxy quantities, but they are quarantined and not accepted as this session’s `HOLDOUT-DTI`. In particular, a historical format pass is not a holdout result or uniqueness audit. See the current [run card](../run-card.json) for null-valued fields and blockers.
