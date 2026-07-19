# 🎵 Music Recommender Simulation

## Project Summary

This project builds and explains a small music recommender system. The goals were to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what the system gets right and wrong
- Reflect on how this mirrors real-world AI recommenders

My version is a small, explainable recommender called **TuneMatch**. You describe your taste as a simple profile — a favorite genre, a mood, a target energy level, and whether you like acoustic music — and it scores every song in a 17-song catalog against that profile. It then returns a ranked top-5 list, and for each pick it shows exactly why the song was chosen (which features matched and how many points each was worth). There's no machine learning here on purpose: the whole point was to build something I could fully explain, then poke at it to see where it's biased or breaks.

---

## How The System Works

Real-world recommenders (Spotify, YouTube, Netflix) learn from massive amounts of behavioral data — what you play, skip, save, and replay — and combine it with signals from millions of other users to predict what you'll want next. They also weigh business goals like engagement time and catalog promotion, which is why what you see isn't purely about your taste. My version is much simpler and more transparent: instead of learning from behavior, it scores each song against a small, hand-written taste profile using features I chose on purpose. The priority is **explainability over accuracy** — every recommendation can be traced back to concrete reasons (e.g. "matches your favorite genre, close to your target energy") rather than a black-box prediction.

### Features used

**`Song`** carries the audio and metadata attributes each recommendation is scored on:

- `id`, `title`, `artist` — identity and display
- `genre` — categorical style (e.g. indie, pop)
- `mood` — emotional tone (e.g. chill, upbeat)
- `energy` — intensity, `0.0`–`1.0`
- `tempo_bpm` — speed in beats per minute
- `valence` — musical positivity/happiness, `0.0`–`1.0`
- `danceability` — how suited it is to dancing, `0.0`–`1.0`
- `acousticness` — how acoustic vs. electronic it is, `0.0`–`1.0`

**`UserProfile`** stores the listener's stated preferences that songs are matched against:

- `favorite_genre` — preferred genre (matched against `Song.genre`)
- `favorite_mood` — preferred mood (matched against `Song.mood`)
- `target_energy` — the energy level they're in the mood for (compared to `Song.energy`)
- `likes_acoustic` — whether to reward or penalize high `acousticness`

### Scoring, in plain language

The `Recommender` compares each `Song` to the `UserProfile` feature by feature, adds up weighted points for matches (exact matches on genre/mood, closeness on energy, a bonus/penalty for acousticness), and builds the top `k` list. It doesn't just sort once and slice, though — it picks songs one at a time and applies a **diversity penalty** so the list doesn't fill up with the same artist or genre (more on that below). Each recommendation comes with a short explanation listing which features drove its score, including any penalty that was applied.

### Algorithm Recipe (current)

These are the weights the code uses today, after the experiments described further down. They live as named constants at the top of [`recommender.py`](src/recommender.py) so they're easy to tune.

| Feature | Rule | Points |
| --- | --- | --- |
| Genre | Exact match with `favorite_genre` | **+1.0** |
| Mood | Exact match with `favorite_mood` | **+1.0** |
| Energy | Closeness to `target_energy`: `3.0 × (1 − |song.energy − target_energy|)`, clamped to `[0, 1]` | **0.0 to +3.0** |
| Acousticness | If `likes_acoustic`: `+0.5 × acousticness`; else `−0.5 × acousticness` | **−0.5 to +0.5** |

**Maximum possible score = 5.5** (1.0 + 1.0 + 3.0 + 0.5).

On top of the raw score, a **diversity penalty** is applied while the top-k list is being built, so no single artist or genre takes over:

| Penalty | When | Points |
| --- | --- | --- |
| Repeat artist | The song's artist is already in the list so far | **−2.0 per repeat** |
| Repeat genre | The song's genre is already in the list so far | **−0.75 per repeat** |

In pseudocode:

```
# 1. score every song
score = 0
if song.genre == user.favorite_genre:  score += 1.0
if song.mood  == user.favorite_mood:   score += 1.0
closeness = clamp(1 - abs(song.energy - user.target_energy), 0, 1)
score += 3.0 * closeness
score += 0.5 * song.acousticness  if user.likes_acoustic  else  -0.5 * song.acousticness

# 2. build the top-k greedily, subtracting diversity penalties for repeats
for each slot:
    pick the highest-scoring remaining song after subtracting
        2.0 * (times its artist already chosen)
      + 0.75 * (times its genre already chosen)
```

**Why these numbers:** I started with genre as the anchor (+2.0) and energy as a tie-breaker (+1.5), but after experimenting I flipped it — energy is now the heaviest signal because "how energetic do I want this to feel" turned out to separate songs more usefully than a genre label. Mood stays a flat +1.0, and acousticness is just a small nudge. The energy closeness is clamped so a nonsense target (like `2.0`) can't drive the score negative. The diversity penalty is deliberately harsher on repeat artists (−2.0) than repeat genres (−0.75), since hearing the same artist twice in a five-song list feels worse than hearing two songs of the same genre.

### Potential biases I expect

