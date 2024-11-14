import pandas as pd
import math
from tqdm import tqdm
import os

# Create output directory if it doesn't exist
output_dir = 'chunks_missing'
os.makedirs(output_dir, exist_ok=True)

# Read the CSV file
df = pd.read_csv('missing.csv')

# Calculate number of chunks needed (rounding up)
total_rows = len(df)
chunk_size = 5
num_chunks = math.ceil(total_rows / chunk_size)

# Split and save chunks with progress bar
for i in tqdm(range(num_chunks), desc="Creating chunks"):
    start_idx = i * chunk_size
    end_idx = min((i + 1) * chunk_size, total_rows)
    
    chunk = df[start_idx:end_idx]
    chunk.to_csv(f'{output_dir}/test_chunk_{i+1}.csv', index=False)
