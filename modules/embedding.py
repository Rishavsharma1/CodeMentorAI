
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR / "data" / "combined_dataset.json"

VECTOR_STORE_PATH = BASE_DIR / "vector_store"

EMBEDDINGS_PATH = VECTOR_STORE_PATH / "embeddings.npy"


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# --------------------------------------------------
# GENERATE EMBEDDINGS
# --------------------------------------------------

def generate_embeddings():

    print("Loading combined dataset...")

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not dataset:
        raise ValueError("Dataset is empty!")

    print("Total records:", len(dataset))

    # Extract natural-language questions
    questions = [
        record["question"]
        for record in dataset
    ]

    if len(questions) != len(dataset):
        raise ValueError("Dataset and question count mismatch!")

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("\nGenerating embeddings...")

    embeddings = model.encode(
        questions,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Store embeddings as float32
    embeddings = embeddings.astype("float32")

    # Create vector store directory if required
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

    # Save embeddings
    np.save(EMBEDDINGS_PATH, embeddings)

    print("\nEmbedding generation completed!")
    print("Number of embeddings:", embeddings.shape[0])
    print("Embedding dimensions:", embeddings.shape[1])
    print("Saved at:", EMBEDDINGS_PATH)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_embeddings()
