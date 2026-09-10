from backend.data.policy_corpus import (
    POLICY_DOCUMENTS,
)
from backend.app.db.policy_vector_store import (
    create_policy_table,
    replace_policy_documents,
)


create_policy_table()

print(
    "Preparing and replacing public ABL policy corpus..."
)

replace_policy_documents(
    POLICY_DOCUMENTS
)

print(
    f"Policy corpus stored successfully: "
    f"{len(POLICY_DOCUMENTS)} documents."
)
