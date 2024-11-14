import pandas as pd
import json

# Read the JSON file with summaries
with open('summarized_answers.json', 'r') as f:
    summaries = json.load(f)

# Create DataFrame directly from the summaries
result_df = pd.DataFrame([
    {
        'trustii_id': item['trustii_id'],
        'Response': item['summary']
    }
    for item in summaries
    if 'trustii_id' in item and 'summary' in item
])

# Remove duplicates based on trustii_id, keep the first occurrence
result_df = result_df.drop_duplicates(subset=['trustii_id'])

# Save to new CSV
result_df.to_csv('train2_missing.csv', index=False)

print(f"Created train2.csv with {len(result_df)} rows")
