# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

TuneMatch

---

## 2. Intended Use

TuneMatch suggests songs from a small catalog. You give it your taste. It gives you a ranked list back.

- It picks songs that fit your favorite genre, mood, and energy level.
- It assumes you can name your taste in simple words (like "pop" or "chill").
- It is built for a classroom project, not for real users. It is a demo, not a product.

---

## 3. How the Model Works

Think of it like a points game. Every song starts with zero points.

- A song earns points if its genre matches what you like.
- It earns more points if its mood matches too.
- It earns points for being close to the energy level you want. Closer means more points.
- It can earn a small bonus if you like acoustic songs and the song is acoustic.

We add up the points for each song. Then we sort the songs from most points to least. The top ones become your recommendations. Each pick also comes with a short "why" so you can see the reasons.

We changed two things from the starter code. First, we wrote the real scoring rules (the starter just returned the first few songs). Second, we ran an experiment: we made energy count more and genre count less, to see how the list changes.

---

## 4. Data

The catalog is a small CSV file of songs.

- It has 17 songs.
- Genres include pop, lofi, rock, jazz, ambient, hip hop, classical, reggae, metal, country, edm, and folk.
- Moods include happy, chill, intense, relaxed, sad-ish tones, and more.
- We added 7 new songs to the 10 that came with the starter. We picked genres and moods that were missing.
- A lot of taste is still missing. There is only one song for most genres. Many world music styles, languages, and eras are not here at all.

---

## 5. Strengths

The system works well when a user has a clear, common taste.

- It gives good results for mainstream profiles like "pop and happy" or "chill lofi." The top pick usually feels right.
- It captures the idea that genre and mood matter, and that energy should feel close to what you want.
- The results matched my intuition in testing. A high-energy pop user got upbeat pop. A chill lofi user got quiet, acoustic songs. The reasons shown for each pick made sense.

---

## 6. Limitations and Bias

The clearest weakness I found was an energy-gap filter bubble that quietly favors
average listeners over extreme ones. Energy is scored as `weight * (1 - |song.energy -
target|)`, and after the weight-shift experiment energy is the single heaviest signal
(3.0 points vs. 1.0 for genre), so how close a song sits to the target energy now
dominates the ranking. Because most of the catalog clusters in the middle (mean energy
0.60, with only 5 of 17 songs below 0.40), a mid-energy song is never far from *anyone's*
target and therefore gets a structural advantage, while users who want very low or very
high energy see a narrower, lower-scoring set of real matches. The problem compounds with
the catalog's genre skew: because matching is exact-string and almost every genre has just
one song (lofi is the largest at 3 of 17), a niche user gets one genre-boosted track and
then a list ranked almost entirely by energy closeness — the same mid-energy songs that
surface for everyone else. In short, the system risks recommending a similar "safe middle"
to most users regardless of their stated taste, which is exactly the kind of homogenizing
filter bubble real recommenders are criticized for.

Other known limitations: it ignores `tempo_bpm`, `valence`, and `danceability` entirely;
it gives no signal when a requested genre/mood is absent from the catalog; and an
out-of-range energy target produces negative, uninterpretable scores (see Evaluation).

---

## 7. Evaluation

I stress-tested the recommender by running `python -m src.main` against seven user
profiles: three "normal" tastes and four adversarial / edge-case profiles designed to
try to trick the scoring logic. For each profile I looked at the top 5 songs and their
per-feature reason breakdowns to check that the ranking made sense.

> **Note on weights:** the outputs below were produced *after* the weight-shift experiment,
> so genre is worth **+1.0** and energy is worth up to **+3.0**. Scores here are higher than
> earlier runs because energy now dominates the ranking.

**Profiles tested:**

