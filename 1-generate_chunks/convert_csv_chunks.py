import pandas as pd
import os
from tqdm import tqdm

def convert_csv_to_chunks(csv_path, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Print diagnostic information
    print(f"Total rows in CSV: {len(df)}")
    print(f"Index range: {df.index.min()} to {df.index.max()}")
    print(f"Number of non-null values in each column:")
    print(df.count())
    
    # Check for missing values
    print("\nMissing values in each column:")
    print(df.isnull().sum())
    
    # Print the first few rows with null values if any exist
    null_rows = df[df.isnull().any(axis=1)]
    if not null_rows.empty:
        print("\nFirst few rows with null values:")
        print(null_rows.head())
    
    # Iterate through each row with tqdm progress bar
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Converting chunks"):
        # Create chunk content with the specified format
        # chunk_content = f"query:\n{row['Query']}\nresponse:\n{row['Response']}"
        chunk_content = f"{row['Response']}"
        
        # Create a filename for the chunk
        chunk_filename = f"chunk_{index}.txt"
        
        # Write the chunk to a file
        with open(os.path.join(output_dir, chunk_filename), 'w', encoding='utf-8') as f:
            f.write(chunk_content)

if __name__ == "__main__":
    # Specify input CSV and output directory
    csv_path = "train_enriched.csv"
    output_dir = "chunks"
    
    # Convert CSV to chunks
    convert_csv_to_chunks(csv_path, output_dir)
    print(f"Conversion complete. Chunks saved in '{output_dir}' directory.")
