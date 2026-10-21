# QUARANTINED — DO NOT SUBMIT

These artifacts arrived from concurrent main commit
`1cdb07f` / merge `b57875f` while the audit PR was open. They are preserved, not endorsed.
Original HTML, README, code and run-card claims are historical **untrusted evidence**.
They are outside the Pages publishing directory. Do not execute the original generator to
publish files back under `docs/`.

The generator uses seeded random synthetic strands and random background fill. It does not
read basement depth, gravity or magnetic measurements. Its “footprint” is a random mask
adjusted to a prescribed pixel count, not the competition footprint. Matching the count
is not matching the geometry. No required holdout or registry comparisons are implemented
in that generator. Its advertised holdout intervals, feature AUC and uniqueness numbers
are not reproducible from the delivered code and are withdrawn as acceptance evidence.

The original validator ignores all NaN when checking the range; it never compares to the
real footprint, and its CLI does not return a failed validation exit code. This can mark
an invalid NaN candidate as OK. Use the independent audit instead.

See `evidence/concurrent-artifact-audit.json` for the measured format checks against the
hash-pinned mirrored template. Even an all-finite format-valid synthetic TIFF is **not**
a geologically validated or protocol-unique submission. No organizer receipt was supplied.
