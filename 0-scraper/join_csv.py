import pandas as pd

# Read both CSV files
test_df = pd.read_csv('test.csv')
train2_df = pd.read_csv('train2_missing.csv')

# Merge the dataframes on trustii_id
# using left join to keep all rows from test.csv
merged_df = pd.merge(
    test_df,
    train2_df,
    on='trustii_id',
    how='left'
)

# Remove rows where Response is NaN (no summary available)
final_df = merged_df.dropna(subset=['Response'])

# Select only the columns we want
final_df = final_df[['trustii_id', 'Query', 'Response']]

# Save to new CSV
final_df.to_csv('final_train.csv', index=False)

print(f"Created final_train.csv with {len(final_df)} rows")
print(f"Dropped {len(test_df) - len(final_df)} rows due to missing summaries") 