- **Energy dominates everything.** After the weight shift, energy is worth up to +3.0 while genre and mood are only +1.0 each. That means a song sitting on your target energy can beat a genuine genre match that's slightly off-energy. The "safe middle" of the catalog (songs around 0.5–0.6 energy) is close to almost everyone's target, so those songs surface for a lot of different users — a classic filter-bubble effect.
- **Exact-label bias.** Matching is exact-string, so `"indie"` ≠ `"indie pop"` and near-miss genres/moods score zero. This favors songs whose labels happen to match the catalog's vocabulary and quietly penalizes anything tagged differently.
- **Extreme tastes get less.** Because most of the catalog clusters mid-energy, a user who wants very high or very low energy has fewer strong matches than someone in the middle.
- **Unused signals.** `tempo_bpm`, `valence`, and `danceability` exist on each `Song` but the profile has no matching preference, so they don't influence recommendations at all yet.
- **Cold-start / thin catalog.** With a tiny hand-built catalog and a hand-entered profile, the system reflects whatever assumptions went into that data rather than real listening behavior.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

`python -m src.main` runs the recommender against several built-in profiles. Here's the first one, a **High-Energy Pop** listener (`genre=pop, mood=happy, energy=0.9`):

```
Loaded songs: 17

============================================================
  PROFILE: High-Energy Pop
  Prefs: genre='pop', mood='happy', energy=0.9
============================================================

1. Sunrise City - Neon Echo   (score 4.76)
     - genre match: pop (+1.0)
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.90 (+2.76)

2. Rooftop Lights - Indigo Parade   (score 3.58)
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.90 (+2.58)

3. Gym Hero - Max Pulse   (score 3.16)
     - genre match: pop (+1.0)
     - energy 0.93 vs target 0.90 (+2.91)
     - diversity: repeat genre (-0.75)

4. Storm Runner - Voltline   (score 2.97)
     - energy 0.91 vs target 0.90 (+2.97)

5. Pulse Reactor - Circuit Halo   (score 2.97)
     - energy 0.89 vs target 0.90 (+2.97)
```

*Sunrise City* wins easily — it's the only song matching genre **and** mood while sitting right on the target energy. The interesting bit is #2 vs #3: `Gym Hero` actually has a higher raw score than `Rooftop Lights`, but it's a second pop song, so the diversity penalty (`repeat genre -0.75`) knocks it below the mood-matched `Rooftop Lights`. That's the diversity rule doing its job — keeping the list from turning into an all-pop block.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

**1. Weight shift — doubled energy, halved genre.** I started with genre as the anchor (+2.0) and energy as a tie-breaker (+1.5). Then I flipped it: genre down to +1.0, energy up to +3.0. The rankings noticeably changed — songs that just matched a genre label but felt "off" energy-wise dropped, and songs that sat right on the target energy climbed, even across genres. It made the lists feel more like "the right vibe" and less like "everything tagged pop." It also made energy the dominant signal, which is a trade-off I document in the bias section.

**2. Diversity penalty.** Without it, a user's top 5 could be three songs by the same artist or four songs of one genre. I added a penalty applied while building the list: −2.0 for a repeat artist, −0.75 for a repeat genre, stacking per repeat. For the Chill Lofi profile this pushed a second LoRoom track out of the top 5 entirely and gave five different artists instead of a cluster.

**3. Stress-testing weird profiles.** I ran adversarial profiles — a conflicting `sad` + high-energy user, an unknown genre (`kpop`), a blank profile, and an impossible `energy=2.0`. Most degraded gracefully (a missing genre/mood just scores 0 and the other signals take over). The `energy=2.0` case exposed a real bug: the energy math went negative and printed a broken `(+-0.33)` string. I fixed it by clamping energy closeness to `[0, 1]`. Full outputs and per-profile comparisons are in the [model card](model_card.md).

---

## Limitations and Risks

A few honest limitations (I go deeper in the [model card](model_card.md)):

- **Tiny catalog.** Only 17 songs, and most genres have just one track. A niche taste gets one real match and then a list ranked by energy.
- **No understanding of the music itself.** It only knows the numbers and labels in the CSV — no lyrics, no language, no actual audio.
- **Energy can overpower taste.** Because energy is the heaviest weight, the mid-energy "safe middle" of the catalog gets recommended to lots of different users, which is a filter-bubble risk.
- **Exact-match only.** `"indie"` and `"indie pop"` are treated as totally unrelated, so inconsistent tags silently cost songs points.
- **Hand-entered data.** Both the catalog and the profiles are made up by me, so any bias in that data flows straight into the results.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

The biggest thing I learned is that a "recommendation" is a lot less magical than it feels from the outside. Under the hood it's really just turning preferences into numbers, adding up points, and sorting. There's no understanding of the music happening — the system is only as smart as the features I decided to score and the weights I chose for them. Watching the rankings completely change when I doubled the energy weight drove that home: small, invisible decisions by whoever builds the system quietly decide what everyone sees.

That's also where bias sneaks in. My recommender doesn't set out to be unfair, but it ends up favoring the middle of the catalog and punishing anything with an unusual genre label, just because of how I wrote the math and what data I happened to include. Nobody chose that on purpose — it fell out of the design. It made me think differently about apps like Spotify: behind the "for you" feeling, someone picked the features, the weights, and the training data, and those choices shape the taste of millions of people. Building even a tiny version made those hidden trade-offs feel real.



