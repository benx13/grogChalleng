from together import Together
import os

if "OPENAI_API_KEY" not in os.environ:
    os.environ["TOGETHER_API_KEY"] = 'XXX'

class OpenAILLM:
    def __init__(self, model='meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', temperature=0):
        self.client = Together()
        self.model = model
        self.temperature = temperature
        

    def invoke(self, context, query=''):
        try:
            print("\n\n")
            # Format context for better LLM consumption
            def format_context(context: list) -> str:
                formatted_docs = []
                for i, doc in enumerate(context, 1):
                    doc = str(doc).strip()
                    if doc:
                        doc = doc.replace("<SEP>", "\n")
                        doc = doc.replace("<s>", "") 
                        doc = doc.replace("</s>", "")
                        formatted_docs.append(f"Document {i}:\n{doc}")
                return "\n\n".join(formatted_docs)
                
            context = format_context(context)
            print(context)
            print("\n\n")
            system_prompt = f"""
            You are a helpful documentation agent responding to questions about data in the tables provided.

            ---Goal---
            Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
            If you don't know the answer, just say so. Do not make anything up.
            Do not include information where the supporting evidence for it is not provided.

            ---Data context--
            {context}

            answer the question in a human like format and CONCISELY and in a single line format not as a markdown
            the goal of these reponses is to evaluate a rag competition where the submission files are very close to following examples which will be examined by bertSCORE so stick to answering style of the given examples below

            examples:

            example1:
            question:
            When should OTA Requestors invoke the ApplyUpdateRequest command?
            response:
            OTA Requestors should invoke the ApplyUpdateRequest command once they are ready to apply a previously downloaded Software Image (Section ApplyUpdateRequest Command).

            example2:
            question:
            What is the definition of an interaction?
            response:
            An interaction is defined as a sequence of transactions.


            example3:
            question:
            What is the minimal requirement for Subscription path?
            response:
            "Defined in Section 2.11.2.2, “Subscribe Interaction Limits”."

            example4:
            question:
            What is the purpose of the Time Synchronization Cluster?
            response:
            "The Time Synchronization Cluster provides attributes for reading a Node’s current time and allows Administrators to set the current time, time zone, and daylight savings time (DST) settings."

            example5:
            question:
            What is the purpose of the Administrator Commissioning Cluster?
            response:
            "The Administrator Commissioning Cluster is used to trigger a Node to allow a new Administrator to commission it. It defines Attributes, Commands, and Responses needed for this purpose."

            example6:
            question:
            What does the 'InterfaceEnabled' attribute indicate?
            response:
            The 'InterfaceEnabled' attribute indicates whether the associated network interface is enabled or not.

            example7:
            question:
            What is the ID and name of the command that resets counts?
            response:
            "The ID of the command is 0x00, and its name is ResetCounts."

            example8:
            question:
            What type of initialization vectors do Devices use?
            response:
            Devices use random initialization vectors.

            example9:
            question:
            What is a downstream subscription?
            response:
            A downstream subscription is when clients subscribe to the proxy.

            example10:
            question:
            What are the Management Opcodes for BTP Control Frames?
            response:
            "The Management Opcodes for BTP Control Frames are defined in Table 28, “BTP Control codes”."

            example11:
            question:
            What does the RxDataCount attribute indicate?
            response:
            The RxDataCount attribute indicates the total number of received unique MAC Data frames.

            example12:
            question:
            What does an Action ID indicate according to the Matter Specification?
            response:
            It indicates an action as defined in the Interaction Model specification.

            example13:
            question:
            "According to the specification, how are Certification Declarations generated and transmitted?
            response:
            They are not generated by any Node but are stored and transmitted to a Commissioner by a Commissionee during the conveyance of the Attestation Information in response to an Attestation Request command.          
                        
            Using the provided contexts, respond concisely and exactly to the question. Answer only from the two contexts given below.

            """

            print(system_prompt)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )

            result = response.choices[0].message.content
            return {"response": result}
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
        self.model = new_model
        print(f"Model switched to: {new_model}")

if __name__ == "__main__":
    # Example usage
    openai_llm = OpenAILLM(model='Qwen/Qwen2.5-7B-Instruct-Turbo')
    
    # Sample contexts and question
    context = "Pete Warden is a software engineer and entrepreneur known for his work in machine learning and mobile technology."
    query = "Who is Pete Warden and what is he known for?"

    result = openai_llm.invoke(context, query)
    print("LLM Response:")
    print(result)