| # | Profile | genre | mood | energy | notes |
|---|---------|-------|------|--------|-------|
| A | High-Energy Pop | pop | happy | 0.90 | normal |
| B | Chill Lofi | lofi | chill | 0.35 | normal, `likes_acoustic=True` |
| C | Deep Intense Rock | rock | intense | 0.90 | normal |
| D | Conflicting | pop | sad | 0.95 | mood `sad` absent from catalog |
| E | Unknown genre | kpop | happy | 0.60 | genre absent from catalog |
| F | Out-of-range energy | edm | euphoric | 2.00 | impossible energy value |
| G | Blank taste | (empty) | (empty) | 0.50 | no categorical signal |

**What I looked for:** that genre+mood matches float to the top, that energy acts as a
strong ranking signal, and that the system degrades gracefully when a profile is weird
(unknown genre, blank taste, impossible energy).

**What surprised me:** two things. First, after doubling the energy weight, energy now
*outranks* genre — a song that matches genre but is off-target on energy can lose to a
non-genre song that sits on the target energy (visible in profile A, where the energy-only
songs Storm Runner and Pulse Reactor at 2.97 nearly catch the genre-matched Gym Hero at
3.91). Second, the out-of-range energy profile (`energy=2.0`) exposed a bug: the formula
`3.0 * (1 - abs(song.energy - target))` is not clamped, so an impossible target pushes
energy points **negative**, dragging total scores below zero and printing a malformed
`(+-0.33)` string. Real matches (genre/mood) still ranked #1, but the numbers stopped being
interpretable — a good argument for clamping energy closeness to `[0, 1]` and validating
input ranges.

### Normal profiles

```
============================================================
  PROFILE: High-Energy Pop
  Prefs: genre='pop', mood='happy', energy=0.9
============================================================

1. Sunrise City - Neon Echo   (score 4.76)
     - genre match: pop (+1.0)
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.90 (+2.76)
2. Gym Hero - Max Pulse   (score 3.91)
     - genre match: pop (+1.0)
     - energy 0.93 vs target 0.90 (+2.91)
3. Rooftop Lights - Indigo Parade   (score 3.58)
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.90 (+2.58)
4. Storm Runner - Voltline   (score 2.97)
     - energy 0.91 vs target 0.90 (+2.97)
5. Pulse Reactor - Circuit Halo   (score 2.97)
     - energy 0.89 vs target 0.90 (+2.97)
```

```
============================================================
  PROFILE: Chill Lofi
  Prefs: genre='lofi', mood='chill', energy=0.35, likes_acoustic=True
============================================================

1. Library Rain - Paper Lanterns   (score 5.43)
     - genre match: lofi (+1.0)
     - mood match: chill (+1.0)
     - energy 0.35 vs target 0.35 (+3.00)
     - likes acoustic (0.86) (+0.43)
2. Midnight Coding - LoRoom   (score 5.14)
     - genre match: lofi (+1.0)
     - mood match: chill (+1.0)
     - energy 0.42 vs target 0.35 (+2.79)
     - likes acoustic (0.71) (+0.35)
3. Spacewalk Thoughts - Orbit Bloom   (score 4.25)
     - mood match: chill (+1.0)
     - energy 0.28 vs target 0.35 (+2.79)
     - likes acoustic (0.92) (+0.46)
4. Focus Flow - LoRoom   (score 4.24)
     - genre match: lofi (+1.0)
     - energy 0.40 vs target 0.35 (+2.85)
     - likes acoustic (0.78) (+0.39)
5. Paper Boats - Wren & Hollow   (score 3.39)
     - energy 0.33 vs target 0.35 (+2.94)
     - likes acoustic (0.90) (+0.45)
```

