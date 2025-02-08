import requests
from bs4 import BeautifulSoup
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

client = boto3.client("bedrock-runtime", region_name="us-east-1")

load_dotenv()

serp_api_key = os.getenv("SERP_API_KEY")

def get_web_links(search_query):
    search_url = f"https://serpapi.com/search.json?q={search_query}&api_key={serp_api_key}&num=3"

    response = requests.get(search_url)
    if response.status_code == 200:
        results = response.json()
        links = [result['link'] for result in results.get('organic_results', [])]
        return links
    else:
        print(f"ERROR: Failed to retrieve search results. Status code: {response.status_code}")
        return []

p

MODEL_ID = "amazon.titan-text-premier-v1:0"
MAX_TOKENS = 500
def get_web_query(subject, purpose):

    query = f"Please generate a google search query that can find me websites about {subject} to {purpose}"
    native_request = {
        "inputText": search_query,
        "textGenerationConfig": {
            "maxTokenCount": MAX_TOKENS,
            "temperature": 0.5,
        },
    }

    request = json.dumps(native_request)

    try:
        # Invoke the model with the request.
        response = client.invoke_model(modelId=MODEL_ID, body=request)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        exit(1)
    

    model_response = json.loads(response["body"].read())

    # Extract and print the response text.
    response_text = model_response["results"][0]["outputText"]

def scrape_web_content(links):
    content_dict = {}
    
    for link in links:
        response = requests.get(link)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_name = soup.title.string if soup.title else link
            raw_data = soup.get_text()
            content_dict[page_name] = (link, raw_data)
    
    return content_dict

subject = "Python programming"
purpose = "Learn to code"
search_query = get_web_query(subject, purpose)
print(search_query)
links = get_web_links(search_query)
print(links)
web_content = scrape_web_content(links)
print(web_content)
#scraped_content = scrape_web_content(links)
#for page_name, (url, raw_data) in scraped_content.items():
#    print(f"Page Name: {page_name}\nURL: {url}\nRaw Data: {raw_data[:100]}...\n")
