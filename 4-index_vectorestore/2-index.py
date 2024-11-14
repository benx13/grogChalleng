import os
from pymilvus import (
    connections, utility, FieldSchema, CollectionSchema, DataType,
    Collection, AnnSearchRequest, WeightedRanker
)
from milvus_model.hybrid import BGEM3EmbeddingFunction  # Ensure this module is available
from tqdm import tqdm
from pymilvus import MilvusClient
import pickle
import json

def load_graph_from_file(file_path):
    # Read the graph from a GML file
    G = pickle.load(open(file_path, 'rb'))
    return G


def read_chunks_from_graph(graph_path):
    """
    Read text chunks from a graph file.

    Args:
        graph_path (str): Path to the graph file.

    Returns:
        list: A list of text strings.
    """
    G = load_graph_from_file('neo4j_networkx_graph.pickle')
    data = []

    for node in tqdm(G.nodes(data=True)):
        # print(node)
        metadata = {}
        metadata['elementId'] = node[0]
        metadata['type'] = node[1].get('type', '')
        metadata['pdf'] = node[1].get('pdf', '')
        metadata['talk'] = node[1].get('talk', '')
        metadata['name'] = node[1].get('name')
        # print()
        # print()
        # print()
        # print(metadata)
        document = (
            f"This document describes the node:{node[1].get('name')} of type: {node[1].get('type', '')}"
            f"\n"
            f"text:"
            f"\n"
            f"{node[1].get('description')}"
        )
        # print()
        # print()
        # print(document)
        data.append({'doc':document, 'metadata':metadata})

    for edge in tqdm(G.edges(data=True)):
        # print(edge)
        metadata = {}
        metadata['source_node_elementId'] = edge[0]
        metadata['target_node_elementId'] = edge[1]
        metadata['elementId'] = edge[2].get('key')
        document = edge[2].get('description')
        data.append({'doc':document, 'metadata':metadata})

    return data


def read_chunks_from_folder(input_folder):
    """
    Read text chunks from files in the specified folder in sorted order.

    Args:
        input_folder (str): Path to the folder containing text chunks.

    Returns:
        list: A list of text strings.
    """
    texts = []
    print("Loading text chunks from input folder...")
    # Get all txt files and sort them
    txt_files = []
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                txt_files.append(file_path)
    
    # Sort the files to ensure consistent ordering
    txt_files.sort()
    
    # Read the files in order
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read().strip()
            texts.append(text)
    
    print(f"Loaded {len(texts)} text chunks in order.")
    return texts