```
============================================================
  PROFILE: Deep Intense Rock
  Prefs: genre='rock', mood='intense', energy=0.9
============================================================

1. Storm Runner - Voltline   (score 4.97)
     - genre match: rock (+1.0)
     - mood match: intense (+1.0)
     - energy 0.91 vs target 0.90 (+2.97)
2. Gym Hero - Max Pulse   (score 3.91)
     - mood match: intense (+1.0)
     - energy 0.93 vs target 0.90 (+2.91)
3. Pulse Reactor - Circuit Halo   (score 2.97)
     - energy 0.89 vs target 0.90 (+2.97)
4. Ironclad - Blackforge   (score 2.79)
     - energy 0.97 vs target 0.90 (+2.79)
5. Sunrise City - Neon Echo   (score 2.76)
     - energy 0.82 vs target 0.90 (+2.76)
```

### Adversarial / edge-case profiles

```
============================================================
  PROFILE: Conflicting (sad + high energy)
  Prefs: genre='pop', mood='sad', energy=0.95
============================================================

1. Gym Hero - Max Pulse   (score 3.94)
     - genre match: pop (+1.0)
     - energy 0.93 vs target 0.95 (+2.94)
2. Sunrise City - Neon Echo   (score 3.61)
     - genre match: pop (+1.0)
     - energy 0.82 vs target 0.95 (+2.61)
3. Ironclad - Blackforge   (score 2.94)
     - energy 0.97 vs target 0.95 (+2.94)
4. Storm Runner - Voltline   (score 2.88)
     - energy 0.91 vs target 0.95 (+2.88)
5. Pulse Reactor - Circuit Halo   (score 2.82)
     - energy 0.89 vs target 0.95 (+2.82)
```
*Finding:* the mood `sad` matches no song, so genre + energy alone drive the ranking.
The system quietly ignores the impossible mood rather than returning nothing.

```
============================================================
  PROFILE: Unknown genre (kpop)
  Prefs: genre='kpop', mood='happy', energy=0.6
============================================================

1. Rooftop Lights - Indigo Parade   (score 3.52)
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.60 (+2.52)
2. Sunrise City - Neon Echo   (score 3.34)
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.60 (+2.34)
3. Island Time - Palm Groove   (score 2.85)
     - energy 0.55 vs target 0.60 (+2.85)
4. Concrete Poetry - Verse Machine   (score 2.76)
     - energy 0.68 vs target 0.60 (+2.76)
5. Dust and Highways - June Callahan   (score 2.64)
     - energy 0.48 vs target 0.60 (+2.64)
```
*Finding:* a genre absent from the catalog simply scores 0 for genre everywhere, so mood
becomes the deciding factor. Graceful, but a user asking for k-pop gets no signal that the
catalog has none.

```
============================================================
  PROFILE: Out-of-range energy (2.0)
  Prefs: genre='edm', mood='euphoric', energy=2.0
============================================================

1. Pulse Reactor - Circuit Halo   (score 1.67)
     - genre match: edm (+1.0)
     - mood match: euphoric (+1.0)
     - energy 0.89 vs target 2.00 (+-0.33)
2. Ironclad - Blackforge   (score -0.09)
     - energy 0.97 vs target 2.00 (+-0.09)
3. Gym Hero - Max Pulse   (score -0.21)
     - energy 0.93 vs target 2.00 (+-0.21)
4. Storm Runner - Voltline   (score -0.27)
     - energy 0.91 vs target 2.00 (+-0.27)
5. Sunrise City - Neon Echo   (score -0.54)
     - energy 0.82 vs target 2.00 (+-0.54)
```
*Finding (bug):* an impossible energy target drives energy points **negative** and prints
`(+-0.33)`. Genre/mood still rank #1 correctly, but scores lose meaning. Fix: clamp energy
closeness to `[0, 1]` and/or validate that `energy` is within `0.0-1.0`.

