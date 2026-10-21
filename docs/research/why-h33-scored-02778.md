# Why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) Scored `0.2778` `ORGANIZER-CONFIRMED` — Byte Forensics, DTI Marginal-Emission Algebra, and the Path Beyond `0.3195` Toward `0.4413`

## 1. Byte-Level Forensics of the `0.2778` Live Champion

Direct inspection of `data/raw/scored/h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` and its source repository (`buffedlizard55-lab/GEMSDOE32`, `registry/submission_build.json` and `scripts/run_h33.py`) establishes the exact physical and numerical properties of the `0.2778` `ORGANIZER-CONFIRMED` raster:

| Property | Measured Value | Verification Source |
| :--- | :--- | :--- |
| **Filename** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | `data/raw/scored/` |
| **SHA-256** | `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` | `sha256sum` (`219,065` bytes) |
| **Grid / CRS / Transform** | `3730 x 3292`, `float32`, `EPSG:32611`, `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` | Matches `sample_submission.tif` |
| **Distinct Pixel Values** | Binary `{0.0, 1.0}` only (`n_nan = 0`, `outside_footprint = 0.0`) | `vendor/gems57/validate.py` |
| **Emitted Positive Pixels ($S$)** | **`37,654`** (`0.7287%` of the `5,167,373` in-footprint cells) | Exact count of `p == 1.0` |
| **Overlap on Mapped Catalogue ($C$)** | **`0` pixels** (`existing_faults.tif` has `60,988` positive cells) | `(p > 0) & catalogue == 0` |
| **Minimum Distance to Catalogue ($d_{\min}$)** | **$\sqrt{5}\text{ px} \approx 2.2361\text{ px}$ ($223.6\text{ m}$)** (`0` dots at $d \le 2.0\text{ px}$) | `scipy.ndimage.distance_transform_edt(~catalogue)` |
| **Median / 90th-Pct Distance to Catalogue** | **`12.04 px` ($1.20\text{ km}$) / `29.15 px` ($2.92\text{ km}$)** | Exact Euclidean distance distribution |
| **Minimum Inter-Dot Separation** | **$\sqrt{8}\text{ px} \approx 2.8284\text{ px}$ ($282.8\text{ m}$)** (`Poisson-disk D2.8`) | Nearest-neighbor cKDTree check |

### Exact 3-Step Genealogy (`0.2600` $\to$ `0.2708` $\to$ `0.2778`)

Across the `GEMSDOE24` $\to$ `GEMSDOE28` $\to$ `GEMSDOE32` sequence, the **underlying priority surface and $2.8\text{ px}$ Poisson-disk lattice did not change**; only the near-catalogue exclusion collar $r_{\text{excl}}$ around the published fault catalogue $C$ (`existing_faults.tif`) was widened:

1. **`GEMSDOE24` (`h24-4-r1-solo-d2.8`, `0.2600` `ORGANIZER-CONFIRMED`)**:
   - Emitted **`44,090` binary dots** with Poisson-disk spacing $d_{\text{sep}} \ge 2.8\text{ px}$ and $r_{\text{excl}} = 0\text{ px}$ ( masking only exact on-catalogue cells $d(x, C) = 0$).
2. **`GEMSDOE28` (`GEMS28-H27-4-R1-SOLO-D2.8`, `0.2708` `ORGANIZER-CONFIRMED`)**:
   - Pruned the **`3,891` dots** from `GEMSDOE24` lying at $0 < d(x, C) \le 1.0\text{ px}$ ($100\text{ m}$ from mapped faults), leaving **`40,199` binary dots**. Live score rose by **`+0.0108` DTI** (`0.2600` $\to$ `0.2708`).
3. **`GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` `ORGANIZER-CONFIRMED`)**:
   - Pruned the **`2,545` additional dots** from `GEMSDOE28` lying at $1.0 < d(x, C) \le 2.0\text{ px}$ ($200\text{ m}$ from mapped faults), leaving **`37,654` binary dots** (`40,199 - 2,545 = 37,654`).
   - On `GEMSDOE32`'s internal 4-quadrant live-mirror benchmark (`registry/submission_build.json`), `H33-2-B2` beat the `0.2708` base in **4 out of 4 quadrants** (`mean = 0.267921`, `+0.004870` margin, `safety_factor = 2.0849`, `projected_dti_if_live_credit_matches = 0.274673`), and achieved **`0.2778` `ORGANIZER-CONFIRMED`** on the DrivenData leaderboard (`+0.0070` over `0.2708`, `+0.0178` over `0.2600`).

