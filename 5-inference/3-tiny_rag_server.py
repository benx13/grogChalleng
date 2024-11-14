from flask import Flask, request, jsonify
from pipeline import RAGPipeline

app = Flask(__name__)
pipeline = RAGPipeline(components_path='5-inference/components.yaml')

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('query')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        result = pipeline.process(question)
        response = result['Response Output-1_response']
        
        return jsonify({'answer': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)

