"""
Gemini integration for MoodLense.

parse_user_input:        specialized prompting — natural language -> UserProfile
explain_recommendations: RAG — retrieved song metadata grounds the explanation
"""

import json
import logging
import os
from pathlib import Path
from google import genai
from google.genai import types
from recommender import UserProfile

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.0-flash-lite"

VALID_MOODS = {
    "chill", "relaxed", "focused", "moody", "happy", "intense",
    "melancholic", "nostalgic", "romantic", "sad", "serene",
    "energetic", "aggressive", "tense",
}
VALID_GENRES = {
    "lofi", "ambient", "jazz", "synthwave", "pop", "rock",
    "soul", "metal", "country", "electronic", "r&b", "folk",
    "drum and bass", "classical", "indie pop",
}

# Few-shot examples teach Gemini the exact vocabulary score_song() expects.
_PARSE_SYSTEM = """\
You are a music taste parser for MoodLense, a recommendation system.
Convert the user's description into structured music preferences.

Valid moods: chill, relaxed, focused, moody, happy, intense, melancholic, nostalgic, romantic, sad, serene, energetic, aggressive, tense
Valid genres: lofi, ambient, jazz, synthwave, pop, rock, soul, metal, country, electronic, r&b, folk, drum and bass, classical, indie pop

Energy: 0.0 = completely quiet/calm  ->  1.0 = maximum intensity
Acousticness: true = natural/organic instruments  |  false = electronic/produced

Respond ONLY with valid JSON. No explanation. Schema:
{"favorite_genre": str, "favorite_mood": str, "target_energy": float, "likes_acoustic": bool}

Examples:
"tired after work, need something soft" -> {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.30, "likes_acoustic": true}
"hype me up, gym session" -> {"favorite_genre": "electronic", "favorite_mood": "energetic", "target_energy": 0.95, "likes_acoustic": false}
"rainy Sunday, nostalgic vibes" -> {"favorite_genre": "folk", "favorite_mood": "nostalgic", "target_energy": 0.35, "likes_acoustic": true}
"sad and heavy, nothing light" -> {"favorite_genre": "metal", "favorite_mood": "melancholic", "target_energy": 0.70, "likes_acoustic": false}
"focus mode, coding late at night" -> {"favorite_genre": "lofi", "favorite_mood": "focused", "target_energy": 0.42, "likes_acoustic": false}
"""


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to .env: GEMINI_API_KEY=your-key"
        )
    return genai.Client(api_key=api_key.strip())


def _strip_fences(text: str) -> str:
    """Remove markdown code fences Gemini sometimes wraps around JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]  # slice, not lstrip — avoids stripping JSON characters
    return text.strip()


def parse_user_input(text: str) -> UserProfile:
    """Map natural language to a structured UserProfile."""
    client = _get_client()
    logger.info("parse_user_input | input=%r", text)

    response = client.models.generate_content(
        model=_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=_PARSE_SYSTEM,
            max_output_tokens=150,
            temperature=0.1,
        ),
    )

    raw = _strip_fences(response.text)
    logger.info("parse_user_input | llm_output=%s", raw)

    data = json.loads(raw)

    mood  = data.get("favorite_mood",  "chill")
    genre = data.get("favorite_genre", "pop")
    if mood not in VALID_MOODS:
        logger.warning("Unknown mood %r — defaulting to 'chill'", mood)
        mood = "chill"
    if genre not in VALID_GENRES:
        logger.warning("Unknown genre %r — defaulting to 'pop'", genre)
        genre = "pop"

    return UserProfile(
        favorite_genre=genre,
        favorite_mood=mood,
        target_energy=max(0.0, min(1.0, float(data.get("target_energy", 0.5)))),
        likes_acoustic=bool(data.get("likes_acoustic", False)),
    )


def explain_recommendations(user_input: str, recommendations: list) -> str:
    """Generate a plain-English explanation grounded in retrieved song metadata."""
    client = _get_client()

    catalog_context = "\n".join(
        f"  {i + 1}. {song['title']} by {song['artist']}"
        f" | genre: {song['genre']}, mood: {song['mood']}"
        f", energy: {song['energy']:.2f}, acousticness: {song['acousticness']:.2f}"
        f" | match score: {score:.2f}"
        for i, (song, score, _) in enumerate(recommendations)
    )

    prompt = (
        f'A user said: "{user_input}"\n\n'
        f"Retrieved songs from catalog:\n{catalog_context}\n\n"
        "Write 2-3 warm, friendly sentences explaining why these songs fit the user's mood. "
        "Name at least two specific songs and mention one concrete attribute "
        "(mood, energy level, or acoustic feel). No bullet points."
    )

    logger.info("explain_recommendations | songs=%d", len(recommendations))

    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=250),
    )

    result = response.text.strip()
    logger.info("explain_recommendations | chars=%d", len(result))
    return result