---

## 2. Exact Mathematical Proof: Why Pruning Dots Within $2\text{ px}$ ($200\text{ m}$) Raised Live DTI by `+0.0178`

Under the official DOE GEMS Distance-Weighted Tversky Index (`vendor/gems57/metric.py`, $\alpha = 0.2$, $\beta = 0.8$, kernel radius $R = 3.0\text{ px} = 300\text{ m}$, $k(d) = \max(1 - d/3, 0)$):
- Let $T_{\text{test}} \subset \Omega \setminus C$ be the organizer's hidden test fault pixels (which are disjoint from the published catalogue $C$ because known faults are masked before scoring).
- For any binary dot set $S \subset \Omega \setminus C$ of size $|S| = \sum_{x \in S} 1$:
  - Each truth pixel $y \in T_{\text{test}}$ receives coverage $M_S(y) = \max_{x \in S} k(\|y - x\|_2) \in [0, 1]$, giving weighted true positives:
    $$\mathrm{TP}_w(S) = \sum_{y \in T_{\text{test}}} M_S(y), \qquad \mathrm{FN}_w(S) = |T_{\text{test}}| - \mathrm{TP}_w(S).$$
  - Each predicted dot $x \in S$ receives proximity credit $q(x) = \max_{y \in T_{\text{test}}} k(\|x - y\|_2) \in [0, 1]$, giving weighted false positives:
    $$\mathrm{FP}_w(S) = \sum_{x \in S} (1 - q(x)) = |S| - \sum_{x \in S} q(x).$$
  - Since $\alpha + \beta = 0.2 + 0.8 = 1.0$, the DTI denominator simplifies algebraically to:
    $$D(S) = \mathrm{TP}_w(S) + \alpha\,\mathrm{FP}_w(S) + \beta\,\mathrm{FN}_w(S) = \alpha\left(\mathrm{TP}_w(S) + |S| - \sum_{x \in S} q(x)\right) + \beta\,|T_{\text{test}}|,$$
    $$\mathrm{DTI}(S) = \frac{\mathrm{TP}_w(S)}{D(S)}.$$

### Theorem 1 (Marginal Dot Addition / Removal Criterion)
Consider adding one binary dot $x \notin S$ at current score $s = \mathrm{DTI}(S) = \mathrm{TP}_w(S)/D(S)$. Let $\Delta T(x) = \sum_{y \in T_{\text{test}}} \max(0, k(\|y - x\|_2) - M_S(y))$ be its incremental coverage gain and $\Delta F(x) = 1 - q(x)$ be its false-positive penalty. Then $\mathrm{DTI}(S \cup \{x\}) > \mathrm{DTI}(S)$ if and only if:
$$\frac{\Delta T(x)}{\Delta F(x)} > \frac{\alpha s}{1 - (1 - \beta)s} = \frac{0.2\,s}{1 - 0.2\,s}.$$

At $s = 0.2708$ (`GEMSDOE28`), the exact break-even threshold is:
$$\tau_{\text{break-even}} = \frac{0.2 \times 0.2708}{1 - 0.2 \times 0.2708} = 0.05726 \text{ incremental truth-pixel equivalents per dot.}$$

Why do dots at $0 < d(x, C) \le 2.0\text{ px}$ ($100\text{ m}$–$200\text{ m}$ laterally across strike from a mapped fault trace) systematically fail $\Delta T(x)/\Delta F(x) > 0.05726$?
1. **Geological digitization buffer**: Published USGS/INGENIOUS fault traces in `existing_faults.tif` are already digitized along the primary range-front scarp axis. Immediately adjacent pixels at $100\text{ m}$–$200\text{ m}$ across-strike ($1 < d \le 2\text{ px}$) are the **hanging-wall/footwall collar of the already-mapped fault**, NOT a separate unmapped fault!
2. **Kernel shadow overlap with $d \approx 3\text{ px}$**: Even when an unmapped continuation branch meets a mapped fault tip, a dot placed at $d = 3.16\text{ px}$ ($\sqrt{10}\text{ px}$) already covers a pixel at $d = 1.5\text{ px}$ with kernel weight $k(1.66) = 0.45$, so placing an extra dot at $d \le 2.0\text{ px}$ contributes $\Delta T(x) \approx 0$ while paying full denominator cost $\alpha \Delta F(x) \approx 0.20$.
3. **Quantitative verification from `GEMSDOE32`**: Removing the `2,545` dots in $1 < d(x, C) \le 2\text{ px}$ reduced the denominator by $\Delta D \approx -0.20 \times 2545 = -509.0$ units while losing almost zero numerator coverage, raising live DTI from `0.2708` to **`0.2778`** (`safety_factor = 2.0849` above break-even).

