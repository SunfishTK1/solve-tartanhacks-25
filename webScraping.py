import requests
from bs4 import BeautifulSoup
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

client = boto3.client("bedrock-runtime", region_name="us-east-1")

load_dotenv()

serp_api_key = os.getenv("SERP_API_KEY")
open_page_rank_api_key = os.getenv("OPEN_PAGE_RANK_API_KEY")

def merge_dict_lists(list1, list2, shared_key):
    # Create a dictionary from list2 for faster lookup
    lookup_dict = {d[shared_key]: d for d in list2}
    
    # Create the merged list
    merged_list = []
    
    # Iterate through list1 and merge with matching items from list2
    for item1 in list1:
        merged_dict = item1.copy()  # Create a copy of the first dictionary
        
        # If there's a matching item in list2, update the merged dictionary
        if item1[shared_key] in lookup_dict:
            merged_dict.update(lookup_dict[item1[shared_key]])
            
        merged_list.append(merged_dict)
    
    return merged_list

def trim_www(content_list):
    for item in content_list:
        if 'domain' in item:
            item['domain'] = item['domain'].replace('www.', '')
    return content_list


MAX_LINKS_PER_SEARCH = 5
def get_web_links(search_queries):
    links = []
    for i, query in enumerate(search_queries):

        search_url = f"https://serpapi.com/search.json?q={query}&api_key={serp_api_key}&num={MAX_LINKS_PER_SEARCH}"

        response = requests.get(search_url)
        if response.status_code == 200:
            results = response.json()
            cur_links = [result['link'] for result in results.get('organic_results', [])]
            links.extend(cur_links)
        else:
            print(f"ERROR: Failed to retrieve search results for {query}. Status code: {response.status_code}")
    
    return links

MODEL_ARN = "arn:aws:bedrock:us-east-1:585768144713:inference-profile/us.anthropic.claude-3-haiku-20240307-v1:0"
MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"
MAX_TOKENS = 100
MAX_SEARCHES = 10
def get_web_query(subject, purpose):

    query = f"""Please generate search queries about {subject} that have web content that I can scrape to {purpose}.
            Please output only the queries and nothing else, with the queries surrounded in quotation marks and comma separated. Produce a maximum of {MAX_SEARCHES} items."""
    
    inference_config = {
        "temperature": 0.7,       # Controls the creativity or randomness of the response
        "maxTokens": 200,         # Limits the number of tokens in the model's response
        "topP": 1.0,              # Top-p sampling for generating more natural responses
    }
    try:
        response = client.converse(
            modelId=MODEL_ARN,
            messages=[{"role": "user", "content": [{"text": query}]}],
            inferenceConfig=inference_config
        )

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke {MODEL_ARN}. Reason: {e}")
        exit(1)

    request_id = response['ResponseMetadata']['RequestId']
    search_queries = response['output']['message']['content'][0]['text'].split(",")
    stop_reason = response['stopReason']
    input_tokens = response['usage']['inputTokens']
    output_tokens = response['usage']['outputTokens']
    total_tokens = response['usage']['totalTokens']
    latency_ms = response['metrics']['latencyMs']


    # Extract and print the response text.
    return search_queries

CHAR_LIMIT = 200
def scrape_web_content(links, analytics=True):
    content_list = []
    
    for link in links:
        website_dict = {}
        response = requests.get(link)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_name = soup.title.string if soup.title else link
            raw_data = soup.get_text()[:CHAR_LIMIT]
            domain = urlparse(link).netloc

            website_dict['domain'] = domain
            website_dict['url'] = link
            website_dict['raw_data'] = raw_data
            content_list.append(website_dict)
    
    content_list = trim_www(content_list)
    
    if analytics:
        analytics_data = fetch_analytics_data(links)
        content_list = merge_dict_lists(content_list, analytics_data, 'domain')
    
    for item in content_list:
        if 'error' in item:
            del item['error']
        if 'status_code' in item:
            del item['status_code']
        if 'page_rank_integer' in item:
            item['page_authority_int'] = item.pop('page_rank_integer')
        if 'page_rank_decimal' in item:
            item['page_authority'] = item.pop('page_rank_decimal')
    
    return content_list


def fetch_analytics_data(links):
    domains = [trim_www(urlparse(link).netloc) for link in links]
    domains_param = "&".join([f"domains[]={domain}" for domain in domains])
    url = f"https://openpagerank.com/api/v1.0/getPageRank?{domains_param}"
    headers = {"API-OPR": open_page_rank_api_key}

    response = requests.get(url, headers=headers)

    analytics_data = []
    
    if response.status_code == 200:
        data = response.json()
        if "response" in data and data["response"]:
            analytics_data = data["response"]
        else:
            return {"error": "Invalid response structure"}
    else:
        return {"error": f"Failed to retrieve data. Status code: {response.status_code}"}
    
    unique_domains = set()
    unique_analytics_data = []

    for entry in analytics_data:
        domain = entry.get('domain')
        if domain and domain not in unique_domains:
            unique_domains.add(domain)
            unique_analytics_data.append(entry)
        
    return unique_analytics_data


def generate_queries(subject, purpose, logging=False):
    search_queries = get_web_query(subject, purpose)
    if logging:
        print(f"Queries: {search_queries}\n\n")

    return search_queries

def webscrape(queries, logging=False):
    links = get_web_links(queries)
    if logging:
        print(f"Links: {links}\n\n")
    web_content = scrape_web_content(links)
    if logging:
        print(f"Content: {web_content}\n\n")
    
    return web_content