"""
RAG AI Workbench Application Template
Retrieval-Augmented Generation pipeline with vector search and document processing

Dependencies: Agent 4/5 (inference)
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document in the RAG system"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            # Generate ID from content hash
            self.id = hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class RetrievalResult:
    """Result from vector search"""
    document: Document
    score: float
    rank: int


@dataclass
class RAGResponse:
    """Response from RAG pipeline"""
    query: str
    answer: str
    retrieved_documents: List[RetrievalResult]
    generation_metadata: Dict[str, Any]


class EmbeddingService:
    """
    Service for generating embeddings using Agent 4/5 inference
    """

    def __init__(self, agent_url: str = "http://localhost:8000"):
        self.agent_url = agent_url

    async def embed_text(self, text: str, model: str = "text-embedding-ada-002") -> np.ndarray:
        """
        Generate embedding for text using inference agent

        Args:
            text: Input text to embed
            model: Embedding model identifier

        Returns:
            Embedding vector as numpy array
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/embeddings",
                    json={"text": text, "model": model}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return np.array(data["embedding"])
                    else:
                        logger.error(f"Embedding failed: {response.status}")
                        # Return dummy embedding for demo
                        return np.random.randn(1536)
        except Exception as e:
            logger.error(f"Embedding service error: {e}")
            # Fallback: return random embedding
            return np.random.randn(1536)

    async def embed_batch(self, texts: List[str], model: str = "text-embedding-ada-002") -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        tasks = [self.embed_text(text, model) for text in texts]
        return await asyncio.gather(*tasks)


class VectorStore:
    """
    In-memory vector store with similarity search
    In production, this would integrate with Pinecone, Weaviate, or similar
    """

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.documents: Dict[str, Document] = {}
        self.embeddings: np.ndarray = None
        self.doc_ids: List[str] = []

    async def add_document(self, document: Document):
        """Add a document to the vector store"""
        if document.embedding is None:
            # Generate embedding
            document.embedding = await self.embedding_service.embed_text(document.content)

        self.documents[document.id] = document
        self._rebuild_index()

    async def add_documents(self, documents: List[Document]):
        """Add multiple documents to the vector store"""
        # Generate embeddings for documents without them
        texts_to_embed = [doc.content for doc in documents if doc.embedding is None]
        if texts_to_embed:
            embeddings = await self.embedding_service.embed_batch(texts_to_embed)
            embed_idx = 0
            for doc in documents:
                if doc.embedding is None:
                    doc.embedding = embeddings[embed_idx]
                    embed_idx += 1

        for doc in documents:
            self.documents[doc.id] = doc

        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the embedding matrix for search"""
        if not self.documents:
            return

        self.doc_ids = list(self.documents.keys())
        embeddings_list = [self.documents[doc_id].embedding for doc_id in self.doc_ids]
        self.embeddings = np.vstack(embeddings_list)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Search for similar documents using cosine similarity

        Args:
            query: Search query text
            top_k: Number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of retrieval results sorted by score
        """
        if not self.documents:
            return []

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Compute cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        similarities = np.dot(doc_norms, query_norm)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Build results
        results = []
        for rank, idx in enumerate(top_indices, 1):
            score = float(similarities[idx])
            if score >= min_score:
                doc_id = self.doc_ids[idx]
                results.append(RetrievalResult(
                    document=self.documents[doc_id],
                    score=score,
                    rank=rank
                ))

        return results

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID"""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str):
        """Remove a document from the store"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._rebuild_index()

    def count(self) -> int:
        """Get total number of documents"""
        return len(self.documents)


class LLMService:
    """
    Service for generating responses using Agent 4/5 LLM inference
    """

    def __init__(self, agent_url: str = "http://localhost:8000"):
        self.agent_url = agent_url

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate text using LLM inference agent

        Args:
            prompt: Input prompt
            model: Model identifier
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generation result with text and metadata
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Generation failed: {response.status}")
                        return {
                            "text": "Error: LLM service unavailable",
                            "model": model,
                            "error": True
                        }
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            return {
                "text": f"Error: {str(e)}",
                "error": True
            }


class RAGPipeline:
    """
    Complete Retrieval-Augmented Generation pipeline
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_service: LLMService,
        top_k: int = 3
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.top_k = top_k

    def _build_prompt(self, query: str, context_docs: List[Document]) -> str:
        """Build RAG prompt with retrieved context"""
        context_str = "\n\n".join([
            f"[Document {i+1}]\n{doc.content}"
            for i, doc in enumerate(context_docs)
        ])

        prompt = f"""You are a helpful AI assistant. Use the following context documents to answer the user's question. If the answer cannot be found in the context, say so.

Context:
{context_str}

Question: {query}

