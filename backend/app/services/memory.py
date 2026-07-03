import json
import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from app.core.config import DATA_DIR


class MemoryManager:
    def __init__(self, data_dir: str = str(DATA_DIR)):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_store: Dict[str, List[Dict]] = {}
        self.short_term: Dict[str, List[str]] = {}
        self._chroma_client = None
        self._chroma_collections: Dict[str, Any] = {}
        self._init_json_store()

    def _init_json_store(self):
        store_file = self.data_dir / "memory.json"
        if store_file.exists():
            try:
                with open(store_file, "r") as f:
                    self.json_store = json.load(f)
            except Exception:
                self.json_store = {}

    def _save_json_store(self):
        store_file = self.data_dir / "memory.json"
        with open(store_file, "w") as f:
            json.dump(self.json_store, f, indent=2, default=str)

    def _get_chroma(self):
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(
                    path=str(self.data_dir / "chroma_db")
                )
            except ImportError:
                return None
        return self._chroma_client

    def _get_collection(self, namespace: str):
        if namespace not in self._chroma_collections:
            client = self._get_chroma()
            if client is None:
                return None
            self._chroma_collections[namespace] = client.get_or_create_collection(
                name=namespace,
                metadata={"hnsw:space": "cosine"}
            )
        return self._chroma_collections[namespace]

    def save_short_term(self, namespace: str, text: str):
        if namespace not in self.short_term:
            self.short_term[namespace] = []
        self.short_term[namespace].append(text)
        if len(self.short_term[namespace]) > 100:
            self.short_term[namespace] = self.short_term[namespace][-100:]

    def recall_short_term(self, namespace: str, last_n: int = 10) -> str:
        if namespace not in self.short_term:
            return "No short-term memory found."
        items = self.short_term[namespace][-last_n:]
        return "\n".join(f"[{i+1}] {item}" for i, item in enumerate(items))

    def save_long_term(self, namespace: str, text: str, metadata: Optional[Dict] = None):
        if namespace not in self.json_store:
            self.json_store[namespace] = []
        entry = {
            "text": text,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.json_store[namespace].append(entry)
        self._save_json_store()
        collection = self._get_collection(namespace)
        if collection is not None:
            try:
                entry_id = f"doc_{int(time.time() * 1000)}"
                collection.add(
                    documents=[text],
                    ids=[entry_id],
                    metadatas=[{**metadata, "timestamp": time.time()}] if metadata else [{"timestamp": time.time()}]
                )
            except Exception:
                pass

    def recall_long_term(self, namespace: str, last_n: int = 10) -> str:
        if namespace not in self.json_store or not self.json_store[namespace]:
            return "No long-term memory found."
        items = self.json_store[namespace][-last_n:]
        return "\n".join(
            f"[{i+1}] {item['text']}"
            for i, item in enumerate(items)
        )

    def search_long_term(self, namespace: str, query: str, top_k: int = 5) -> str:
        collection = self._get_collection(namespace)
        if collection is not None:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=min(top_k, collection.count() or 1)
                )
                if results and results["documents"]:
                    docs = results["documents"][0]
                    distances = results["distances"][0] if results.get("distances") else [0] * len(docs)
                    output = []
                    for doc, dist in zip(docs, distances):
                        score = max(0, 1 - dist)
                        output.append(f"[Score: {score:.2f}] {doc}")
                    return "\n\n".join(output) if output else "No matching memories found."
            except Exception as e:
                pass
        if namespace in self.json_store and self.json_store[namespace]:
            query_lower = query.lower()
            scored = []
            for item in self.json_store[namespace]:
                text = item["text"].lower()
                words = set(query_lower.split())
                text_words = set(text.split())
                overlap = len(words & text_words)
                if overlap > 0:
                    scored.append((overlap, item["text"]))
            scored.sort(key=lambda x: x[0], reverse=True)
            if scored:
                return "\n\n".join(
                    f"[Relevance: {s}] {t}" for s, t in scored[:top_k]
                )
        return "No matching memories found."

    def clear(self, namespace: str) -> str:
        if namespace in self.json_store:
            del self.json_store[namespace]
            self._save_json_store()
        if namespace in self.short_term:
            del self.short_term[namespace]
        try:
            collection = self._get_collection(namespace)
            if collection is not None:
                client = self._get_chroma()
                if client:
                    client.delete_collection(namespace)
                if namespace in self._chroma_collections:
                    del self._chroma_collections[namespace]
        except Exception:
            pass
        return f"Memory cleared for namespace: {namespace}"

    def save(self, namespace: str, text: str, memory_type: str = "long_term", metadata: Optional[Dict] = None) -> str:
        if memory_type == "short_term":
            self.save_short_term(namespace, text)
            return f"Saved to short-term memory ({namespace})"
        else:
            self.save_long_term(namespace, text, metadata)
            return f"Saved to long-term memory ({namespace})"

    def recall(self, namespace: str, memory_type: str = "long_term", last_n: int = 10) -> str:
        if memory_type == "short_term":
            return self.recall_short_term(namespace, last_n)
        else:
            return self.recall_long_term(namespace, last_n)


memory_manager = MemoryManager()
