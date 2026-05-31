"""Embeddings generation worker."""
from app.workers.celery_worker import celery_app


@celery_app.task(name="workers.embeddings.index_document")
def index_document(doc_id: str) -> dict:
    return {"doc_id": doc_id, "status": "indexed"}
