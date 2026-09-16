from abc import ABC, abstractmethod
import anthropic
from google import genai
import os

class PrefixProvider(ABC):
    @abstractmethod
    def generate_prefix(self, chunk_text: str) -> str:
        pass    

class MockProvider(PrefixProvider):
    def generate_prefix(self, chunk_text: str) -> str:
        if not chunk_text:
            return "PREFIX_EMPTY"
        prefix = chunk_text.strip()[:10]
        return f"PREFIX_{prefix}"
      
class AnthropicProvider(PrefixProvider):
      def __init__(self, api_key: str=None):
        # Neu khong truyen api_key, SDK tu doc bien moi truong ANTHROPIC_API_KEY
          self.client = anthropic.Anthropic(api_key=api_key)
      def generate_prefix(self, chunk_text:str) -> str:
        prompt = (
            "Tom tat chu de chinh cua doan hoi thoai sau trong 1 cau ngan "
            "(khong qua 10 tu), khong can giai thich them:\n\n"
            f"{chunk_text}"
        ) 
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            messages=[{"role" : "user", "content":prompt}]
        )
        # response.content la list cac block, lay text tu block dau tien
        return response.content[0].text.strip()

class GeminiProvider(PrefixProvider):
    def __init__(self, api_key: str=None):
        # Neu khong truyen api_key, client tu doc bien moi truong GOOGLE_API_KEY hoac GEMINI_API_KEY
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=key)

    def generate_prefix(self, chunk_text: str) -> str :
        prompt = (
            "Tom tat chu de chinh cua doan hoi thoai sau trong 1 cau ngan "
            "(khong qua 10 tu), khong can giai thich them:\n\n"
            f"{chunk_text}"
        )
        try:
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents= prompt
            )    
        except Exception as e:
            print (f"\nBi loi: {chunk_text}\n")
            return ""    
        
        return response.text.strip()
    
    
if __name__ == "__main__":
    chunk = "Invoice data for September 2026"
    provider = MockProvider()
    prefix = provider.generate_prefix(chunk)
    print(prefix)   
            