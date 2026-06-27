import os
from .embeddings import get_embedding
from ai.vector_store import VectorStore  # Corrected import
import openai

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    embedding = await get_embedding(query)
    vector_store = VectorStore()  # Assume VectorStore is properly initialized elsewhere
    results = vector_store.search(embedding, top_k=top_k)
    return results

async def answer_question(query: str, session_id: str, user_id: str) -> dict:
    context_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    if not context_chunks:
        return {'answer': 'No relevant information found.', 'sources': []}

    sources = [{'filename': chunk['metadata']['source_filename'], 'location': chunk['metadata']['page_or_row']} for chunk in context_chunks]
    context_texts = [chunk['text'] for chunk in context_chunks]
    prompt = f"Answer the following question based on the provided context:\n\nContext:\n{''.join(context_texts)}\n\nQuestion:\n{query}"

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}]
    )
    answer = response.choices[0].message.content

    return {'answer': answer, 'sources': sources}