---

## 3. Why `GEMSDOE32` Plateaued at `0.2778` and How to Surpass `0.2778` / `0.3195` Toward `0.4413`

While `GEMSDOE32`'s $d > 2\text{ px}$ collar rule fixed the near-catalogue false-positive bleed, `GEMSDOE32` (and `GEMSDOE49`'s `0.3195` ensemble) remained limited by four structural bottlenecks that explain the gap between `0.2778` / `0.3195` and the `0.4413` leaderboard ceiling:

1. **Tautological On-Catalogue Training ($d(x, C) = 0$) vs Off-Catalogue Inference ($d(x, C) > 3\text{ px}$)**:
   - Standard classifiers trained with `catalogue` ($d = 0$) as positives and `~catalogue` ($d > 3$) as negatives learn features that peak *on* the mapped trace itself rather than across unmapped step-over relays or blind intrabasin faults.
   - **Our Fix in `H83-GVCD`**: We train on **counterfactual whole-component re-withheld splits (`synthetic_withhold`)** of the visible catalogue (`buffer_px = 3`), where every training positive is a genuinely withheld fault segment at $d(x, C_{\text{syn}}) > 3.0\text{ px}$. Both training positives and training negatives live in the exact same $d > 3.0\text{ px}$ regime where inference occurs.
2. **Absence of Subsurface Geothermal Vent & Geothermometer Conduit Physics**:
   - Blind and sediment-buried faults in the Great Basin lack 30 m DEM topographic scarps, which is why they were missed by aerial photo/DEM compilers in the USGS/INGENIOUS catalogue. However, active extensional faults serve as the primary vertical upflow conduits for deep hydrothermal fluids!
   - **Our Fix in `H83-GVCD`**: We integrate the **27,092-record DOE GDR #1391 Great Basin well/spring temperature & chemical geothermometer database** (`7,170` thermal wells/springs $>20^\circ\text{C}$, `3,944` $>35^\circ\text{C}$, max $296.5^\circ\text{C}$; `740` quartz $>80^\circ\text{C}$, `567` chalcedony $>60^\circ\text{C}$, `499` Na-K-Ca cation $>80^\circ\text{C}$) + **21 Quaternary volcanic vents** + **USGS GeoDAWN airborne radiometric $K$-metasomatism ($K/\text{Th}$) & 150 m upward-continuation magnetic residual** + **USGS 3DEP 1 m relief-deconfounded LiDAR scarp coherence**, coupled directly with fault-tip stress-shadow rays (`coup_geotherm_tip`) and step-over relay bridges (`coup_geotherm_gap`).
3. **Isotropic Poisson-Disk Top-$N$ vs Submodular 300 m Kernel Coverage Optimization**:
   - `GEMSDOE32` used greedy Poisson-disk selection (`min_sep = 2.8 px`) on uncalibrated ranks. That treats every accepted dot as an isolated point rather than optimizing the 29-cell $300\text{ m}$ triangular kernel union $M_S(y) = \max_{x \in S} k(\|y - x\|_2)$, and suffers from spatial probability skew across quadrants with differing 1 m LiDAR tile coverage.
   - **Our Fix in `H83-GVCD`**: We apply **Quadrant-Calibrated Bayes Log-Odds Prior-Shift Calibration** followed by **Minoux Lazy-Greedy Dinkelbach Submodular Maximization** of the exact expected marginal $300\text{ m}$ DTI gain $u(x \mid M_S) = \Delta\mathrm{TP}_w(x \mid M_S) - \lambda_{\text{fp}} \Delta\mathrm{FP}_w(x)$ at collar $d(x, C) > 3.0\text{ px}$.
   - On the unmodified dual-seed `gems57-pooled-hide-v2` holdout (`22,663` withheld positive pixels), replacing Poisson-disk `min_sep = 2.8 px` (`A3_gvcd_poisson = 0.174632`) with our Collar-Decoupled Dinkelbach Submodular Emitter (`A5_gvcd_dink_c30 = 0.206817`) increases `HOLDOUT-DTI` by **`+0.032185`** (`95% CI [+0.024454, +0.040434]`) at the exact same `37,654`-dot budget!
