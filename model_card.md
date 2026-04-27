# Model Card: Music Recommender Simulation

## 1. Model Name  

MoodLense 1.0
---

## 2. Intended Use    

MoodLense 1.0 is a content-based filtering model that suggests songs from a catalog based on four listener preferences: favourite genre, favourite mood, how energetic they want the music to feel, and whether they prefer acoustic or electronic sounds. It assumes the user taste can be described in those four terms and that those preferences stay constant — it does not learn overtime. This is a classroom simulation built to explore how scoring logic works and where it breaks down.

---

## 3. How the Model Works  

Each song is described and evaluated by four qualities: its genre (like lofi or metal), its mood (like chill or intense), an energy level on a scale from 0 to 1, and an acousticness score that says how "live and organic" versus "electronic and produced" it sounds.

When a listener comes in, they tell the system their favourite genre, favourite mood, how energetic they want the music, and whether they prefer acoustic or electronic sounds. The system then goes through every song in the catalog and gives it a score based on how well it matches those four preferences.

Mood and genre are not just yes-or-no matches — there are similarity tables that give partial credit for related categories. For example, if you want "chill" music and a song is "relaxed," it scores 70% of the full mood points rather than zero. Energy is scored using a bell curve: songs closest to your target energy score highest, and songs far away score near zero. Acoustic preference is scored as a straight percentage — the more acoustic a song is, the better it scores for someone who wants acoustic, and the worse for someone who does not.

The four component scores are then added up with different weights: mood counts for 35%, genre for 25%, energy for 25%, and acousticness for 15%. The songs with the highest totals are returned as the top recommendations.

The main changes from the starter logic were expanding the mood and genre similarity tables to cover a wider range of categories, and adding more song variety to the catalog to better test edge cases.

The additional change was the implementation of a Diversity Penalty feature that penalizes the same artist appearing multiple times in the recommendation list. The feature uses a decay factor that controls how harsh that penalty is: 0.5 halves an artist's score with each repeat.

---

## 4. Data  

The catalog contains 22 songs (20 unique titles, with LoRoom and Neon Echo each appearing in two variants) spanning 15 genres — lofi, pop, rock, ambient, jazz, synthwave, indie pop, soul, metal, country, electronic, r&b, folk, drum and bass, and classical — and 14 moods ranging from chill and serene to aggressive and tense. Songs were added beyond the original starter set to improve genre and mood coverage.

The catalog is intentionally small for a simulation, which creates some gaps. Most genres and moods have only one song each, so when a listener's first-choice genre has no good match, the fallback options are very limited. Energy levels also cluster at the quiet end and the loud end, leaving almost nothing for listeners who want something in the middle. Styles like reggae, hip-hop, blues, and Latin are completely absent, as are moods like nostalgic longing or quiet joy that sit between the defined categories. Real listening taste is much more varied and personal than this dataset can capture.

---

## 5. Strengths  

The system works best for listeners with clear, well-represented preferences. When a listener's genre and mood both have good catalog coverage, the scoring feels natural and the top result is a good match. Across 11 test profiles, 8 achieved a rank-1 score above 0.85, indicating strong alignment for the majority of listener types.

The partial credit system for related moods and genres also behaves sensibly in most cases. A lofi fan correctly gets ambient and jazz suggestions as runner-ups rather than something completely unrelated like metal.

The bell curve for energy means small differences near the target barely affect the score, which prevents the system from being overly harsh about songs that are close but not exact — that feels right for how people actually listen.

The diversity penalty meaningfully improves within-list variety. Genre diversity increases from 3.6 to 4.6 unique genres per top-5 list, and average max artist repeat drops from 2.3 to 1.5 when the penalty is active.

---

## 6. Limitations and Bias 

The system only knows four things about a listener — genre, mood, energy, and acoustic preference. It has no awareness of tempo, lyrics, language, listening history, time of day, or whether the listener wants something familiar or something new. Two songs can score identically and be nothing alike in practice.

Entire styles of music are missing from the catalog. Reggae, hip-hop, blues, Latin, and many others have no representation, so listeners whose taste lives in those areas will always get mismatched results. Even within represented genres, most have only one song, meaning the system runs out of good options quickly and fills the remaining slots with loosely related alternatives.

