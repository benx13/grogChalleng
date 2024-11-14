import networkx as nx
import pickle
import random
from tqdm import tqdm
import json
from llama_index.core import Document
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from flask import Flask, request, Response, jsonify
from py2neo import Graph, Node, Relationship

def load_graph_from_file(file_path):
    # Read the graph from a GraphML file
    G = nx.read_graphml(file_path)
    return G

G = load_graph_from_file('3-lightRAG2neo4J/graph_chunk_entity_relation7x.graphml')

def export_to_neo4j(G, neo4j_uri, neo4j_user, neo4j_password):
    # Connect to Neo4j
    neo4j_graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # Clear the existing graph in Neo4j
    neo4j_graph.delete_all()

    # Create nodes
    neo4j_nodes = {}
    for node, data in tqdm(G.nodes(data=True), desc="Exporting nodes"):
        node_type = data.get('type', 'Unknown')
        # Clean up the data
        node_data = {k: v for k, v in data.items() if k != 'type'}
        
        # Clean up description if it exists
        if 'description' in node_data:
            # Take the first description before <SEP>
            node_data['description'] = ' '.join(node_data['description'].split('<SEP>'))
            node_data['description'] = ' '.join(node_data['description'].split('"'))

        neo4j_node = Node(node_type, name=node, **node_data)
        neo4j_graph.create(neo4j_node)
        neo4j_nodes[node] = neo4j_node

    # Create relationships
    for source, target, data in tqdm(G.edges(data=True), desc="Exporting edges"):
        start_node = neo4j_nodes[source]
        end_node = neo4j_nodes[target]
        rel_type = data.get('relationship', 'CONNECTED_TO').upper()
        
        # Clean up relationship data
        rel_data = data.copy()
        if 'description' in rel_data:
            # Take the first description before <SEP>
            rel_data['description'] = ' '.join(rel_data['description'].split('<SEP>'))
            rel_data['description'] = ' '.join(rel_data['description'].split('"'))
        
        relationship = Relationship(start_node, rel_type, end_node, **rel_data)
        neo4j_graph.create(relationship)

    print("Graph export to Neo4j completed successfully.")

# Example usage:
neo4j_uri = "bolt://localhost:7689"
neo4j_user = "neo4j"
neo4j_password = "strongpassword"
export_to_neo4j(G, neo4j_uri, neo4j_user, neo4j_password)


