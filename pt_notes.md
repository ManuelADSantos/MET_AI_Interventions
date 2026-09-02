# Progress notes — MET-AI Interventions

Newest first. One entry per working day.

---

## 2026-09-02

**New analyses**
- **LLM-competence split** (`RESULTS.md` §11.7, `llm_competence_analysis.py`): classified each
  of 12 items as AI-correct (baseline modal answer matches correct answer, 5 items) or AI-wrong
  (7 items). Condition × AI-competence interaction χ²(4) = 25.7, p < .001, driven by pause points
  (b = −0.45): its deficit falls on AI-correct items (g = −0.65) not AI-wrong (g = −0.23).
  Reliability/alternatives/reflection show uniform effects across item types (|b| ≤ 0.22).
  Key finding: no intervention improves accuracy on AI-wrong items — direct evidence for the
  verification-asymmetry account (Fok & Weld 2024).
- **Item difficulty distribution figure** (`notebook_analysis_output/item_difficulty_llm_competence.png`):
  two-panel plot — (A) per-item accuracy by condition sorted by baseline difficulty, background
  shaded by AI-competence classification; (B) per-item intervention effect in percentage points.

**Documentation**
- `RESULTS.md` §11.7 added; paper strategy (§12) updated with LLM-competence finding and
  qualitative data status.
- `METHODS.md` §5 and §7 updated (new analysis row + reproduce command).
- `README.md` code index updated with `llm_competence_analysis.py`.

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
- **Qualitative coding** (`RESULTS.md` §11.6, `qualitative_coding.py`, codebook v2): lexical
  multi-label coding of 821 strategies + 645 manipulation answers. Blanket reliance highest at
  baseline (19% vs 4-14% in interventions, p < .001); 39% of alternatives participants adopted
  cross-checking the two replies as their strategy — adopted strategies did not convert to
  accuracy. Verification mostly routes back through the AI itself (4-15%) or stays unspecified;
  independent checking against the scenario stays rare (low-reliability code, flagged).
  Manipulation self-reports match the quantitative signatures (reliability -> vigilance + trust
  drop, pause -> friction 23%, reflection -> "no change" 24%).
- **Codebook validation** (`validation/`, two rounds, blind annotation by the analyst LLM):
  dev sample n = 160 against v1 exposed recall gaps (strategies Jaccard .50) -> v2 fixed rules,
  retired selective-reliance. Fresh held-out sample n = 120 scored once against v2:
  **strategies Jaccard .65 (exact 55%), manipulation .76 (exact 75%), macro-F1 .70**.
  Publication-grade codes (F1 >= .7): more careful .90, reasoning check .86, no change .82,
  effort/time .80, full reliance .74, manipulation use .73. Low-reliability (flagged † in
  §11.6): verify-against-source .40, unspecified double-checking .53, trust codes,
  slowed/friction. Prevalences are lower bounds (34%/53% uncoded).

**Commits**: 72318ca, afa6f38, 720179b, c2a3060 (parallel), d2c5953, 51200bb, ed4e73d, f97b52d,
87746a8, 6e5827f.

**Open (not doable from this repo)**
- Overleaf paper writing — next check-in **Wednesday**.
- CHI submission (Kai) + inform Paul; fallback: extended abstract/poster.
- Precision Conference profile: DBLP → "N/A", link ORCID.
- Replicae core materials: self-fidelity/replication-score section update.
- For publication-grade IRR, have a human coder annotate
  `data_analysis/analysis/final_data/validation/holdout_sample_key.csv` and score with
  `validation/score_validation.py` (LLM-annotator validation done: held-out Jaccard .65/.76,
  macro-F1 .70; codebook v2).
