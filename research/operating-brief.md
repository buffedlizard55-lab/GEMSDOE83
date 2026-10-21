# Starting brief — condensed from the supplied user prompt

This is a requirements digest, not a verbatim transcript. Read it and README before work.

- Review the repository and prior-session work first. Create a unique GeoTIFF, never a copied
  old submission. Make download and submit readiness obvious at the beginning of the website.
- Stay in the single assigned method lane. Stop and log duplicate if surface rank correlation
  exceeds 0.90 or more than 70% of dots are within 3 px of registry dots. Check before and after placement.
- Reuse cached features and the shared `evaluate_holdout.py` and `submission_writer.py`. Do not fork
  a broken shared tool: fix it in the template once and report the change.
- Holdout: hide whole fault segments with a buffer; compute every catalogue-derived feature
  from visible faults only; mask visible faults pixel-exactly; pooled DTI, alpha 0.2, beta 0.8,
  triangular kernel of radius 300 m. Run every feature alone; AUC above 0.90 is a leakage alarm.
- Generate and rank three to five candidate geological hypotheses before implementation. Name
  layers, physical transform, off-catalogue rationale, novelty, confounder and cost. Verify
  availability of any new official free data before calling an idea viable.
- At most three experiments or two hours. A candidate must beat the current same-instrument
  holdout best before a separate selector may promote it to a weekly slot.
- Label actual results HOLDOUT-DTI (version, positives, 95% CI) or ORGANIZER-CONFIRMED
  (submission-page receipt). Never pass a projection off as a score.
- End with one JSON run card: hypothesis, mechanism, non-fault mimic, holdout and CI,
  registry correlation/overlap, raster hash, validator, submission name, short note, verdict.
  A negative is a deliverable, and missing measurements must remain null, not zero.
- Range must be [0,1], finite inside the footprint, single-band TIFF, exact template CRS,
  shape and transform. Provide a unique name, note no longer than 140 characters, and an
  executive-summary subpage explaining submission. No inspection-only claim of readiness.
- Use official verified sources, auditable tables and manual-review links. Flag contradictions
  and access limitations. No fabricated data, scores, geological discoveries, or assurances.
- Clean GitHub Pages UI. Three passes: implement/test; review edge cases/fix;
  check against all original requirements. Open and merge a pull request.
- Keep Maximize P(Win) and Own the Outcome central. Focus on fault mapping that can inform
  geothermal exploration, not claims that the model has directly discovered geothermal vents.

## User-supplied source entry points (not all reachable/verified)

- https://www.drivendata.org/competitions/306/competition-doe-gems/
- https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- https://github.com/drivendataorg/gems-prize-reference-solution
- https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- https://gbcge.org/current-projects/ingenious/
- https://epsg.io/32611
- https://en.wikipedia.org/wiki/Tversky_index
- https://docs.nlr.gov/docs/fy26osti/96647.pdf
- https://gdr.openei.org/submissions/1391

The supplied sibling-site score list is a user-report, not a set of organizer receipts.
An upstream historical version is preserved in `evidence/upstream/docs__score-ledger.csv`;
it is not the full, current user-prompt list. Conflicting supplied leaderboard values cannot
all be described as current. No leaderboard maximum has been independently confirmed.
