from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple

# Optional Phase 4 env override (applied on top of "balanced" strategy weights).
_EXPERIMENT = os.environ.get("MUSIC_RECOMMENDER_EXPERIMENT", "").strip().lower()


@dataclass(frozen=True)
class StrategyWeights:
    """Numeric emphasis for Genre-First / Mood-First / Energy-Focused modes."""
    w_genre: float
    w_mood: float
    w_energy_mult: float
    # Advanced features (Challenge 1) — max contribution scales
    w_popularity: float  # × (popularity/100)
    w_decade: float  # × decade similarity [0,1]
    w_mood_tag: float  # mood appears in mood_tags
    w_production: float  # bedroom vs user prefers lofi/bedroom
    w_instrumental: float  # user wants instrumental
    w_language: float  # preferred_language matches vocal_language


def _strategy_table() -> Dict[str, StrategyWeights]:
    base_adv = StrategyWeights(
        w_genre=2.0,
        w_mood=1.0,
        w_energy_mult=1.0,
        w_popularity=0.45,
        w_decade=0.85,
        w_mood_tag=0.55,
        w_production=0.35,
        w_instrumental=0.4,
        w_language=0.25,
    )
    genre_first = StrategyWeights(
        w_genre=2.85,
        w_mood=0.75,
        w_energy_mult=0.8,
        w_popularity=0.5,
        w_decade=0.9,
        w_mood_tag=0.45,
        w_production=0.3,
        w_instrumental=0.35,
        w_language=0.2,
    )
    mood_first = StrategyWeights(
        w_genre=1.1,
        w_mood=2.35,
        w_energy_mult=0.95,
        w_popularity=0.4,
        w_decade=0.75,
        w_mood_tag=0.95,
        w_production=0.4,
        w_instrumental=0.45,
        w_language=0.25,
    )
    energy_focused = StrategyWeights(
        w_genre=1.2,
        w_mood=0.85,
        w_energy_mult=2.15,
        w_popularity=0.35,
        w_decade=0.55,
        w_mood_tag=0.4,
        w_production=0.25,
        w_instrumental=0.3,
        w_language=0.15,
    )
    return {
        "balanced": base_adv,
        "genre_first": genre_first,
        "mood_first": mood_first,
        "energy_focused": energy_focused,
    }


STRATEGIES: Dict[str, StrategyWeights] = _strategy_table()


def get_strategy_weights(mode: Optional[str]) -> StrategyWeights:
    """Resolve scoring weights; unknown modes fall back to balanced."""
    m = (mode or "balanced").strip().lower()
    w = STRATEGIES.get(m, STRATEGIES["balanced"])
    if _EXPERIMENT == "weight_shift":
        return StrategyWeights(
            w_genre=1.0,
            w_mood=1.0,
            w_energy_mult=2.0,
            w_popularity=w.w_popularity,
            w_decade=w.w_decade,
            w_mood_tag=w.w_mood_tag,
            w_production=w.w_production,
            w_instrumental=w.w_instrumental,
            w_language=w.w_language,
        )
    return w


def _norm(s: str) -> str:
    """Normalize a label string for case-insensitive comparison."""
    return str(s).strip().casefold()


def energy_similarity(song_energy: float, target_energy: float) -> float:
    """Energy closeness in [0, 1] from absolute difference to target on [0, 1]."""
    return max(0.0, min(1.0, 1.0 - abs(float(song_energy) - float(target_energy))))


def _mood_tag_tokens(mood_tags: str) -> List[str]:
    return [_norm(p) for p in str(mood_tags).split("|") if p.strip()]


def _decade_similarity(song_decade: int, preferred: int) -> float:
    """1.0 same start year; falls off over ~30 years."""
    return max(0.0, 1.0 - abs(int(song_decade) - int(preferred)) / 30.0)


