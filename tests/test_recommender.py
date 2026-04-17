from src.recommender import Song, UserProfile, Recommender, recommend_songs, score_song

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_score_song_returns_numeric_score_and_reason_strings():
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
    }
    song = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
    }
    total, reasons = score_song(user_prefs, song)
    assert total == 4.0
    assert isinstance(reasons, list)
    assert any("genre match (+2." in r for r in reasons)
    assert any("mood match (+1." in r for r in reasons)
    assert any(r.startswith("energy fit (+") for r in reasons)


def test_recommend_songs_diversity_appends_reason_when_genre_repeats():
    """Second pick same genre as first should note diversity adjustment (Challenge 3)."""
    songs = [
        {
            "id": 1,
            "title": "A",
            "artist": "Artist1",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.9,
            "tempo_bpm": 120.0,
            "valence": 0.8,
            "danceability": 0.8,
            "acousticness": 0.2,
            "popularity": 50,
            "release_decade": 2020,
            "mood_tags": "happy",
            "production_style": "studio",
            "instrumental": 0,
            "vocal_language": "en",
        },
        {
            "id": 2,
            "title": "B",
            "artist": "Artist2",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.88,
            "tempo_bpm": 118.0,
            "valence": 0.8,
            "danceability": 0.8,
            "acousticness": 0.2,
            "popularity": 40,
            "release_decade": 2020,
            "mood_tags": "happy",
            "production_style": "studio",
            "instrumental": 0,
            "vocal_language": "en",
        },
        {
            "id": 3,
            "title": "C",
            "artist": "Artist3",
            "genre": "rock",
            "mood": "happy",
            "energy": 0.5,
            "tempo_bpm": 100.0,
            "valence": 0.5,
            "danceability": 0.5,
            "acousticness": 0.5,
            "popularity": 30,
            "release_decade": 2020,
            "mood_tags": "happy",
            "production_style": "studio",
            "instrumental": 0,
            "vocal_language": "en",
        },
    ]
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.9}
    out = recommend_songs(prefs, songs, k=2, scoring_mode="balanced", apply_diversity=True)
    joined = " ".join(" ".join(r) for _, _, r in out)
    assert "diversity adjustment" in joined


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
