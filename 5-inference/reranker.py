from abc import ABC, abstractmethod
from flashrank import Ranker, RerankRequest
from typing import List, Dict, Union, Optional

class BaseReranker(ABC):
    @abstractmethod
    def invoke(self, query: str, input_context: List[str]) -> List[str]:
        pass

class FlashRankReranker(BaseReranker):
    def __init__(self, model_name: str = "rank-T5-flan", cache_dir: Optional[str] = None):
        """Initialize FlashRank reranker with specified model.
        
        Args:
            model_name (str): Name of the ranking model to use
            cache_dir (str, optional): Directory to cache the model
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.ranker = Ranker(
            model_name=model_name, 
            cache_dir=cache_dir if cache_dir else "/tmp"
        )

    def invoke(self, query: str, input_context: List[str]) -> List[str]:
        """Rerank input_context based on query relevance.
        
        Args:
            query (str): The search query
            input_context (List[str]): List of document texts to rerank
            
        Returns:
            List[str]: Reranked input_context
        """
        try:
        #     # Format input_context for FlashRank
        #     passages = []
        #     for idx, text in enumerate(input_context):
        #         passage = {
        #             "id": str(idx),
        #             "text": text
        #         }
        #         passages.append(passage)

        #     # Create rerank request
        #     rerank_request = RerankRequest(query=query, passages=passages)
            
        #     # Get reranked results
        #     results = self.ranker.rerank(rerank_request)
            
        #     # Sort results by score and extract text and get top@4
        #     reranked_docs = [result['text'] for result in sorted(results, key=lambda x: x['score'], reverse=True)][:]
            return {"context": input_context}

        except Exception as e:
            print(f"An error occurred during reranking: {e}")
            import traceback
            print(traceback.format_exc())
            return documents  # Return original documents if reranking fails

class RerankerFactory:
    @staticmethod
    def create_reranker(reranker_type: str, **kwargs) -> BaseReranker:
        if reranker_type.lower() == 'flashrank':
            return FlashRankReranker(**kwargs)
        else:
            raise ValueError(f"Unknown reranker type: {reranker_type}")

class Reranker:
    def __init__(self, reranker_type: str, **kwargs):
        self.reranker = RerankerFactory.create_reranker(reranker_type, **kwargs)

    def invoke(self, query: str, input_context: List[str]) -> List[str]:
        return self.reranker.invoke(query, input_context)

if __name__ == "__main__":
    # Example usage
    documents = [
        "Introduce lookahead decoding: a parallel decoding algo to accelerate LLM inference",
        "vLLM is a fast and easy-to-use library for LLM inference and serving",
        "There are many ways to increase LLM inference throughput"
    ]
    
    reranker = Reranker('flashrank', model_name="rank-T5-flan")
    results = reranker.invoke("How to speed up LLMs?", documents)
    
    print("\nReranked Results:")
    for idx, doc in enumerate(results['context'], 1):
        print(f"\n{idx}. {doc}")
