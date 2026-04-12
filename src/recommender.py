import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its audio attributes loaded from songs.csv.

    Attributes:
        id: Unique song identifier.
        title: Song title.
        artist: Artist name.
        genre: Genre label (e.g. "pop", "lofi", "rock").
        mood: Mood label (e.g. "happy", "chill", "intense").
        energy: Perceived intensity, in [0, 1].
        tempo_bpm: Speed of the song in beats per minute.
        valence: Musical positiveness, in [0, 1]. Higher = happier.
        danceability: Suitability for dancing, in [0, 1].
        acousticness: Confidence the track is acoustic, in [0, 1].
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
    Represents a user's music taste preferences used to score songs.

    Attributes:
        favorite_genre: Preferred genre label (e.g. "pop", "jazz").
        favorite_mood: Preferred mood label (e.g. "happy", "relaxed").
        target_energy: Desired energy level, in [0, 1].
        likes_acoustic: True if the user prefers acoustic songs
            (acousticness >= 0.5), False for electronic/produced.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    Content-based music recommender that scores songs against a UserProfile.

    Uses score_song() internally to rank songs by weighted feature similarity
    across genre, mood, energy, and acousticness.
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k songs ranked by match score for the given user."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        scored = sorted(
            self.songs,
            key=lambda s: score_song(user_prefs, {
                "genre": s.genre,
                "mood": s.mood,
                "energy": s.energy,
                "tempo_bpm": s.tempo_bpm,
                "valence": s.valence,
                "danceability": s.danceability,
                "acousticness": s.acousticness,
            }),
            reverse=True,
        )
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language explanation of why a song was recommended."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        song_dict = {
            "genre": song.genre,
            "mood": song.mood,
            "energy": song.energy,
            "acousticness": song.acousticness,
        }
        return _build_explanation(user_prefs, song_dict)


MOOD_VALENCE = {
    "happy": 0.80, "chill": 0.55, "intense": 0.50,
    "relaxed": 0.70, "focused": 0.55, "moody": 0.35
}

def score_song(user_prefs: Dict, song: Dict) -> float:
    """
    Score a single song against a user's preferences. Returns a float in [0, 1].

    Scoring breakdown:
        - genre (0.40): binary match — 1 if genre matches, 0 otherwise.
        - mood (0.25): composite of mood match (70%) and valence similarity (30%).
        - energy (0.25): composite of energy (50%), normalized tempo (30%),
          and danceability (20%), compared against user's target_energy.
        - acousticness (0.10): binary zone check — 1 if song.acousticness >= 0.5
          matches user.likes_acoustic, 0 otherwise.

    Args:
        user_prefs: Dict with keys "genre", "mood", "energy", "likes_acoustic".
        song: Dict with keys "genre", "mood", "energy", "tempo_bpm",
              "valence", "danceability", "acousticness".

    Returns:
        Weighted score in [0, 1].
    """
    # genre: binary match (weight 0.40)
    genre_score = 1 if song["genre"] == user_prefs["genre"] else 0

    # mood: composite of mood match + valence similarity (weight 0.25)
    mood_match = 1 if song["mood"] == user_prefs["mood"] else 0
    valence_target = MOOD_VALENCE.get(user_prefs["mood"], 0.5)
    valence_sim = 1 - abs(song["valence"] - valence_target)
    mood_score = 0.7 * mood_match + 0.3 * valence_sim

    # energy: composite of energy + normalized tempo + danceability (weight 0.25)
    norm_tempo = (song["tempo_bpm"] - 60) / 92
    composite_energy = 0.5 * song["energy"] + 0.3 * norm_tempo + 0.2 * song["danceability"]
    energy_score = 1 - abs(composite_energy - user_prefs["energy"])

    # acousticness: binary zone check — >= 0.5 means acoustic (weight 0.10)
    is_acoustic = song["acousticness"] >= 0.5
    acoustic_score = 1 if is_acoustic == user_prefs["likes_acoustic"] else 0

    return (0.40 * genre_score
          + 0.25 * mood_score
          + 0.25 * energy_score
          + 0.10 * acoustic_score)


def _build_explanation(user_prefs: Dict, song: Dict) -> str:
    """
    Build a plain-language explanation of why a song matches the user's preferences.

    Checks each feature and appends a reason string if the feature matches.
    Returns a fallback string if no features match strongly.
    """
    reasons = []
    if song["genre"] == user_prefs["genre"]:
        reasons.append(f"Matches your genre ({song['genre']})")
    if song["mood"] == user_prefs["mood"]:
        reasons.append(f"Matches your mood ({song['mood']})")
    if abs(song["energy"] - user_prefs["energy"]) < 0.15:
        reasons.append("Energy is close to your target")
    if user_prefs["likes_acoustic"] and song["acousticness"] > 0.6:
        reasons.append("Has the acoustic feel you like")
    elif not user_prefs["likes_acoustic"] and song["acousticness"] < 0.4:
        reasons.append("Has the electric energy you like")
    return ". ".join(reasons) if reasons else "Decent overall match"


def load_songs(csv_path: str) -> List[Dict]:
    """
    Load songs from a CSV file and return them as a list of dicts.

    Numeric fields (energy, tempo_bpm, valence, danceability, acousticness)
    are cast to float. The id field is cast to int.

    Args:
        csv_path: Path to songs.csv relative to the working directory.

    Returns:
        List of song dicts, one per row in the CSV.
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Score and rank all songs against the user's preferences, returning the top k.

    Args:
        user_prefs: Dict with keys "genre", "mood", "energy", "likes_acoustic".
        songs: List of song dicts as returned by load_songs().
        k: Number of top results to return.

    Returns:
        List of (song_dict, score, explanation) tuples, sorted by score descending.
    """
    scored = sorted(songs, key=lambda s: score_song(user_prefs, s), reverse=True)
    results = []
    for song in scored[:k]:
        s = score_song(user_prefs, song)
        explanation = _build_explanation(user_prefs, song)
        results.append((song, s, explanation))
    return results
