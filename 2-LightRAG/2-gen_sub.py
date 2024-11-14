import os
import pandas as pd
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
from pprint import pprint
from tqdm import tqdm
import asyncio
from typing import List, Dict
import numpy as np
import signal
import sys
from datetime import datetime

# Use environment variable for API key instead of hardcoding
os.environ["OPENAI_API_KEY"] = "XXXXX"
WORKING_DIR = "/Users/benx13/code/rags/challenge/LightRAG/matter_v7X"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# Define custom LLM and embedding functions with controlled parameters
async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    return await openai_complete_if_cache(
        "gpt-4o-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        max_tokens=512,  # Limit token usage
        **kwargs,
    )

async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embedding(
        texts,
        model="text-embedding-3-small",  # Use smaller embedding model
    )

# Initialize RAG with custom functions and disabled caching
rag = LightRAG(
    working_dir=WORKING_DIR,
    enable_llm_cache=False,  # Disable caching to prevent token accumulation
    llm_model_func=llm_model_func,
    embedding_func=EmbeddingFunc(
        embedding_dim=1536,
        max_token_size=8192,
        func=embedding_func
    ),
    embedding_batch_num=32,
    embedding_func_max_async=16,
)

def batch_queries(queries: List[Dict], batch_size: int = 32):
    for i in range(0, len(queries), batch_size):
        yield queries[i:i + batch_size]

async def process_batch(rag: LightRAG, batch: List[Dict]) -> List[Dict]:
    tasks = []
    for item in batch:
        query = item['Query']
        if pd.isna(query) or str(query).strip() == '':
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        else:
            tasks.append(
                asyncio.create_task(
                    rag.aquery(
                        query, 
                        param=QueryParam(
                            mode="hybrid",
                            max_token_for_text_unit=1024  # Limit context size
                        )
                    )
                )
            )
    
    results = await asyncio.gather(*tasks)
    
    processed_batch = []
    for item, result in zip(batch, results):
        if pd.isna(item['Query']) or str(item['Query']).strip() == '':
            processed_batch.append({
                'trustii_id': item['trustii_id'],
                'Query': '',
                'Response': ''
            })
        else:
            processed_batch.append({
                'trustii_id': item['trustii_id'],
                'Query': item['Query'],
                'Response': result
            })
    
    return processed_batch

def save_results(predictions, merged_df, final=False):
    """Save current results to CSV"""
    if predictions:
        new_predictions_df = pd.DataFrame(predictions)
        final_results_df = pd.concat([merged_df, new_predictions_df], ignore_index=True)
        final_results_df = final_results_df.sort_values('trustii_id')
        suffix = "final" if final else "interrupted"
        output_file = f"merged_results_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_results_df.to_csv(output_file, index=False)
        print(f"\nSaved {len(predictions)} predictions to {output_file}")
    else:
        print("\nNo new predictions to save")

def signal_handler(signum, frame):
    """Handle Ctrl+C by saving current results"""
    print("\nCtrl+C detected. Saving current results...")
    save_results(predictions, merged_df)
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Main processing logic
test_df = pd.read_csv("test.csv")
merged_df = pd.read_csv("/Users/benx13/code/rags/challenge/LightRAG/merged_results__77X.csv")

missing_queries = test_df[~test_df['trustii_id'].isin(merged_df['trustii_id'])]
print(f"Found {len(missing_queries)} missing queries")

queries_to_process = missing_queries.to_dict('records')

predictions = []
loop = asyncio.get_event_loop()

try:
    for batch in tqdm(list(batch_queries(queries_to_process, 32)), desc="Processing batches"):
        batch_predictions = loop.run_until_complete(process_batch(rag, batch))
        predictions.extend(batch_predictions)

    # Save final results
    save_results(predictions, merged_df, final=True)

except Exception as e:
    print(f"\nError occurred: {e}")
    print("Saving current results before exit...")
    save_results(predictions, merged_df)
    raise e