```
============================================================
  PROFILE: Blank taste (empty strings)
  Prefs: genre='', mood='', energy=0.5
============================================================

1. Dust and Highways - June Callahan   (score 2.94)
     - energy 0.48 vs target 0.50 (+2.94)
2. Island Time - Palm Groove   (score 2.85)
     - energy 0.55 vs target 0.50 (+2.85)
3. Midnight Coding - LoRoom   (score 2.76)
     - energy 0.42 vs target 0.50 (+2.76)
4. Focus Flow - LoRoom   (score 2.70)
     - energy 0.40 vs target 0.50 (+2.70)
5. Coffee Shop Stories - Slow Stereo   (score 2.61)
     - energy 0.37 vs target 0.50 (+2.61)
```
*Finding:* with no genre or mood to match, the ranking collapses to "closest energy to
0.5" — effectively a mid-energy popularity list. Reasonable fallback, but shows how much
the system leans on energy when categorical signals are absent.

### Profile-by-profile comparisons

Each pair below contrasts the top-5 outputs and explains why the difference makes sense:

- **A vs B (High-Energy Pop / Chill Lofi):** A surfaces loud, upbeat pop (Sunrise City,
  Gym Hero at ~0.9 energy); B surfaces quiet acoustic lofi (Library Rain, Midnight Coding
  at ~0.35). They sit at opposite ends of the energy axis, and B is the only one that earns
  the acoustic bonus — no song overlaps. This is the cleanest proof the energy preference
  works.
- **A vs C (High-Energy Pop / Deep Intense Rock):** both target energy 0.90, so their
  energy-driven tails are nearly identical (both list Gym Hero, Storm Runner, Pulse Reactor).
  Only the #1 differs — A's genre/mood lift Sunrise City, C's lift Storm Runner — showing
  that with equal energy targets the categorical match just re-orders the same energetic pool.
- **A vs D (High-Energy Pop / Conflicting):** identical genre (pop) and near-identical energy,
  but D's mood `sad` matches nothing, so D loses the +1 mood boost that put Sunrise City #1
  for A. D therefore promotes Gym Hero (pop, no mood match) to #1 — a valid mood clearly
  outranks a dead one.
- **A vs E (High-Energy Pop / Unknown genre):** both want happy songs, but A also matches
  genre pop and targets higher energy. A's happy-pop tracks score higher and its list skews
  energetic; E, with no genre credit and a 0.60 target, ranks the same happy songs lower and
  pulls in mid-energy tracks (Island Time). Losing genre credit demotes but doesn't erase the
  mood-matched songs.
- **A vs F (High-Energy Pop / Out-of-range energy):** both lean high-energy, but A produces
  clean positive scores while F's impossible 2.0 target drives everything negative. Same kind
  of energetic songs surface at the top, yet F's numbers are meaningless — the contrast
  isolates the clamping bug.
- **A vs G (High-Energy Pop / Blank taste):** A has full genre/mood/energy signal and returns
  high-energy pop; G has no categorical signal and collapses to a mid-energy list (Dust and
  Highways, Island Time). Shows how much the categorical matches shape A's result.
- **B vs C (Chill Lofi / Deep Intense Rock):** polar opposites — 0.35 vs 0.90 energy, acoustic
  vs electric. Zero overlap in the top 5; the energy axis alone cleanly separates a relaxed
  listener from an intense one.
- **B vs D (Chill Lofi / Conflicting):** opposite energy targets (0.35 vs 0.95) plus B's
  acoustic bonus versus D's pop/high-energy focus mean completely disjoint lists — a calm
  acoustic set against a loud pop set.
- **B vs E (Chill Lofi / Unknown genre):** B (0.35, acoustic) returns low-energy acoustic
  lofi; E (0.60, happy) returns brighter mid-energy songs. Both keep one working signal
  (B's genre+acoustic, E's mood), and the different energy targets pull their lists apart.
- **B vs F (Chill Lofi / Out-of-range energy):** B is a clean low-energy result; F is a broken
  high-energy one with negative scores. No overlap — they test opposite ends of the energy
  range, one valid and one degenerate.
- **B vs G (Chill Lofi / Blank taste):** both lean toward lower energy (0.35 vs 0.50), so their
  candidate pools overlap (Midnight Coding, Focus Flow appear in both). But B's genre, mood,
  and acoustic boosts lift Library Rain to #1, while G ranks purely by energy — a direct
  illustration of what the categorical signals add on top of energy.
