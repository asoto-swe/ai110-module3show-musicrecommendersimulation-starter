from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

# --- Scoring weights (the "recipe") ---
GENRE_WEIGHT = 1.0      # exact genre match (halved from 2.0 in the weight-shift experiment)
MOOD_WEIGHT = 1.0       # exact mood match
ENERGY_WEIGHT = 3.0     # max points for a perfect energy match, scaled by closeness (doubled from 1.5)
ACOUSTIC_WEIGHT = 0.5   # bonus/penalty nudge based on the user's acoustic preference

# --- Diversity penalties ---
# Applied while building the top-k list: each time a song's artist (or genre) is
# already present in the songs picked so far, we subtract this many points. This
# keeps the top results from being dominated by one artist or one genre.
ARTIST_PENALTY = 2.0    # per song already chosen from the same artist
GENRE_PENALTY = 0.75    # per song already chosen from the same genre


def _diversity_rerank(entries: List[Dict], k: int) -> List[Tuple]:
    """
    Greedily pick k songs, penalizing any whose artist or genre already appears
    in the picks so far. Each entry is a dict with keys: item, base, reasons,
    artist, genre. Returns a list of (item, final_score, reasons) tuples.
    """
    # Sort by base score first so ties during selection break toward the higher raw score.
    remaining = sorted(entries, key=lambda e: e["base"], reverse=True)
    chosen: List[Tuple] = []
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}

    while remaining and len(chosen) < k:
        best = None
        best_index = 0
        best_adjusted = None
        best_penalty = (0.0, 0.0)
        for index, entry in enumerate(remaining):
            artist_pen = ARTIST_PENALTY * artist_counts.get(entry["artist"], 0)
            genre_pen = GENRE_PENALTY * genre_counts.get(entry["genre"], 0)
            adjusted = entry["base"] - artist_pen - genre_pen
            if best_adjusted is None or adjusted > best_adjusted:
                best_adjusted = adjusted
                best = entry
                best_index = index
                best_penalty = (artist_pen, genre_pen)

        remaining.pop(best_index)
        artist_pen, genre_pen = best_penalty
        reasons = list(best["reasons"])
        if artist_pen > 0:
            reasons.append(f"diversity: repeat artist (-{artist_pen:.2f})")
        if genre_pen > 0:
            reasons.append(f"diversity: repeat genre (-{genre_pen:.2f})")

        chosen.append((best["item"], best_adjusted, reasons))
        artist_counts[best["artist"]] = artist_counts.get(best["artist"], 0) + 1
        genre_counts[best["genre"]] = genre_counts.get(best["genre"], 0) + 1

    return chosen

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score a single Song against a UserProfile. Returns (score, reasons)."""
        score = 0.0
        reasons: List[str] = []

        # Genre — strongest categorical signal
        if song.genre == user.favorite_genre:
            score += GENRE_WEIGHT
            reasons.append(f"genre match: {song.genre} (+{GENRE_WEIGHT:.1f})")

        # Mood — half the weight of genre
        if song.mood == user.favorite_mood:
            score += MOOD_WEIGHT
            reasons.append(f"mood match: {song.mood} (+{MOOD_WEIGHT:.1f})")

        # Energy — gradient: closer to the target earns more points.
        # Clamp closeness to [0, 1] so an out-of-range target can't push points negative.
        energy_closeness = max(0.0, min(1.0, 1.0 - abs(song.energy - user.target_energy)))
        energy_points = ENERGY_WEIGHT * energy_closeness
        score += energy_points
        reasons.append(
            f"energy {song.energy:.2f} vs target {user.target_energy:.2f} "
            f"(+{energy_points:.2f})"
        )

        # Acousticness — small preference nudge
        if user.likes_acoustic:
            acoustic_points = ACOUSTIC_WEIGHT * song.acousticness
            score += acoustic_points
            reasons.append(f"likes acoustic ({song.acousticness:.2f}) (+{acoustic_points:.2f})")
        else:
            acoustic_points = ACOUSTIC_WEIGHT * song.acousticness
            score -= acoustic_points
            reasons.append(f"dislikes acoustic ({song.acousticness:.2f}) (-{acoustic_points:.2f})")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Songs, ranked by score and spread out by the diversity penalty."""
        entries = []
        for song in self.songs:
            base, reasons = self._score(user, song)
            entries.append({
                "item": song,
                "base": base,
                "reasons": reasons,
                "artist": song.artist,
                "genre": song.genre,
            })

        ranked = _diversity_rerank(entries, k)
        return [song for song, _score, _reasons in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable score-and-reasons string for one song."""
        score, reasons = self._score(user, song)
        return f"Score {score:.2f} — " + "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file, converting numeric columns to floats.
    Required by src/main.py
    """
    numeric_fields = {
        "energy",
        "tempo_bpm",
        "valence",
        "danceability",
        "acousticness",
    }
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song: Dict = {}
            for key, value in row.items():
                if key == "id":
                    song[key] = int(value)
                elif key in numeric_fields:
                    song[key] = float(value)
                else:
                    song[key] = value
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against user preferences (dict).
    Returns (score, reasons).

    Expected user_prefs keys: "genre", "mood", "energy",
    and optionally "likes_acoustic" (bool).
    """
    score = 0.0
    reasons: List[str] = []

    # Genre — strongest categorical signal
    if song.get("genre") == user_prefs.get("genre"):
        score += GENRE_WEIGHT
        reasons.append(f"genre match: {song.get('genre')} (+{GENRE_WEIGHT:.1f})")

    # Mood — half the weight of genre
    if song.get("mood") == user_prefs.get("mood"):
        score += MOOD_WEIGHT
        reasons.append(f"mood match: {song.get('mood')} (+{MOOD_WEIGHT:.1f})")

    # Energy — gradient: closer to the target earns more points
    target_energy = user_prefs.get("energy")
    if target_energy is not None:
        # Clamp closeness to [0, 1] so an out-of-range target can't push points negative.
        energy_closeness = max(0.0, min(1.0, 1.0 - abs(song.get("energy", 0.0) - target_energy)))
        energy_points = ENERGY_WEIGHT * energy_closeness
        score += energy_points
        reasons.append(
            f"energy {song.get('energy', 0.0):.2f} vs target {target_energy:.2f} "
            f"(+{energy_points:.2f})"
        )

    # Acousticness — small preference nudge (only if the user expressed a preference)
    likes_acoustic = user_prefs.get("likes_acoustic")
    acousticness = song.get("acousticness", 0.0)
    if likes_acoustic is True:
        acoustic_points = ACOUSTIC_WEIGHT * acousticness
        score += acoustic_points
        reasons.append(f"likes acoustic ({acousticness:.2f}) (+{acoustic_points:.2f})")
    elif likes_acoustic is False:
        acoustic_points = ACOUSTIC_WEIGHT * acousticness
        score -= acoustic_points
        reasons.append(f"dislikes acoustic ({acousticness:.2f}) (-{acoustic_points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores songs, applies the diversity penalty, and returns the top k.
    Each item is (song_dict, score, explanation).
    Required by src/main.py
    """
    entries: List[Dict] = []
    for song in songs:
        base, reasons = score_song(user_prefs, song)
        entries.append({
            "item": song,
            "base": base,
            "reasons": reasons,
            "artist": song.get("artist", ""),
            "genre": song.get("genre", ""),
        })

    ranked = _diversity_rerank(entries, k)
    return [
        (song, final_score, "; ".join(reasons) if reasons else "no strong matches")
        for song, final_score, reasons in ranked
    ]
