# Quarantined historical H83-B artifacts — DO NOT SUBMIT

These files and scripts were present in the checkout but the published readiness state contradicted them. They have been moved out of `docs/` so GitHub Pages cannot offer them as submission downloads. They are preserved for audit and education only; do not run their builder or treat their receipts as current validation.

## Independent format-only audit in this session

The reference was the local `data/sample_submission.tif` restored from an owner-supplied GitHub mirror whose hash matches the local manifest. The mirror is **not organizer-authenticated**. `scripts/validate_artifact.py` re-opened the archived files and reported:

- `gemsdoe83-h83b-dilational-jog-aug-b2-40000-20261004T220000Z-c48ac2b3-zeros.tif`: `format_valid: true`; SHA-256 `e731b16b2811ff6c0b581742acbd4b7a18858b8a83d5b4f2e4031967bc735a5`. This is format-only, not scientifically validated, not compared against the complete canonical registry, not authorized for submission, and not proven unique.
- The matching `-nan.tif`: `format_valid: false`; SHA-256 `4379f3ea044a27c69b0a17c6887f1d260debe47caaf874921266ad1390d82789`. It has NaN outside the footprint, so the strict whole-raster range check fails.
- The `.zip` contains one GeoTIFF but inherits no scientific or submission-readiness status.

Receipts are in `evidence/format-audit-*.json`. The old run card, build receipts, holdout output, hypotheses, and local scripts are kept alongside the TIFFs so their assumptions can be reviewed. The old cross-registry check sampled only a few rasters and used binary Pearson correlation; that is not the specified full-registry rank-correlation audit. The prior holdout/writer implementation is not the named canonical shared tool. The old `H83-B` claims are therefore not accepted as `HOLDOUT-DTI` for this session.

The `zeros` TIFF is deliberately not linked from the published site. The `format_valid` result does **not** mean “OK to submit.”
