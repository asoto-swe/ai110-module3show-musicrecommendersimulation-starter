"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


# Named profiles used to stress-test the scoring logic.
# The first three are "normal" tastes; the rest are adversarial / edge cases
# designed to see whether the scoring can be tricked or behaves oddly.
PROFILES = [
    # --- Normal profiles ---
    ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.9}),
    ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True}),
    ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.9}),

    # --- Adversarial / edge-case profiles ---
    # Conflicting signals: wants high energy but a sad mood (rare combo in catalog).
    ("Conflicting (sad + high energy)", {"genre": "pop", "mood": "sad", "energy": 0.95}),
    # Genre that does not exist in the catalog: mood/energy must carry the ranking.
    ("Unknown genre (kpop)", {"genre": "kpop", "mood": "happy", "energy": 0.6}),
    # Impossible energy target above the 0-1 range: how graceful is the math?
    ("Out-of-range energy (2.0)", {"genre": "edm", "mood": "euphoric", "energy": 2.0}),
    # Empty-ish profile: no genre/mood match possible, energy defaults dominate.
    ("Blank taste (empty strings)", {"genre": "", "mood": "", "energy": 0.5}),
]


def print_recommendations(name: str, user_prefs: dict, songs: list) -> None:
    """Score the catalog for one named profile and print the top 5."""
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 60)
    print(f"  PROFILE: {name}")
    prefs_line = ", ".join(f"{key}={value!r}" for key, value in user_prefs.items())
    print(f"  Prefs: {prefs_line}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} - {song['artist']}   (score {score:.2f})")
        for reason in explanation.split("; "):
            print(f"     - {reason}")

    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, user_prefs in PROFILES:
        print_recommendations(name, user_prefs, songs)


if __name__ == "__main__":
    main()
