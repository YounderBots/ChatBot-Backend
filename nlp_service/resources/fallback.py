from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Temporary in-memory intent phrases
# Later → load from Admin Service / DB
INTENT_PHRASES = {
    "billing_issue": ["billing problem", "payment failed", "invoice not generated"],
    "subscription_issue": [
        "cancel subscription",
        "upgrade plan",
        "subscription expired",
    ],
    "technical_issue": ["app not working", "unable to login", "system error"],
}


def suggest_similar_intents(
    user_text: str, threshold: float = 0.35, top_k: int = 2
) -> list:
    """
    Returns a list of intent names that are semantically
    close to the user message.
    """

    corpus = []
    intent_index = []

    # Flatten phrases
    for intent, phrases in INTENT_PHRASES.items():
        for phrase in phrases:
            corpus.append(phrase)
            intent_index.append(intent)

    # Add user text at the end
    corpus.append(user_text)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(corpus)

    user_vector = vectors[-1]
    intent_vectors = vectors[:-1]

    similarities = cosine_similarity(user_vector, intent_vectors)[0]

    scored_intents = {}

    for score, intent in zip(similarities, intent_index):
        if score >= threshold:
            scored_intents[intent] = max(scored_intents.get(intent, 0), score)

    # Sort intents by similarity score
    sorted_intents = sorted(scored_intents.items(), key=lambda x: x[1], reverse=True)

    return [intent for intent, _ in sorted_intents[:top_k]]
