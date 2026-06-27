import os
import tempfile
from fastapi import UploadFile
import tiktoken
from pypdf import PdfReader
from .embeddings import get_embedding

async def chunk(text: str, chunk_size: int = 1000, overlap: int = 200):
    enc = tiktoken.get_encoding('cl100k_base')
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap
    return chunks

async def ingest_pdf(file: UploadFile, session_id: str, user_id: str):
    contents = await file.read()
    original_filename = file.filename or 'uploaded_file.pdf'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1])
    tmp.write(contents)
    tmp.flush()
    file_path = tmp.name

    try:
        reader = PdfReader(file_path)
        text_by_page = [page.extract_text() for page in reader.pages]
        all_chunks = []
        for page_index, page_text in enumerate(text_by_page):
            chunks = await chunk(page_text, chunk_size=1000, overlap=200)
            for i, chunk in enumerate(chunks):
                metadata = {
                    'source_filename': original_filename,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'page_or_row': f'Page {page_index + 1}'
                }
                embedding = await get_embedding(chunk)
                all_chunks.append({'text': chunk, 'embedding': embedding, 'metadata': metadata})
        return all_chunks
    finally:
        os.unlink(file_path)