Some moods like aggressive or sad connect to very few others, so if the one matching song is not quite right, the remaining recommendations feel unrelated. Listeners who prefer moods like happy or intense connect to many more songs and naturally get better results.

The acoustic preference is weighted at only 15%, which is not enough to override mood and energy when they point in a different direction. In practice, a listener who specifically wants acoustic music will often receive electronic-sounding recommendations because the other dimensions outweigh that preference.

The system also has no way to penalise a song for appearing too often — so one song with broadly average qualities can end up recommended to almost every listener regardless of how different their tastes are.

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

2. **Tables improve filler quality, not top-pick quality.** Rank-1 average score: MoodLense 0.86 vs Binary 0.85 — near-identical. Rank-5 average score: MoodLense 0.54 vs Binary 0.35 — MoodLense is +0.19. The real value of partial credit is in the lower slots: MoodLense fills positions 3–5 with related-mood songs that still earn partial scores, while Binary drops to near-zero for anything that is not an exact genre/mood match.

3. **Diversity penalty: what it fixes and what it costs.** Active in 7/11 profiles, the penalty raises average unique artists per list from 3.8 to 5.0 and unique genres from 3.6 to 4.6, and cuts max artist repeat from 2.2 to 1.0. Rank-1 is unchanged across all 11 profiles. The cost: rank-5 average score drops from 0.61 (No-Diversity) to 0.54, and personalization index falls from 35% to 31% because the penalty surfaces the same alternative artists across different profiles, reducing cross-user variety even as it improves within-list variety.

4. **Catalog coverage trade-off.** MoodLense covers 77% of the catalog vs 86% for Binary and No-Diversity. Partial credit keeps recommending the same "good enough" songs across profiles; Binary, forced to give zero to non-matches, explores more of the catalog. Five songs are never surfaced by MoodLense across all 11 profiles: Focus Flow, Velvet Undertow, Porch Swing Dusk, Pine & Fog, and Retro Drift — genre/mood dead zones where no current user profile is close enough.

5. **All improvements are incremental, not dramatic.** The top-5 overlap between MoodLense and Binary is 3.5/5 songs, and between MoodLense and No-Diversity it is 3.8/5. Partial credit and the diversity penalty together change only 1–2 positions per list on average. The models agree most of the time; the gains from similarity tables and diversity happen at the margins, in the lower slots.

6. **Sanity check vs Random.** Random rank-1 agrees with MoodLense in only 1/11 profiles and has no meaningful preference-based score, confirming MoodLense is making intentional, preference-driven choices rather than getting lucky.

---

## 8. Future Work  

Adding more song attributes would make matching more precise — tempo, danceability, and valence are already in the dataset but currently unused. Letting listeners rank their preferences (for example, "mood matters more to me than genre") would also help instead of applying the same fixed weights to everyone.

[Completed in Updated Version] ✅ Artist Diversity Feature Implemented 
The diversity problem could be addressed by adding a rule that penalises a song slightly if something very similar has already been selected — so the top 5 feels varied rather than clustered around one corner of the catalog.

[Completed in Updated Version] ✅ Friendly Explanations & Tabulate Display 
Implemented Explanations could be friendlier. Instead of showing raw numbers, the system could say something like "this song matches your mood perfectly and is close to your energy target" in plain language.

For more complex tastes, the system could allow multiple moods or genres rather than just one of each — for example, someone who listens to both jazz and lo-fi, or wants something that is both focused and a little melancholic.

Expanding the catalog is the highest-leverage improvement available. Adding even one song per missing genre (reggae, hip-hop, blues, Latin) and filling the mid-energy gap would directly address the gaps identified in evaluation.

---

## 9. Personal Reflection  

I learned that there are different types of recommender systems — content-based and collaborative. I was surprised by how many factors shape what gets recommended: the weights, how preferences are defined, how data is labelled and processed. Small changes in any of those can change the results completely. It made me think differently about the apps I use every day and how much is happening behind something that feels effortless.
