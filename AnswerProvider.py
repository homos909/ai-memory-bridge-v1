from abc import ABC, abstractmethod
from google import genai
import os

class AnswerProvider(ABC):
    @abstractmethod
    def generate_answer(self, question: str, retrieved_chunks: list[str]) -> str:
        pass

class MockAnswerProvider(AnswerProvider):
    def generate_answer(self, question: str, retrieved_chunks: list[str]) -> str:
        if not retrieved_chunks:
            return "ANSWER_EMPTY"
        count = len(retrieved_chunks)
        return f"ANSWER_{question}_{count}chunks"

class GeminiProvider(AnswerProvider):
    def __init__(self, api_key: str = None):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=key)

    def generate_answer(self, question: str, retrieved_chunks: list[str]) -> str:
        context = "\n".join(retrieved_chunks)
        prompt = (
            f"Dua tren thong tin sau: {context}\n\n"
            f"Tra loi cau hoi: {question}"
        )
        try:
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
        except Exception as e:
            print (f"\nBi loi: {question}\n")
            return ""
  
        return response.text.strip()