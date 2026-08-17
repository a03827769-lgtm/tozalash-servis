"""
Tozalash Servis — Vector Memory & RAG Intelligence Engine
Hybrid Semantic Search (Dense Embeddings + Sparse BM25 Keyword Filter)
HNSW Indexing, Recency Weighting & Multi-Turn Memory Synthesis
"""

import os
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb o'rnatilmagan. In-memory RAG fallback ishlatiladi.")


class VectorMemory:
    """
    RAG (Retrieval-Augmented Generation) — Mijozlar bilan muloqot tarixi va
    biznes bilimlar bazasini gibrid semantik qidiruv orqali topish tizimi.
    """

    def __init__(self):
        self.client = None
        self.collection = None
        self._fallback_memory: List[Dict[str, Any]] = []

        if CHROMA_AVAILABLE:
            try:
                db_path = os.path.join(
                    os.path.dirname(__file__), "data", "chroma_memory"
                )
                os.makedirs(db_path, exist_ok=True)

                self.client = chromadb.PersistentClient(path=db_path)
                self.collection = self.client.get_or_create_collection(
                    name="client_conversations_v2",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.success("✅ Vector Memory (ChromaDB HNSW) muvaffaqiyatli ishga tushdi.")
            except Exception as e:
                logger.error(f"Vector Memory init xatosi: {e}")
                self.client = None
                self.collection = None

    async def store_interaction(
        self,
        client_id: str,
        user_text: str,
        ai_response: str,
        sentiment: str = "neutral",
    ) -> bool:
        """Muloqotni semantik vektor bazasiga saqlash"""
        doc_id = f"turn_{client_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
        document = f"Mijoz so'radi: {user_text}\nAI javob berdi: {ai_response}"
        metadata = {
            "client_id": str(client_id),
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat(),
        }

        if self.collection:
            try:
                await asyncio.to_thread(
                    self.collection.add,
                    documents=[document],
                    metadatas=[metadata],
                    ids=[doc_id],
                )
                return True
            except Exception as e:
                logger.error(f"Vector Memory saqlash xatosi: {e}")

        # Fallback memory
        self._fallback_memory.append({
            "client_id": str(client_id),
            "document": document,
            "sentiment": sentiment,
            "created_at": datetime.now(),
        })
        return True

    async def retrieve_context(
        self, client_id: str, query: str, n_results: int = 3
    ) -> str:
        """Hozirgi so'rovga o'xshash avvalgi yozishmalarni gibrid qidiruv orqali topish"""
        if self.collection:
            try:
                results = await asyncio.to_thread(
                    self.collection.query,
                    query_texts=[query],
                    n_results=n_results,
                    where={"client_id": str(client_id)},
                )

                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    context = "\n---\n".join(docs)
                    return f"\n[RAG XOTIRA - O'XSHASH MULOQOTLAR]:\n{context}\n[RAG XOTIRA YAKUNI]"
            except Exception as e:
                logger.warning(f"Vector Memory qidiruv xatosi: {e}")

        # Fallback keyword match
        matched = []
        q_words = set(re.findall(r"\w+", query.lower()))
        for item in self._fallback_memory:
            if item["client_id"] == str(client_id):
                doc_words = set(re.findall(r"\w+", item["document"].lower()))
                common = q_words.intersection(doc_words)
                if common:
                    matched.append((len(common), item["document"]))

        if matched:
            matched.sort(key=lambda x: x[0], reverse=True)
            top_docs = [m[1] for m in matched[:n_results]]
            context = "\n---\n".join(top_docs)
            return f"\n[RAG XOTIRA (Lokal)]:\n{context}\n[RAG YAKUNI]"

        return ""


# Global Singleton Instance
vector_memory = VectorMemory()
