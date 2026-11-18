
import json
import numpy as np
import faiss
from pathlib import Path


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

EMBEDDINGS_PATH = BASE_DIR / "vector_store" / "embeddings.npy"

DATASET_PATH = BASE_DIR / "data" / "combined_dataset.json"

INDEX_PATH = BASE_DIR / "vector_store" / "code_index.faiss"

METADATA_PATH = BASE_DIR / "vector_store" / "metadata.json"


# --------------------------------------------------
# BUILD FAISS VECTOR DATABASE
# --------------------------------------------------

def build_vector_database():

    print("Loading combined dataset...")

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    print("Total dataset records:", len(dataset))

    print("\nLoading embeddings...")

    embeddings = np.load(EMBEDDINGS_PATH)
    embeddings = embeddings.astype("float32")

    print("Embeddings shape:", embeddings.shape)

    # Verify that dataset and embeddings match
    if len(dataset) != embeddings.shape[0]:
        raise ValueError(
            f"Dataset and embeddings mismatch! "
            f"Dataset: {len(dataset)}, "
            f"Embeddings: {embeddings.shape[0]}"
        )

    # Create FAISS index
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    # Add embeddings
    index.add(embeddings)

    print("Total vectors added:", index.ntotal)

    # Verify index count
    if index.ntotal != len(dataset):
        raise ValueError("FAISS index and dataset count mismatch!")

    # Save FAISS index
    faiss.write_index(index, str(INDEX_PATH))

    # Save corresponding metadata in the same order
    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=4, ensure_ascii=False)

    print("\nFAISS vector database created successfully!")

    print("Index saved at:", INDEX_PATH)
    print("Metadata saved at:", METADATA_PATH)


if __name__ == "__main__":
    build_vector_database()
