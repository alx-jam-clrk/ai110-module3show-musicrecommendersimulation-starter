"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    #Load songs from CSV
    songs = load_songs("data/songs.csv")
    print("Loaded songs: " + str(len(songs)))
 
    # Taste profile
    user_prefs = {"genre": "pop", "mood": "relaxed", "energy": 0.71, "likes_acoustic": True}
    energy_paradox = {"genre": "lofi", "mood": "chill", "energy": 0.0, "likes_acoustic": True}
    genre_intruder = {"genre": "synthwave", "mood": "chill", "energy": 0.40, "likes_acoustic": True}
    valence_trap = {"genre": "jazz", "mood": "happy", "energy": 0.40, "likes_acoustic": True}
    
    recommendations = recommend_songs(valence_trap, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
