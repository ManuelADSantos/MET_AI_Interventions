# A Design Space of Metacognition Interventions in Human-AI Interaction
*Deep-research synthesis — June 2026. Sources: psychology, HCI (CHI/IUI/CSCW/FAccT/AIES), learning sciences, and commercial products. All claims verified against primary sources unless marked [UNVERIFIED].*

---

## Part A — How to build the design space (CHI best practices)

### Derivation methods used by exemplary CHI design-space papers
| Method | Exemplar | How |
|---|---|---|
| Morphological/parametric analysis | Card, Mackinlay & Robertson, *TOIS* 1991 ([dl.acm.org/10.1145/123078.128726](https://dl.acm.org/doi/10.1145/123078.128726)) | Zwicky-style decomposition into parameters + composition operators |
| Systematic corpus review + iterative coding | Rasmussen et al. CHI 2012 (shape-change); Bae et al. CHI 2022 (47 physicalizations, [arXiv:2202.10520](https://arxiv.org/abs/2202.10520)); Lee et al. CHI 2024 (115 papers on writing assistants, [arXiv:2403.14117](https://arxiv.org/pdf/2403.14117)) | Code corpus into aspects → dimensions → codes; most common modern method |
| User/expert elicitation | Wobbrock et al. CHI 2009 (gesture elicitation, n=20); Liao et al. CHI 2020 (XAI Question Bank, 20 practitioner interviews, [arXiv:2001.02478](https://arxiv.org/pdf/2001.02478)) | Bottom-up generation, then taxonomize |
| Subsumption of prior taxonomies | Schulz et al. TVCG 2013 (visualization tasks) | Show prior frameworks map into the space |

**Best practice = combine corpus review with expert elicitation** (the Liao 2020 pattern matches your Study 1 design: literature-derived structure + ~10–20 expert interviews; n=10 is defensible via information power, Malterud et al. 2016, [doi](https://journals.sagepub.com/doi/full/10.1177/1049732315617444), and the CHI modal sample of 12, Caine CHI 2016, [doi](https://dl.acm.org/doi/10.1145/2858036.2858498)).

### Validation methods observed (pick ≥2)
1. **Coverage/classification test**: place every corpus item in the space; report placement reliability (Pousman & Stasko AVI 2006; Bae 2022 public gallery).
2. **Generate-and-test / generativity**: point to unpopulated promising regions; generate a new intervention from the space (Card et al. 1991's "better than the mouse" argument).
3. **Expert validation**: practitioners judge usefulness/completeness (Liao 2020).
4. **Consensus metrics**: agreement scores / multi-coder IRR (Wobbrock 2009; Lee 2024).
5. **Cross-Consistency Assessment**: pairwise check of dimension-value combinations for incoherent cells (Ritchey, [swemorph.com/pdf/gma.pdf](https://www.swemorph.com/pdf/gma.pdf)) — the formal orthogonality check.
6. **Behavioral validation** (your Study 2): rare; would exceed current practice.

Contribution typing (Wobbrock & Kientz 2016, [doi](https://dl.acm.org/doi/10.1145/2907069)): design space = **theoretical** contribution, blended with **survey** (corpus) and **empirical** (Study 2).

---

## Part B — The design space

### Dimensions (refined against the evidence; reduced to 5)

The evidence forced two additions to the candidate dimensions: (1) **"object of metacognition"** must be its own dimension — interventions targeting the user's model of *themselves* (self-confidence calibration; Ma et al. CHI 2024) are empirically distinct from those targeting the user's model of *the AI* (AI-literacy tutorials; He et al. CHI 2023) and of the *joint decision*; (2) Tankelevitch et al.'s two opportunity classes become a **direction** dimension (boost user metacognition vs. reduce metacognitive demand).

It also forced three reductions (parsimony per the CCA, Part E Step 3): *initiative* and *bindingness* collapse into one **user-control** axis (their cross-cells are incoherent: user-triggered × mandatory cannot exist; system-triggered × optional ≈ default-bypassable); *granularity* is derivable from timing (pre-interaction training is inherently session/program-level; pre-advice and in-interaction are inherently trial-level) and is dropped; *adaptivity* has exactly one verified occupant (FLoRA) and becomes a cross-cutting modifier applicable to any cell rather than a dimension.

| # | Dimension | Values |
|---|---|---|
| D1 | **Metacognitive target** | planning / monitoring / evaluation |
| D2 | **Object** | self (own cognition) / AI (model of the AI's competence) / joint output–decision |
| D3 | **Timing** | pre-interaction (training, planning) / pre-advice (before AI output shown) / in-interaction / post-interaction (feedback, delayed probe) |
| D4 | **User control** | mandatory / default-on, bypassable / opt-in (user-invoked) |
| D5 | **Direction** | boost user metacognition / reduce metacognitive demand (offload to interface) |

*Cross-cutting modifier:* adaptivity (static vs. state-/trace-triggered delivery) — applicable to any cell; currently near-empty in HAI (gap 3, Part C).

*Note on cluster tables below:* codings are written as target / object / timing / initiative / bindingness; read the last two slots together as D4 user control (system+mandatory → mandatory; system+default → default-bypassable; user+optional → opt-in).

### Populated design space
Provenance: **[L-HCI]** HCI literature, **[L-PSY]** psychology, **[L-EDU]** learning sciences, **[P]** product practice. Coding: D1 target / D2 object / D3 timing / D4 initiative / D5 bindingness.

#### Cluster 1 — Forcing & friction (boost; system; trial)
| Intervention | Source + evidence | Coding |
|---|---|---|
| Decide-first (independent decision before AI advice) | Buçinca et al. CSCW 2021 ([doi](https://dl.acm.org/doi/10.1145/3449287)): reduced overreliance > XAI; disliked; benefits skew to high Need-for-Cognition. Psych root: suspending own judgment changes advice weighting (Yaniv & Choshen-Hillel 2012) [L-HCI, L-PSY] | eval / joint / pre-advice / system / mandatory |
| Wait / slow AI (response delay) | Buçinca 2021; Park et al. CSCW 2019: slower algorithm → better reliance discrimination [L-HCI] | monit / AI / in / system / mandatory |
| On-demand AI (default = unaided) | Buçinca 2021 [L-HCI] | monit / self / in / user / optional |
| Selective frictions (extra click + expertise reminder) | Collins et al. 2024, NeurIPS-BML workshop, non-archival ([arXiv:2407.12804](https://arxiv.org/abs/2407.12804)): reduced click-through, but spillover to no-friction topics [L-HCI] | monit / self / pre-advice / system / default-bypassable |
| Partial explanations (user completes the reasoning) | CSCW 2025 ([doi](https://dl.acm.org/doi/10.1145/3710946)): reduced overreliance [L-HCI] | eval / joint / in / system / mandatory |

#### Cluster 2 — Prompting & questioning (boost; system; trial-session)
| Intervention | Source + evidence | Coding |
|---|---|---|
| AI-framed questioning (Socratic, evidence-as-question) | Danry et al. CHI 2023 ([doi](https://dl.acm.org/doi/10.1145/3544548.3580672)): beat causal explanations on discernment accuracy [L-HCI] | eval / joint / in / system / mandatory |
| Metacognitive prompts in GenAI search (pause, consider alternatives) | Singh et al. ASIS&T 2025 ([doi](https://asistdl.onlinelibrary.wiley.com/doi/10.1002/pra2.1287)): deeper querying; moderated by metacognitive flexibility [L-HCI] | monit+plan / self / in / system / optional |
| Devil's advocate / provocations | Chiang et al. IUI 2024 ([doi](https://dl.acm.org/doi/10.1145/3640543.3645199)): deeper group deliberation. Drosos & Sarkar 2025, preprint only ([arXiv:2501.17247](https://arxiv.org/abs/2501.17247)) [L-HCI] | eval / joint / in-post / system / optional |
| Self-explanation prompts ("explain the AI's answer before accepting") | Psych base: g=0.55 meta-analytic (Bisra et al. 2018, [doi](https://link.springer.com/article/10.1007/s10648-018-9434-x)); ITS base: Aleven & Koedinger 2002 [L-PSY, L-EDU] | monit / joint / in / system / mandatory |
| Consider-the-opposite ("one reason the AI might be wrong") | Koriat et al. 1980 ([pdf](https://iipdm.haifa.ac.il/images/publications/Asher_Koriat/1980-Koriat-Lichtenstein-Fischhoff-JEPHLM.pdf)): contradicting reasons improved calibration, supporting reasons did nothing; Lord et al. 1984. Cheap; fragile in exact replication [L-PSY] | eval / joint / pre-decision / system / mandatory |
| ExtendAI (AI feedback extends user's own written rationale) | CHI 2025 ([doi](https://dl.acm.org/doi/10.1145/3706598.3713295)): better integration, slightly better decisions vs. RecommendAI [L-HCI] | plan+eval / self / pre+in / mixed / mandatory |
| Premortem ("assume the AI-assisted plan failed — why?") | Klein 2007 HBR; Veinott et al. 2010: ~2× overconfidence reduction vs. pro/con [effect size thin] [L-PSY] | plan / joint / pre / system / optional |

#### Cluster 3 — Confidence elicitation & calibration feedback (boost; self)
| Intervention | Source + evidence | Coding |
|---|---|---|
| Self-confidence calibration: Think (justify before confidence) + Feedback (accuracy feedback on past confidence) | Ma et al. CHI 2024 ([doi](https://dl.acm.org/doi/10.1145/3613904.3642671)): both calibrated self-confidence → more rational reliance; Think demanding/disliked [L-HCI] | monit / self / pre+post / system / mandatory |
| Calibration feedback loops | Lichtenstein & Fischhoff 1980: gains mostly after first feedback round, weak transfer; Martin 2025 null for scoring-rule feedback ([doi](https://onlinelibrary.wiley.com/doi/full/10.1002/ffo2.199)) [L-PSY] | eval / self / post / system / n.a. |
| Performance vs. environmental feedback dissociation | Stone & Opel 2000: performance feedback fixes calibration, environmental feedback fixes discrimination — match feedback to deficit [L-PSY] | eval vs monit / self / post / system / n.a. |
| Confidence self-rating per item (spaced repetition apps) | Brainscape 1–5 confidence rating drives scheduling ([brainscape.com](https://www.brainscape.com/academy/brainscape-vs-anki/)); Anki ease buttons [P] | monit / self / post / system / mandatory |
| Prediction/postdiction practice | Bare practice fails (Bol et al.); structured guidelines + group setting works (Bol et al. 2012, [doi](https://www.sciencedirect.com/science/article/abs/pii/S0361476X12000094)) [L-EDU] | monit / self / pre+post / system / optional |
| Delayed confidence probe | Delayed-JOL effect, Nelson & Dunlosky 1991: extremely robust monitoring-accuracy gain; retrospective > prospective confidence (Siedlecka et al. 2016) [L-PSY] | monit / self / post(delayed) / system / n.a. |

#### Cluster 4 — Communicating AI uncertainty & provenance (reduce demand; AI/joint)
| Intervention | Source + evidence | Coding |
|---|---|---|
| Calibrated confidence scores | Zhang, Liao & Bellamy FAT* 2020 ([doi](https://dl.acm.org/doi/10.1145/3351095.3372852)): improved trust calibration, NOT joint accuracy [L-HCI] | monit / AI / in / system / default |
| Frequency-format uncertainty + decide-first interaction | Cao, Liu & Huang CSCW 2024 ([doi](https://dl.acm.org/doi/10.1145/3637318)): frequency format helps reliance, reduces confirmation bias [L-HCI] | monit / AI / pre-advice+in / system / default |
| First-person verbal hedges ("I'm not sure, but...") | Kim et al. FAccT 2024 ([doi](https://dl.acm.org/doi/10.1145/3630106.3658941)): reduced overreliance on wrong answers; wording matters [L-HCI] | monit / AI / in / system / default |
| Inline citations as verification scaffold | Perplexity; NotebookLM grounding to user's own sources ([support](https://support.google.com/notebooklm/answer/16164461)) [P] | eval / joint / post / system-provided, user-exercised / optional |
| Double-check button (search-verify highlights) | Gemini "double-check response" ([support](https://support.google.com/gemini/answer/14143489)); availability unstable [P] | eval / joint / post / user / optional |
| Visible reasoning (extended thinking) | Anthropic visible extended thinking, Feb 2025 ([anthropic.com](https://www.anthropic.com/news/visible-extended-thinking)) [P] | eval / AI / in / system / default |
| Code provenance (matched-source links, no confidence) | GitHub Copilot code referencing ([docs](https://docs.github.com/en/copilot/concepts/completions/code-referencing)) [P] | eval / joint / post / system / default |
| Explanations as verification-cost reducers | Vasconcelos et al. CSCW 2023 ([doi](https://dl.acm.org/doi/10.1145/3579605)): explanations cut overreliance only when they lower verification cost — cost-benefit moderator for the whole cluster [L-HCI] | eval / joint / in / system / default |

#### Cluster 5 — Training & literacy (boost; pre-interaction; session-longitudinal)
| Intervention | Source + evidence | Coding |
|---|---|---|
| AI-fallibility tutorial (reveals AI's and own miscalibration) | He, Kuiper & Gadiraju CHI 2023 ([doi](https://dl.acm.org/doi/10.1145/3544548.3581025)): partially mitigated Dunning-Kruger under-reliance [L-HCI] | monit / AI+self / pre / system / optional |
| Debugging-the-AI pretask | He et al. HT 2024 ([doi](https://dl.acm.org/doi/10.1145/3648188.3675130)): **backfired** — induced under-reliance. Key null [L-HCI] | monit / AI / pre / system / mandatory |
| Probabilistic-reasoning training (~1h) | Mellers et al. 2014 ([doi](https://journals.sagepub.com/doi/10.1177/0956797614524255)): durable Brier improvement over years; strongest-evidence training on the list [L-PSY] | plan+eval / self / pre / system / optional |
| SRL strategy instruction | Meta-analyses d≈0.6–0.7, durable (de Boer et al. 2018) [L-EDU] | all / self / pre+in / system / program |
| Skill training itself improves self-assessment | Kruger & Dunning 1999 study 4; incentives do NOT (Ehrlinger et al. 2008, [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2702783/)) [L-PSY] | eval / self / pre / n.a. / n.a. |

#### Cluster 6 — Externalization & dashboards (mixed direction; session)
| Intervention | Source + evidence | Coding |
|---|---|---|
| Open learner models (system's model of user made inspectable) | Bull & Kay SMILI, IJAIED 2016; viewing improves knowledge monitoring (Brusilovsky et al. 2020, [RPTEL](https://telrp.springeropen.com/articles/10.1186/s41039-020-00137-5)) [L-EDU] | monit / self / in-post / user / optional |
| Dual-view OLM (self-assessment shown next to system model) | Bull SMILI studies — direct calibration display [L-EDU] | monit / self / post / user / optional |
| Teacher/manager dashboards (other-regulation) | Khanmigo teacher dashboard ([khanmigo.ai/teachers](https://www.khanmigo.ai/teachers)) [P]; caveat: dashboard benefit correlates with existing metacognitive awareness — Matthew effect (Chen et al. 2023) [L-EDU] | monit / other / post / user / optional |
| Sensemaking tools for LLM outputs at scale | Gero et al. CHI 2024 ([doi](https://dl.acm.org/doi/10.1145/3613904.3642139)) [L-HCI] | eval / joint / post / user / optional |

#### Cluster 7 — Integrated tutor modes (boost; opt-in modes; session)
| Intervention | Source + evidence | Coding |
|---|---|---|
| Answer-withholding Socratic modes | ChatGPT Study Mode (July 2025, [openai.com](https://openai.com/index/chatgpt-study-mode/)); Gemini Guided Learning (Aug 2025); Claude Learning Mode (April 2025); Khanmigo. ALL opt-in and trivially bypassable; no peer-reviewed efficacy evidence for any of them as of June 2026 [P] | monit+eval / self / in / system within user-chosen mode / opt-in, bypassable |
| Guardrailed GenAI tutor (hints, withheld solutions) | Bastani et al. PNAS 2025 ([doi](https://www.pnas.org/doi/10.1073/pnas.2422633122)): vanilla ChatGPT → −17% on unassisted exam; guardrails eliminated the harm [L-EDU] | monit / self / in / system / mandatory (within tool) |
| Adaptive trace-triggered SRL scaffolds | FLoRA engine, LAK 2025 ([doi](https://dl.acm.org/doi/full/10.1145/3706468.3706559)): GPT-4o scaffolds from real-time trace analytics — the only verified ADAPTIVE metacognitive intervention found [L-EDU] | all / self / in / system / adaptive |
| Plan review before agentic execution | Gemini/ChatGPT Deep Research editable plans + clarifying questions ([gemini.google](https://gemini.google/overview/deep-research/)) [P] | plan / joint / pre / mixed / default |
| Pre-writing intent elicitation | Khan Academy Writing Coach: clarify assignment → thesis → evidence before drafting ([khanmigo.ai/writingcoach](https://www.khanmigo.ai/writingcoach)) [P] | plan / self / pre / system / mandatory (within tool) |

#### Negative/cautionary entries (what absence of intervention does)
- Unscaffolded LLM access suppresses monitoring/evaluation actions — "metacognitive laziness" (Fan et al. BJET 2025, [doi](https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13544)); −17% unassisted-exam effect (Bastani PNAS 2025).
- Higher confidence in AI → less critical thinking; higher self-confidence → more (Lee et al. CHI 2025, survey of 319 knowledge workers, [doi](https://dl.acm.org/doi/10.1145/3706598.3713778)) — direct support for the self-confidence object (D2).
- Market erosion of friction: Copilot Workspace editable plans sunset (May 2025); Tesla removed lane-change confirmation — user control (D4) drifts toward opt-in unless value is demonstrated.

---

## Part C — Gaps (underpopulated regions)

1. **Planning × pre-interaction is the emptiest populated-by-research region.** Products have it (deep-research plan review, Writing Coach); HCI research has almost no controlled tests of planning-stage metacognitive support. Psych offers ready transfers: premortem, reference-class forecasting, GJP-style training.
2. **Object = self is almost absent from products.** No major chatbot elicits user confidence or gives calibration feedback; the only commercial confidence-rating UIs are flashcard apps. Research shows it works (Ma et al. CHI 2024) — a research-to-product gap your paper can name.
3. **Adaptivity is nearly unexplored in HAI.** Only ed-tech (FLoRA) triggers metacognitive support from behavioral traces. No CHI/IUI study adapts intervention delivery to the user's metacognitive state. (Connects to MET-AI's adaptive-interface agenda.)
4. **Post-interaction & longitudinal cells are thin**: almost everything is trial-level and immediate; delayed probes (delayed-JOL — extremely robust in psych) and longitudinal calibration feedback are untested in HAI.
5. **Bindingness is confounded with effectiveness**: effective interventions are mandatory and disliked (Buçinca; Ma's Think); products converge on opt-in bypassable modes with zero efficacy evidence. The effectiveness × acceptability × bindingness trade-off is an open empirical question — strong Study 2 candidate.
6. **Group/team object barely populated** (Chiang et al. devil's advocate only).
7. **Known backfires cluster at object = AI, timing = pre** (debugging pretask; environmental feedback raising overconfidence) — the space predicts where backfires live, which is itself a generativity argument.

## Part D — Implications for Study 2 sampling
- The headline contrast (interventions equivalent under reliance taxonomies, different in this space) is directly available: e.g., decide-first vs. consider-the-opposite vs. confidence-elicitation — all "cognitive forcing" under Buçinca's umbrella, but differing on D1 (eval/monit), D2 (joint/self), D3 (pre-advice/pre-decision/post).
- Strongest psych transfers not yet tested in HAI: consider-the-opposite, delayed confidence probe, premortem — high-novelty, low-implementation-cost conditions.
- Include one bindingness contrast (mandatory vs. bypassable version of the same intervention) to speak to the product-erosion problem.

---

## Part E — Construction & validation protocol (executing the CHI best practices)

How each best practice from Part A becomes a concrete step in the paper:

**Step 1 — Corpus assembly (survey-contribution rigor, Lee et al. 2024 pattern).** Three provenance streams: (a) structured literature search across CHI/IUI/CSCW/FAccT/AIES + psychology + learning sciences (the entries above are the seed corpus, ~45 interventions); (b) product audit with dated, official-source evidence; (c) 10 expert interviews. Report stream sizes and overlap (convergence statistic).

**Step 2 — Dimension derivation (codebook TA, aspect→dimension→code hierarchy).** Open-code interventions on mechanism, then iterate dimensions with the constraint that every value set is exhaustive and values within a dimension are mutually exclusive. Document the iteration (Halskov & Lundqvist: design spaces are constructed, not discovered — show the construction).

**Step 3 — Cross-Consistency Assessment (Zwicky/Ritchey).** Pairwise-check dimension values; declare incoherent cells rather than leaving them as "gaps," and use CCA to MERGE dimensions whose cross-cells are degenerate. This is what reduced the space from 8 to 5 dimensions: initiative × bindingness had incoherent cells (user-triggered × mandatory) and redundant ones (system × optional ≈ default-bypassable), so they collapse into one user-control axis; granularity was fully predictable from timing; adaptivity had a single occupant and became a modifier. Remaining near-incoherence to declare: *reduce-demand × object=self* (D5×D2) is occupied only by OLM dashboards. Distinguishing incoherent cells from genuine gaps is what makes the gap analysis (Part C) credible — and the documented reduction itself demonstrates methodological rigor to reviewers.

**Step 4 — Coverage test (Pousman & Stasko pattern).** Two coders independently place all corpus interventions on all 8 dimensions; report placement agreement (IRR) per dimension. Dimensions with chance-level agreement get revised or dropped — this is the internal validation of D1–D8.

**Step 5 — Discriminative power.** Show the space separates interventions that existing taxonomies merge: the Cluster-1/2/3 entries are all "cognitive forcing functions" in the reliance literature but occupy distinct cells here (the headline argument). Conversely show subsumption (Schulz pattern): Tankelevitch's two opportunity classes = D8; Buçinca's forcing functions = D5 mandatory × D3 in/pre-advice; Lai et al.'s assistance elements map onto Cluster 4.

**Step 6 — Generativity demonstration (Card et al. generate-and-test).** Generate novel interventions from underpopulated cells — concrete examples derived from this space:
  1. *Delayed calibration digest* (D3 post-delayed × D2 self — empty cell): end-of-week summary in a chatbot showing the user's stated confidence vs. verified outcomes across the week's AI-assisted decisions. Transfers the delayed-JOL effect (most robust monitoring intervention in psychology) to HAI; no product or paper does this.
  2. *Premortem before agentic delegation* (D1 planning × D3 pre × D2 joint — research-empty): before launching an AI agent on a long task, the interface asks "assume the result turns out unusable — what went wrong?" and turns answers into checkpoints. Transfers Klein's premortem to the automation-strategy demand Tankelevitch identifies.
  3. *Adaptive consider-the-opposite* (adaptivity modifier × D1 eval — empty in HAI): trigger "name one reason this might be wrong" only when behavioral traces show fast, uncritical acceptance (response time below the user's deliberation baseline). Combines Koriat et al. 1980 with FLoRA-style trace triggering; addresses the acceptability problem by intervening rarely.
  4. *Bypassable decide-first* (D4 user-control contrast on a proven intervention): decide-first with a visible "skip" — tests whether effectiveness survives the loss of bindingness the market will impose anyway.

**Step 7 — Behavioral validation (Study 2; beyond current practice).** Sample experiment conditions along single-dimension contrasts (Part D); the space's dimensions are supported where cells predict outcome differences. This exceeds what any verified design-space paper has done (none ran a controlled experiment on their dimensions) — claim it as such, citing the validation-method review in Part A.

**Figure 1 recommendation:** the 5-dimension space as a morphological chart with the ~45 corpus interventions plotted and the 4 generated interventions marked in empty cells — simultaneously the coverage test, gap map, and generativity demo in one figure (Bae et al. gallery pattern). Five dimensions also make the chart actually drawable on one CHI page; the 8-dimension version would not have been.