Answer:"""

        return prompt

    async def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> RAGResponse:
        """
        Execute RAG pipeline: retrieve + generate

        Args:
            query: User query
            top_k: Number of documents to retrieve (uses default if None)
            model: LLM model to use
            temperature: Generation temperature

        Returns:
            RAGResponse with answer and metadata
        """
        if top_k is None:
            top_k = self.top_k

        # Step 1: Retrieve relevant documents
        retrieval_results = await self.vector_store.search(query, top_k=top_k)

        if not retrieval_results:
            # No documents found
            return RAGResponse(
                query=query,
                answer="No relevant documents found in the knowledge base.",
                retrieved_documents=[],
                generation_metadata={"error": "no_documents"}
            )

        # Step 2: Build prompt with context
        context_docs = [result.document for result in retrieval_results]
        prompt = self._build_prompt(query, context_docs)

        # Step 3: Generate answer
        generation_result = await self.llm_service.generate(
            prompt=prompt,
            model=model,
            max_tokens=500,
            temperature=temperature
        )

        return RAGResponse(
            query=query,
            answer=generation_result.get("text", "Error generating response"),
            retrieved_documents=retrieval_results,
            generation_metadata={
                "model": model,
                "temperature": temperature,
                "num_retrieved": len(retrieval_results),
                "error": generation_result.get("error", False)
            }
        )


class RAGWorkbench:
    """
    High-level interface for RAG AI Workbench application
    """

    def __init__(
        self,
        agent_url: str = "http://localhost:8000",
        port: int = 3000
    ):
        self.agent_url = agent_url
        self.port = port

        # Initialize components
        self.embedding_service = EmbeddingService(agent_url)
        self.vector_store = VectorStore(self.embedding_service)
        self.llm_service = LLMService(agent_url)
        self.pipeline = RAGPipeline(self.vector_store, self.llm_service)

    async def ingest_documents(self, documents: List[Dict[str, Any]]):
        """
        Ingest documents into the RAG system

        Args:
            documents: List of document dicts with 'content' and optional 'metadata'
        """
        doc_objects = [
            Document(
                id="",  # Will be auto-generated
                content=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]

        await self.vector_store.add_documents(doc_objects)
        logger.info(f"Ingested {len(doc_objects)} documents")

    async def query(self, query: str, top_k: int = 3) -> RAGResponse:
        """Execute a RAG query"""
        return await self.pipeline.query(query, top_k=top_k)

    def get_stats(self) -> Dict[str, Any]:
        """Get workbench statistics"""
        return {
            "document_count": self.vector_store.count(),
            "agent_url": self.agent_url,
            "port": self.port,
            "status": "ready" if self.vector_store.count() > 0 else "empty"
        }

    def get_fastapi_app(self):
        """Generate FastAPI application code for deployment"""
        return '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="RAG AI Workbench", version="1.0.0")

class IngestRequest(BaseModel):
    documents: List[Dict[str, Any]]

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/ingest")
async def ingest_documents(request: IngestRequest):
    """Ingest documents into RAG system"""
    # Implementation here
    return {"status": "success", "count": len(request.documents)}

@app.post("/query")
async def query(request: QueryRequest):
    """Execute RAG query"""
    # Implementation here
    return {"query": request.query, "answer": "Response here"}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {"document_count": 0, "status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
'''


async def main():
    """Demo RAG AI Workbench"""
    print("RAG AI Workbench Application Template")
    print("=" * 50)

    # Initialize workbench
    workbench = RAGWorkbench(agent_url="http://localhost:8000", port=3000)

    # Sample documents
    sample_docs = [
        {
            "content": "Apache Spark is a unified analytics engine for large-scale data processing. It provides high-level APIs in Java, Scala, Python and R.",
            "metadata": {"source": "spark_docs", "category": "overview"}
        },
        {
            "content": "Spark SQL is a Spark module for structured data processing. It provides a DataFrame API that makes it easy to manipulate structured data.",
            "metadata": {"source": "spark_docs", "category": "sql"}
        },
        {
            "content": "MLlib is Apache Spark's scalable machine learning library consisting of common learning algorithms and utilities.",
            "metadata": {"source": "spark_docs", "category": "ml"}
        },
        {
            "content": "GraphX is a graph processing framework built on top of Spark. It provides an API for graph computation and graph-parallel computation.",
            "metadata": {"source": "spark_docs", "category": "graph"}
        }
    ]

    print("\nIngesting sample documents...")
    await workbench.ingest_documents(sample_docs)

    stats = workbench.get_stats()
    print(f"Document count: {stats['document_count']}")
    print(f"Status: {stats['status']}")

    # Example queries
    queries = [
        "What is Apache Spark?",
        "How does Spark handle machine learning?",
        "Tell me about graph processing in Spark"
    ]

    print("\n" + "=" * 50)
    print("Example RAG Queries:")
    print("=" * 50)

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)

        response = await workbench.query(query, top_k=2)

        print(f"Answer: {response.answer}")
        print(f"\nRetrieved documents: {len(response.retrieved_documents)}")
        for result in response.retrieved_documents:
            print(f"  - Rank {result.rank}: {result.document.content[:100]}... (score: {result.score:.3f})")

    print("\n" + "=" * 50)
    print("FastAPI Application Template:")
    print("=" * 50)
    print(workbench.get_fastapi_app())


if __name__ == "__main__":
    asyncio.run(main())
