#!/usr/bin/env python3

import os

def get_missing_files():
    # Get list of CSV files in chunks directory
    chunks_dir = "chunks"
    output_dir = "output"
    
    # Get all CSV files from chunks
    chunk_files = {
        os.path.splitext(f)[0] 
        for f in os.listdir(chunks_dir) 
        if f.endswith('.csv')
    }
    
    # Get all JSON files from output
    output_files = {
        os.path.splitext(f)[0] 
        for f in os.listdir(output_dir) 
        if f.endswith('.json')
    }
    
    # Find files that are in chunks but not in output
    missing_files = chunk_files - output_files
    
    # Print results
    if missing_files:
        print("Files to process:")
        for file in sorted(missing_files):
            print(f"- {file}.csv")
        print(f"\nTotal files to process: {len(missing_files)}")
    else:
        print("All files have been processed!")

if __name__ == "__main__":
    get_missing_files() 


