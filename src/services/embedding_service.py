import chromadb

from src.config import settings

chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)


class EmbeddingService:
    def __init__(self, client: chromadb.ClientAPI, collection_name: str) -> None:
        self._collection = client.get_or_create_collection(name=collection_name)

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict] | None = None) -> None:
        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 5) -> dict:
        return self._collection.query(query_texts=[query_text], n_results=n_results)

    def delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)


embedding_service = EmbeddingService(chroma_client, settings.chroma_collection_name)


def get_embedding_service() -> EmbeddingService:
    return embedding_service
