"""
Music Recommender CLI: stress profiles, scoring modes, diversity, tabulate output.

Run from repo root::

    python -m src.main

Scoring mode (Challenge 2 — Strategy pattern via ``get_strategy_weights``)::

    SCORING_MODE=genre_first python -m src.main
    SCORING_MODE=mood_first python -m src.main
    SCORING_MODE=energy_focused python -m src.main

Compare all modes on the first profile only::

    SHOW_MODE_COMPARE=1 python -m src.main

Phase 4 weight experiment still supported::

    MUSIC_RECOMMENDER_EXPERIMENT=weight_shift python -m src.main
"""

import os
from typing import Any, Dict, List, Tuple

from tabulate import tabulate

from src.recommender import load_songs, recommend_songs

_OUT_WIDTH = 72

STRESS_PROFILES: List[Tuple[str, Dict[str, Any]]] = [
    (
        "High-Energy Pop",
        {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.92,
            "likes_acoustic": False,
            "preferred_decade": 2020,
            "preferred_language": "en",
        },
    ),
    (
        "Chill Lofi",
        {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.35,
            "likes_acoustic": True,
            "preferred_decade": 2020,
            "prefers_bedroom_production": True,
            "wants_instrumental": True,
        },
    ),
    (
        "Deep Intense Rock",
        {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.88,
            "likes_acoustic": False,
            "preferred_decade": 2010,
        },
    ),
]

EDGE_PROFILES: List[Tuple[str, Dict[str, Any]]] = [
    (
        "Adversarial: very high energy + somber mood",
        {
            "favorite_genre": "pop",
            "favorite_mood": "somber",
            "target_energy": 0.95,
            "likes_acoustic": False,
            "preferred_decade": 2020,
        },
    ),
    (
        "Edge: melancholic classical + low energy",
        {
            "favorite_genre": "classical",
            "favorite_mood": "melancholic",
            "target_energy": 0.25,
            "likes_acoustic": True,
            "preferred_decade": 1990,
        },
    ),
    (
        "Edge: jazz + relaxed",
        {
            "favorite_genre": "jazz",
            "favorite_mood": "relaxed",
            "target_energy": 0.45,
            "likes_acoustic": True,
        },
    ),
]

SCORING_MODES = ("balanced", "genre_first", "mood_first", "energy_focused")


def _print_profile_section(title: str, prefs: Dict[str, Any], scoring_mode: str) -> None:
    """Print a labeled block for one user profile."""
    banner = "=" * _OUT_WIDTH
    print(banner)
    print(f"  PROFILE: {title}")
    print(f"  genre={prefs['favorite_genre']!r}  mood={prefs['favorite_mood']!r}  "
          f"target_energy={prefs['target_energy']}")
    print(f"  SCORING_MODE={scoring_mode!r}  (diversity penalties on)")
    print(banner)


def _print_recommendations_table(
    recommendations: List[Tuple[Dict[str, Any], float, List[str]]],
) -> None:
    """Challenge 4: tabular output including concatenated reasons."""
    rows = []
    for i, (song, score, reasons) in enumerate(recommendations, start=1):
        reasons_cell = " \n".join(reasons)
        rows.append(
            [
                i,
                song.get("title", ""),
                song.get("artist", ""),
                song.get("genre", ""),
                f"{score:.2f}",
                reasons_cell,
            ]
        )
    headers = ["#", "Title", "Artist", "Genre", "Score", "Reasons (scoring)"]
    print(tabulate(rows, headers=headers, tablefmt="grid", stralign="left"))


def _mode_compare_first_profile(songs: List[Dict[str, Any]]) -> None:
    """Print top-5 for each strategy on the first stress profile."""
    title, prefs = STRESS_PROFILES[0]
    print("\n" + "=" * _OUT_WIDTH)
    print("  MODE COMPARE (Challenge 2) — same profile, different strategies")
    print("  Profile:", title)
    print("=" * _OUT_WIDTH + "\n")
    for mode in SCORING_MODES:
        print(f"\n--- scoring_mode={mode!r} ---\n")
        rec = recommend_songs(
            prefs, songs, k=5, scoring_mode=mode, apply_diversity=True,
        )
        _print_recommendations_table(rec)


def main() -> None:
    """Load CSV, run profiles with selected scoring mode and diversity-aware ranking."""
    songs = load_songs("data/songs.csv")
    scoring_mode = os.environ.get("SCORING_MODE", "balanced").strip().lower()
    if scoring_mode not in SCORING_MODES:
        scoring_mode = "balanced"

    print(f"Loaded songs: {len(songs)}")
    exp = os.environ.get("MUSIC_RECOMMENDER_EXPERIMENT", "").strip()
    if exp:
        print(f"(MUSIC_RECOMMENDER_EXPERIMENT={exp!r})")
    print(f"(SCORING_MODE={scoring_mode!r})")
    print()

    if os.environ.get("SHOW_MODE_COMPARE", "").strip() in ("1", "true", "yes"):
        _mode_compare_first_profile(songs)
        return

    all_profiles = [("Stress test — " + n, p) for n, p in STRESS_PROFILES]
    all_profiles += [("Edge / adversarial — " + n, p) for n, p in EDGE_PROFILES]

    for title, user_prefs in all_profiles:
        _print_profile_section(title, user_prefs, scoring_mode)
        recommendations = recommend_songs(
            user_prefs,
            songs,
            k=5,
            scoring_mode=scoring_mode,
            apply_diversity=True,
            diversity_artist_penalty=0.65,
            diversity_genre_penalty=0.35,
        )
        _print_recommendations_table(recommendations)
        print()


if __name__ == "__main__":
    main()
