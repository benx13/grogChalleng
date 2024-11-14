from neo4j import GraphDatabase
from pprint import pprint

class GraphRetriever:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.query2 = """
        CALL {
        CALL db.index.fulltext.queryRelationships("relationshipIndex",  $prompt) 
        YIELD relationship, score
        RETURN relationship, score, type(relationship) AS type
        }
        WITH collect({relationship: relationship, type: type, score: score}) AS results
        UNWIND results AS result
        WITH results, result
        ORDER BY result.score DESC
        LIMIT 40
        WITH collect(result) AS sortedResults, max(result.score) AS maxScore

        // Calculate the average score
        UNWIND sortedResults AS result
        WITH sortedResults, maxScore, result
        WITH sortedResults, maxScore, avg(result.score) AS avgScore

        // Calculate the standard deviation
        UNWIND sortedResults AS result
        WITH sortedResults, maxScore, avgScore, result
        WITH sortedResults, maxScore, avgScore,
            sqrt(avg((result.score - avgScore)^2)) AS stdDev

        // Determine the cluster threshold - More lenient (e.g., 2*stdDev)
        WITH sortedResults, maxScore, avgScore, stdDev,
            maxScore - 2*stdDev AS clusterThreshold

        // Apply a more lenient threshold filter
        UNWIND sortedResults AS result
        WITH result, maxScore, clusterThreshold
        WHERE result.score >= clusterThreshold

        RETURN 
            startNode(result.relationship).name AS startNodeName,
            endNode(result.relationship).name AS endNodeName,
            result.relationship.description AS relationshipDescription,
            type(result.relationship) AS relationshipType,
            result.score AS score,
            maxScore,
            result.score / maxScore AS relativeScore,
            clusterThreshold
        ORDER BY result.score DESC;
        """
        self.query1 = """
        CALL {
        CALL db.index.fulltext.queryNodes("nodeIndex", $prompt) YIELD node, score
        RETURN node, score, "node" as type
        }
        WITH collect({node: node, type: type, score: score}) as results
        UNWIND results as result
        WITH results, result
        ORDER BY result.score DESC
        LIMIT 40
        WITH collect(result) as sortedResults, max(result.score) as maxScore

        // Calculate the average score
        UNWIND sortedResults as result
        WITH sortedResults, maxScore, result
        WITH sortedResults, maxScore, avg(result.score) as avgScore

        // Calculate the standard deviation
        UNWIND sortedResults as result
        WITH sortedResults, maxScore, avgScore, result
        WITH sortedResults, maxScore, avgScore,
            sqrt(avg((result.score - avgScore)^2)) as stdDev

        // Determine the cluster threshold
        WITH sortedResults, maxScore, avgScore, stdDev,
            maxScore - 1*stdDev as clusterThreshold

        // Now unwind and apply the threshold filter
        UNWIND sortedResults as result
        WITH result, maxScore, avgScore, stdDev, clusterThreshold
        WHERE result.score >= clusterThreshold  // Apply the threshold filter

        RETURN 
            result.node.name as name,
            result.node.description as description,
            result.score as score,
            maxScore,
            result.score / maxScore as relativeScore,
            clusterThreshold
        ORDER BY result.score DESC
            
        """
    def close(self):
        if self.driver:
            self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def safe_get(self, obj, key, default=''):
        """Safely get a value from a dictionary or object."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        try:
            return getattr(obj, key, default)
        except:
            return default

    def process_node(self, node):
        """Process a node and return a tuple of its properties."""
        return (
            self.safe_get(node, 'name'),
            self.safe_get(node, 'labeled'),
            self.safe_get(node, 'description')
        )

    def invoke(self, input_prompt):
        try:
            # Run both queries
            parameters = {"prompt": f"{input_prompt}"}
            results1 = self.run_query(self.query1, parameters=parameters)
            results2 = self.run_query(self.query2, parameters=parameters)

            nodes = set()
            relations = set()
            context = []

            # Process results from the first query (nodes)
            for result in results1:
                if result.get('name') and result.get('description'):
                    nodes.add((
                        result['name'],
                        '',  # labeled field is empty for direct node queries
                        result['description']
                    ))

            # Process results from the second query (relationships)
            for result in results2:
                if result.get('startNodeName') and result.get('endNodeName'):
                    # Add both nodes involved in the relationship
                    nodes.add((result['startNodeName'], '', ''))
                    nodes.add((result['endNodeName'], '', ''))
                    
                    # Add the relationship if it exists
                    if result.get('relationshipDescription'):
                        relations.add(result['relationshipDescription'])

            # Format the output
            if nodes:
                #context.append('*** Nodes:')
                for name, labeled, description in nodes:
                    if description:
                        context.append(f"Node: {name} --> {description}")
                    else:
                        context.append(f"{name}")
                    #context.append('-----')
                #context.append('\n')
                
            if relations:
                context.append('*** Relationships')
                for relation in relations:
                    context.append(relation)
                    #context.append('-----')

            return {
                'context': context
            }

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            print(traceback.format_exc())
            return {'context': f"Error occurred: {str(e)}"}

        finally:
            # Close the connection
            if isinstance(self, GraphRetriever):
                self.close()

if __name__ == "__main__":
        # Neo4j connection details
    uri = "bolt://localhost:7689"  # Update with your Neo4j URI
    user = "neo4j"  # Update with your username
    password = "strongpassword"  # Update with your password



    # Create a Neo4j connection
    retriever = GraphRetriever(uri, user, password)



    context = retriever.invoke('Sigma2 Key (S2K)')

    print('##########################################################')
    print('##########################################################')
    print('##########################################################')

    # print(context['context'])
    for i in context['context']:
        print(i)






