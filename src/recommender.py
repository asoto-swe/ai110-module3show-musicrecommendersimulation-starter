from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

# --- Scoring weights (the "recipe") ---
GENRE_WEIGHT = 2.0      # exact genre match
MOOD_WEIGHT = 1.0       # exact mood match (half of genre)
ENERGY_WEIGHT = 1.5     # max points for a perfect energy match, scaled by closeness
ACOUSTIC_WEIGHT = 0.5   # bonus/penalty nudge based on the user's acoustic preference

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

        # Energy — gradient: closer to the target earns more points
        energy_closeness = 1.0 - abs(song.energy - user.target_energy)
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
        """Return the top-k Songs ranked by score for the given user."""
        ranked = sorted(
            self.songs,
            key=lambda song: self._score(user, song)[0],
            reverse=True,
        )
        return ranked[:k]

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
        energy_closeness = 1.0 - abs(song.get("energy", 0.0) - target_energy)
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
    Scores and ranks songs, returning the top k.
    Each item is (song_dict, score, explanation).
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "no strong matches"
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
