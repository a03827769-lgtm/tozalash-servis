import os
import json
import chromadb
from loguru import logger
from datetime import datetime

class MemoryManager:
    """
    AgentDB-style Memory System using ChromaDB.
    Provides semantic search and persistent memory for the 50-agent swarm.
    """
    def __init__(self, db_path="data/chroma_memory"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="swarm_patterns",
                metadata={"hnsw:space": "cosine"}
            )
            logger.success("MemoryManager: Swarm 'Brain' (ChromaDB) successfully initialized.")
        except Exception as e:
            logger.error(f"MemoryManager: Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def retrieve_with_reasoning(self, query: str, n_results: int = 3) -> list:
        """
        Search the memory for similar past interactions (Patterns).
        """
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results and results.get("documents") and results["documents"][0]:
                logger.info(f"MemoryManager: Found {len(results['documents'][0])} relevant memories for query.")
                memories = []
                for idx, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][idx]
                    memories.append({
                        "content": doc,
                        "metadata": metadata
                    })
                return memories
            return []
        except Exception as e:
            logger.error(f"MemoryManager: Retrieval error: {e}")
            return []

    def store_pattern(self, user_query: str, agent_name: str, response: str, success: bool = True):
        """
        Learn a pattern and store it in long-term memory.
        """
        if not self.collection:
            return False
            
        try:
            pattern_id = f"pattern_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            pattern_text = f"User asked: {user_query}\nAgent ({agent_name}) responded: {response}"
            
            metadata = {
                "agent": agent_name,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            self.collection.add(
                documents=[pattern_text],
                metadatas=[metadata],
                ids=[pattern_id]
            )
            logger.info(f"MemoryManager: Learned new pattern -> {pattern_id}")
            return True
        except Exception as e:
            logger.error(f"MemoryManager: Failed to store pattern: {e}")
            return False

# Global instance
memory_db = MemoryManager()
