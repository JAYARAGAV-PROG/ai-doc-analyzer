"""
RAG Pipeline: Document chunking, embedding, and retrieval
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ChromaDB storage path
CHROMA_PATH = Path(__file__).parent / "chroma_db"
CHROMA_PATH.mkdir(exist_ok=True)

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


class RAGPipeline:
    """RAG pipeline for document processing and retrieval"""
    
    def __init__(self):
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("✓ Embedding model loaded")
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def chunk_document(self, text: str) -> List[str]:
        """Split document into chunks"""
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Document split into {len(chunks)} chunks")
        return chunks
    
    def store_document(self, doc_id: int, text: str, metadata: Optional[Dict] = None) -> str:
        """
        Store document in ChromaDB
        Returns: collection_id (vector_store_id)
        """
        collection_name = f"doc_{doc_id}"
        
        # Create or get collection
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except Exception:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"doc_id": str(doc_id)}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        # Chunk the document
        chunks = self.chunk_document(text)
        
        if not chunks:
            logger.warning("No chunks created from document")
            return collection_name
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.create_embeddings(chunks)
        
        # Prepare data for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "chunk_index": i,
                "doc_id": str(doc_id),
                **(metadata or {})
            }
            for i in range(len(chunks))
        ]
        
        # Store in ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"✓ Stored {len(chunks)} chunks in ChromaDB")
        return collection_name
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query into multiple variations for better retrieval
        Returns 5-6 alternate queries
        """
        # In a production system, you might use an LLM for this
        # For now, we'll create simple variations
        expansions = [
            query,
            f"What is {query}?",
            f"Explain {query}",
            f"Information about {query}",
            f"Details regarding {query}",
            f"Can you tell me about {query}?"
        ]
        return expansions[:6]
    
    def hybrid_search(self, doc_id: int, query: str, top_k: int = 20) -> List[Dict]:
        """
        Perform hybrid search: semantic + keyword
        Returns top_k chunks
        """
        collection_name = f"doc_{doc_id}"
        
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Collection not found: {collection_name}")
            return []
        
        # Expand query
        query_variations = self.expand_query(query)
        
        # Generate embeddings for all query variations
        query_embeddings = self.create_embeddings(query_variations)
        
        # Perform semantic search for each variation
        all_results = []
        
        for i, query_embedding in enumerate(query_embeddings):
            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, 10),
                    include=["documents", "metadatas", "distances"]
                )
                
                # Process results
                if results and results['ids']:
                    for j in range(len(results['ids'][0])):
                        all_results.append({
                            'id': results['ids'][0][j],
                            'text': results['documents'][0][j],
                            'metadata': results['metadatas'][0][j],
                            'distance': results['distances'][0][j],
                            'query_variation': i
                        })
            except Exception as e:
                logger.warning(f"Search failed for variation {i}: {e}")
                continue
        
        # Remove duplicates and sort by distance
        seen_ids = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x['distance']):
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
                if len(unique_results) >= top_k:
                    break
        
        logger.info(f"Hybrid search returned {len(unique_results)} unique chunks")
        return unique_results
    
    def rerank_chunks(self, query: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Rerank chunks by similarity to original query
        Returns top_k most relevant chunks
        """
        if not chunks:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        chunk_embeddings = self.embedding_model.encode(chunk_texts)
        
        # Calculate cosine similarity
        from numpy import dot
        from numpy.linalg import norm
        
        similarities = []
        for i, chunk_emb in enumerate(chunk_embeddings):
            similarity = dot(query_embedding, chunk_emb) / (norm(query_embedding) * norm(chunk_emb))
            chunks[i]['similarity'] = float(similarity)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k chunks
        reranked = [chunks[i] for i, _ in similarities[:top_k]]
        logger.info(f"Reranked to top {len(reranked)} chunks")
        return reranked
    
    def retrieve_context(self, doc_id: int, query: str, intent: str = "fact") -> List[Dict]:
        """
        Retrieve relevant context based on query intent
        
        Intent types:
        - document: Document-level questions
        - section: Section-level questions
        - fact: Fact-level questions (default)
        """
        # Perform hybrid search
        chunks = self.hybrid_search(doc_id, query, top_k=20)
        
        if not chunks:
            return []
        
        # Rerank based on intent
        if intent == "document":
            # For document-level, return more diverse chunks
            return self.rerank_chunks(query, chunks, top_k=5)
        elif intent == "section":
            # For section-level, return standard amount
            return self.rerank_chunks(query, chunks, top_k=3)
        else:  # fact
            # For fact-level, return most relevant chunks
            return self.rerank_chunks(query, chunks, top_k=3)
    
    def get_collection_stats(self, doc_id: int) -> Dict:
        """Get statistics about a document's collection"""
        collection_name = f"doc_{doc_id}"
        
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            return {
                'collection_name': collection_name,
                'chunk_count': count,
                'exists': True
            }
        except Exception as e:
            return {
                'collection_name': collection_name,
                'chunk_count': 0,
                'exists': False,
                'error': str(e)
            }


# Global instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


if __name__ == "__main__":
    # Test RAG pipeline
    rag = get_rag_pipeline()
    print("RAG Pipeline initialized successfully")
