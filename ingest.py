"""
ingest.py - Doc du lieu chat, chunk, embedding, luu vao ChromaDB persistent.

Chien luoc chunk: gop CHUNK_SIZE message/chunk, overlap OVERLAP message
giua cac chunk lien tiep de khong mat ngu canh noi tiep.
"""

import time
import json
import chromadb
import PrefixProvider
from PrefixProvider import PrefixProvider, MockProvider  
from PrefixProvider import PrefixProvider, MockProvider, AnthropicProvider, GeminiProvider
from google import genai

CHUNK_SIZE = 2      # so message goc trong 1 chunk
OVERLAP = 1         # so message chong lan giua 2 chunk lien tiep
DB_PATH = "./chroma_db"
COLLECTION_NAME = "chat_history"


def load_messages(json_path: str) -> list[dict]:
    """Doc file JSON, tra ve list message dang [{"role": ..., "content": ...}, ...]"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["messages"]


def chunk_messages(messages: list[dict], chunk_size: int, overlap: int, provider: PrefixProvider) -> list[str]:
    """
    Gop nhieu message lien tiep thanh 1 chunk (dang text).
    Vi du chunk_size=4, overlap=1:
      chunk 1: message[0:4]
      chunk 2: message[3:7]   (message[3] la diem overlap)
      chunk 3: message[6:10]
    """
    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(messages), step):
        window = messages[start:start + chunk_size]
        if not window:
            break
        # Ghep cac message trong window thanh 1 doan text co dinh dang ro rang
        message_text = "\n".join(f"{m['role']}: {m['content']}" for m in window)
        prefix = provider.generate_prefix(message_text)
        text = f"[{prefix}]\n{message_text}"
        chunks.append(text)
        time.sleep(13)  # free tier: 5 request/phut => nghi ~12-13s giua moi request
        if start + chunk_size >= len(messages):
            break
    return chunks


def ingest_to_chroma(chunks: list[str], collection_name: str, db_path: str):
    """Tao/mo collection persistent, ingest cac chunk vao do."""
    client = chromadb.PersistentClient(path=db_path)

    # get_or_create de chay lai nhieu lan khong bi loi "collection da ton tai"
    collection = client.get_or_create_collection(name=collection_name)

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)

    print(f"Da ingest {len(chunks)} chunk vao collection '{collection_name}' tai '{db_path}'")


if __name__ == "__main__":
    messages = load_messages("sample_data.json")
    print(f"Doc duoc {len(messages)} message tu sample_data.json")

    provider = GeminiProvider()
    chunks = chunk_messages(messages, CHUNK_SIZE, OVERLAP, provider)
    print(f"Da chia thanh {len(chunks)} chunk (chunk_size={CHUNK_SIZE}, overlap={OVERLAP})\n")

    # In thu chunk dau tien de kiem tra
    print("--- Chunk dau tien (mau) ---")
    print(chunks[0])
    print("---\n")

    ingest_to_chroma(chunks, COLLECTION_NAME, DB_PATH)
