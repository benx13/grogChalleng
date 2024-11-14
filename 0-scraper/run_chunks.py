#!/usr/bin/env python3

import os
import subprocess
from tqdm import tqdm
import time

def run_scrapers(batch_size=5):
    chunks_dir = "chunks_missing"
    script_path = "/Users/benx13/code/rags/challenge/scraper/scrape.py"
    python_path = "/usr/bin/python3"
    
    # Get all CSV files
    csv_files = sorted([
        os.path.join(chunks_dir, f) 
        for f in os.listdir(chunks_dir) 
        if f.endswith('.csv')
    ])
    
    if not csv_files:
        print("No CSV files found in chunks_2nd_pass directory!")
        return
    
    # Process files in batches
    for i in range(0, len(csv_files), batch_size):
        batch = csv_files[i:i+batch_size]
        processes = []
        
        # Launch batch of processes
        for csv_file in tqdm(batch, desc=f"Launching batch {i//batch_size + 1}"):
            cmd = f"{python_path} {script_path} -i {csv_file}"
            
            try:
                # Launch in background with nohup
                full_cmd = f"nohup {cmd} > logs_{os.path.basename(csv_file)}.out 2>&1 &"
                process = subprocess.Popen(full_cmd, shell=True)
                processes.append((process, os.path.basename(csv_file)))
                tqdm.write(f"🚀 Launched: {os.path.basename(csv_file)}")
            except subprocess.CalledProcessError as e:
                tqdm.write(f"❌ Failed to launch: {os.path.basename(csv_file)} - {str(e)}")
        
        tqdm.write(f"\n🎉 Launched batch {i//batch_size + 1} ({len(processes)} processes)")
        tqdm.write("Monitor logs with:")
        for _, filename in processes:
            tqdm.write(f"tail -f logs_{filename}.out")
        
        # Wait for all processes in batch to complete
        tqdm.write("\n⏳ Waiting for batch to complete...")
        while True:
            # Check if any python process is running for the current batch
            running = False
            for csv_file in batch:
                check_cmd = f"pgrep -f '{script_path} -i {csv_file}'"
                if subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE).returncode == 0:
                    running = True
                    break
            
            if not running:
                break
                
            time.sleep(10)  # Check every 10 seconds
        
        tqdm.write("✅ Batch complete!\n")

if __name__ == "__main__":
    run_scrapers(batch_size=10) 