# TinyRAG: An Efficient RAG Implementation for Offline Challenges
## Quick Summary
- **Performance**: 
  - Accuracy: 0.66%
- **Retrieval System**:
  - Custom graph store implementation
  - Hybrid BM25 + dense search vector store
- **Language Model**:
  - LLM: QWEN 2.5 7B instruct
- **Resources**:
   - 5GB GPU Memory
   - 3GB System RAM


This repository contains our submission for the offline RAG system challenge, powered by TinyRAG, an efficient and fully offline Retrieval-Augmented Generation (RAG) implementation. TinyRAG combines advanced retrieval techniques with lightweight, scalable models to deliver high accuracy and performance in an offline setting.

## Overview

TinyRAG is designed to work without online dependencies, reaching a submission accuracy of approximately 0.66% Our approach combines a graph-based knowledge retrieval system and a vector-based hybrid search to enhance both speed and retrieval quality.

Our solution combines efficient retrieval mechanisms with lightweight models to create a robust RAG system. We utilize a hybrid approach, leveraging both graph-based and vector-based retrieval methods to enhance result quality while maintaining performance.

## Data Pipeline

TinyRAG's data pipeline is structured into three main steps:

### 1. Data Collection and Enhancement
In the first stage, TinyRAG collects data by scraping relevant content from web sources, with a focus on extracting high-quality information for offline use.

We implemented a two-step process to enrich the training dataset:
- **Web Scraping**: Automated extraction of relevant content from the target website
- **Data Formatting**: Utilized gpt-4o-mini to standardize the scraped content to match the original dataset structure

### 2. Indexing and Knowledge Base Construction

Once data is gathered, we build an efficient indexing system through two main components:

* **Knowledge Graph Construction**: Using the Lightrag project, a lightweight version of Graphrag, TinyRAG constructs a knowledge graph based on the scraped data. We employ gpt-4o-mini for entity and relationship extraction, though larger models like Quin 72B-instruct can also be used for enhanced performance.
* **Vector Store with Hybrid Search**: TinyRAG utilizes the Melvis VectorDB to store dense embeddings and support hybrid BM25 + dense retrieval. This combination allows for efficient retrieval of both sparse and dense features.

