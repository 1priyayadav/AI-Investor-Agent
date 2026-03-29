"""
ChromaDB vector store for ET/news/filing RAG. Falls back to in-memory keyword search if Chroma is unavailable.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from backend.core.config import settings
from backend.utils.logger import logger


class _InMemoryStore:
    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []

    def add(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        self._docs = [d for d in self._docs if d["id"] != doc_id]
        self._docs.append({"id": doc_id, "text": text, "metadata": metadata or {}})

    def query(self, query_text: str, n_results: int, metadata_filter: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
        q = query_text.lower()
        words = set(re.findall(r"\w+", q))
        scored: list[tuple[float, dict[str, Any]]] = []
        for d in self._docs:
            md = d.get("metadata") or {}
            if metadata_filter:
                ok = all(md.get(k) == v for k, v in metadata_filter.items())
                if not ok:
                    continue
            text = d["text"].lower()
            score = sum(1 for w in words if w in text) + len(text) * 0.001
            if score > 0 or not words:
                scored.append((score, d))
        scored.sort(key=lambda x: -x[0])
        out = []
        for _, d in scored[:n_results]:
            out.append({"text": d["text"], "metadata": d.get("metadata", {})})
        return out


class VectorService:
    def __init__(self) -> None:
        self._fallback = _InMemoryStore()
        self._collection = None
        self._chroma = None
        try:
            import chromadb

            host = settings.CHROMA_HOST
            port = settings.CHROMA_PORT
            self._chroma = chromadb.HttpClient(host=host, port=port)
            self._collection = self._chroma.get_or_create_collection(
                name="et_investor_docs",
                metadata={"description": "ET Markets, filings, news"},
            )
            logger.info("ChromaDB vector service ready.")
        except Exception as e:
            logger.warning(f"ChromaDB unavailable, using in-memory vector fallback: {e}")
            self._collection = None

    def store_document(self, doc_id: str, text: str, metadata: Optional[dict[str, Any]] = None) -> None:
        metadata = metadata or {}
        if self._collection is not None:
            try:
                self._collection.upsert(
                    ids=[doc_id],
                    documents=[text],
                    metadatas=[metadata],
                )
                return
            except Exception as e:
                logger.error(f"Chroma upsert failed: {e}")
        self._fallback.add(doc_id, text, metadata)

    def query_documents(
        self,
        query_text: str,
        n_results: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        if self._collection is not None:
            try:
                where = None
                if metadata_filter:
                    parts = []
                    for k, v in metadata_filter.items():
                        parts.append({k: {"$eq": v}})
                    if len(parts) == 1:
                        where = parts[0]
                    elif len(parts) > 1:
                        where = {"$and": parts}
                res = self._collection.query(
                    query_texts=[query_text],
                    n_results=n_results,
                    where=where,
                )
                out = []
                ids = res.get("ids") or [[]]
                docs = res.get("documents") or [[]]
                metas = res.get("metadatas") or [[]]
                for i in range(len(ids[0])):
                    out.append(
                        {
                            "id": ids[0][i],
                            "text": docs[0][i],
                            "metadata": metas[0][i] if metas[0] else {},
                        }
                    )
                return out
            except Exception as e:
                logger.error(f"Chroma query failed: {e}")
        return self._fallback.query(query_text, n_results, metadata_filter)


def stable_id(prefix: str, text: str) -> str:
    return prefix + "_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


vector_service = VectorService()