def compute_score_and_reasons(
    user_prefs: Dict[str, Any],
    song: Dict[str, Any],
    weights: Optional[StrategyWeights] = None,
) -> Tuple[float, List[str]]:
    """Full score: core genre/mood/energy plus optional advanced CSV features (math-based)."""
    w = weights or get_strategy_weights(user_prefs.get("scoring_mode"))
    reasons: List[str] = []
    total = 0.0

    fg = str(user_prefs["favorite_genre"])
    fm = str(user_prefs["favorite_mood"])
    te = float(user_prefs["target_energy"])
    genre = str(song["genre"])
    mood = str(song["mood"])
    energy = float(song["energy"])

    if _norm(genre) == _norm(fg):
        total += w.w_genre
        reasons.append(f"genre match (+{w.w_genre:.2f})")
    if _norm(mood) == _norm(fm):
        total += w.w_mood
        reasons.append(f"mood match (+{w.w_mood:.2f})")

    e_sim = energy_similarity(energy, te)
    energy_points = w.w_energy_mult * e_sim
    total += energy_points
    if w.w_energy_mult != 1.0:
        reasons.append(
            f"energy fit (+{energy_points:.2f}); sim {e_sim:.2f} × {w.w_energy_mult:.2f}; "
            f"song {energy:.2f} vs target {te:.2f}"
        )
    else:
        reasons.append(
            f"energy fit (+{energy_points:.2f}); song {energy:.2f} vs target {te:.2f}"
        )

    # --- Advanced features (only if columns exist on song dict) ---
    if "popularity" in song:
        pop = int(song["popularity"])
        pop_pts = w.w_popularity * (pop / 100.0)
        total += pop_pts
        reasons.append(f"popularity ({pop}/100) → +{pop_pts:.2f}")

    if "release_decade" in song and user_prefs.get("preferred_decade") is not None:
        pref_d = int(user_prefs["preferred_decade"])
        sd = int(song["release_decade"])
        d_sim = _decade_similarity(sd, pref_d)
        d_pts = w.w_decade * d_sim
        total += d_pts
        reasons.append(
            f"decade fit (+{d_pts:.2f}); song {sd}s vs preferred {pref_d}s (sim {d_sim:.2f})"
        )

    if "mood_tags" in song:
        tags = _mood_tag_tokens(str(song["mood_tags"]))
        tag_hit = _norm(fm) in tags
        if tag_hit:
            scale = 0.5 if _norm(mood) == _norm(fm) else 1.0
            tag_pts = w.w_mood_tag * scale
            total += tag_pts
            reasons.append(
                f"detailed mood tag (+{tag_pts:.2f}); '{fm}' in tags"
                + (" (half weight; primary mood already matched)" if scale < 1.0 else "")
            )

    if "production_style" in song and user_prefs.get("prefers_bedroom_production"):
        if _norm(song["production_style"]) == "bedroom":
            total += w.w_production
            reasons.append(f"bedroom/lofi production match (+{w.w_production:.2f})")

    if "instrumental" in song and user_prefs.get("wants_instrumental"):
        if int(song["instrumental"]) == 1:
            total += w.w_instrumental
            reasons.append(f"instrumental match (+{w.w_instrumental:.2f})")

    if "vocal_language" in song and user_prefs.get("preferred_language"):
        if _norm(song["vocal_language"]) == _norm(str(user_prefs["preferred_language"])):
            total += w.w_language
            reasons.append(f"language match (+{w.w_language:.2f})")

    return total, reasons


def compute_score(
    favorite_genre: str,
    favorite_mood: str,
    target_energy: float,
    genre: str,
    mood: str,
    energy: float,
) -> float:
    """Legacy numeric score using balanced weights and no advanced columns."""
    prefs = {"favorite_genre": favorite_genre, "favorite_mood": favorite_mood, "target_energy": target_energy}
    song = {"genre": genre, "mood": mood, "energy": energy}
    return compute_score_and_reasons(prefs, song, get_strategy_weights("balanced"))[0]


