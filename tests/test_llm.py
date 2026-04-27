import pytest
from unittest.mock import MagicMock, patch
from src.llm import _strip_fences, parse_user_input, explain_recommendations
from recommender import UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client(response_text: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp
    return mock_client


def _recs():
    return [
        ({"title": "Chill Vibes", "artist": "Artist A", "genre": "lofi",
          "mood": "chill", "energy": 0.3, "acousticness": 0.8}, 0.92, []),
        ({"title": "Soft Rain", "artist": "Artist B", "genre": "ambient",
          "mood": "serene", "energy": 0.2, "acousticness": 0.9}, 0.85, []),
    ]


# ---------------------------------------------------------------------------
# _strip_fences — pure function, no mocking needed
# ---------------------------------------------------------------------------

def test_strip_fences_plain_json_unchanged():
    raw = '{"favorite_genre": "lofi", "favorite_mood": "chill"}'
    assert _strip_fences(raw) == raw


def test_strip_fences_removes_json_code_fence():
    raw = '```json\n{"favorite_genre": "lofi"}\n```'
    assert _strip_fences(raw) == '{"favorite_genre": "lofi"}'


def test_strip_fences_removes_plain_code_fence():
    raw = '```\n{"favorite_genre": "lofi"}\n```'
    assert _strip_fences(raw) == '{"favorite_genre": "lofi"}'


# ---------------------------------------------------------------------------
# parse_user_input
# ---------------------------------------------------------------------------

def test_parse_user_input_returns_correct_user_profile():
    payload = '{"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.3, "likes_acoustic": true}'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("tired after work")
    assert isinstance(profile, UserProfile)
    assert profile.favorite_genre == "lofi"
    assert profile.favorite_mood == "chill"
    assert abs(profile.target_energy - 0.3) < 1e-9
    assert profile.likes_acoustic is True


def test_parse_user_input_unknown_mood_defaults_to_chill():
    payload = '{"favorite_genre": "pop", "favorite_mood": "zen", "target_energy": 0.5, "likes_acoustic": false}'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("feeling zen")
    assert profile.favorite_mood == "chill"


def test_parse_user_input_unknown_genre_defaults_to_pop():
    payload = '{"favorite_genre": "bossa nova", "favorite_mood": "chill", "target_energy": 0.4, "likes_acoustic": true}'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("chill bossa nova vibes")
    assert profile.favorite_genre == "pop"


def test_parse_user_input_energy_clamped_above_one():
    payload = '{"favorite_genre": "electronic", "favorite_mood": "energetic", "target_energy": 1.5, "likes_acoustic": false}'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("max energy")
    assert profile.target_energy == 1.0


def test_parse_user_input_energy_clamped_below_zero():
    payload = '{"favorite_genre": "ambient", "favorite_mood": "serene", "target_energy": -0.3, "likes_acoustic": true}'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("very calm")
    assert profile.target_energy == 0.0


def test_parse_user_input_strips_json_fence():
    payload = '```json\n{"favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.9, "likes_acoustic": false}\n```'
    with patch("src.llm._get_client", return_value=_mock_client(payload)):
        profile = parse_user_input("rock out")
    assert profile.favorite_genre == "rock"
    assert profile.favorite_mood == "intense"


def test_parse_user_input_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        parse_user_input("test")


# ---------------------------------------------------------------------------
# explain_recommendations
# ---------------------------------------------------------------------------

def test_explain_recommendations_returns_non_empty_string():
    client = _mock_client("These songs are perfect for winding down.")
    with patch("src.llm._get_client", return_value=client):
        result = explain_recommendations("tired after work", _recs())
    assert isinstance(result, str)
    assert result.strip() != ""


def test_explain_recommendations_calls_api_exactly_once():
    client = _mock_client("Great picks for your mood.")
    with patch("src.llm._get_client", return_value=client):
        explain_recommendations("gym session", _recs())
    assert client.models.generate_content.call_count == 1


def test_explain_recommendations_includes_song_titles_in_prompt():
    client = _mock_client("Here are your picks.")
    with patch("src.llm._get_client", return_value=client):
        explain_recommendations("rainy Sunday", _recs())
    prompt = client.models.generate_content.call_args.kwargs["contents"]
    assert "Chill Vibes" in prompt
    assert "Soft Rain" in prompt
