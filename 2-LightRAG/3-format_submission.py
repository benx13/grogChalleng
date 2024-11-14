import pandas as pd

# Read the CSV files
submissions = pd.read_csv('/Users/benx13/code/rags/challenge/LightRAG/submission_enriched____.csv')
test_queries = pd.read_csv('test.csv')

# Merge the dataframes on trustii_id
merged_df = pd.merge(
    test_queries,
    submissions,
    on='trustii_id',
    how='inner'
)

# Reorder columns if needed
merged_df = merged_df[['trustii_id', 'Query', 'Response']]

# Save the merged result
merged_df.to_csv('merged_results__33X.csv', index=False)
