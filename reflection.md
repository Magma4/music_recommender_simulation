# Phase 4 reflection — comparing profiles

Plain-language notes on how different preference dictionaries change the top five, and why that matches (or fights) intuition.

---

## High-Energy Pop vs Chill Lofi

**What changed:** High-Energy Pop chases **pop**, **happy**, and **very high** target energy, so **Sunrise City** and **Gym Hero** rise because they carry the **pop** label and loud energy—even though *Gym Hero* is **intense**, not happy. Chill Lofi locks onto **lofi + chill + low energy**, so **Library Rain** and **Midnight Coding** take the top slots with a **perfect or near-perfect** triple match.

**Why it makes sense:** the scorer rewards **matching strings** and **energy proximity**. Pop profiles therefore “stick to” the pop rows in the CSV; lofi profiles cluster on the few lofi rows. The two worlds barely overlap in the data, so the lists look almost like different mini-playlists.

---

## Chill Lofi vs Deep Intense Rock

**What changed:** Chill Lofi favors **low energy** and **chill**; rock profile favors **rock**, **intense**, and **high** energy. **Storm Runner** dominates the rock run because it is the only **rock** row and it hits **intense** and **~0.91** energy. Chill Lofi never surfaces rock because **genre** must match exactly for the big genre bonus.

**Why it makes sense:** with a tiny catalog, **genre is a gate**: if your favorite genre has one row, that row has a huge advantage. Lofi has three rows, so you see more variety in positions 2–5 than rock does.

---

## Adversarial (somber + very high energy + pop) vs High-Energy Pop

**What changed:** Both profiles ask for **pop** and very high energy. The adversarial one asks for **somber** mood; High-Energy Pop asks for **happy**. **Sunrise City** (happy) still wins the happy profile on mood points; for **somber**, no track gets both **pop** and **somber** in this CSV, so the list is mostly **pop** tracks sorted by energy fit—**Gym Hero** stays near the top because **genre + energy** outweigh the missing mood match.

**Why it makes sense:** the recipe **never subtracts** points for a “wrong” mood; it only **fails to add** the mood bonus. So “I want somber” does not push sad-sounding pop to the front unless the **mood column** actually says **somber**. That is easy to *trick* with conflicting words: high energy still drags in gym-style pop.

---

## Baseline scoring vs weight-shift experiment

**What changed:** With `MUSIC_RECOMMENDER_EXPERIMENT=weight_shift`, genre matches add **1.0** instead of **2.0**, and energy similarity is multiplied by **2**, so two songs that differ only in energy separation can swap order; pure **energy** ties break more often on **mood** or **id**.

**Why it makes sense:** you deliberately moved importance from **discrete genre** toward **continuous energy**. Rankings become **more sensitive** to the energy dial and less to “being in the right genre bucket,” which can feel **fairer** for cross-genre listeners or **worse** for people who treat genre as non-negotiable.