We leveraged LightRAG (a lightweight implementation of Microsoft's GraphRAG) for knowledge base creation:

- **One-time Processing**: Generated a persistent knowledge base for subsequent RAG operations
- **Dual Indexing**: Content indexed into both graph and vector stores
- **Cost-Efficient**: Complete indexing cost with gpt-4o-mini: $2.4
- **Scalability Options**: Compatible with larger models for potential performance improvements:
  - qwen2.5 72B

### 3. Graph Conversion and Custom Retrieval

The final phase optimizes retrieval by converting the Lightrag-generated graph into a Neo4j-compatible format. This step minimizes the costs associated with the LightRag retrieval approach (outlined in the Graphrag paper). After conversion, we implement a custom retrieval method that combines:
-	Fuzzy Search and Clustering: A tailored search mechanism to retrieve relevant nodes and relationships efficiently.
-	Unified Retrieval System: By merging the graph-based and vector-based retrieval mechanisms, TinyRAG achieves a powerful and flexible retrieval process that adapts to various query types.

### 4. Offline Retrieval-Augmented Generation Pipeline

With the data stores established, TinyRAG’s offline RAG pipeline processes user queries as follows:
- Parallel Retrieval: A user query is processed in parallel through both the Vector Store (using hybrid BM25 and dense search) and the Graph Store’s custom fuzzy search clustering retriever, which leverages the entity relationships graph.
- Re-ranking: The combined retrieved data is fed into an offline re-ranker based on Flan-T5 to enhance relevance.
- Generation: The re-ranked data is input into a small-language model (SLM), specifically Quin 7b-instruct, which runs locally via Ollama. This model generates the final response to the user query.

## Setup Instructions

### 0. we skip the scraping step as it doesn't contribute into the submission score, bearly noticable difference

### 1. chunk generation:
   ```bash
   python 1-generate_chunks/convert_csv_chunks.py
   ```

### 2. lightrag indexing
1. Clone and install LightRAG:
   ```bash
   cd 2-LightRAG
   pip install -e .
   ```
2. Configure the indexing script based on your model deployment (local/cloud) we prefere to use gpt-4o-mini for convience generating the entire graph will cost 2.4$
3. Run the indexing script:
   ```bash
   python 2-LightRAG/1-index.py
   ```

### 2. Graph Database Integration
We utilize Neo4j for enhanced graph querying capabilities:

1. Initialize Neo4j container:
   ```bash
   docker run -p 7476:7474 -p 7689:7687 --name neo4j-apoc \
   -e NEO4J_apoc_export_file_enabled=true \
   -e NEO4J_apoc_import_file_enabled=true \
   -e NEO4J_apoc_import_file_use__neo4j__config=true \
   -e NEO4J_PLUGINS='["graph-data-science", "apoc"]' \
   -e NEO4J_AUTH=neo4j/strongpassword \
   neo4j:5.23.0
   ```

2. Export graph structure:
   ```bash
   python 2-export_graph.py
   ```
   Source graph location: `lightrag/matter_v7X/graph_chunk_entity_relation.graphml`

3. Neo4j Configuration
Access the Neo4j browser interface:
- URL: `http://localhost:7476/browser/`
- Credentials: 
  - Username: `neo4j`
  - Password: `strongpassword`

Create necessary indexes:
```cypher
CREATE FULLTEXT INDEX nodeIndex FOR (n:Unknown) ON EACH [n.name, n.description]
##########

#####
CREATE FULLTEXT INDEX relationshipIndex FOR ()-[r:CONNECTED_TO]-() ON EACH [r.description, r.keywords]
```

### 4. Vector Store Implementation
we couldn't have much time to migrate into FAISS if it allowed we can update the version of this with Faiss 

We chose Milvus for vector storage due to its:
- Efficient hybrid search capabilities (BM25 + vector similarity)
- Native support for BGE-m3 multilingual embeddings
- Straightforward deployment process

#### Deployment
```bash
chmod 777 4-index_vectorstore/1-stand_alone.sh
bash 4-index_vectorstore/1-stand_alone.sh start
python 4-index_vectorestore/2-index.py

```

### 5. Inference Pipeline Architecture
<a href="https://ibb.co/Vjm754J"><img src="https://i.ibb.co/NVS8bBt/Screenshot-2024-11-10-at-12-18-54-PM.png" alt="Screenshot-2024-11-10-at-12-18-54-PM" border="0"></a>
Our pipeline implements a sophisticated retrieval and generation workflow:

#### Components
- **Dual Retrieval**: Parallel querying of Milvus vector store and Neo4j graph store
- **Reranking**: FlashRANK implementation (based on flan-t5) for result optimization
- **Generation**: Qwen2.5 7B (via ollama) for response synthesis

The entire pipeline is configurable through our visual pipeline builder, allowing for easy modifications and experimentation.


before building the pipeline you have to configure the components in components.yaml 
for now the following are supported:

```bash
components:
  query_input:
    input: {}
    output:
      query: str

  retrievers:
    - type: "vector"
      parameters:
        uri: "tcp://192.168.1.96:19530"
        collection_name: "XXX"
      input:
        query: str
      output:
        context: List[str]
      method: "invoke"

    - type: "graph"
      parameters:
        uri: "bolt://localhost:7689"
        user: "neo4j"
        password: "strongpassword"
      input:
        query: str
      output:
        context: List[str]
      method: "invoke"

  reranker:
    type: "flashrank"
    parameters:
      model_name: "rank-T5-flan"
      cache_dir: "/tmp"
    input:
      query: str
      input_context: List[str]
    output:
      context: List[str]
    method: "invoke"

  join:
    parameters:
      separator: "\n\nContext {i}:\n"
      final_separator: "\n\n----------\n\n"
    input:
      context_1: List[str]
      context_2: List[str]
    output:
      combined_context: str

  join_lists:
    parameters: {}
    input:
      context_1: List[str]
      context_2: List[str]
    output:
      input_context: List[str]
    method: "invoke"

   #any api call that has the same structure as openai api
  llm:
    type: "openai"
    parameters:
      model: "Qwen/Qwen2.5-7B-Instruct-Turbo"
      temperature: 0
    input:
      query: str
      context: str
    output:
      response: str
    method: "invoke"

   #could also use local ollama via langchain:
   #    llm:
   #  type: "ollama"
   #  parameters:
   #    model: "Qwen2.5-0.5B-Instruct"
   #    temperature: 0
   #  input:
   #    query: str
   #    context: str
   #  output:
   #    response: str
   #  method: "invoke"


  response_output:
    input:
      response: str
    output: {}

```


```bash
streamlit run 1-pipeline_builder.py
```

create the same pipeline as in the screenshot

```bash
python 2-main.py
```

This will reproduce the sumission file

### 6. User Interface

```bash
python 3-tiny_rag_server.py
```
then 

```bash
docker run -d -p 9099:9099 --add-host=host.docker.internal:host-gateway -e PIPELINES_URLS="https://github.com/benx13/openwebui-pipeline/blob/master/tinyRAG_pipeline.py"  --name pipelinesX99 --restart always ghcr.io/open-webui/pipelines:main
```
and 
```bash
docker run -d -p 3000:8080 -e OPENAI_API_KEY=0p3n-w3bu! -e OPENAI_API_BASE_URL=http://host.docker.internal:9099 -e ENABLE_OLLAMA_API=FALSE -e WEBUI_AUTH=FALSE  --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

then you can access the user interface from the link:

```bash
http://localhost:3000
```

<a href="https://ibb.co/4tw3pqx"><img src="https://i.ibb.co/ZXR7xjC/Screenshot-2024-11-13-at-9-30-43-AM.png" alt="Screenshot-2024-11-13-at-9-30-43-AM" border="0"></a>


## Future Improvements
- Enhanced graph relationship modeling
- Additional reranking strategies
- Integration of larger language models
- Performance optimization for scale
