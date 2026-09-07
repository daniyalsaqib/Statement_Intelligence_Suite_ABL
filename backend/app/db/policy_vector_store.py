import os

import psycopg
from dotenv import load_dotenv

from backend.app.services.embedding_service import create_embedding


# Load values from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(DATABASE_URL)


def create_policy_table():

    connection = get_connection()

    with connection.cursor() as cursor:

        # Enable pgvector
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Store public ABL policy chunks and their embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384) NOT NULL
            );
        """)

    connection.commit()
    connection.close()


def store_policy_document(title: str, source: str, content: str):

    # Convert policy text into a 384-dimensional vector
    embedding = create_embedding(content)

    # pgvector expects vectors in this format:
    # [0.12,-0.45,0.33,...]
    vector_string = "[" + ",".join(
        str(value) for value in embedding
    ) + "]"

    connection = get_connection()

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
    connection.close()


def search_policy_documents(question: str, limit: int = 3) -> list[dict]:

    # Convert the user's question into the same 384-dimensional vector
    question_embedding = create_embedding(question)

    vector_string = "[" + ",".join(
        str(value) for value in question_embedding
    ) + "]"

    connection = get_connection()

    with connection.cursor() as cursor:

        # <=> calculates cosine distance between vectors
        # Smaller distance = more semantically similar
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