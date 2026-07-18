# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

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

The `Recommender` compares each `Song` to the `UserProfile` feature by feature, adds up weighted points for matches (exact matches on genre/mood, closeness on energy, a bonus/penalty for acousticness), and returns the top `k` highest-scoring songs. Each recommendation also comes with a short explanation listing which features drove its score.

### Algorithm Recipe (finalized)

The weights are deliberately ranked so that **genre anchors** the result while **mood and energy break ties**. All weights live as named constants in [`recommender.py`](src/recommender.py) so they're easy to tune during experiments.

| Feature | Rule | Points |
| --- | --- | --- |
| Genre | Exact match with `favorite_genre` | **+2.0** |
| Mood | Exact match with `favorite_mood` | **+1.0** |
| Energy | Closeness to `target_energy`: `1.5 × (1 − |song.energy − target_energy|)` | **0.0 to +1.5** |
| Acousticness | If `likes_acoustic`: `+0.5 × acousticness`; else `−0.5 × acousticness` | **−0.5 to +0.5** |

**Maximum possible score = 5.0** (2.0 + 1.0 + 1.5 + 0.5).

In pseudocode:

```
score = 0
if song.genre == user.favorite_genre:  score += 2.0
if song.mood  == user.favorite_mood:   score += 1.0
score += 1.5 * (1 - abs(song.energy - user.target_energy))   # energy closeness
score += 0.5 * song.acousticness  if user.likes_acoustic  else  -0.5 * song.acousticness
```

Then sort all songs by `score` (highest first) and return the top `k`.

**Why these numbers:** genre is the strongest identity signal ("I'm into indie"), so it carries the most weight; mood is real but fuzzier and subjective, so it's worth half of genre; energy is a continuous value, so it's scored as a *gradient* (closer = more points) rather than a hard match; acousticness is a simple preference toggle, so it only nudges the ranking.

### Potential biases I expect

- **Genre over-prioritization.** Because a genre match (+2.0) outweighs a mood match (+1.0), the system can bury a song that perfectly fits the user's mood just because its genre label differs. Great cross-genre matches may never surface.
- **Popularity/exact-label bias.** Matching is exact-string, so `"indie"` ≠ `"indie pop"` and near-miss genres score zero. This favors songs whose labels happen to match the catalog's vocabulary and penalizes anything tagged inconsistently.
- **Middle-energy penalty for extreme tastes.** The energy gradient rewards songs near the target, so a user who wants very high or very low energy gets a narrower slice of the catalog than a user near the middle.
- **Unused signals.** `tempo_bpm`, `valence`, and `danceability` exist on each `Song` but the profile has no matching preference, so they don't influence recommendations yet — potentially good matches on those dimensions are ignored.
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

Running `python -m src.main` against the default **pop / happy / 0.8-energy** profile produces:

```
Loaded songs: 17

============================================================
  MUSIC RECOMMENDER
  Profile: genre=pop, mood=happy, energy=0.8
============================================================

1. Sunrise City - Neon Echo   (score 4.47)
     - genre match: pop (+2.0)
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.80 (+1.47)

2. Gym Hero - Max Pulse   (score 3.30)
     - genre match: pop (+2.0)
     - energy 0.93 vs target 0.80 (+1.30)

3. Rooftop Lights - Indigo Parade   (score 2.44)
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.80 (+1.44)

4. Night Drive Loop - Neon Echo   (score 1.42)
     - energy 0.75 vs target 0.80 (+1.42)

5. Pulse Reactor - Circuit Halo   (score 1.36)
     - energy 0.89 vs target 0.80 (+1.36)
```

The top result, *Sunrise City*, is the only song that matches genre **and** mood while sitting almost exactly on the target energy — exactly what we'd expect for this profile.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



