from pipeline import RAGPipeline
import pandas as pd
from tqdm import tqdm

if __name__ == "__main__":
    components_path = "/Users/benx13/code/rags/challenge/inference/components.yaml"
    
    try:
        # Read queries from test.csv
        data = pd.read_csv('test.csv')
        
        # Initialize pipeline once
        pipeline = RAGPipeline(components_path=components_path)
        results_list = []
        
        # Process rows sequentially with progress bar
        for _, row in tqdm(data.iterrows(), total=len(data), desc="Processing queries"):
            trustii_id = row['trustii_id']
            query = row['Query']
            
            try:
                # Only process if query is not empty
                if pd.isna(query) or str(query).strip() == '':
                    response = ''
                else:
                    result = pipeline.process(query)
                    # Extract response from results 
                    response = result.get(next(k for k in result.keys() if k.endswith('_response')), '')
                    if isinstance(response, dict):
                        response = response.get('response', '')
            except Exception as e:
                print(f"Error processing query {trustii_id}: {str(e)}")
                response = ''
            
            results_list.append({
                'trustii_id': trustii_id,
                'Query': query if not pd.isna(query) else '',
                'Response': response
            })
        
        # Convert results to dataframe and save
        results_df = pd.DataFrame(results_list)
        results_df.to_csv('submission1.csv', index=False)
        
    except KeyboardInterrupt:
        # Save current results on Ctrl+C
        if results_list:
            results_df = pd.DataFrame(results_list)
            results_df.to_csv('submission1.csv', index=False)
            print("\nSaved partial results to submission.csv")
        raise