def score_song(
    user_prefs: Dict[str, Any],
    song: Dict[str, Any],
    *,
    scoring_mode: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """Return (score, reasons) for one catalog dict."""
    prefs = dict(user_prefs)
    if scoring_mode is not None:
        prefs = {**prefs, "scoring_mode": scoring_mode}
    return compute_score_and_reasons(prefs, song, get_strategy_weights(prefs.get("scoring_mode")))


class ScoringStrategy(Protocol):
    """Strategy protocol: plug different emphasis without changing recommend_songs callers."""

    def weights(self) -> StrategyWeights: ...


@dataclass
class ModeStrategy:
    """Concrete strategy wrapper for dependency injection / tests."""
    mode: str = "balanced"

    def weights(self) -> StrategyWeights:
        return get_strategy_weights(self.mode)


def _effective_rank_score(
    song: Dict[str, Any],
    base_score: float,
    picked: List[Dict[str, Any]],
    artist_penalty: float,
    genre_penalty: float,
) -> float:
    """Subtract diversity penalties if artist/genre already chosen (Challenge 3)."""
    adj = base_score
    artist = _norm(song["artist"])
    genre = _norm(song["genre"])
    for p in picked:
        if _norm(p["artist"]) == artist:
            adj -= artist_penalty
        if _norm(p["genre"]) == genre:
            adj -= genre_penalty
    return adj


def recommend_songs(
    user_prefs: Dict[str, Any],
    songs: List[Dict[str, Any]],
    k: int = 5,
    *,
    scoring_mode: Optional[str] = None,
    apply_diversity: bool = True,
    diversity_artist_penalty: float = 0.65,
    diversity_genre_penalty: float = 0.35,
) -> List[Tuple[Dict[str, Any], float, List[str]]]:
    """
    Score every song, then either sort by base score or greedy top-k with diversity penalties.
    """
    mode = scoring_mode or user_prefs.get("scoring_mode")
    weights = get_strategy_weights(mode)
    prefs = dict(user_prefs)
    if mode:
        prefs["scoring_mode"] = mode

    scored: List[Tuple[float, List[str], Dict[str, Any]]] = []
    for s in songs:
        total, reasons = compute_score_and_reasons(prefs, s, weights)
        scored.append((total, reasons, s))

    if not apply_diversity:
        scored.sort(key=lambda t: (-t[0], int(t[2]["id"])))
        return [(t[2], t[0], t[1]) for t in scored[:k]]

    # Greedy diversity-aware selection (Challenge 3)
    remaining = scored.copy()
    out: List[Tuple[Dict[str, Any], float, List[str]]] = []
    picked_songs: List[Dict[str, Any]] = []

    while len(out) < k and remaining:
        best_i = -1
        best_eff = -1e18
        best_sid = 10**9
        for i, (base, reasons, song) in enumerate(remaining):
            eff = _effective_rank_score(
                song, base, picked_songs, diversity_artist_penalty, diversity_genre_penalty
            )
            sid = int(song["id"])
            if eff > best_eff or (eff == best_eff and sid < best_sid):
                best_eff = eff
                best_sid = sid
                best_i = i

        base, reasons, song = remaining.pop(best_i)
        eff = _effective_rank_score(
            song, base, picked_songs, diversity_artist_penalty, diversity_genre_penalty
        )
        reasons = list(reasons)
        gap = base - eff
        if gap > 1e-6:
            reasons.append(f"diversity adjustment (−{gap:.2f}); artist/genre overlap with earlier picks")
        out.append((song, base, reasons))
        picked_songs.append(song)

    return out


@dataclass
class Song:
    """One song with metadata, audio features, and extended catalog fields."""
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
    popularity: int = 50
    release_decade: int = 2020
    mood_tags: str = ""
    production_style: str = "studio"
    instrumental: int = 0
    vocal_language: str = "en"


@dataclass
class UserProfile:
    """User taste profile: favorite genre/mood, target energy, acoustic flag."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def song_dataclass_to_dict(s: Song) -> Dict[str, Any]:
    """Flatten Song for dict-based scoring."""
    return {
        "id": s.id,
        "title": s.title,
        "artist": s.artist,
        "genre": s.genre,
        "mood": s.mood,
        "energy": s.energy,
        "tempo_bpm": s.tempo_bpm,
        "valence": s.valence,
        "danceability": s.danceability,
        "acousticness": s.acousticness,
        "popularity": s.popularity,
        "release_decade": s.release_decade,
        "mood_tags": s.mood_tags,
        "production_style": s.production_style,
        "instrumental": s.instrumental,
        "vocal_language": s.vocal_language,
    }


class Recommender:
    """Object-oriented wrapper: rank Song instances with configurable strategy."""

    def __init__(
        self,
        songs: List[Song],
        *,
        scoring_mode: str = "balanced",
        apply_diversity: bool = False,
    ):
        self.songs = songs
        self.scoring_mode = scoring_mode
        self.apply_diversity = apply_diversity

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        prefs: Dict[str, Any] = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        dicts = [song_dataclass_to_dict(s) for s in self.songs]
        ranked = recommend_songs(
            prefs,
            dicts,
            k,
            scoring_mode=self.scoring_mode,
            apply_diversity=self.apply_diversity,
        )
        ids = {int(s.id): s for s in self.songs}
        return [ids[int(r[0]["id"])] for r in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        prefs: Dict[str, Any] = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
            "scoring_mode": self.scoring_mode,
        }
        _, reasons = compute_score_and_reasons(
            prefs, song_dataclass_to_dict(song), get_strategy_weights(self.scoring_mode)
        )
        return "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict[str, Any]]:
    """Read songs CSV into dicts with typed fields including extended columns."""
    rows: List[Dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                    "popularity": int(row["popularity"]),
                    "release_decade": int(row["release_decade"]),
                    "mood_tags": row["mood_tags"],
                    "production_style": row["production_style"],
                    "instrumental": int(row["instrumental"]),
                    "vocal_language": row["vocal_language"],
                }
            )
    return rows
