# Progress notes — MET-AI Interventions

Newest first. One entry per working day.

---

## 2026-08-25

**Data verification**
- SUS scoring audited against the standard Brooke procedure (10 items after dropping the
  attention check at position 8, alternating v−1 / 5−v, sum × 2.5): recomputed from raw JSONs for
  all 925 participants, **0 mismatches** across all five computation sites.

**New analyses (meeting action items → `RESULTS.md` §11, code in
`data_analysis/analysis/final_data/followup_analyses.py` + independent replication
`meeting_analyses.py`)**
- **Temporal**: accuracy flat across all 12 positions in every condition; halves/thirds null;
  excluding trial 1 changes every g by ≤ 0.017. Learning/fatigue/first-trial artifacts ruled out.
- **Easy vs hard × condition**: significant interaction (χ²(4) = 24.6, p < .001) carried entirely
  by pause points — its deficit concentrates on easy items (easy g = −0.65, hard g = −0.17).
  Updates the meeting's "no differential effect" read.
- **Dunning–Kruger section**: classic pattern in all five conditions; shape not modulated by
  condition; perceived-percentile slope ≈ 0 everywhere (global monitoring uninformative);
  artifact checks (linear, homoscedastic) → phrase as regression + better-than-average, not an
  ability-specific deficit.
- **Mixed models**: condition effects on confidence/accuracy survive difficulty + position + NFC
  controls; reliability cards' deflation steepens with difficulty (−5.7 pp/SD); **NFC raises
  confidence (+3.3 pp/SD) with zero accuracy effect**.
- **Bayesian null**: improvement ruled out everywhere (BF₀₊ = 11–58). Strict equivalence only for
  reflection (BF₀₁ = 8.4, TOST |g| < .3); reliability/alternatives inconclusive (BF₀₁ ≈ 1); pause
  points a real deficit. Pause BF₀₊ numerical discrepancy between the two implementations resolved
  by high-precision quadrature: 58.2.
- **2PL IRT** (exploratory, not committed): all item discriminations < 1, 1PL adequate — item
  responses barely reflect a person-level trait, quantifying the "participants inherit the AI's
  psychometrics" circularity.
- **Scale correlations** (`RESULTS.md` §10.17): SUS/UEQ/Trust coupling and the
  scale-overconfidence link are strongest at baseline and attenuated by every intervention; no
  scale correlates with actual score anywhere.

**Documentation**
- `MONITORING_WITHOUT_CONTROL.md`: literature memo — six explanations for monitoring improving
  without performance, with verified anchors (Buçinca 2021; Fok & Weld 2024; calibration-training
  meta-analysis; PNAS Nexus 2025) and a to-verify list.
- `RESULTS.md` §12 **Paper strategy**: per-intervention claims table encoding the equivalence
  nuance (headline = "no intervention *improves* performance", not "performance unchanged");
  Limitations renumbered to §13.
- Verdict tables in `README.md` and `RESULTS.md` §1 now carry BF₀₊.
- Consolidated the parallel session's `MEETING_ANALYSES.md` into §11 (its numbers cross-validated
  mine; kept `meeting_analyses.py` as the replication script).

**Commits**: 72318ca, afa6f38, 720179b, c2a3060 (parallel), d2c5953, 51200bb, ed4e73d.

**Open (not doable from this repo)**
- Overleaf paper writing — next check-in **Wednesday**.
- CHI submission (Kai) + inform Paul; fallback: extended abstract/poster.
- Precision Conference profile: DBLP → "N/A", link ORCID.
- Replicae core materials: self-fidelity/replication-score section update.
- Qualitative coding of free-text responses (why participants didn't act on sensed AI errors).
