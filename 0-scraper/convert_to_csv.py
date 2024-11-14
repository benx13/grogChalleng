#!/usr/bin/env python3

import os
import json
import csv
from tqdm import tqdm

def convert_output_to_csv():
    output_dir = "output"
    output_file = "train2.csv"
    
    # Collect all conversations from JSON files
    all_conversations = []
    
    # Process each JSON file
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    for json_file in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(os.path.join(output_dir, json_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # Extract question and answer from conversation
                    conversation = item['conversation']
                    if len(conversation) >= 2:
                        query = conversation[0]['content']
                        response = conversation[1]['content']
                        all_conversations.append({
                            'trustii_id': item['trustii_id'],
                            'Query': query,
                            'Response': response
                        })
        except Exception as e:
            tqdm.write(f"Error processing {json_file}: {str(e)}")
    
    # Sort by trustii_id
    all_conversations.sort(key=lambda x: int(x['trustii_id']))
    
    # Write to CSV
    if all_conversations:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['trustii_id', 'Query', 'Response'])
            writer.writeheader()
            writer.writerows(all_conversations)
        
        tqdm.write(f"\n✅ Converted {len(all_conversations)} conversations to {output_file}")
    else:
        tqdm.write("❌ No conversations found to convert")

if __name__ == "__main__":
    convert_output_to_csv() 