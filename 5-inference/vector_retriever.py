import os
from pymilvus import (
    connections, utility, FieldSchema, CollectionSchema, DataType,
    Collection, AnnSearchRequest, WeightedRanker
)
from milvus_model.hybrid import BGEM3EmbeddingFunction
from tqdm import tqdm
from pymilvus import MilvusClient
import pickle
import json

class VectorRetriever:
    def __init__(self, uri, collection_name):
        self.uri = uri
        self.collection_name = collection_name
        self.embedding_function = BGEM3EmbeddingFunction(
            model_name='BAAI/bge-m3',
            device='mps',
            use_fp16=True
        )
        self.dense_dim = self.embedding_function.dim['dense']
        self.collection = self.load_collection()
        self.client = MilvusClient(uri=uri)

    def create_collection(self):
        connections.connect("default", uri=self.uri)
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=16384),
            FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="context", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dense_dim),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=4096),
        ]
        schema = CollectionSchema(fields, description="Hybrid search collection")

        if not utility.has_collection(self.collection_name):
            collection = Collection(
                name=self.collection_name, schema=schema, consistency_level="Strong"
            )
            collection.create_index(
                "sparse_vector", {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
            )
            collection.create_index(
                "dense_vector", {"index_type": "AUTOINDEX", "metric_type": "IP"}
            )
            print(f"Collection '{self.collection_name}' created.")
        else:
            collection = Collection(name=self.collection_name)
            print('going to load')
            collection.load()
            print(f"Collection '{self.collection_name}' already exists.")

        return collection

    def load_collection(self):
        """Load collection into memory"""
        connections.connect("default", uri=self.uri)
        collection = Collection(name=self.collection_name)
        collection.load()
        print(f"Collection '{self.collection_name}' loaded into memory")
        return collection
    def perform_hybrid_search(self, query, sparse_weight=0.7, dense_weight=1.0, limit=2):
        query_embeddings = self.embedding_function.encode_documents([query])

        dense_search_params = {"metric_type": "IP", "params": {}}
        dense_req = AnnSearchRequest(
            data=[query_embeddings["dense"][0].tolist()],
            anns_field="dense_vector",
            param=dense_search_params,
            limit=limit,
        )

        sparse_search_params = {"metric_type": "IP", "params": {}}
        sparse_req = AnnSearchRequest(
            data=[query_embeddings["sparse"][[0]]],
            anns_field="sparse_vector",
            param=sparse_search_params,
            limit=limit,
        )

        rerank = WeightedRanker(sparse_weight, dense_weight)

        search_results = self.collection.hybrid_search(
            [sparse_req, dense_req], rerank=rerank, limit=limit, output_fields=["text"]
        )[0]

        return [hit.entity.get("text").replace('\n', '') for hit in search_results]

    def check_collection_info(self):
        print(f"Collection Name: {self.collection.name}")
        print(f"Collection Schema: {self.collection.schema}")

        collection_info = self.collection.describe()
        print(f"Collection Info: {collection_info}")

        result = self.client.query(
            collection_name=self.collection_name,
            filter="",
            output_fields=["count(*)"],
        )

        count = result[0]['count(*)']
        print(f"Number of sparse vectors: {count}")
        print(f"Number of dense vectors: {count}")

    def invoke(self, query, top_k=4):
        try:
            # print(f"[VectorRetriever] Processing query: {query}")
            
            results = self.perform_hybrid_search(query, limit=top_k)
            
            # Build context string
            context_parts = []
            
            for idx, text in enumerate(results, 1):
                context_parts.extend([
                   # f"\nResult {idx}:",
                    text.strip(),
                   # "-" * 80
                ])
            
            # Join all parts with newlines
            final_context = context_parts
            
            # # Debug print to verify the content
            # print("\n[VectorRetriever] Generated context:")
            # print(final_context)
            # print("\n[VectorRetriever] End of context")
            
            return {'context': final_context}
            
        except Exception as e:
            print(f"[VectorRetriever] Error: {e}")
            import traceback
            print(traceback.format_exc())
            raise

    def close(self):
        """
        Closes the connection to the Milvus server.
        """
        try:
            connections.disconnect("default")
            print("Disconnected from Milvus server.")
        except Exception as e:
            print(f"Error while disconnecting: {e}")

if __name__ == "__main__":
    uri = "tcp://192.168.1.96:19530"
    collection_name = "X"
    
    retriever = VectorRetriever(uri, collection_name)
    retriever.check_collection_info()
    
    query = "acronym of SRP"
    results = retriever.invoke(query)

    for i in results['context']:
        print(i)

    # Close the connection when done
    retriever.close()
