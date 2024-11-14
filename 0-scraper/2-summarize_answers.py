#!/usr/bin/env python3

import os
import json
import time
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import functools

os.environ["OPENAI_API_KEY"] = "XXXX"


def process_item(item):
    """Process a single item with OpenAI API"""
    global client
    max_retries = 3
    retry_delay = 5  # seconds
    
    try:
        # Extract question and answer from conversation
        question = next(msg['content'] for msg in item['conversation'] 
                     if msg['role'] == 'user')
        answer = next(msg['content'] for msg in item['conversation'] 
                    if msg['role'] == 'assistant')
        
        # Create prompt for summarization with question context
        prompt = f"""Given this technical question and its answer, please extract 2-3 key sentences from the answer that best capture the main technical details. Do not rephrase or modify the extracted sentences.

Question: {question}
Answer: {answer}

Here are some examples:

Technical Q&A 1:
Q: When should OTA Requestors invoke the ApplyUpdateRequest command?
A: OTA Requestors should invoke the ApplyUpdateRequest command once they are ready to apply a previously downloaded Software Image. This command is part of the OTA update process and signals readiness for installation. The timing of invocation is critical for proper software updates.

Extracted key sentences:
OTA Requestors should invoke the ApplyUpdateRequest command once they are ready to apply a previously downloaded Software Image.

Technical Q&A 2:
Q: What does the 'WiFiSecurityBitmap' data type encode?
A: The 'WiFiSecurityBitmap' data type encodes the supported Wi-Fi security types present in the Security field of the WiFiInterfaceScanResultStruct. This bitmap allows devices to indicate which security protocols they support. The encoding ensures interoperability between different WiFi-capable Matter devices.

Extracted key sentences:
The 'WiFiSecurityBitmap' data type encodes the supported Wi-Fi security types present in the Security field of the WiFiInterfaceScanResultStruct.

Technical Q&A 3:
Q: How does the Matter protocol handle device commissioning?
A: The Matter protocol uses a multi-step commissioning flow that begins with device discovery using DNS-SD. The commissioner then establishes a secure PASE session with the commissionee using a setup code. After successful authentication, the commissioner provisions operational credentials and network configuration to the device.

Extracted key sentences:
The Matter protocol uses a multi-step commissioning flow that begins with device discovery using DNS-SD. The commissioner then establishes a secure PASE session with the commissionee using a setup code.

Technical Q&A 4:
Q: What is the purpose of the GroupKeyManagement cluster?
A: The GroupKeyManagement cluster is responsible for managing group keys used in Matter group communications. It maintains a list of GroupKeySet entries that contain the keys and associated metadata for each group. The cluster provides commands for adding, removing, and updating group keys to ensure secure multicast communication.

Extracted key sentences:
The GroupKeyManagement cluster is responsible for managing group keys used in Matter group communications. It maintains a list of GroupKeySet entries that contain the keys and associated metadata for each group.

Now, please extract 2-3 key sentences from this technical answer:
{answer}

output format: <answer> 
without any additional text such as:
- Based on the provided context
- the provided context
- from the provided context
- According to the provided context

Extracted key sentences:"""
        
        # Call OpenAI API with retries
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                break  # If successful, break the retry loop
            except Exception as api_error:
                if attempt == max_retries - 1:  # Last attempt
                    raise api_error  # Re-raise the last error if all retries failed
                tqdm.write(f"Retry {attempt + 1}/{max_retries} for trustii_id: {item['trustii_id']} - {str(api_error)}")
                time.sleep(retry_delay)  # Wait before retrying
        
        # Extract summary
        summary = response.choices[0].message.content.strip()
        
        return {
            "trustii_id": item['trustii_id'],
            "original_answer": answer,
            "summary": summary,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "trustii_id": item['trustii_id'],
            "error": str(e),
            "status": "error"
        }

def worker_init():
    """Initialize OpenAI client for each worker"""
    global client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def summarize_answers(json_file="combined_output_missed.json", num_workers=16):
    # Load combined JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summarized_data = []
    failed_items = []
    
    # Process items in parallel
    with ProcessPoolExecutor(max_workers=num_workers, initializer=worker_init) as executor:
        # Create progress bar
        with tqdm(total=len(data), desc="Processing answers") as pbar:
            # Submit all tasks
            futures = []
            for item in data:
                future = executor.submit(process_item, item)
                futures.append(future)
            
            # Process results as they complete
            for future in futures:
                result = future.result()
                if result['status'] == 'success':
                    summarized_data.append({
                        "trustii_id": result['trustii_id'],
                        "original_answer": result['original_answer'],
                        "summary": result['summary']
                    })
                    tqdm.write(f"✅ Processed trustii_id: {result['trustii_id']}")
                else:
                    failed_items.append({
                        "trustii_id": result['trustii_id'],
                        "error": result['error']
                    })
                    tqdm.write(f"❌ Failed trustii_id: {result['trustii_id']} - {result['error']}")
                
                # Save progress
                with open('summarized_answers.json', 'w', encoding='utf-8') as f:
                    json.dump(summarized_data, f, indent=2, ensure_ascii=False)
                
                if failed_items:
                    with open('failed_summaries.json', 'w', encoding='utf-8') as f:
                        json.dump(failed_items, f, indent=2, ensure_ascii=False)
                
                pbar.update(1)
    
    # Final stats
    tqdm.write(f"\n✅ Successfully processed: {len(summarized_data)} answers")
    tqdm.write(f"❌ Failed: {len(failed_items)} answers")
    tqdm.write("📁 Results saved to summarized_answers.json")
    if failed_items:
        tqdm.write("❗ Failed items saved to failed_summaries.json")

if __name__ == "__main__":
    # Make sure OPENAI_API_KEY is set in environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    summarize_answers(num_workers=48)