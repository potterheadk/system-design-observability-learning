import os
import google.generativeai as genai
import ollama

class LLMInterface:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class GeminiClient(LLMInterface):
    def __init__(self):
        # You need to get a free API key from https://aistudio.google.com/
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ WARNING: GEMINI_API_KEY is missing")
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"

class OllamaClient(LLMInterface):
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        try:
            # Assumes you have Ollama running on your host machine or in a container
            # For docker-to-host communication, we might need configuration
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            return f"Ollama Error: {str(e)}"

def get_llm_client():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "ollama":
        return OllamaClient()
    return GeminiClient()