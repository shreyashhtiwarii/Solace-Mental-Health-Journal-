import os
import chromadb
from chromadb.utils import embedding_functions

# Initialize ChromaDB client with local persistence
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
client = chromadb.PersistentClient(path=DB_DIR)

# Use the default lightweight embedding function for local embeddings (all-MiniLM-L6-v2)
# This model downloads locally on first run and is free.
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def get_or_create_collection():
    return client.get_or_create_collection(
        name="journal_entries",
        embedding_function=sentence_transformer_ef
    )

def add_entry_to_vector_store(entry_id: int, user_id: str, content: str, mood_label: str):
    """Embeds and saves a journal entry to ChromaDB for future RAG retrieval."""
    collection = get_or_create_collection()
    
    collection.add(
        documents=[content],
        metadatas=[{"user_id": user_id, "mood": mood_label}],
        ids=[f"{user_id}_{entry_id}"]
    )

def retrieve_relevant_entries(user_id: str, current_content: str, limit: int = 3) -> str:
    """Retrieves the most semantically similar past entries for the same user."""
    collection = get_or_create_collection()
    
    try:
        results = collection.query(
            query_texts=[current_content],
            n_results=limit,
            where={"user_id": user_id}
        )
        
        if not results['documents'] or not results['documents'][0]:
            return ""
            
        # Format the context text
        context_parts = []
        for doc in results['documents'][0]:
            context_parts.append(f"- \"{doc}\"")
            
        return "\n".join(context_parts)
    except Exception as e:
        print(f"ChromaDB retrieval error: {e}")
        return ""
