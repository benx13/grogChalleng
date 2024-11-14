import os
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete, o1_mini_complete
from tqdm import tqdm

os.environ["OPENAI_API_KEY"] = "XXXXX"

WORKING_DIR = "2-LightRAG/matter_v7XX"


if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete  # Use gpt_4o_mini_complete LLM model
    # llm_model_func=gpt_4o_complete  # Optionally, use a stronger model
)

# Process files in batches of 10
batch_size = 32
files = sorted(os.listdir("chunks"))
for i in tqdm(range(2240, len(files), batch_size), desc="Processing batches"):
    batch_texts = []
    batch_files = files[i:i + batch_size]
    
    for filename in batch_files:
        filepath = os.path.join("chunks", filename)
        with open(filepath, "r") as f:
            batch_texts.append(f.read())
    
    rag.insert(batch_texts)