def create_collection(milvus_uri, collection_name, dense_dim):

    """
    Create a Milvus collection with the specified schema.

    Args:
        milvus_uri (str): URI of the Milvus instance.
        collection_name (str): Name of the collection to create.
        dense_dim (int): Dimension of the dense vectors.

    Returns:
        Collection: The created Milvus collection.
    """
    connections.connect("default", uri=milvus_uri)
    # Define schema
    fields = [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=16384),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=dense_dim),
    ]
    schema = CollectionSchema(fields, description="Hybrid search collection")

    # Create the collection if it does not exist
    if not utility.has_collection(collection_name):
        collection = Collection(
            name=collection_name, schema=schema, consistency_level="Strong"
        )
        # Create indices
        collection.create_index(
            "sparse_vector", {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
        )
        collection.create_index(
            "dense_vector", {"index_type": "AUTOINDEX", "metric_type": "IP"}
        )
        print(f"Collection '{collection_name}' created.")
    else:
        collection = Collection(name=collection_name)
        print(f"Collection '{collection_name}' already exists.")
    


    collection.load()
    return collection

def insert_into_collection_json(collection, embedding_function):
    print("Loading and processing data...")

    # with open(json_path, 'r') as file:
    #     json_data = json.load(file

    json_data = read_chunks_from_folder('chunks')
    batch_size = 1
    total_inserted = 0
    for i_range in tqdm(range(0, len(json_data), batch_size)):
        batch_data = json_data[i_range:i_range+batch_size]
        docs = []

        # print(batch_data)
        # print('------------------')
        # print('------------------')
        for item in batch_data:
            doc = item
            if doc == '':
                doc = 'nothing'
            docs.append(doc)

        # print(f"Generating embeddings for batch {i//batch_size + 1}...")

        embeddings = embedding_function.encode_documents(docs)

        entities = []
        for j, text in enumerate(docs):
            sparse_row = embeddings["sparse"]._getrow(j)
            indices = sparse_row.indices
            data = sparse_row.data
            sparse_vector = {int(idx): float(val) for idx, val in zip(indices, data)}

            entity = {
                "text": text,
                "dense_vector": embeddings["dense"][j].tolist(),
                "sparse_vector": sparse_vector
            }
            entities.append(entity)

        collection.insert(entities)
        total_inserted += len(entities)
        # print(f"Inserted batch {i//batch_size + 1} ({len(entities)} entities)")

    print(f"Total inserted: {total_inserted} entities into '{collection.name}' collection.")

def insert_into_collection(collection, texts, embedding_function):
    print("Generating embeddings...")

    metadatas = []
    docs = []
    for i in texts:
        # Serialize metadata to JSON string
        metadata_json = json.dumps(i['metadata'])
        metadatas.append(metadata_json)
        docs.append(i['doc'])
    texts = docs
    metadatas = metadatas

    print(len(texts))
    print(len(metadatas))
    embeddings = embedding_function.encode_documents(texts)

    entities = []
    for i, (text, metadata) in enumerate(zip(texts, metadatas)):
        # Correctly get the i-th row of the sparse matrix
        sparse_row = embeddings["sparse"].getrow(i)

        # Extract the indices and data of the non-zero elements
        indices = sparse_row.indices
        data = sparse_row.data

        # Construct the sparse vector as a dictionary
        sparse_vector = {int(idx): float(val) for idx, val in zip(indices, data)}
        print(metadata)
        print(type(metadata))
        entity = {
            "text": text,
            "dense_vector": embeddings["dense"][i].tolist(),
            "sparse_vector": sparse_vector,
            'metadata': metadata
        }
        entities.append(entity)

    batch_size = 50
    for i in range(0, len(entities), batch_size):
        batch_entities = entities[i:i + batch_size]
        collection.insert(batch_entities)
    print(f"Inserted {len(texts)} entities into '{collection.name}' collection.")


def perform_hybrid_search(collection, query, embedding_function, sparse_weight=0.7, dense_weight=1.0, limit=2):
    """
    Perform a hybrid search on the collection using the embedded query.

    Args:
        collection (Collection): The Milvus collection to search.
        query (str): The input query from the user.
        embedding_function (BGEM3EmbeddingFunction): The embedding function to use.
        sparse_weight (float): Weight for the sparse vector.
        dense_weight (float): Weight for the dense vector.
        limit (int): Number of results to return.

    Returns:
        list: Results from the hybrid search.
    """
    # Generate embeddings for the query
    query_embeddings = embedding_function.encode_documents([query])

    # Create ANN search requests
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

    # Perform hybrid search
    search_results = collection.hybrid_search(
        [sparse_req, dense_req], rerank=rerank, limit=limit, output_fields=["text", 'metadata']
    )[0]

    return [hit.entity.get("text").replace('\n', '') for hit in search_results]

def check_collection_info(client, collection_name,collection):
    """
    Check the count of vectors in the specified collection.

    Args:
        client (MilvusClient): The Milvus client to use for querying.
        collection_name (str): The name of the collection to check.

    Returns:
        int: The count of vectors in the collection.
    """

       # Check if the collection exists
     # Enhanced print statements for collection details

    
    print(f"Collection Name: {collection.name}")
    print(f"Collection Schema: {collection.schema}")

    collection_info = collection.describe()
    print(f"Collection Info: {collection_info}")

    result = client.query(
        collection_name=collection_name,
        filter="",
        output_fields=["count(*)"],
    )

    count = result[0]['count(*)']
    print(f"Number of sparse vectors: {count}")
    print(f"Number of dense vectors: {count}")
    

def main():
    # Step 1: Read chunks from folder
    from milvus_model.hybrid import BGEM3EmbeddingFunction

    # input_folder = "/Users/wassi/OneDrive/Bureau/chunking/output_chunks/test"  # Replace with your input folder path
    # texts = read_chunks_from_folder(input_folder)
    
    # print(texts[1])
    
    # texts = read_chunks_from_graph('neo4j_networkx_graph.pickle')
    # Step 2: Create collection

    milvus_uri = "tcp://localhost:19530"  # Replace with your Milvus URI
    collection_name = "XXX"
    embedding_function = BGEM3EmbeddingFunction(
        model_name='BAAI/bge-m3', # Specify the model name
        device='cuda:0', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
        use_fp16=True # Whether to use fp16. `False` for `device='cpu'`.
    )

    dense_dim = embedding_function.dim['dense']
    collection = create_collection(milvus_uri, collection_name, dense_dim)

    # check if collection 
    client = MilvusClient(uri="http://localhost:19530")
    # check_collection_info(client, collection_name,collection)

    
    # Step 3: Insert into collection
    insert_into_collection_json(collection, embedding_function)

    check_collection_info(client, collection_name,collection)
    
    # Step 4: Input a question from the user
    # query = "main objective tinyMAN framework"

    # # Step 5: Perform hybrid search
    # results = perform_hybrid_search(collection, query, embedding_function, limit=15)

    # # Display the search results
    # print("/nHybrid search results:")
    # for idx, text in enumerate(results, 1):
    #     print(f"{idx}. {text}")
    #     print("-" * 40)  # Add a separator line

if __name__ == "__main__":
    main()
