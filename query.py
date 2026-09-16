"""
query.py - Hoi 1 cau, tim top chunk lien quan nhat trong ChromaDB da ingest.
Chay ingest.py TRUOC khi chay file nay.
"""

import sys
import chromadb
from AnswerProvider import AnswerProvider,MockAnswerProvider, GeminiProvider

DB_PATH = "./chroma_db"
COLLECTION_NAME = "chat_history"


def search(query_text: str, n_results: int = 9):
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(query_texts=[query_text], n_results=n_results)

    print(f"\nCau hoi: {query_text}\n")
    print("Top ket qua lien quan nhat:")
    for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0])):
        print(f"\n  [{i+1}] (khoang cach={distance:.4f})")
        print(f"  {doc}")
    return results["documents"][0]

def ask(question: str, provider: AnswerProvider):
    retrieved_chunks = search(question)
    results = provider.generate_answer(question, retrieved_chunks)
    print (f"\nCau tra lơi: {results}\n")
    return results

if __name__ == "__main__":
    provider = GeminiProvider()
    # Cho phep truyen cau hoi qua command line, hoac dung cau mac dinh de test
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Homos hoc gi ve SQL?"

    ask(question, provider)

