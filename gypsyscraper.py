# script to download all file linked in a page and its subpages keeping the url of the page as 
# the name of the destination folder
#

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
DEBUG=False
# the starting url from where to start recursively download files
STARTING_URL='https://www.comune.rivadelgarda.tn.it/Aree-tematiche/Edilizia-e-Urbanistica/URBANISTICA/PRG/Piano-Regolatore-Generale'
# starting path where store files on local filesystem
STARTING_PATH="scraped"
# included path for files that are linked outside 
INCLUDE=['content',]
# strings to remove from destination folder names (usually pagination stuffs)
REMOVE_FROM_FOLDERNAME=['(offset)',]

def is_external(url):
    res = urlparse(url).netloc and urlparse(url).netloc != urlparse(STARTING_URL).netloc
    if res and DEBUG: print(f"Skip as external {url}")
    return res

def is_parent_link(url):

    res = not (STARTING_URL in url)
    if res and DEBUG:print(f"Skip as parent {url}")    
    #return urlparse(link).path.count('/') <= urlparse(base_url).path.count('/')
    
    return res

def is_included(url,include):
    for item in include:
        if item in url:
            return True
    return False

def download_file(url,base_url):

    link_text = urlparse(url)
    base_name = os.path.basename(link_text.path)
    dir = urlparse(base_url)
    dir = dir.path[1:]

    local_filename = base_name.replace('/', '_')  # Replace slashes to avoid directory issues
    response = requests.get(url, stream=True)


    dest_path = os.path.join(STARTING_PATH,dir)

    for remove in REMOVE_FROM_FOLDERNAME:
        dest_path.replace(remove,'')

    os.makedirs(dest_path, exist_ok=True)

    dest_path = os.path.join(dest_path,local_filename)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {dest_path}")
    else:
        print(f"Failed to download: {url} (Status code: {response.status_code})")

def scrape_links(base_url, depth=0, max_depth=3,include_urls=['']):
    if depth > max_depth:
        return

    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {base_url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    


    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)
        
        # Skip external and parent links
        if( is_external(full_url) or is_parent_link(full_url) and not is_included(full_url, include_urls) ) :
            continue

        if href.endswith(('.pdf', '.zip', '.jpg', '.png', '.txt', '.docx', '.xlsx')):  # You can add more file types
            #print(f"${full_url} + ${base_url}")
            download_file(full_url,base_url)
        else:
            # Recursively scrape deeper links
            scrape_links(full_url, depth + 1, max_depth,include_urls)

if __name__ == "__main__":
            
    max_depth = 10
    scrape_links(STARTING_URL, max_depth=max_depth,include_urls=INCLUDE)