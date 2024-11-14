from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseComponent(ABC):
    """Base class for all pipeline components"""
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}

    @abstractmethod
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """Execute the component's main functionality"""
        pass

class QueryInput(BaseComponent):
    """Component that handles the initial query input"""
    def invoke(self, query: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process the initial query.
        
        Args:
            query (str): The input query
            **kwargs: Additional arguments
            
        Returns:
            Dict[str, Any]: Dictionary containing the query
        """
        print(f"[QueryInput] Processing query: {query}")
        if not query:
            raise ValueError("Query cannot be empty")
        return {"query": query}

class ResponseOutput(BaseComponent):
    """Component that handles the final response output"""
    def invoke(self, response: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process the final response.
        
        Args:
            response (str): The response to output
            **kwargs: Additional arguments
            
        Returns:
            Dict[str, Any]: Dictionary containing the response
        """
        print(f"[ResponseOutput] Final response: {response}")
        if not response:
            raise ValueError("Response cannot be empty")
        return {"response": response}

class Join(BaseComponent):
    """Component that joins multiple input strings into a single string"""
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Join multiple context strings into a single string.
        
        Args:
            **kwargs: Variable number of context inputs (context_1, context_2, etc.)
            
        Returns:
            Dict[str, Any]: Dictionary containing the combined context
        """
        print(f"[Join] Joining {len(kwargs)} contexts")
        
        # Get parameters or use defaults
        separator = self.parameters.get('separator', "\n\nContext {i}:\n")
        final_separator = self.parameters.get('final_separator', "\n\n----------\n\n")
        
        # Filter out non-context inputs
        contexts = {k: v for k, v in kwargs.items() if k.startswith('context_')}
        
        if not contexts:
            raise ValueError("No context inputs provided")
        
        # Sort contexts by their number to ensure consistent order
        sorted_contexts = sorted(contexts.items(), key=lambda x: int(x[0].split('_')[1]))
        
        # Join contexts with numbered separators
        combined = []
        for i, (_, context) in enumerate(sorted_contexts, 1):
            if context:  # Only add non-empty contexts
                combined.append(separator.format(i=i) + context.strip())
        
        # Join all parts with the final separator
        result = final_separator.join(combined)
        
        print(f"[Join] Successfully combined {len(contexts)} contexts")
        return {"combined_context": result}

class JoinLists(BaseComponent):
    """Component that merges multiple lists into a single list"""
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Merge multiple input lists into a single list.
        
        Args:
            list_1 (List[str]): First list of strings
            list_2 (List[str]): Second list of strings
            **kwargs: Additional arguments
            
        Returns:
            Dict[str, Any]: Dictionary containing the merged list
        """
        print(f"[JoinLists] Merging input lists")
        
        list_1 = kwargs.get('context_1', [])
        list_2 = kwargs.get('context_2', [])
        
        if not isinstance(list_1, list) or not isinstance(list_2, list):
            raise ValueError("Inputs must be lists")
            
        # Merge lists while removing duplicates using a set
        merged = list(dict.fromkeys(list_1 + list_2))
        
        print(f"[JoinLists] Successfully merged lists. Total items: {len(merged)}")
        return {"input_context": merged}

class ContextFormatter(BaseComponent):
    """Component that formats context for LLM input"""
    def invoke(self, context: list = None, query: str = None, **kwargs) -> Dict[str, Any]:
        """
        Format context list into a clean string for LLM consumption.
        
        Args:
            context (list): List of context strings to format (from reranker)
            query (str): Original query
            **kwargs: Additional arguments
            
        Returns:
            Dict[str, Any]: Dictionary containing the formatted context
        """
        print(f"[ContextFormatter] Formatting {len(context) if context else 0} context items")
        
        if not context:
            raise ValueError("Reranked context list cannot be empty")
            
        # Get parameters or use defaults
        separator = self.parameters.get('separator', '\n\n---\n\n')
        prefix = self.parameters.get('prefix', 'Relevant context:\n\n')
        
        # Join contexts with separator
        formatted_context = prefix + separator.join(str(c) for c in context)
        
        print(f"[ContextFormatter] Successfully formatted context")
        return {"formatted_context": formatted_context}

# Example usage
if __name__ == "__main__":
    # Test QueryInput
    query_input = QueryInput()
    result = query_input.invoke(query="What is the capital of France?")
    print(result)
    
    # Test ResponseOutput
    response_output = ResponseOutput()
    result = response_output.invoke(response="The capital of France is Paris.")
    print(result)
    
    # Test JoinLists
    join_lists = JoinLists()
    result = join_lists.invoke(
        list_1=["item1", "item2"], 
        list_2=["item2", "item3"]
    )
    print(result)  # Should print: {'merged_list': ['item1', 'item2', 'item3']}