- **C vs D (Deep Intense Rock / Conflicting):** both high energy (0.90 vs 0.95), so they share
  most songs (Gym Hero, Storm Runner, Ironclad, Pulse Reactor). C's valid `intense` mood puts
  Storm Runner #1; D's dead `sad` mood lets pop-genre Gym Hero take #1. Same energetic pool,
  reordered by whichever categorical signal actually fires.
- **C vs E (Deep Intense Rock / Unknown genre):** C targets high energy and matches rock/intense;
  E targets mid energy and only matches happy. Their tops diverge because the energy gap alone
  reshuffles which songs are "closest," before the categorical boosts even apply.
- **C vs F (Deep Intense Rock / Out-of-range energy):** both aim high-energy and both surface
  the same heavy tracks (Storm Runner, Ironclad, Pulse Reactor), but C's scores are valid while
  F's collapse negative — showing the bug is about the *number*, not the *ordering* of the top.
- **C vs G (Deep Intense Rock / Blank taste):** C returns a high-energy rock/metal set; G returns
  a mid-energy grab-bag. The energy target (0.90 vs 0.50) is the whole story once C's categorical
  boosts are removed.
- **D vs E (Conflicting / Unknown genre):** a neat mirror image — D keeps its *genre* signal
  (pop exists) and loses mood, so pop songs top its list; E keeps its *mood* signal (happy exists)
  and loses genre, so happy songs top its list. Each profile leans on whichever of its two
  categorical preferences the catalog can actually satisfy.
- **D vs F (Conflicting / Out-of-range energy):** both are pop/edm high-energy-ish, but D's 0.95
  target is valid (positive scores) while F's 2.0 is not (negative scores). Similar intent,
  opposite validity.
- **D vs G (Conflicting / Blank taste):** D still has genre pop plus a high energy target, so it
  returns energetic pop; G has nothing and returns mid-energy filler. D's single surviving genre
  signal is enough to visibly tilt the list toward pop.
- **E vs F (Unknown genre / Out-of-range energy):** E is a valid mid-energy happy result; F is a
  broken high-energy one. Both have one dead categorical signal, but only F additionally breaks
  the math via its impossible energy value.
- **E vs G (Unknown genre / Blank taste):** both land in mid-energy territory (0.60 vs 0.50) and
  share tail songs (Island Time, Dust and Highways). E's working `happy` mood lifts Rooftop
  Lights and Sunrise City above the pack; G, with no mood at all, ranks strictly by energy —
  isolating the effect of a single mood match.
- **F vs G (Out-of-range energy / Blank taste):** F still ranks its genre+mood match (Pulse
  Reactor) #1 despite negative scores, while G has no categorical signal and falls back cleanly
  to mid-energy songs. Side by side they contrast a *math* failure (F) with a *graceful*
  fallback (G).

---

## 8. Future Work

Here is what I would do next.

- Use more song features. Right now tempo, valence, and danceability are ignored. I would add them.
- Fix the energy bug. I would clamp the energy score so it never goes negative.
- Handle missing matches. If the catalog has no k-pop, tell the user instead of staying quiet.
- Add more songs. A bigger, more even catalog would help niche tastes.
- Improve variety. I would stop the list from filling up with near-identical mid-energy songs.
- Let users rank what matters most to them (genre vs mood vs energy).

---

## 9. Personal Reflection

This project made recommenders feel less like magic. It is really just points and sorting.

I learned that the weights matter a lot. When I doubled the energy weight, the whole list changed. Small choices by the builder shape what users see.

The surprising part was the edge cases. A weird input like energy 2.0 broke the math in a quiet way. That made me realize how easy it is for bias or bugs to hide inside a simple rule. Now I think about apps like Spotify differently. Someone chose those rules, and those choices decide what millions of people hear.
