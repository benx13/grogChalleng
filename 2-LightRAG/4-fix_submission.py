import os
import pandas as pd
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
from pprint import pprint
from tqdm import tqdm
#########
# Uncomment the below two lines if running in a jupyter notebook to handle the async nature of rag.insert()
# import nest_asyncio 
# nest_asyncio.apply() 
#########
os.environ["OPENAI_API_KEY"] = "XXXXX"
WORKING_DIR = "/Users/benx13/code/rags/challenge/LightRAG/matter_"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete  # Use gpt_4o_mini_complete LLM model
    # llm_model_func=gpt_4o_complete  # Optionally, use a stronger model
)

# Read both files
test_df = pd.read_csv("test.csv")
merged_df = pd.read_csv("/Users/benx13/code/rags/challenge/LightRAG/merged_results__33X.csv")

# Find missing queries by comparing trustii_ids
missing_queries = test_df[~test_df['trustii_id'].isin(merged_df['trustii_id'])]
print(f"Found {len(missing_queries)} missing queries")

# Create predictions only for missing queries
predictions = []
for _, row in missing_queries.iterrows():
    query = row['Query']
    # If query is empty or NaN, save with empty response
    if pd.isna(query) or str(query).strip() == '':
        print(f"Empty query found for trustii_id: {row['trustii_id']}")
        predictions.append({
            'trustii_id': row['trustii_id'],
            'Query': '',
            'Response': ''
        })
    else:
        response = rag.query(query, param=QueryParam(mode="hybrid"))
        predictions.append({
            'trustii_id': row['trustii_id'],
            'Query': query,
            'Response': response
        })

# Combine existing results with new predictions
if predictions:
    new_predictions_df = pd.DataFrame(predictions)
    final_results_df = pd.concat([merged_df, new_predictions_df], ignore_index=True)
    # Sort by trustii_id to maintain order
    final_results_df = final_results_df.sort_values('trustii_id')
    final_results_df.to_csv("merged_results__33XXX.csv", index=False)
    print(f"Added {len(predictions)} new predictions to merged_results.csv")
else:
    print("No missing queries found")