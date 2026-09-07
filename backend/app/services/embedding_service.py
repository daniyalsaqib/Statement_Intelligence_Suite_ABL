from sentence_transformers import SentenceTransformer


# Load the free MiniLM embedding model
# It converts text into a 384-number vector
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embedding(text: str) -> list[float]:

    # Convert text into an embedding vector
    embedding = model.encode(text)

    # Convert NumPy array into normal Python list
    return embedding.tolist()