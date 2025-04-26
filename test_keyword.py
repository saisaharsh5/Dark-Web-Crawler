import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def search_onion_links(keyword):
    search_engines = [
        {
            'name': 'Ahmia',
            'html_url': f"https://ahmia.fi/search/?q={keyword}"
        },
        {
            'name': 'Onion.Live',
            'html_url': f"https://onion.live/search?q={keyword}"
        },
        {
            'name': 'Torch',
            'html_url': f"http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/cgi-bin/omega/omega?q={keyword}",
            'requires_tor': True
        }
    ]

    headers = {"User-Agent": "Mozilla/5.0"}
    tor_proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    all_results = []

    for engine in search_engines:
        try:
            proxies = tor_proxies if engine.get('requires_tor', False) else None
            response = requests.get(engine['html_url'], headers=headers, proxies=proxies, timeout=30)

            if response.status_code != 200:
                print(f"Skipping {engine['name']} (status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            if engine['name'] == 'Ahmia':
                results = [(a.text.strip(), a['href']) for a in soup.find_all("a", href=True) if ".onion" in a['href']]
            elif engine['name'] == 'Onion.Live':
                results = [(a.text.strip(), a['href']) for a in soup.select("a") if ".onion" in a['href']]
            elif engine['name'] == 'Torch':
                results = [(a.text.strip(), a['href']) for a in soup.select("a") if ".onion" in a['href']]
            else:
                results = []

            all_results.extend(results)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {engine['name']}: {e}")

    return clean_onion_links(all_results)

def clean_onion_links(onion_links):
    cleaned_links = []
    for title, link in onion_links:
        match = re.search(r"redirect_url=(http[s]?://[^\s]+)", link)
        if match:
            link = match.group(1)
        cleaned_links.append((title, link))

    unique_links = list(set(cleaned_links))
    df_cleaned = pd.DataFrame(unique_links, columns=["Title", "Onion Link"])
    return df_cleaned

# Example usage
results = search_onion_links("Bitcoin")
if results is not None:
    print(results)
