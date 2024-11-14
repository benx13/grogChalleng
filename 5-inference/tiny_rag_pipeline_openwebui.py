from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import os
import time
import requests
import json


def test_chat_api(query: str):
    url = "http://host.docker.internal:5002/ask"
    
    payload = {
        "query": query,
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json().get('answer')
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "wiki_pipeline"
        self.name = "tinyRAG"

        # Initialize rate limits
        #self.valves = self.Valves(**{"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")})

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        response = test_chat_api(query=user_message)


        def response_generator(response):
            for i in response.split("\n"):
                time.sleep(0.1)
                yield f"{i}\n"

        return response_generator(response)
