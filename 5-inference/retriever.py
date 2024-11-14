from abc import ABC, abstractmethod
from graph_retriever import GraphRetriever
from vector_retriever import VectorRetriever

class BaseRetriever(ABC):
    @abstractmethod
    def invoke(self, input_prompt):
        pass

    @abstractmethod
    def close(self):
        pass

class RetrieverFactory:
    @staticmethod
    def create_retriever(retriever_type, **kwargs):
        print(f"Creating {retriever_type} retriever with parameters: {kwargs}")  # Debug print
        if retriever_type.lower() == 'graph':
            return GraphRetriever(**kwargs)
        elif retriever_type.lower() == 'vector':
            # Make sure required parameters are present
            required_params = ['uri', 'collection_name']
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"Missing required parameter '{param}' for vector retriever")
            return VectorRetriever(**kwargs)
        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")

class Retriever:
    def __init__(self, retriever_type, **kwargs):
        print(f"Initializing {retriever_type} retriever")
        print(f"Parameters: {kwargs}")  # Debug print
        self.retriever = RetrieverFactory.create_retriever(retriever_type, **kwargs)

    def invoke(self, query, **kwargs):
        print(f"Retriever invoke called with query: {query}")  # Debug print
        return self.retriever.invoke(query)

    def close(self):
        if hasattr(self.retriever, 'close'):
            self.retriever.close()

if __name__ == "__main__":
    # Example usage for Graph Retriever
    graph_retriever = Retriever('graph', uri="bolt://localhost:7687", user="neo4j", password="strongpassword")
    
    # Example usage for Vector Retriever
    vector_retriever = Retriever('vector', uri="tcp://192.168.1.96:19530", collection_name="X")

    # Use graph retriever
    query = "ZCL"
    # graph_results = graph_retriever.invoke(query)
    # print("Results from Graph Retriever:")
    # print(graph_results)

    # Use vector retriever
    vector_results = vector_retriever.invoke(query)
    print("\nResults from Vector Retriever:")
    print(vector_results)

    # Close the connections
    graph_retriever.close()
    vector_retriever.close()
