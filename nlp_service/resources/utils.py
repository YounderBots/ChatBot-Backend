from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_entities(rasa_entities: list) -> dict:
    return {e["entity"]: e["value"] for e in rasa_entities}


def similarity_fallback(user_text: str, intent_phrases: dict) -> list:
    corpus = []
    intent_map = []

    for intent, phrases in intent_phrases.items():
        for p in phrases:
            corpus.append(p)
            intent_map.append(intent)

    corpus.append(user_text)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(corpus)

    user_vector = vectors[-1]
    phrase_vectors = vectors[:-1]

    similarities = cosine_similarity(user_vector, phrase_vectors)[0]

    scored = {}
    for score, intent in zip(similarities, intent_map):
        if score >= 0.35:
            scored[intent] = max(scored.get(intent, 0), score)

    return sorted(scored, key=scored.get, reverse=True)[:2]
