
import json
import re
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_PATH = BASE_DIR / "vector_store" / "code_index.faiss"
METADATA_PATH = BASE_DIR / "vector_store" / "metadata.json"


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# --------------------------------------------------
# KEYWORD UTILITIES
# --------------------------------------------------

STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "to", "of",
    "in", "on", "for", "and", "or", "with", "using",
    "use", "how", "can", "i", "we", "you", "write",
    "create", "implement", "function", "python"
}


def extract_keywords(text):
    """Extract meaningful words from a question."""

    words = re.findall(r"[a-zA-Z_]+", text.lower())

    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def calculate_keyword_score(query, candidate):
    """Calculate keyword overlap between two questions."""

    query_words = extract_keywords(query)
    candidate_words = extract_keywords(candidate)

    if not query_words:
        return 0.0

    common_words = query_words.intersection(candidate_words)

    return len(common_words) / len(query_words)


# --------------------------------------------------
# CODE RETRIEVER CLASS
# --------------------------------------------------

class CodeRetriever:

    def __init__(self):

        print("Loading FAISS index...")

        self.index = faiss.read_index(str(INDEX_PATH))

        print("Loading metadata...")

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            self.metadata = json.load(file)

        print("Loading embedding model...")

        self.model = SentenceTransformer(MODEL_NAME)

        print("Code retriever initialized successfully!")

    # --------------------------------------------------
    # HYBRID SEARCH
    # --------------------------------------------------

    def search(self, query, top_k=5):

        if not isinstance(query, str) or not query.strip():
            return []

        if top_k <= 0:
            return []

        # Search a larger candidate pool before reranking.
        candidate_count = min(
            self.index.ntotal,
            max(top_k * 10, 50)
        )

        # Convert query into an embedding.
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        query_embedding = query_embedding.astype("float32")

        # Retrieve semantic candidates from FAISS.
        scores, indices = self.index.search(
            query_embedding,
            candidate_count
        )

        results = []

        # Calculate combined relevance scores.
        for semantic_score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            if idx >= len(self.metadata):
                continue

            record = self.metadata[idx]

            question = record.get("question", "")
            code = record.get("code", "")

            keyword_score = calculate_keyword_score(
                query,
                question
            )

            # Combined ranking:
            # 75% semantic similarity
            # 25% keyword relevance

            combined_score = (
                0.75 * float(semantic_score)
                + 0.25 * keyword_score
            )

            results.append({
                "question": question,
                "code": code,
                "similarity_score": float(semantic_score),
                "keyword_score": float(keyword_score),
                "combined_score": float(combined_score)
            })

        # Sort using combined relevance.
        results.sort(
            key=lambda item: item["combined_score"],
            reverse=True
        )

        return results[:top_k]


# --------------------------------------------------
# TEST RETRIEVER
# --------------------------------------------------

if __name__ == "__main__":

    retriever = CodeRetriever()

    test_query = (
        "Write a Python function to calculate "
        "the factorial of a number using recursion."
    )

    print("\nSearching for:", test_query)

    results = retriever.search(test_query, top_k=5)

    print("\nRetrieved examples:\n")

    for i, result in enumerate(results, start=1):

        print(f"Example {i}")
        print("Question:", result["question"])
        print("Semantic Score:", round(result["similarity_score"], 4))
        print("Keyword Score:", round(result["keyword_score"], 4))
        print("Combined Score:", round(result["combined_score"], 4))
        print("Code:")
        print(result["code"])
        print("-" * 60)
