from abc import ABC, abstractmethod
from ollama_llm import OllamaLLM
from openai_llm import OpenAILLM


class BaseLLM(ABC):
    @abstractmethod
    def invoke(self, context_graph, context_vector, question):
        pass


class LLMFactory:
    @staticmethod
    def create_llm(llm_type, **kwargs):
        if llm_type.lower() == 'ollama':
            return OllamaLLM(**kwargs)
        elif llm_type.lower() == 'openai':
            return OpenAILLM(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

class LLM:
    def __init__(self, llm_type, **kwargs):
        self.llm = LLMFactory.create_llm(llm_type, **kwargs)

    def invoke(self, context, query):
        return self.llm.invoke(context, query)

if __name__ == "__main__":
    # Example usage
    llm = LLM('openai', model='gpt-4o-mini', temperature=0)
    
    # Sample contexts and question
    context_graph = ["Pete Warden is a software engineer and entrepreneur known for his work in machine learning and mobile technology."]
    question = "Who is Pete Warden and what is he known for?"

    result = llm.invoke(context_graph, question)
    print("LLM Response:")
    print(result)
