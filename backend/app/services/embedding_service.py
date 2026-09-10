from functools import lru_cache


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    """
    Load the embedding runtime only when Policy RAG actually needs it.

    FastEmbed uses ONNX Runtime, avoiding the much heavier
    Sentence Transformers + PyTorch runtime.
    """
    from fastembed import TextEmbedding

    return TextEmbedding(
        model_name=MODEL_NAME,
        threads=1,
    )


def create_document_embedding(
    text: str,
) -> list[float]:
    model = _get_model()

    vector = next(
        iter(
            model.passage_embed([text])
        )
    )

    return [
        float(value)
        for value in vector
    ]


def create_query_embedding(
    text: str,
) -> list[float]:
    model = _get_model()

    vector = next(
        iter(
            model.query_embed([text])
        )
    )

    return [
        float(value)
        for value in vector
    ]


# Backward-compatible helper.
def create_embedding(
    text: str,
) -> list[float]:
    return create_query_embedding(text)
