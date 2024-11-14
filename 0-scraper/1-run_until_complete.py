#!/usr/bin/env python3

import os
import subprocess
import json
import csv
import time
from tqdm import tqdm

def get_unanswered_questions():
    """Compare original chunks with output and return files with unanswered questions"""
    chunks_dir = "chunks_missing"
    output_dir = "output"
    retry_dir = "chunks_missing_2nd_pass"
    os.makedirs(retry_dir, exist_ok=True)
    
    unanswered_files = []
    
    # Process each original CSV file
    for csv_file in os.listdir(chunks_dir):
        if not csv_file.endswith('.csv'):
            continue
            
        base_name = os.path.splitext(csv_file)[0]
        json_file = f"{base_name}.json"
        json_path = os.path.join(output_dir, json_file)
        
        # Get answered question IDs from JSON
        answered_ids = set()
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                answered_ids = {str(item['trustii_id']) for item in data}
        
        # Check original CSV for unanswered questions
        csv_path = os.path.join(chunks_dir, csv_file)
        retry_path = os.path.join(retry_dir, f"{base_name}_retry.csv")
        unanswered = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            total_questions = 0
            for row in reader:
                total_questions += 1
                if row['trustii_id'] not in answered_ids:
                    unanswered.append(row)
        
        # If there are unanswered questions, create retry file
        if unanswered:
            with open(retry_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['trustii_id', 'Query'])
                writer.writeheader()
                writer.writerows(unanswered)
            unanswered_files.append({
                'file': retry_path,
                'count': len(unanswered),
                'total': total_questions,
                'original': csv_file
            })
    
    return unanswered_files

def print_summary(unanswered_files):
    """Print summary of unanswered questions"""
    if not unanswered_files:
        tqdm.write("\n🎉 All questions have been answered!")
        return False
        
    tqdm.write("\n📊 Summary of Unanswered Questions:")
    tqdm.write("-" * 80)
    tqdm.write(f"{'Original File':<30} {'Total':<10} {'Answered':<10} {'Remaining':<10} {'Progress':<10}")
    tqdm.write("-" * 80)
    
    total_questions = 0
    total_unanswered = 0
    
    for file_info in unanswered_files:
        total = file_info['total']
        remaining = file_info['count']
        answered = total - remaining
        progress = (answered / total) * 100
        
        total_questions += total
        total_unanswered += remaining
        
        tqdm.write(f"{file_info['original']:<30} {total:<10} {answered:<10} {remaining:<10} {progress:>6.1f}%")
    
    tqdm.write("-" * 80)
    total_progress = ((total_questions - total_unanswered) / total_questions) * 100
    tqdm.write(f"Overall Progress: {total_progress:.1f}% ({total_questions - total_unanswered}/{total_questions} questions answered)")
    tqdm.write(f"Remaining Questions: {total_unanswered}")
    tqdm.write("-" * 80)
    
    return True

def run_scrapers(batch_size=5):
    """Run scrapers in batches"""
    script_path = "/Users/benx13/code/rags/challenge/scraper/scrape.py"
    python_path = "/usr/bin/python3"
    
    while True:
        # Get current unanswered questions
        unanswered_files = get_unanswered_questions()
        if not print_summary(unanswered_files):
            break
            
        total_unanswered = sum(file_info['count'] for file_info in unanswered_files)
        tqdm.write(f"\n📊 Found {total_unanswered} unanswered questions across {len(unanswered_files)} files")
        
        # Process files in batches
        for i in range(0, len(unanswered_files), batch_size):
            batch = unanswered_files[i:i+batch_size]
            processes = []
            
            # Launch batch of processes
            for file_info in tqdm(batch, desc=f"Launching batch {i//batch_size + 1}"):
                csv_file = file_info['file']
                count = file_info['count']
                cmd = f"{python_path} {script_path} -i {csv_file}"
                
                try:
                    full_cmd = f"nohup {cmd} > logs_{os.path.basename(csv_file)}.out 2>&1 &"
                    process = subprocess.Popen(full_cmd, shell=True)
                    processes.append((process, os.path.basename(csv_file)))
                    tqdm.write(f"🚀 Launched: {os.path.basename(csv_file)} ({count} questions)")
                except subprocess.CalledProcessError as e:
                    tqdm.write(f"❌ Failed to launch: {os.path.basename(csv_file)} - {str(e)}")
            
            tqdm.write(f"\n⏳ Waiting for batch to complete...")
            while True:
                # Check if any python process is running for the current batch
                running = False
                for file_info in batch:
                    check_cmd = f"pgrep -f '{script_path} -i {file_info['file']}'"
                    if subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE).returncode == 0:
                        running = True
                        break
                
                if not running:
                    break
                    
                time.sleep(10)  # Check every 10 seconds
            
            tqdm.write("✅ Batch complete!\n")
            
            # Break the batch loop to recheck all files
            break
        
        # After batch completes, wait a bit and continue main loop
        tqdm.write("\n🔍 Checking for remaining questions...")
        time.sleep(30)  # Wait for file system to sync

if __name__ == "__main__":
    run_scrapers(batch_size=10)