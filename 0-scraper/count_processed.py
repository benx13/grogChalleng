#!/usr/bin/env python3

import os
import json

def count_processed_questions():
    output_dir = "output"
    total_questions = 0
    file_counts = []
    
    # Check if output directory exists
    if not os.path.exists(output_dir):
        print("Output directory not found!")
        return
    
    # Process each JSON file
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = len(data)
                    total_questions += count
                    file_counts.append((filename, count))
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")
    
    # Print results
    print("\nProcessed questions per file:")
    print("-" * 50)
    for filename, count in sorted(file_counts):
        print(f"{filename}: {count} questions")
    
    print("\nTotal processed questions:", total_questions)

if __name__ == "__main__":
    count_processed_questions() 