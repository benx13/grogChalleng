from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class OllamaLLM:
    def __init__(self, model='llama3.1:8b-instruct-q8_0', temperature=0):
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
        )
        self.prompt = PromptTemplate(
            template="""Using the provided contexts, respond concisely and exactly to the question. Answer only from the two contexts given below.

            context: {context}

            question: {query}
            """,
            input_variables=["context", "query"],
        )
        self.rag_chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, context, query=''):
        try:
            print()
            print()
            print()
            # Format context for better LLM consumption
            def format_context(context: list) -> str:
                # Format each document with a prefix
                formatted_docs = []
                for i, doc in enumerate(context, 1):
                    doc = str(doc).strip()
                    if doc:
                        # Remove special formatting tokens
                        doc = doc.replace("<SEP>", "\n")
                        doc = doc.replace("<s>", "") 
                        doc = doc.replace("</s>", "")
                        formatted_docs.append(f"Document {i}:\n{doc}")
                
                # Join all formatted documents
                formatted_context = "\n\n".join(formatted_docs)
                
                return formatted_context
                
            # Format the context before printing
            context = format_context(context)
            print(context)
            print()
            print()
            print()
            result = self.rag_chain.invoke({
                "context": context,
                "query": query
            })

            response = {"response": result}
            return response
        except Exception as e:
            print(f"An error occurred while invoking the LLM: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    def switch_model(self, new_model: str):
        """
        Switch the current model to a new one.
        
        Args:
            new_model (str): The name of the new model to use.
        """
        self.llm = ChatOllama(
            model=new_model,
            temperature=self.llm.temperature,
        )
        print(f"Model switched to: {new_model}")

if __name__ == "__main__":
    # Example usage
    ollama_llm = OllamaLLM(model='qwen2.5:0.5b-instruct')
    
    # Sample contexts and question
    context = "Pete Warden is a software engineer and entrepreneur known for his work in machine learning and mobile technology."
    query = "Who is Pete Warden and what is he known for?"

    result = ollama_llm.invoke(context, query)
    print("LLM Response:")
    print(result)





