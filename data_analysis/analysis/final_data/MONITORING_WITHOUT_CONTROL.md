# Why Monitoring Improves but Performance Does Not — Literature Memo

Working memo for the paper's discussion section. The finding to explain: interventions improved
metacognitive monitoring (estimation error g = −0.46/−0.65; discrimination g = +0.50/+0.28) but
not task performance (directional BF₀₊ = 11–58 against any improvement; `RESULTS.md` §11.1).

Reference list is split into **verified** (link checked Aug 2026) and **from memory** (verify in
Zotero before citing).

---

## 1. The framework: monitoring and control are separable stages

The canonical metacognition model (Nelson & Narens, 1990) splits the meta-level into
**monitoring** (assessing one's own performance) and **control** (using that assessment to change
behavior). Koriat & Goldsmith (1996) formalized the chain: monitoring → control → performance —
performance gains require *both* accurate monitoring *and* an effective control policy. Fleming &
Lau (2014) add the orthogonal distinction between metacognitive **bias** (overall
confidence level) and **sensitivity** (does confidence track correctness trial by trial).

**Where our interventions act:** almost entirely on *bias/global calibration* (self-estimates
drop 1.6–1.9 items; ΔConf rises), while *sensitivity* stays near chance (AUC2 0.52 → 0.57;
perceived-percentile slope on actual percentile ≈ 0 in every condition, `RESULTS.md` §11.4).
A participant whose global self-assessment improves but who cannot tell *which* item is wrong has
no signal to act on — the monitoring→control chain is broken at the hand-off, not at monitoring.

## 2. Five candidate explanations, mapped to evidence

### 2.1 Monitoring gains don't include a control policy (education literature)

Training studies in learning contexts repeatedly improve monitoring accuracy without automatic
performance transfer; performance moves only when the improved monitoring is coupled to a usable
control action (restudy selection, answer change). Dunlosky & Rawson (2012) show the causal path
runs through control quality; Thiede, Anderson & Therriault (2003) improved comprehension only
when better monitoring redirected restudy. A meta-analysis of calibration interventions
(Gutierrez de Blume, 2021, *Calibrating Calibration*) finds monitoring-accuracy gains are
reliable while performance transfer is inconsistent. **Our design offers exactly one control
action — overriding the AI's suggestion — and no intervention taught or scaffolded *when/how* to
override.** Prediction for follow-up: interventions coupled to an explicit control prompt
("your confidence is low — which statement contradicts the brief?") should convert.

### 2.2 Verification asymmetry: knowing the AI may be wrong ≠ knowing the answer

Fok & Weld (2024) argue AI assistance yields complementary performance only when the human can
**verify** the AI's output; explanations and warnings fail when verification is harder than the
task itself. Our 12 problems are high-information planning vignettes — verifying requires
re-reading and integrating the full brief, i.e. doing the task. A participant who correctly senses
"this answer may be wrong" still holds no better alternative, so the rational move is to submit
the AI's answer anyway. This also explains the easy/hard asymmetry (verification is feasible on
easy items only; cf. Sträter et al., MuC 2024) and the circularity concern: when overriding is
infeasible, participants inherit the AI's psychometric properties — consistent with our 2PL
result that item responses barely reflect a person-level trait (all discriminations a < 1).

### 2.3 Deferring stays cheaper: effort economics and automation bias

Cognitive-effort research shows people avoid demanding strategies when a low-effort option exists
(Kool et al., 2010; Shenhav et al., 2017). The automation literature has the direct analogue:
**automation bias/complacency rises with workload** (Mosier & Skitka, 1998; Parasuraman &
Manzey, 2010). All four interventions *raised* NASA-TLX (up to g = +1.21) without lowering the
cost of independent verification — they made the task more effortful while deferral remained the
cheapest exit. Buçinca, Malaya & Gajos (2021) found the same trade-off for cognitive forcing
functions: less overreliance, worse subjective experience, and benefits concentrated in
low-Need-for-Cognition users. Gajos & Mamykina (2022) show people extract the answer, not the
understanding, unless forced.

### 2.4 Global recalibration without local discrimination (measurement-level account)

The interventions deliver *summary* information (a reliability card per task, two divergent
answers) that rationally lowers the prior on "the AI is right" — a global belief update — but adds
little *item-specific* evidence. That is precisely the pattern we measure: large bias shifts,
minimal sensitivity gains (§1). On Rahnev's (2025) taxonomy our design can detect this
dissociation but cannot estimate efficiency (12 trials, no SDT structure) — a follow-up with
~100 verifiable trials (e.g. the Ravens-matrices paradigm) could test whether sensitivity is
trainable where verification is possible.

### 2.5 Motivation: Prolific participants have no stake in overriding

