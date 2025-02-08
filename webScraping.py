import requests
from bs4 import BeautifulSoup

def get_web_links(search_query):
    api_url = "https://api.bedrock.com/search"
    params = {
        'query': search_query,
        'format': 'json'
    }
    
    response = requests.get(api_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        links = [item['link'] for item in data['results']]
        return links
    else:
        return []

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

search_query = "Python programming"
links = get_web_links(search_query)
scraped_content = scrape_web_content(links)
for page_name, (url, raw_data) in scraped_content.items():
    print(f"Page Name: {page_name}\nURL: {url}\nRaw Data: {raw_data[:100]}...\n")