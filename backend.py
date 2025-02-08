import json
import requests

def run_query(api_key, search_query, input_data):
    url = "https://bedrock.aws.amazon.com/chatgpt/o3"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "query": search_query,
        "data": input_data
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

# Example usage
api_key = "your_api_key_here"
search_query = "example query"
input_data = {"key": "value"}

result = run_query(api_key, search_query, input_data)
print(json.dumps(result, indent=2))

def create_evaluation_graph(api_key, query):
    initial_questions = [
        "What is the business model?",
        "What is the target market?",
        "What are the revenue streams?",
        "What are the costs involved?",
        "What is the competitive landscape?"
    ]

    nodes = []
    adjacency_list = {}

    node_num = 0
    for question in initial_questions:
        nodes.append({"id": node_num, "question": question, "answers": []})
        adjacency_list[i] = []
        node_num += 1

    # Make a query to Bedrock to generate a list of questions
    response = run_query(api_key, query, {"questions": initial_questions})

    if "error" in response:
        return response

    generated_questions = response.get("generated_questions", [])

    for question in generated_questions:
        nodes.append({"id": node_num, "question": question, "answers": []})
        adjacency_list[i] = []
        node_num += 1

    # Link questions together to form the graph
    for i in range(1, len(nodes)):
        adjacency_list[i].append(i + 1)

    graph = {
        "nodes": nodes,
        "adjacency_list": adjacency_list
    }

    return graph

# Example usage
api_key = "your_api_key_here"
evaluation_query = "Evaluate the business potential of a new tech startup"
evaluation_graph = create_evaluation_graph(api_key, evaluation_query)
print(json.dumps(evaluation_graph, indent=2))