import networkx as nx
import json
import yaml
from typing import Dict, Any
import pandas as pd
# Import base components
from components import QueryInput, ResponseOutput, Join, JoinLists, ContextFormatter
from retriever import Retriever
from llm import LLM
from reranker import Reranker

class RAGPipeline:
    def __init__(self, barfi_path="/Users/benx13/code/rags/challenge/inference/schema.barfi", components_path="components.yaml"):
        print("Initializing RAG Pipeline...")
        
        # Load configurations
        with open(components_path, 'r') as f:
            self.components_config = yaml.safe_load(f)['components']
        
        # Component class mapping
        self.component_classes = {
            'query_input': QueryInput,
            'response_output': ResponseOutput,
            'reranker': lambda params: Reranker('flashrank', **params),
            'vector_retriever': lambda params: Retriever('vector', **params),
            'graph_retriever': lambda params: Retriever('graph', **params),
            'join': Join,
            'join_lists': JoinLists,
            'context_formatter': ContextFormatter,
            'llm': lambda params: LLM('openai', **params)
        }
        
        self.pipeline_graph = self._load_barfi_schema(barfi_path)
        self.components = {}
        self._initialize_components()
        
        print("Pipeline initialized successfully")

    def _load_barfi_schema(self, barfi_path: str) -> nx.DiGraph:
        """Load the pipeline graph from a barfi schema file"""
        print(f"Loading pipeline schema from {barfi_path}")
        
        with open(barfi_path, 'r', encoding='utf-8') as f:
            barfi_data = json.load(f)
            
        G = nx.DiGraph()
        
        # Add nodes
        for node_id, node_data in barfi_data['nodes'].items():
            component_type = node_data['type'].lower().replace(' ', '_')
            print(f"Adding node: {node_id} of type {component_type}")
            G.add_node(
                node_id, 
                type=component_type,
                parameters=node_data.get('parameters', {}),
                interfaces=node_data.get('interfaces', {})
            )
        
        # Add edges
        for edge in barfi_data['edges']:
            print(f"Adding edge: {edge['source']} -> {edge['target']}")
            G.add_edge(
                edge['source'], 
                edge['target'],
                source_port=edge['source_port'],
                target_port=edge['target_port']
            )
            
        return G

    def _initialize_components(self):
        """Initialize component instances"""
        print("\nInitializing components...")
        
        for node_id, node_data in self.pipeline_graph.nodes(data=True):
            component_type = node_data['type'].lower().replace(' ', '_')
            parameters = node_data.get('parameters', {})

            
            try:
                if 'retriever' in component_type:
                    # Extract retriever type from component type (e.g., 'vector' from 'vector_retriever')
                    retriever_type = component_type.split('_')[0]
                    print(f"Initializing {retriever_type} retriever for node {node_id}")
                    print(f"Parameters: {parameters}")  # Debug print
                    
                    # Make sure we're passing the correct parameters
                    if retriever_type == 'vector':
                        if 'uri' not in parameters or 'collection_name' not in parameters:
                            raise ValueError(f"Vector retriever requires 'uri' and 'collection_name' parameters. Got: {parameters}")
                    
                    self.components[node_id] = Retriever(retriever_type, **parameters)
                
                elif component_type == 'llm':
                    print(f"Initializing LLM for node {node_id}")
                    self.components[node_id] = LLM('openai', **parameters)
                
                elif component_type == 'reranker':
                    self.components[node_id] = Reranker('flashrank', **parameters)
                
                elif component_type in ['query_input', 'response_output', 'join', 'join_lists', 'context_formatter']:
                    print(f"Initializing {component_type} for node {node_id}")
                    component_class = self.component_classes[component_type]
                    self.components[node_id] = component_class(parameters)
                
                else:
                    print(f"Warning: Unknown component type {component_type}")
                    
            except Exception as e:
                print(f"Error initializing component {node_id}: {str(e)}")
                raise

    def process(self, query: str) -> Dict[str, Any]:
        """Execute the pipeline with step-by-step verbose output"""
        print("\n" + "="*80)
        print("PIPELINE EXECUTION START")
        print("="*80)
        
        results = {}
        
        # Get processing order
        try:
            processing_order = list(nx.topological_sort(self.pipeline_graph))
            print("\nStep 0: Pipeline Initialization")
            print("Input:")
            print(f"  - Initial query: {query}")
            print("Execution:")
            print(f"  - Determined processing order: {processing_order}")
            print("Output:")
            print("  - Pipeline ready for execution")
            print("Status: ✅ Success")
            print("-"*80)
            
        except nx.NetworkXUnfeasible:
            print("Status: ❌ Failed - Cyclic dependency detected")
            print("-"*80)
            raise ValueError("Pipeline graph must be acyclic")

        # Process each node in order
        for step, node_id in enumerate(processing_order, 1):
            node_data = self.pipeline_graph.nodes[node_id]
            component_type = node_data['type'].lower().replace(' ', '_')
            component = self.components.get(node_id)
            
            print(f"\nStep {step}: {component_type.replace('_', ' ').title()}")
            
            # Collect inputs for the component
            inputs = {}
            
            # Special handling for QueryInput - pass the initial query
            if component_type == 'query_input':
                inputs['query'] = query
            else:
                # For all other components, collect inputs from predecessors
                for pred in self.pipeline_graph.predecessors(node_id):
                    edge_data = self.pipeline_graph[pred][node_id]
                    source_port = edge_data['source_port']
                    target_port = edge_data['target_port']
                    
                    # Get the output from the predecessor's results
                    pred_output = results.get(f"{pred}_{source_port}")
                    if pred_output is not None:
                        inputs[target_port] = pred_output
            
            # Print inputs
            print("Input:")
            for input_name, input_value in inputs.items():
                if input_name in ['context', 'combined_context'] and isinstance(input_value, str):
                    print(f"  - {input_name}:")
                    for line in input_value.split('\n'):
                        print(f"    {line}")
                else:
                    print(f"  - {input_name}: {input_value}")
            
            # Invoke the component
            success = False
            try:
                print("Execution:")
                print(f"  - Invoking {component_type} component")
                component_results = component.invoke(**inputs)
                print(f"Component results: {component_results}")
                # Store and print results
                print("Output:")
                for output_name, output_value in component_results.items():
                    result_key = f"{node_id}_{output_name}"
                    results[result_key] = output_value
                    
                    # Format output based on type
                    if output_name in ['context', 'combined_context'] and isinstance(output_value, str):
                        print(f"  - {output_name}:")
                        for line in output_value.split('\n'):
                            print(f"    {line}")
                    else:
                        print(f"  - {output_name}: {output_value}")
                
                success = True
                    
            except Exception as e:
                print("Execution Error:")
                print(f"  - {str(e)}")
                print(f"Status: ❌ Failed - {str(e)}")
                raise
            finally:
                if success:
                    print("Status: ✅ Success")
                print("-"*80)
        
        print("\n" + "="*80)
        print("PIPELINE EXECUTION COMPLETE")
        final_success = len(results) == len(processing_order)
        print(f"Overall Status: {'✅ Success' if final_success else '❌ Failed'}")
        print("="*80)
        return results

    def close(self):
        """Close all components that have a close method"""
        for component in self.components.values():
            if hasattr(component, 'close'):
                component.close()
if __name__ == "__main__":
    # Example usage
    pipeline = RAGPipeline(components_path="5-inference/components.yaml")

    response = pipeline.process('hello there')
    print(response)