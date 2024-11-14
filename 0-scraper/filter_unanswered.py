#!/usr/bin/env python3

import os
import json
import csv
import shutil
from tqdm import tqdm

def filter_unanswered_questions():
    chunks_dir = "chunks"
    output_dir = "output"
    retry_dir = "chunks_2nd_pass"
    
    # Create retry directory if it doesn't exist
    os.makedirs(retry_dir, exist_ok=True)
    
    # Get list of CSV files
    csv_files = [f for f in os.listdir(chunks_dir) if f.endswith('.csv')]
    
    # Process each CSV file with progress bar
    for csv_file in tqdm(csv_files, desc="Processing chunks"):
        base_name = os.path.splitext(csv_file)[0]
        json_file = f"{base_name}.json"
        json_path = os.path.join(output_dir, json_file)
        
        # Get answered question IDs from JSON if it exists
        answered_ids = set()
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    answered_ids = {str(item['trustii_id']) for item in data}
            except Exception as e:
                tqdm.write(f"Error reading {json_file}: {str(e)}")
                continue
        
        # Read original CSV and filter out answered questions
        csv_path = os.path.join(chunks_dir, csv_file)
        retry_path = os.path.join(retry_dir, f"{base_name}_retry.csv")
        unanswered = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['trustii_id'] not in answered_ids:
                        unanswered.append(row)
            
            # If there are unanswered questions, create retry file
            if unanswered:
                with open(retry_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['trustii_id', 'Query'])
                    writer.writeheader()
                    writer.writerows(unanswered)
                tqdm.write(f"{csv_file}: {len(unanswered)} questions need retry")
                
        except Exception as e:
            tqdm.write(f"Error processing {csv_file}: {str(e)}")

if __name__ == "__main__":
    filter_unanswered_questions() 