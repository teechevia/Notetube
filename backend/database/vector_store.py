import os
import uuid

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer, CrossEncoder


PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "notetube_sources"
EMBEDDING_BATCH_SIZE = 32


class LocalEmbeddings(Embeddings):

    def __init__(self):
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        vectors = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        return vectors.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:

        vector = self.model.encode(
            [text],
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        return vector[0].tolist()


embeddings = LocalEmbeddings()

os.makedirs(
    PERSIST_DIRECTORY,
    exist_ok=True,
)


def get_vector_store():

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY,
    )


def add_documents_to_store(docs):

    if not docs:
        return

    vector_store = get_vector_store()

    total = len(docs)

    print(
        f"Embedding {total} document chunks locally..."
    )

    for start in range(
        0,
        total,
        EMBEDDING_BATCH_SIZE,
    ):

        batch = docs[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        texts = [
            doc.page_content
            for doc in batch
        ]

        metadatas = [
            doc.metadata
            for doc in batch
        ]

        ids = [
            str(uuid.uuid4())
            for _ in batch
        ]

        vectors = embeddings.embed_documents(
            texts
        )

        vector_store._collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas,
        )

        completed = min(
            start + len(batch),
            total,
        )

        print(
            f"Embedded {completed}/{total} chunks"
        )

    print(
        "Local embedding complete."
    )


def delete_source_from_store(
    source_id: int,
):

    vector_store = get_vector_store()

    vector_store._collection.delete(
        where={
            "source_id": source_id
        }
    )


def delete_notebook_from_store(
    notebook_id: int,
):

    try:

        vector_store = get_vector_store()

        vector_store._collection.delete(
            where={
                "notebook_id": notebook_id
            }
        )

    except Exception as error:

        print(
            f"Error deleting chroma notebook: {error}"
        )


# ============================================================
# RERANKER
# ============================================================

_reranker = None


def get_reranker():

    global _reranker

    if _reranker is None:

        print(
            "Loading local reranker..."
        )

        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

        print(
            "Local reranker loaded."
        )

    return _reranker


def rerank_documents(
    query: str,
    documents,
    top_k: int = 6,
):

    if not documents:
        return []

    model = get_reranker()

    pairs = [
        [
            query,
            document.page_content,
        ]
        for document in documents
    ]

    scores = model.predict(
        pairs,
        show_progress_bar=False,
    )

    ranked = sorted(
        zip(documents, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        document
        for document, score in ranked[:top_k]
    ]

def get_neighbor_chunks(
    documents,
    window: int = 2,
):
    """
    Expand retrieved chunks with nearby chunks from the same source.

    This preserves local document structure, so a retrieved heading,
    definition, or model reference can bring along its explanation.
    """

    if not documents:
        return []

    vector_store = get_vector_store()
    collection = vector_store._collection

    expanded = []
    seen = set()

    for doc in documents:
        source_id = doc.metadata.get("source_id")
        chunk_index = doc.metadata.get("chunk_index")

        if source_id is None or chunk_index is None:
            continue

        try:
            chunk_index = int(chunk_index)
        except (TypeError, ValueError):
            continue

        start = max(0, chunk_index - window)
        end = chunk_index + window

        result = collection.get(
            where={
                "$and": [
                    {"source_id": source_id},
                    {"chunk_index": {"$gte": start}},
                    {"chunk_index": {"$lte": end}},
                ]
            },
            include=["documents", "metadatas"],
        )

        documents_data = result.get("documents", [])
        metadatas_data = result.get("metadatas", [])

        for content, metadata in zip(
            documents_data,
            metadatas_data,
        ):
            key = (
                metadata.get("source_id"),
                metadata.get("chunk_index"),
            )

            if key in seen:
                continue

            seen.add(key)

            from langchain_core.documents import Document

            expanded.append(
                Document(
                    page_content=content,
                    metadata=metadata,
                )
            )

    return expanded