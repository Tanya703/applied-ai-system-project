# Model Card: AI-Enhanced Music Recommender

## 1. Model Name  

MoodLense 2.0
---

## 2. Intended Use    

MoodLense 2.0 is a music recommendation system that combines a hand-crafted scoring engine with two Gemini-powered AI layers. It suggests songs from a 22-track catalog based on how a listener describes their mood in plain English — no structured inputs required. The system parses natural language into preferences, scores the catalog, and explains the results in plain English. This is a classroom simulation built to explore how heuristic scoring and LLM integration work together and where each breaks down.

---

## 3. How the Model Works  

The system has three layers working in sequence.

**Input — specialized prompting (`parse_user_input`)**
The user types a free-text description of how they are feeling. Gemini converts it into a structured profile with exact values for genre, mood, energy, and acousticness. A system prompt with five few-shot examples constrains Gemini to the exact vocabulary the scoring engine understands — this prevents the model from returning values the engine cannot use.

**Core engine — heuristic scoring (`recommender.py`)**
Each song is scored against the parsed profile using four dimensions. Mood and genre are not yes-or-no matches — similarity tables give partial credit for related categories (for example, "relaxed" scores 70% of full points when the target is "chill"). Energy is scored using a Gaussian curve so songs close to the target score nearly as high as an exact match. Acousticness is a straight percentage. The four scores are combined with fixed weights: mood 35%, genre 25%, energy 25%, acousticness 15%. Songs are selected greedily with an artist diversity penalty (decay = 0.5) so no single artist dominates the top-5.

**Output — RAG explanation (`explain_recommendations`)**
The ranked results are fed back to Gemini along with each song's catalog metadata — genre, mood, energy, acousticness, and match score. Because the real data is injected into the prompt before generation, Gemini's explanation is grounded in what the catalog actually contains rather than generic descriptions.

**Guardrails** catch bad LLM outputs before they reach the engine: mood and genre are validated against known vocabulary (unknown values fall back to safe defaults), energy is clamped to [0.0, 1.0], JSON parse errors are caught and shown as friendly messages, and markdown code fences are stripped before parsing.

---

## 4. Data  

The catalog contains 22 songs (20 unique titles, with LoRoom and Neon Echo each appearing in two variants) spanning 15 genres — lofi, pop, rock, ambient, jazz, synthwave, indie pop, soul, metal, country, electronic, r&b, folk, drum and bass, and classical — and 14 moods ranging from chill and serene to aggressive and tense. Songs were added beyond the original starter set to improve genre and mood coverage.

The catalog is intentionally small for a simulation, which creates some gaps. Most genres and moods have only one song each, so when a listener's first-choice genre has no good match, the fallback options are very limited. Energy levels also cluster at the quiet end and the loud end, leaving almost nothing for listeners who want something in the middle. Styles like reggae, hip-hop, blues, and Latin are completely absent, as are moods like nostalgic longing or quiet joy that sit between the defined categories.

---

## 5. Strengths  

The system works best for listeners with clear, well-represented preferences. When a listener's genre and mood both have good catalog coverage, the scoring feels natural and the top result is a good match. Across 11 test profiles, 8 achieved a rank-1 score above 0.85, indicating strong alignment for the majority of listener types.

The partial credit system for related moods and genres behaves sensibly in most cases. A lofi fan correctly gets ambient and jazz suggestions as runner-ups rather than something completely unrelated like metal.

The bell curve for energy means small differences near the target barely affect the score, which prevents the system from being overly harsh about songs that are close but not exact.

The diversity penalty meaningfully improves within-list variety. Genre diversity increases from 3.6 to 4.6 unique genres per top-5 list, and average max artist repeat drops from 2.2 to 1.0 when the penalty is active.

The natural language input layer makes the system accessible to real users — typing "I need something to wind down after work" works just as well as knowing the exact field values. The RAG explanation layer makes the reasoning transparent rather than just presenting a ranked list.

---

## 6. Limitations and Bias 

The system only knows four things about a listener — genre, mood, energy, and acoustic preference. It has no awareness of tempo, lyrics, language, listening history, time of day, or whether the listener wants something familiar or something new. Two songs can score identically and be nothing alike in practice.

Entire styles of music are missing from the catalog. Reggae, hip-hop, blues, Latin, and many others have no representation, so listeners whose taste lives in those areas will always get mismatched results. Even within represented genres, most have only one song, meaning the system runs out of good options quickly and fills the remaining slots with loosely related alternatives.

The acoustic preference is weighted at only 15%, which is not enough to override mood and energy when they point in a different direction. A listener who specifically wants acoustic music will often receive electronic-sounding recommendations because the other dimensions outweigh that preference.

The AI layer adds its own limitations. When Gemini returns a mood or genre outside the valid vocabulary, the guardrail substitutes a default ("chill" or "pop") — the system does not crash, but the substitution may not reflect what the user actually meant. The interactive mode has no conversation memory: each query is independent, so the system cannot refine recommendations based on feedback like "show me something heavier." The system also depends on the Gemini API being available and within quota.

---

## 7. Evaluation  

**Which user profiles you tested**
We tested three typical listeners — someone who likes calm lo-fi music, a pop fan who wants upbeat songs, and a rock fan who wants intense music. Then we created six "tricky" listeners on purpose: someone who wants sad music but at very high energy, someone who likes acoustic instruments but also wants high-energy songs, a metal fan who wants romantic music, and a few others where the preferences intentionally contradict each other or push the system to its limits.

**What you looked for in the recommendations**
We checked whether the songs the system suggested actually matched what each listener asked for — right genre, right mood, right energy level. We also checked whether the scores made sense: the #1 recommendation should score noticeably higher than #5, not just win by a tiny margin.

