#!/usr/bin/env python3

import os
import json
from tqdm import tqdm

def combine_json_files():
    output_dir = "output"
    combined_file = "combined_output_missed.json"
    
    # Collect all conversations from JSON files
    all_conversations = []
    seen_ids = set()
    
    # Process each JSON file
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    for json_file in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(os.path.join(output_dir, json_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Only add conversations we haven't seen before
                for conv in data:
                    if conv['trustii_id'] not in seen_ids:
                        all_conversations.append(conv)
                        seen_ids.add(conv['trustii_id'])
        except Exception as e:
            tqdm.write(f"Error processing {json_file}: {str(e)}")
    
    # Sort by trustii_id
    all_conversations.sort(key=lambda x: int(x['trustii_id']))
    
    # Write combined JSON
    if all_conversations:
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_conversations, f, indent=2, ensure_ascii=False)
        
        tqdm.write(f"\n✅ Combined {len(all_conversations)} unique conversations into {combined_file}")
        tqdm.write(f"📊 Total files processed: {len(json_files)}")
    else:
        tqdm.write("❌ No conversations found to combine")

if __name__ == "__main__":
    combine_json_files()
