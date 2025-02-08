import requests
from bs4 import BeautifulSoup
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from urllib.parse import quote

client = boto3.client("bedrock-runtime", region_name="us-east-1")

load_dotenv()

serp_api_key = os.getenv("SERP_API_KEY")

def get_web_links(search_query):
    # URL-encode the query to handle spaces and special characters
    encoded_query = quote(search_query)
    search_url = f"https://google.serper.dev/search?q={encoded_query}&api_key={serp_api_key}"

    response = requests.get(search_url)
    
    if response.status_code == 200:
        results = response.json()
        # Debug: Uncomment the next line to inspect the JSON structure
        # print(json.dumps(results, indent=2))
        links = [result['link'] for result in results.get('organic', []) if 'link' in result]
        return links
    else:
        print(f"ERROR: Failed to retrieve search results. Status code: {response.status_code}")
        return []

MODEL_ID = "amazon.titan-text-premier-v1:0"
MAX_TOKENS = 500

def get_web_query(subject, purpose):
    search_query = f"Please generate a google search query that can find me websites about {subject} to {purpose}"
    native_request = {
        "inputText": search_query,
        "textGenerationConfig": {
            "maxTokenCount": MAX_TOKENS,
            "temperature": 0.5,
        },
    }

    request_payload = json.dumps(native_request)

    try:
        response = client.invoke_model(modelId=MODEL_ID, body=request_payload)
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        exit(1)
    
    model_response = json.loads(response["body"].read())
    response_text = model_response["results"][0]["outputText"]
    return response_text

def scrape_web_content(links):
    content_dict = {}
    for link in links:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                page_title = soup.title.string.strip() if soup.title and soup.title.string else link
                raw_data = soup.get_text(separator=" ", strip=True)
                content_dict[page_title] = (link, raw_data)
            else:
                print(f"WARNING: Unable to retrieve content from {link}. Status code: {response.status_code}")
        except Exception as e:
            print(f"ERROR: Exception occurred while scraping {link}: {e}")
    return content_dict

# Main execution
def webscrap(search_query):
    search_query = search_query
    #print("Search Query:", search_query)
    links = get_web_links(search_query)
    #print("Retrieved Links:", links)
    web_content = scrape_web_content(links)
    #print("Scraped Web Content:", web_content)
    return web_content
#print(webscrap("What is the trend in Apple's revenue and profit margins over the past five years, and how do they compare to industry benchmarks?"))
#print("Search Query:", search_query)
#search_query = "What is the trend in Apple's revenue and profit margins over the past five years, and how do they compare to industry benchmarks?"
#print("Search Query:", search_query)
#links = get_web_links(search_query)
#print("Retrieved Links:", links)
#web_content = scrape_web_content(links)
#print("Scraped Web Content:", web_content)

#scraped_content = scrape_web_content(links)
#for page_name, (url, raw_data) in scraped_content.items():
#    print(f"Page Name: {page_name}\nURL: {url}\nRaw Data: {raw_data[:100]}...\n")