**What surprised you**
One song — Gym Hero — kept showing up for almost every listener, even ones who asked for completely different genres like metal or electronic. It won by being "good enough" at everything rather than perfect for anyone. We also found that when a listener's preferences conflicted (like wanting calm but high-energy), the system quietly ignored whichever preference carried less mathematical weight. A self-described metal fan received a classical music recommendation as their top result.

**Any simple tests or comparisons you ran**
We ran the program and manually counted how many times each song appeared across all nine top-five lists to spot which songs dominated. We also hand-calculated approximate scores for a few specific cases — like the Romantic Metalhead — to verify whether the numbers matched what the output showed.

The LLM layer is covered by 13 unit tests in `tests/test_llm.py` that mock the Gemini client. These verify guardrail fallbacks (unknown mood → "chill", unknown genre → "pop"), energy clamping (values outside [0.0, 1.0] are corrected), fence stripping, missing API key handling, and that song metadata is injected into the explanation prompt. No real API calls are made during testing.

**Quantitative Results**

| Metric                      | MoodLense 1.0 | Binary Baseline | No-Diversity | Random  |
|-----------------------------|:-------------:|:---------------:|:------------:|:-------:|
| Avg rank-1 score            | 0.86          | 0.85            | 0.86         | n/a*    |
| Avg rank-5 score            | 0.54          | 0.35            | 0.61         | n/a*    |
| Artist diversity (per list) | 5.0           | 4.7             | 3.8          | 4.4     |
| Genre diversity (per list)  | 4.6           | 4.3             | 3.6          | 4.5     |
| Personalization index       | 31%           | 35%             | 35%          | 38%     |
| Avg max artist repeat       | 1.0           | 1.3             | 2.2          | 1.5     |
| Domination index (top song) | 13%           | 13%             | 11%          | 9%      |
| Catalog coverage            | 77%           | 86%             | 86%          | 95%     |

*Random uses no scoring logic; picks are not preference-driven so MoodLense scores do not apply.

**Key Findings**

1. **Similarity tables shift positions 2–5, not rank-1.** Rank-1 agrees with Binary in 10/11 profiles — partial-credit tables almost never change who ranks first. The one exception is the "Romantic Metalhead": partial mood credit (romantic → serene) gives a classical song the edge over the expected metal pick, revealing that fixed weights can silently override a listener's stated genre preference.

2. **Tables improve filler quality, not top-pick quality.** Rank-1 average score: MoodLense 0.86 vs Binary 0.85 — near-identical. Rank-5 average score: MoodLense 0.54 vs Binary 0.35 — MoodLense is +0.19. The real value of partial credit is in the lower slots.

3. **Diversity penalty: what it fixes and what it costs.** Active in 7/11 profiles, the penalty raises average unique artists per list from 3.8 to 5.0 and unique genres from 3.6 to 4.6, and cuts max artist repeat from 2.2 to 1.0. The cost: rank-5 average score drops from 0.61 to 0.54, and personalization index falls from 35% to 31%.

4. **Catalog coverage trade-off.** MoodLense covers 77% of the catalog vs 86% for Binary. Five songs are never surfaced across all 11 profiles: Focus Flow, Velvet Undertow, Porch Swing Dusk, Pine & Fog, and Retro Drift.

5. **All improvements are incremental, not dramatic.** The top-5 overlap between MoodLense and Binary is 3.5/5 songs. Partial credit and the diversity penalty together change only 1–2 positions per list on average.

6. **Sanity check vs Random.** Random rank-1 agrees with MoodLense in only 1/11 profiles, confirming MoodLense is making intentional, preference-driven choices.

---

## 8. Future Work  

[Completed in MoodLense 2.0] ✅ Natural Language Input
The system now accepts free-text descriptions instead of requiring structured field values.

[Completed in MoodLense 2.0] ✅ Friendly Explanations
The RAG layer generates plain-English explanations grounded in actual song metadata.

[Completed in MoodLense 1.0] ✅ Artist Diversity Feature Implemented

Adding more song attributes would make matching more precise — tempo, danceability, and valence are already in the dataset but currently unused. Letting listeners rank their preferences (for example, "mood matters more to me than genre") would also help instead of applying the same fixed weights to everyone.

For more complex tastes, the system could allow multiple moods or genres rather than just one of each — for example, someone who listens to both jazz and lo-fi, or wants something that is both focused and a little melancholic.

Adding conversation memory would let the system refine recommendations based on feedback like "show me something heavier" rather than treating each query as independent.

Expanding the catalog is the highest-leverage improvement available. Adding even one song per missing genre (reggae, hip-hop, blues, Latin) and filling the mid-energy gap would directly address the gaps identified in evaluation.

---

## 9. Personal Reflection  

Building MoodLense 2.0 taught me that connecting a language model to an existing system requires much more precision than just calling an API. The hardest part of the input layer was not the API call itself — it was writing the system prompt. Without the few-shot examples and explicit vocabulary constraints, Gemini would return moods like "melancholy" or "laid-back" that the scoring engine cannot use. The prompt is doing real engineering work, not just describing a task.

The RAG explanation layer taught me what "grounded" means in practice. Without injected song metadata, Gemini produced plausible-sounding but fabricated descriptions. With the metadata, responses named real songs and cited specific attributes that came directly from the data. That difference made clear why retrieval matters: the model is only as honest as the context you give it.

The most important lesson was about the boundary between AI and traditional code. Gemini handles ambiguous natural language well but cannot be trusted to stay within a fixed vocabulary without constraints. The heuristic engine handles precise scoring well but cannot understand "I'm exhausted." Keeping them separate — each doing what it is best at — made the system more reliable and easier to debug than trying to make either one do everything.