Control is agenda-driven (Ariel, Dunlosky & Bailey, 2009): participants regulate toward their
goals, and a flat-paid crowdworker's goal is completion, not accuracy. Consistent signals in our
data: reflection word count does not predict outcomes (`RESULTS.md` §10.10), prompts/task is
flat (~12) across conditions, and time-on-task helps only at baseline (§10.12). Counter-signal:
participants *did* engage (median 973 reflection words; dwell rose 50–70% under pause/reflection),
so pure satisficing can't be the whole story. An accuracy-bonus arm would separate ability from
motivation.

### 2.6 (Sharpest framing) Deference can be rational — then monitoring *shouldn't* change behavior

If a participant believes the AI is at least as accurate as themselves on hard items (they're
right: AI-alone estimates ≈ their own with-AI scores), then deferring even while sensing possible
error is Bayes-rational (cf. algorithm appreciation, Logg, Minson & Moore, 2019). The
interventions changed *beliefs about* the AI (trust drops, perceived AI superiority stops
inflating — §10.5) without changing the *competence ratio* that makes deference optimal. Under
this account the null on performance is not a failure of the interventions but the rational
response to unchanged incentives — and the paper's contribution is showing that metacognition and
reliance behavior are separately addressable targets.

## 3. Positioning against the closest recent work

- The mirror-image result: "AI makes you smarter but none the wiser" (2025 preprint) reports
  performance gains without metacognitive gains; we show the complementary dissociation, which
  together argue monitoring and performance are **independently manipulable** in human-AI settings.
- The performance–metacognition dissociation is emerging as a named phenomenon in the
  human-AI literature (e.g. arXiv 2602.01959; PNAS Nexus metacognitive-sensitivity account of
  trust calibration, 2025) — our study contributes the first (to our knowledge) five-condition
  experimental test showing interventions move monitoring while leaving joint performance fixed.
- Bansal et al. (2021) and Green & Chen (2019) established that explanations/assistance rarely
  produce complementary performance; we extend this from *explanations* to *metacognitive
  interventions*.

## 4. Verified sources

- Buçinca, Malaya & Gajos (2021), CSCW — [doi:10.1145/3449287](https://dl.acm.org/doi/10.1145/3449287), [arXiv:2102.09692](https://arxiv.org/abs/2102.09692)
- Fok & Weld (2024), *AI Magazine* — [doi:10.1002/aaai.12182](https://onlinelibrary.wiley.com/doi/abs/10.1002/aaai.12182), [arXiv:2305.07722](https://arxiv.org/abs/2305.07722)
- Gutierrez de Blume (2021), *J. Educ. Psychol.* meta-analysis — [ResearchGate](https://www.researchgate.net/publication/349179781_Calibrating_Calibration_A_Meta-Analysis_of_Learning_Strategy_Instruction_Interventions_to_Improve_Metacognitive_Monitoring_Accuracy)
- Feature-based explanations reduce overreliance on easy but not hard decisions — MuC 2024, [doi:10.1145/3670653.3670660](https://dl.acm.org/doi/10.1145/3670653.3670660)
- Metacognitive sensitivity & trust calibration — *PNAS Nexus* 2025, [pgaf133](https://academic.oup.com/pnasnexus/article/4/5/pgaf133/8118889)
- AI metacognitive sensitivity improves AI-assisted decisions — [arXiv:2507.22365](https://arxiv.org/pdf/2507.22365)
- Performance–metacognition dissociation in entangled human-AI interaction — [arXiv:2602.01959](https://arxiv.org/pdf/2602.01959)
- "AI makes you smarter but none the wiser" — [ResearchGate preprint](https://www.researchgate.net/publication/396391750_AI_makes_you_smarter_but_none_the_wiser_The_disconnect_between_performance_and_metacognition)

## 5. From-memory sources — verify before citing

Nelson & Narens (1990, *Psych. Learn. Motiv.*); Koriat & Goldsmith (1996, *Psych. Review*);
Fleming & Lau (2014, *Front. Hum. Neurosci.*); Dunlosky & Rawson (2012, *Learn. Instr.*);
Thiede, Anderson & Therriault (2003, *J. Educ. Psychol.*); Ariel, Dunlosky & Bailey (2009,
*JEP: General*); Kool, McGuire, Rosen & Botvinick (2010, *JEP: General*); Shenhav et al. (2017,
*Annu. Rev. Neurosci.*); Mosier & Skitka (1998); Parasuraman & Manzey (2010, *Human Factors*);
Logg, Minson & Moore (2019, *OBHDP*); Gajos & Mamykina (2022, IUI); Bansal et al. (2021, CHI);
Green & Chen (2019, CSCW); Rahnev (2025, *Nat. Commun.*, already in `METHODS.md` §6).
