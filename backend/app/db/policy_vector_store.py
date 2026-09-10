import os

import psycopg
from dotenv import load_dotenv

from backend.app.services.embedding_service import (
    create_document_embedding,
    create_query_embedding,
)


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return psycopg.connect(DATABASE_URL)


def _vector_string(
    embedding: list[float],
) -> str:
    return "[" + ",".join(
        str(value)
        for value in embedding
    ) + "]"


def create_policy_table():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE EXTENSION IF NOT EXISTS vector;"
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_documents (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384) NOT NULL
                );
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def store_policy_document(
    title: str,
    source: str,
    content: str,
):
    embedding = create_document_embedding(
        content
    )

    vector_string = _vector_string(
        embedding
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO policy_documents
                    (title, source, content, embedding)
                VALUES
                    (%s, %s, %s, %s::vector)
                """,
                (
                    title,
                    source,
                    content,
                    vector_string,
                ),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def replace_policy_documents(
    documents: list[dict],
):
    """
    Replace the complete public policy corpus atomically.

    Embeddings are generated before changing the database.
    If database insertion fails, the transaction rolls back.
    """

    prepared_rows = []

    for document in documents:
        embedding = create_document_embedding(
            document["text"]
        )

        prepared_rows.append(
            (
                document["title"],
                document["source"],
                document["text"],
                _vector_string(embedding),
            )
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE policy_documents
                RESTART IDENTITY;
                """
            )

            cursor.executemany(
                """
                INSERT INTO policy_documents
                    (title, source, content, embedding)
                VALUES
                    (%s, %s, %s, %s::vector)
                """,
                prepared_rows,
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def search_policy_documents(
    question: str,
    limit: int = 3,
) -> list[dict]:

    question_embedding = (
        create_query_embedding(
            question
        )
    )

    vector_string = _vector_string(
        question_embedding
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    title,
                    source,
                    content,
                    embedding <=> %s::vector AS distance
                FROM policy_documents
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (
                    vector_string,
                    vector_string,
                    limit,
                ),
            )

            rows = cursor.fetchall()

    finally:
        connection.close()

    return [
        {
            "title": row[0],
            "source": row[1],
            "content": row[2],
            "distance": float(row[3]),
        }
        for row in rows
    ]
