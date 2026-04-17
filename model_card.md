# Model Card — Music Recommender Simulation

## Model Name

**VibeFinder 1.0** — a small, see-through song ranker for learning.

---

## Goal / Task

The recommender **suggests up to five songs** from a fixed list. It does not “learn” from new data each run. It **ranks** every track once, using the same rules, and returns the highest scores.

---

## Data Used

There are **18 songs** in `data/songs.csv`. Each row has **genre**, **mood**, **energy** (0–1), plus **tempo**, **valence**, **danceability**, and **acousticness**. The scorer **only uses genre, mood, and energy** today. The set is **tiny** and made up; many genres or moods appear **once or twice**, so results are **not** like a real streaming catalog.

---

## Algorithm Summary

For each song, we **add points** for a **genre match** and a **mood match** (exact labels, case-insensitive). We **add an energy score** from **how close** the song’s energy is to the user’s target (nearer is better, on a 0–1 scale). Everything is **summed** into one number. We **sort** all songs by that number and take the **top few**. The program also prints **reasons** (e.g. how many points each part earned).

For experiments, you can turn on **weight shift**: **smaller** genre points and **double** energy points, to see how much rankings depend on those choices.

---

## Observed Behavior / Biases

**Genre counts a lot.** A **pop** song with **high energy** can land near the top for someone who asked for **happy pop**, even if the song’s mood is **intense**—because wrong moods are **not punished**, they just **miss** the mood bonus.

**Labels are strict.** “Indie pop” is **not** treated as “pop,” so some tracks that *feel* right never get the big genre bump.

**Small data = sameness.** The same rows show up a lot for certain profiles because there are **few** rows that match at all.

---

## Evaluation Process

We ran **several fake user profiles** in the terminal: high-energy pop, chill lofi, intense rock, plus **edge** mixes (e.g. **somber** mood with **very high** energy). We read the **top five** and the **reason** lines for each. We compared **baseline** scoring to a **weight-shift** run (see `docs/phase4-stress-test-output.txt` and `docs/phase4-weight-shift-output.txt`). **pytest** checks basic ranking and that scores return **numbers + reason strings**.

---

## Intended Use and Non-Intended Use

**Intended:** **Teaching and demos.** Showing how **rules + data** produce recommendations you can **read and argue with**.

**Not intended:** **Real product** decisions, **fairness** claims, or **personalized** music advice for paying users. It should **not** replace human judgment or a real recommender backed by **much more data** and **oversight**.

---

## Ideas for Improvement

1. **Penalize** or **discount** songs when mood clearly **conflicts** with what the user asked for, not only when it fails to match.

2. **Group** related genres (e.g. map “indie pop” under pop) or add **synonyms** for moods.

3. **Diversify** the top five so it is not five **almost identical** tracks when the catalog allows it.

---

## Personal Reflection

**Biggest learning moment:** Seeing **Gym Hero** rank high for “happy” seekers was the wake-up call. The math is “honest,” but it does not know that **intense** and **happy** can clash. **Design choices** (how big genre is vs mood) matter as much as the code.

**AI tools:** They sped up **boilerplate** and **wording**, and helped **brainstorm** edge-case profiles. I still had to **trace the score by hand** for one song and run **`main`** to be sure the terminal matched my understanding. **Trust, then verify.**

**Surprise:** A few **if** rules and addition still **feel** like a “recommendation” because **ranking** and **short explanations** mirror what apps do—just with the **cover removed**.

**Next if I extended this:** I would add **valence** or **tempo bands**, a **diversity** pass on the top five, and a **slightly bigger** CSV so genre is not a **lottery** when only one row matches.
