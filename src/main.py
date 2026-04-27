"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import json
import logging
import os
import sys
from recommender import load_songs, recommend_songs

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")

USERS = {
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood":  "chill",
        "target_energy":  0.40,
        "likes_acoustic": True,
    },
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood":  "happy",
        "target_energy":  0.80,
        "likes_acoustic": False,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood":  "intense",
        "target_energy":  0.90,
        "likes_acoustic": False,
    },

    # --- ADVERSARIAL / EDGE CASE PROFILES ---

    # sad→aggressive = 0.0, so mood contributes nothing (35% weight zeroed out).
    # genre+energy (50%) dominate — expect "Shattered Glass" to rank high
    # despite being the emotional opposite of what was requested.
    "Sad Headbanger": {
        "favorite_genre": "metal",
        "favorite_mood":  "sad",
        "target_energy":  0.97,
        "likes_acoustic": False,
    },


    # likes_acoustic=True conflicts with target_energy=0.90 — every high-energy
    # song in the catalog has near-zero acousticness and vice versa.
    # The 15% acoustic weight is overwhelmed; expect acoustic_score ≈ 0.006.
    "Acoustic Headbanger": {
        "favorite_genre": "rock",
        "favorite_mood":  "intense",
        "target_energy":  0.90,
        "likes_acoustic": True,
    },

    # target_energy=0.385 is equidistant from Library Rain (0.35) and
    # Midnight Coding (0.42) — both perfect lofi/chill matches.
    # Acousticness becomes the only tiebreaker, acting as a hidden ranking signal.
    "Lofi Minimalist": {
        "favorite_genre": "lofi",
        "favorite_mood":  "chill",
        "target_energy":  0.385,
        "likes_acoustic": False,
    },

    # romantic→aggressive = 0.0, low energy, and likes_acoustic=True all point
    # away from metal. Expect "Ivory Rain" (classical) to beat "Shattered Glass"
    # (~0.52 vs ~0.26) — genre alone (25%) loses to three aligned dimensions.
    "Romantic Metalhead": {
        "favorite_genre": "metal",
        "favorite_mood":  "romantic",
        "target_energy":  0.30,
        "likes_acoustic": True,
    },

    # serene→energetic = 0.0: no high-energy song earns mood credit, no serene
    # song can match target_energy=0.90. The system must choose between a mood
    # match with wrong energy or an energy match with zero mood score.
    "Tired Raver": {
        "favorite_genre": "electronic",
        "favorite_mood":  "serene",
        "target_energy":  0.90,
        "likes_acoustic": False,
    },

    # target_energy=1.0 is the hard ceiling — the Gaussian is asymmetric here.
    # "Shattered Glass" (energy=0.97) may beat "Gym Hero" (energy=0.93) because
    # a 0.04 energy edge outweighs the genre gap, surfacing metal for a pop fan.
    "Max Energy Seeker": {
        "favorite_genre": "pop",
        "favorite_mood":  "intense",
        "target_energy":  1.0,
        "likes_acoustic": False,
    },

    # --- DIVERSITY PENALTY TEST PROFILES ---

    # Neon Echo has 4 songs spanning synthwave/pop — this profile scores 3 of
    # them highly enough that without the penalty all top-3 slots go to Neon Echo.
    # With artist_decay=0.5, later picks are penalized and other artists surface.
    "Neon Echo Fan": {
        "favorite_genre": "synthwave",
        "favorite_mood":  "energetic",
        "target_energy":  0.85,
        "likes_acoustic": False,
    },

    # LoRoom has 4 lofi songs — a lofi+focused profile scores all four above
    # non-lofi alternatives, making the top-4 LoRoom-only without the penalty.
    # With artist_decay=0.5, repeat picks are halved, surfacing other lofi artists.
    "LoRoom Fan": {
        "favorite_genre": "lofi",
        "favorite_mood":  "focused",
        "target_energy":  0.40,
        "likes_acoustic": True,
    },
}


def print_recommendations(label: str, recommendations) -> None:
    try:
        from tabulate import tabulate
        use_tabulate = True
    except ImportError:
        use_tabulate = False

    header = f" User Profile: {label} "
    bar = "=" * max(50, len(header) + 2)
    print(f"\n{bar}\n{header}\n{bar}")

    if use_tabulate:
        rows = []
        for rank, (song, score, explanation) in enumerate(recommendations, 1):
            reason_lines = explanation.split("\n")
            first = reason_lines[0].strip()
            rest  = "\n".join("  " + r.strip() for r in reason_lines[1:])
            reasons_cell = first + ("\n" + rest if rest else "")
            rows.append([rank, song["title"], song["artist"], f"{score:.2f}", reasons_cell])

        print(tabulate(
            rows,
            headers=["#", "Title", "Artist", "Score", "Reasons"],
            tablefmt="simple",
            colalign=("right", "left", "left", "right", "left"),
        ))
    else:
        # Fallback: plain ASCII if tabulate is not installed
        for rank, (song, score, explanation) in enumerate(recommendations, 1):
            title_artist = f"{rank}. {song['title']} — {song['artist']}"
            print(f"\n  {title_artist:<45}  Score: {score:.2f}")
            for reason in explanation.split("\n"):
                print(f"     {reason.strip()}")

def interactive_mode(songs: list) -> None:
    try:
        from llm import parse_user_input, explain_recommendations
    except ImportError as e:
        print(f"LLM module unavailable: {e}")
        return

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print("\nMoodLense 1.0 — Natural Language Mode")
    print("Describe what you're in the mood for. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            break

        try:
            profile = parse_user_input(user_input)
            acoustic_label = "acoustic" if profile.likes_acoustic else "electronic"
            print(
                f"\n  [Parsed] genre={profile.favorite_genre}  "
                f"mood={profile.favorite_mood}  "
                f"energy={profile.target_energy:.2f}  "
                f"sound={acoustic_label}"
            )
            prefs = {
                "favorite_genre": profile.favorite_genre,
                "favorite_mood":  profile.favorite_mood,
                "target_energy":  profile.target_energy,
                "likes_acoustic": profile.likes_acoustic,
            }
            recs = recommend_songs(prefs, songs, k=5)
            print_recommendations(f'"{user_input}"', recs)

            explanation = explain_recommendations(user_input, recs)
            print(f"\n  Why these songs:\n  {explanation}\n")

        except json.JSONDecodeError as e:
            logging.error("Could not parse LLM output: %s", e)
            print("  Could not understand that — try rephrasing.\n")
        except Exception as e:
            logging.error("Error: %s", e)
            print(f"  Error: {e}\n")


def main() -> None:
    songs = load_songs(DATA_PATH)
    print(f"Loaded songs: {len(songs)}")

    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_mode(songs)
    else:
        for label, user_prefs in USERS.items():
            recommendations = recommend_songs(user_prefs, songs, k=5)
            print_recommendations(label, recommendations)


if __name__ == "__main__":
    main()
