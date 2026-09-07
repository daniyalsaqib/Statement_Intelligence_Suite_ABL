from backend.data.policy_corpus import POLICY_DOCUMENTS
from backend.app.db.policy_vector_store import (
    create_policy_table,
    store_policy_document,
)


# Make sure the table exists
create_policy_table()


# Store every public ABL policy chunk
for document in POLICY_DOCUMENTS:

    print("Storing:", document["title"])

    store_policy_document(
        title=document["title"],
        source=document["source"],
        content=document["text"],
    )


print("Policy corpus stored successfully.")