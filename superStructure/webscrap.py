import requests
from bs4 import BeautifulSoup
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from urllib.parse import quote

import logging
import time

client = boto3.client("bedrock-runtime", region_name="us-east-1")

load_dotenv()

serp_api_key = os.getenv("SERP_API_KEY")

MAX_SCRAPE_CHARS = 20000
MAX_RETRIES = 1          # Maximum number of retries per page.
RETRY_DELAY = 0.1          # Seconds to wait between retries.

def get_web_links(search_query):
    """
    Uses Serper.dev to retrieve a list of web links for the search query.
    """
    # URL-encode the query to handle spaces and special characters.
    encoded_query = quote(search_query)
    search_url = f"https://google.serper.dev/search?q={encoded_query}&api_key={serp_api_key}"
    
    response = requests.get(search_url)
    if response.status_code == 200:
        results = response.json()
        # Uncomment the next line to inspect the JSON structure.
        # print(json.dumps(results, indent=2))
        links = [result['link'] for result in results.get('organic', []) if 'link' in result]
        return links
    else:
        logging.error(f"ERROR: Failed to retrieve search results. Status code: {response.status_code}")
        return []

AWS_REGION = "us-east-1"
MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
MAX_TOKENS = 512


def get_optimized_query(search_query):
    """
    Enhances a search query for more accurate Google search results using the Converse API.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    
    system_prompt = [
        {"text": "Improve the following search query to yield more accurate Google search results."}
    ]
    
    conversation = [
        {"role": "user", "content": [{"text": search_query}]}
    ]
    
    try:
        response = client.converse(
            modelId=MODEL_ID,
            messages=conversation,
            system=system_prompt,
            inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.5, "topP": 0.9},
        )
        optimized_query = response["output"]["message"]["content"][0]["text"]
        logging.info("Optimized query generated successfully.")
    except Exception as e:
        logging.error(f"ERROR: Failed to fetch optimized query. Reason: {e}")
        return search_query  # Fallback to the original query
    
    return optimized_query

def scrape_web_content(links, max_chars=MAX_SCRAPE_CHARS):
    """
    Scrapes web content from the provided list of links.
    Attempts to scrape each link up to MAX_RETRIES times.
    Limits the scraped text to max_chars per webpage.
    """
    content_dict = {}
    for link in links[:3]:  # Limit to the first 5 links.
        success = False
        attempts = 0
        while attempts < MAX_RETRIES and not success:
            try:
                logging.info(f"Scraping {link} (Attempt {attempts + 1}/{MAX_RETRIES})...")
                response = requests.get(link, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_title = soup.title.string.strip() if soup.title and soup.title.string else link
                    raw_data = soup.get_text(separator=" ", strip=True)
                    limited_data = raw_data[:max_chars]
                    content_dict[page_title] = (link, limited_data)
                    success = True  # Mark as successful.
                else:
                    logging.warning(f"WARNING: Unable to retrieve content from {link}. Status code: {response.status_code}")
                    attempts += 1
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                attempts += 1
                logging.error(f"ERROR: Exception occurred while scraping {link}: {e}. Attempt {attempts} of {MAX_RETRIES}")
                time.sleep(RETRY_DELAY)
        if not success:
            logging.error(f"Failed to scrape {link} after {MAX_RETRIES} attempts. Moving on.")
    return content_dict

# Main execution
def webscrap(search_query):
    #optimized_query = get_optimized_query(search_query)
    links = get_web_links(search_query)
    web_content = scrape_web_content(links)  # Uses default MAX_SCRAPE_CHARS limit.
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